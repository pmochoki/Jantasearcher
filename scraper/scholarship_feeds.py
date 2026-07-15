"""Scholarship RSS/HTML feeds — MSc funding across Europe."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from xml.etree import ElementTree

import httpx

from database.jobs import save_scraped_jobs
from notifications.telegram import notify_scrape_complete
from scraper.config import ScraperConfig
from scraper.models import ScrapedJob

FEEDS: tuple[tuple[str, str], ...] = (
    ("scholarshipdb", "https://scholarshipdb.net/rss/scholarships.xml"),
    ("opportunitydesk", "https://opportunitydesk.org/feed/"),
)


@dataclass
class ScholarshipFeedResult:
    found: int
    inserted: int
    message: str


def _parse_rss(xml_text: str, source: str) -> list[ScrapedJob]:
    jobs: list[ScrapedJob] = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return jobs

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or item.findtext("{http://purl.org/rss/1.0/}description") or "")
        desc = re.sub(r"<[^>]+>", " ", desc).strip()
        if not title or not link:
            continue
        hay = f"{title} {desc}".lower()
        if not any(
            k in hay
            for k in (
                "scholarship",
                "master",
                "masters",
                "msc",
                "funding",
                "grant",
                "stipend",
                "erasmus",
                "daad",
                "engineering",
                "mechatronics",
                "robotics",
            )
        ):
            continue
        jobs.append(
            ScrapedJob(
                title=title[:500],
                company="Scholarship feed",
                location="Europe",
                description=desc[:8000],
                linkedin_url="",
                external_apply_url=link,
                is_easy_apply=False,
                source=source,
                metadata={"opportunity_type": "scholarship", "scrape_source": source},
            )
        )
    return jobs


def run_scholarship_feeds_sync(cfg: ScraperConfig) -> dict:
    cfg.validate_scrape_only()
    scraped: list[ScrapedJob] = []
    for source, url in FEEDS:
        try:
            resp = httpx.get(url, timeout=25.0, follow_redirects=True)
            if resp.status_code == 200:
                scraped.extend(_parse_rss(resp.text, source))
        except httpx.HTTPError:
            continue

    inserted = save_scraped_jobs(scraped, default_source="other").inserted
    notify_scrape_complete(
        found=len(scraped),
        inserted=inserted,
        skipped_easy_apply=0,
        captcha=False,
        source="Scholarship feeds",
    )
    return asdict(
        ScholarshipFeedResult(
            found=len(scraped),
            inserted=inserted,
            message=f"Scholarship feeds: {inserted} new listings",
        )
    )
