from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass

from notifications.telegram import notify_scrape_complete, send_telegram_message
from scraper.config import ScraperConfig
from scraper.linkedin_scraper import run_scraper


@dataclass
class EuScrapeSummary:
    countries_searched: int
    total_found: int
    total_inserted: int
    total_skipped: int
    captcha_detected: bool
    auth_blocked: bool
    results: list[dict]
    message: str


async def run_eu_jobs_scraper(cfg: ScraperConfig) -> EuScrapeSummary:
    cfg.validate()

    results: list[dict] = []
    total_found = 0
    total_inserted = 0
    total_skipped = 0
    captcha_detected = False
    auth_blocked = False

    send_telegram_message(
        "<b>ProjectEagle — EU job scan started</b>\n"
        f"Role: {cfg.job_title}\n"
        f"Countries: {len(cfg.eu_job_locations)}"
    )

    for location in cfg.eu_job_locations:
        if cfg.location_is_excluded(location):
            continue

        loc_cfg = cfg.with_overrides(location=location, max_pages=min(cfg.max_pages, 2))
        result = await run_scraper(loc_cfg, source="linkedin_eu")
        results.append(asdict(result))
        total_found += result.found
        total_inserted += result.inserted
        total_skipped += result.skipped_easy_apply
        captcha_detected = captcha_detected or result.captcha_detected
        auth_blocked = auth_blocked or result.auth_blocked

        if result.auth_blocked:
            break

    msg = f"EU scan finished. {total_inserted} new jobs saved across {len(results)} searches."
    if auth_blocked:
        msg = "EU scan stopped — LinkedIn needs manual verification. Check Telegram for steps."
    elif captcha_detected:
        msg = "EU scan partial — CAPTCHA hit. Complete verification on your phone, then retry."

    notify_scrape_complete(
        found=total_found,
        inserted=total_inserted,
        skipped_easy_apply=total_skipped,
        captcha=captcha_detected or auth_blocked,
        source="EU LinkedIn",
    )

    return EuScrapeSummary(
        countries_searched=len(results),
        total_found=total_found,
        total_inserted=total_inserted,
        total_skipped=total_skipped,
        captcha_detected=captcha_detected,
        auth_blocked=auth_blocked,
        results=results,
        message=msg,
    )


def run_eu_jobs_scraper_sync(cfg: ScraperConfig) -> dict:
    summary = asyncio.run(run_eu_jobs_scraper(cfg))
    return asdict(summary)
