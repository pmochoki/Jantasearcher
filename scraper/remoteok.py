"""RemoteOK — remote engineering roles (public API)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import httpx

from database.jobs import save_scraped_jobs
from notifications.telegram import notify_scrape_complete
from scraper.config import ScraperConfig
from scraper.models import ScrapedJob
from scraper.relevance import is_relevant_listing

API_URL = "https://remoteok.com/api"


@dataclass
class RemoteOkResult:
    found: int
    inserted: int
    message: str


def run_remoteok_scraper_sync(cfg: ScraperConfig) -> dict:
    cfg.validate_scrape_only()
    tags = "engineer,robotics,mechanical,embedded,automation"
    resp = httpx.get(API_URL, params={"tags": tags}, headers={"User-Agent": "ProjectEagle/1.0"}, timeout=30.0)
    resp.raise_for_status()
    raw = resp.json()
    if not isinstance(raw, list):
        raw = []

    scraped: list[ScrapedJob] = []
    for row in raw:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        title = row.get("position") or row.get("title") or ""
        desc = row.get("description") or ""
        if not is_relevant_listing(title=title, description=desc, keywords=cfg.relevance_keywords):
            continue
        url = row.get("url") or row.get("apply_url") or ""
        if not url:
            continue
        scraped.append(
            ScrapedJob(
                title=title,
                company=row.get("company") or "Unknown company",
                location=row.get("location") or "Remote",
                description=desc[:8000],
                linkedin_url="",
                external_apply_url=url,
                is_easy_apply=False,
                source="remoteok",
                metadata={
                    "scrape_source": "remoteok",
                    "remoteok_id": str(row.get("id")),
                    "tags": row.get("tags"),
                },
            )
        )

    inserted = save_scraped_jobs(scraped, default_source="remoteok").inserted
    notify_scrape_complete(
        found=len(scraped),
        inserted=inserted,
        skipped_easy_apply=0,
        captcha=False,
        source="RemoteOK",
    )
    return asdict(RemoteOkResult(found=len(scraped), inserted=inserted, message=f"RemoteOK: {inserted} new jobs"))
