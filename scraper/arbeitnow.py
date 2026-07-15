"""Arbeitnow.com — EU job board (public JSON API, no auth)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import httpx

from database.jobs import save_scraped_jobs
from notifications.telegram import notify_scrape_complete
from scraper.config import ScraperConfig
from scraper.models import ScrapedJob
from scraper.relevance import is_relevant_listing

API_URL = "https://www.arbeitnow.com/api/job-board-api"


@dataclass
class ArbeitnowResult:
    found: int
    inserted: int
    message: str


def run_arbeitnow_scraper_sync(cfg: ScraperConfig) -> dict:
    cfg.validate_scrape_only()
    resp = httpx.get(API_URL, timeout=30.0)
    resp.raise_for_status()
    rows = resp.json().get("data") or []

    scraped: list[ScrapedJob] = []
    for row in rows:
        title = row.get("title") or ""
        desc = row.get("description") or ""
        if not is_relevant_listing(
            title=title,
            description=desc,
            keywords=cfg.relevance_keywords,
        ):
            continue
        url = row.get("url") or ""
        if not url:
            continue
        slug = row.get("slug") or url.rstrip("/").split("/")[-1]
        scraped.append(
            ScrapedJob(
                title=title,
                company=row.get("company_name") or "Unknown company",
                location=row.get("location") or "Europe",
                description=desc[:8000],
                linkedin_url="",
                external_apply_url=url,
                is_easy_apply=False,
                source="arbeitnow",
                metadata={
                    "scrape_source": "arbeitnow",
                    "arbeitnow_slug": slug,
                    "remote": row.get("remote"),
                    "tags": row.get("tags"),
                },
            )
        )

    inserted = save_scraped_jobs(scraped, default_source="arbeitnow")
    notify_scrape_complete(
        found=len(scraped),
        inserted=inserted,
        skipped_easy_apply=0,
        captcha=False,
        source="Arbeitnow",
    )
    return asdict(ArbeitnowResult(found=len(scraped), inserted=inserted, message=f"Arbeitnow: {inserted} new jobs"))
