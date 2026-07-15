"""Adzuna Jobs API — EU country search (requires free API key)."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import date
from urllib.parse import quote

import httpx

from database.jobs import save_scraped_jobs
from notifications.telegram import notify_scrape_complete, send_telegram_message
from scraper.config import ScraperConfig
from scraper.europe_country_codes import NAME_TO_EURES, eures_codes_for_locations
from scraper.hungary_focus import eures_country_batch
from scraper.models import ScrapedJob
from scraper.relevance import is_relevant_listing
from scraper.source_flags import adzuna_configured

API_BASE = "https://api.adzuna.com/v1/api/jobs"


@dataclass
class AdzunaResult:
    found: int
    inserted: int
    countries: list[str]
    message: str


def _where_for_country(cfg: ScraperConfig, country_code: str) -> str:
    if country_code == "hu":
        return cfg.hu_job_locations[0] if cfg.hu_job_locations else "Hungary"
    for name, code in NAME_TO_EURES.items():
        if code == country_code:
            return name
    return country_code.upper()


def _search(
    *,
    country: str,
    what: str,
    where: str,
    app_id: str,
    app_key: str,
    page: int = 1,
    results_per_page: int = 20,
) -> list[dict]:
    url = f"{API_BASE}/{quote(country)}/search/{page}"
    resp = httpx.get(
        url,
        params={
            "app_id": app_id,
            "app_key": app_key,
            "what": what,
            "where": where,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    payload = resp.json()
    rows = payload.get("results") or []
    return rows if isinstance(rows, list) else []


def _parse_created(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def run_adzuna_scraper_sync(cfg: ScraperConfig, *, country_batch_size: int = 3) -> dict:
    cfg.validate_scrape_only()
    app_id = os.getenv("ADZUNA_APP_ID", "").strip()
    app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
    if not adzuna_configured():
        return asdict(
            AdzunaResult(
                found=0,
                inserted=0,
                countries=[],
                message="Adzuna skipped — set ADZUNA_APP_ID and ADZUNA_APP_KEY",
            )
        )

    titles = list(cfg.job_search_titles())[:2]
    all_codes = eures_codes_for_locations(cfg.all_job_search_locations())
    default_country = os.getenv("ADZUNA_COUNTRY", "at").strip().lower() or "at"
    if not all_codes:
        all_codes = [default_country]

    offset = int(os.getenv("ADZUNA_COUNTRY_OFFSET", "0"))
    batch: list[str] = []
    for i in range(country_batch_size):
        batch.append(all_codes[(offset + i) % len(all_codes)])
    batch = eures_country_batch(cfg, batch)

    send_telegram_message(
        "<b>ProjectEagle — Adzuna scan started</b>\n"
        f"Countries: {', '.join(c.upper() for c in batch)}"
    )

    scraped: list[ScrapedJob] = []
    for country in batch:
        where = _where_for_country(cfg, country)
        for title in titles:
            try:
                rows = _search(
                    country=country,
                    what=title,
                    where=where,
                    app_id=app_id,
                    app_key=app_key,
                )
            except httpx.HTTPError:
                continue
            for row in rows:
                job_title = row.get("title") or ""
                desc = row.get("description") or ""
                if not is_relevant_listing(
                    title=job_title,
                    description=desc,
                    keywords=cfg.relevance_keywords,
                ):
                    continue
                redirect = row.get("redirect_url") or row.get("url") or ""
                if not redirect:
                    continue
                company = (row.get("company") or {}).get("display_name") or "Unknown company"
                location = (row.get("location") or {}).get("display_name") or where
                jid = row.get("id")
                scraped.append(
                    ScrapedJob(
                        title=job_title,
                        company=company,
                        location=location,
                        description=desc[:8000],
                        linkedin_url="",
                        external_apply_url=redirect,
                        is_easy_apply=False,
                        posted_date=_parse_created(row.get("created")),
                        source="adzuna",
                        metadata={
                            "scrape_source": "adzuna",
                            "adzuna_id": str(jid) if jid is not None else None,
                            "country": country,
                            "search_title": title,
                            "search_location": where,
                        },
                    )
                )

    inserted = save_scraped_jobs(scraped, default_source="adzuna").inserted
    notify_scrape_complete(
        found=len(scraped),
        inserted=inserted,
        skipped_easy_apply=0,
        captcha=False,
        source="Adzuna",
    )
    result = AdzunaResult(
        found=len(scraped),
        inserted=inserted,
        countries=batch,
        message=f"Adzuna: {inserted} new jobs saved.",
    )
    return asdict(result)
