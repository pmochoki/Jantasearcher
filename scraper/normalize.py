"""Normalize scraped listings into JobInsert rows."""

from __future__ import annotations

from datetime import date
from typing import Any

from ai.text_utils import strip_html
from database.models import JobInsert, detect_ats_platform
from scraper.config import ScraperConfig
from scraper.models import ScrapedJob
from scraper.relevance import is_relevant_listing

_DB_SOURCES = {"linkedin", "profession_hu", "jobline_hu", "other"}

_SOURCE_ID_KEYS: dict[str, str] = {
    "eures": "eures_id",
    "adzuna": "adzuna_id",
    "remoteok": "remoteok_id",
    "arbeitnow": "arbeitnow_slug",
    "indeed": "indeed_id",
}


def normalize_source(source: str) -> str:
    if source in _DB_SOURCES:
        return source
    if source.startswith("linkedin"):
        return "linkedin"
    return "other"


def extract_source_job_id(scrape_source: str, metadata: dict[str, Any]) -> str | None:
    key = _SOURCE_ID_KEYS.get(scrape_source)
    if key:
        value = metadata.get(key)
        if value:
            return str(value)
    for meta_key in ("source_job_id", "eures_id", "adzuna_id", "remoteok_id", "arbeitnow_slug", "indeed_id"):
        value = metadata.get(meta_key)
        if value:
            return str(value)
    return None


def parse_posted_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def scraped_to_job_insert(
    scraped: ScrapedJob | Any,
    cfg: ScraperConfig,
    *,
    default_source: str = "linkedin",
    skip_relevance: bool = False,
) -> JobInsert | None:
    metadata = dict(getattr(scraped, "metadata", None) or {})
    scrape_source = getattr(scraped, "source", None) or default_source
    opportunity_type = metadata.get("opportunity_type")

    title = (getattr(scraped, "title", "") or "").strip()
    company = (getattr(scraped, "company", "") or "").strip() or "Unknown company"
    location = getattr(scraped, "location", "") or ""
    description = strip_html(getattr(scraped, "description", "") or "")[:8000]
    external_url = (getattr(scraped, "external_apply_url", "") or "").strip()

    if not title or not external_url:
        return None

    if cfg.location_is_excluded(location):
        return None

    if not skip_relevance and not is_relevant_listing(
        title=title,
        description=description,
        keywords=cfg.relevance_keywords,
        opportunity_type=opportunity_type,
    ):
        return None

    metadata.setdefault("linkedin_url", getattr(scraped, "linkedin_url", "") or "")
    metadata.setdefault("scrape_source", scrape_source)
    if metadata.get("search_title") is None and cfg.job_title:
        metadata.setdefault("search_title", cfg.job_title)
    if metadata.get("search_location") is None and cfg.location:
        metadata.setdefault("search_location", cfg.location)

    source_job_id = extract_source_job_id(scrape_source, metadata)
    posted_date = parse_posted_date(getattr(scraped, "posted_date", None) or metadata.get("posted_date"))

    return JobInsert(
        source=normalize_source(scrape_source),
        title=title,
        company=company,
        external_url=external_url,
        location=location or None,
        description=description or None,
        source_job_id=source_job_id,
        posted_date=posted_date,
        is_easy_apply=bool(getattr(scraped, "is_easy_apply", False)),
        ats_platform=detect_ats_platform(external_url),
        metadata=metadata,
    )
