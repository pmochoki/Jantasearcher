"""EURES (EU official job mobility portal) — public search API."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from urllib.parse import quote

import httpx

from database.jobs import save_scraped_jobs
from notifications.telegram import notify_scrape_complete, send_telegram_message
from scraper.config import ScraperConfig
from scraper.europe_country_codes import eures_codes_for_locations
from scraper.models import ScrapedJob

EURES_SEARCH = "https://europa.eu/eures/api/jv-searchengine/public/jv-search/search"


@dataclass
class EuresScrapeResult:
    found: int
    inserted: int
    countries: list[str]
    message: str


def _eures_detail_url(job_id: str) -> str:
    return f"https://europa.eu/eures/portal/jv-searchengine/jv-details/{quote(job_id, safe='')}"


def _search(keyword: str, country_codes: list[str], *, page: int = 1, per_page: int = 25) -> list[dict]:
    payload = {
        "resultsPerPage": per_page,
        "page": page,
        "sortSearch": "MOST_RECENT",
        "keywords": [{"keyword": keyword, "specificSearchCode": "EVERYWHERE"}],
        "occupationUris": [],
        "skillUris": [],
        "requiredExperienceCodes": [],
        "positionScheduleCodes": [],
        "sectorCodes": [],
        "educationAndQualificationLevelCodes": [],
        "positionOfferingCodes": [],
        "locationCodes": country_codes,
        "euresFlagCodes": [],
        "otherBenefitsCodes": [],
        "requiredLanguages": [],
        "sessionId": f"projecteagle-{uuid.uuid4().hex[:8]}",
        "requestLanguage": "en",
    }
    resp = httpx.post(EURES_SEARCH, json=payload, timeout=30.0)
    resp.raise_for_status()
    return resp.json().get("jvs") or []


def run_eures_scraper_sync(cfg: ScraperConfig, *, country_batch_size: int = 3) -> dict:
    cfg.validate_scrape_only()
    titles = list(cfg.job_search_titles())[:2]
    all_codes = eures_codes_for_locations(cfg.all_job_search_locations())
    # Rotate through countries in batches (automation passes offset via env hack — use all for manual)
    offset = int(__import__("os").getenv("EURES_COUNTRY_OFFSET", "0"))
    batch: list[str] = []
    for i in range(country_batch_size):
        if not all_codes:
            break
        batch.append(all_codes[(offset + i) % len(all_codes)])

    send_telegram_message(
        "<b>ProjectEagle — EURES scan started</b>\n"
        f"Countries: {', '.join(c.upper() for c in batch) or 'all EU'}"
    )

    scraped: list[ScrapedJob] = []
    for title in titles:
        for code in batch or [""]:
            codes = [code] if code else []
            try:
                rows = _search(title, codes)
            except httpx.HTTPError:
                continue
            for row in rows:
                jid = row.get("id") or ""
                en = (row.get("translations") or {}).get("en") or {}
                hu = (row.get("translations") or {}).get("hu") or {}
                t = en.get("title") or hu.get("title") or row.get("title") or "Unknown role"
                desc = en.get("description") or hu.get("description") or row.get("description") or ""
                employer = (row.get("employer") or {}).get("name") or "Unknown company"
                loc_map = row.get("locationMap") or {}
                loc = ", ".join(loc_map.keys()) if loc_map else code.upper()

                scraped.append(
                    ScrapedJob(
                        title=t,
                        company=employer,
                        location=loc,
                        description=desc[:8000],
                        linkedin_url="",
                        external_apply_url=_eures_detail_url(jid) if jid else "https://europa.eu/eures/",
                        is_easy_apply=False,
                        source="eures",
                        metadata={"eures_id": jid, "scrape_source": "eures"},
                    )
                )

    inserted = save_scraped_jobs(scraped, default_source="eures")
    notify_scrape_complete(
        found=len(scraped),
        inserted=inserted,
        skipped_easy_apply=0,
        captcha=False,
        source="EURES",
    )
    result = EuresScrapeResult(
        found=len(scraped),
        inserted=inserted,
        countries=batch,
        message=f"EURES: {inserted} new jobs saved.",
    )
    return asdict(result)
