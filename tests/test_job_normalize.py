from __future__ import annotations

from datetime import date

from scraper.config import ScraperConfig
from scraper.models import ScrapedJob
from scraper.normalize import extract_source_job_id, normalize_source, scraped_to_job_insert


def test_normalize_source_collapses_api_boards():
    assert normalize_source("eures") == "other"
    assert normalize_source("adzuna") == "other"
    assert normalize_source("linkedin_eu") == "linkedin"
    assert normalize_source("profession_hu") == "profession_hu"


def test_extract_source_job_id():
    meta = {"scrape_source": "adzuna", "adzuna_id": "12345"}
    assert extract_source_job_id("adzuna", meta) == "12345"


def test_scraped_to_job_insert_strips_html_and_sets_metadata():
    cfg = ScraperConfig.from_env()
    scraped = ScrapedJob(
        title="Mechatronics Engineer",
        company="ACME",
        location="Budapest, Hungary",
        description="<p>Robotics and <b>automation</b> role</p>",
        linkedin_url="",
        external_apply_url="https://example.com/apply",
        is_easy_apply=False,
        posted_date=date(2026, 1, 15),
        source="adzuna",
        metadata={
            "scrape_source": "adzuna",
            "adzuna_id": "99",
            "search_title": "Mechatronics Engineer",
            "search_location": "Hungary",
        },
    )
    job = scraped_to_job_insert(scraped, cfg, default_source="adzuna")
    assert job is not None
    assert job.source == "other"
    assert job.source_job_id == "99"
    assert "automation" in (job.description or "")
    assert "<p>" not in (job.description or "")
    assert job.metadata["scrape_source"] == "adzuna"


def test_scraped_to_job_insert_excludes_blocked_location():
    cfg = ScraperConfig.from_env().with_overrides(exclude_locations=("United Kingdom",))
    scraped = ScrapedJob(
        title="Mechatronics Engineer",
        company="ACME",
        location="London, United Kingdom",
        description="robotics engineer graduate",
        linkedin_url="",
        external_apply_url="https://example.com/apply",
        is_easy_apply=False,
        source="eures",
        metadata={"scrape_source": "eures", "eures_id": "abc"},
    )
    assert scraped_to_job_insert(scraped, cfg, default_source="eures") is None
