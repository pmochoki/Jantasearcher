"""Indeed Europe — Playwright search (optional; may hit CAPTCHA)."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from database.jobs import save_scraped_jobs
from notifications.telegram import notify_scrape_complete, send_telegram_message
from scraper.config import ScraperConfig
from scraper.models import ScrapedJob
from scraper.relevance import is_relevant_listing

INDEED_DOMAINS = (
    ("hu", "Hungary"),
    ("de", "Germany"),
    ("at", "Austria"),
    ("nl", "Netherlands"),
)


@dataclass
class IndeedResult:
    found: int
    inserted: int
    message: str
    captcha: bool


async def _scrape_indeed(cfg: ScraperConfig) -> IndeedResult:
    cfg.validate_scrape_only()
    title = cfg.job_search_titles()[0]
    scraped: list[ScrapedJob] = []
    captcha = False

    from scraper.hungary_focus import hungary_focus_enabled

    domains = (("hu", "Hungary"), ("de", "Germany")) if hungary_focus_enabled() else INDEED_DOMAINS[:2]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=cfg.headless, slow_mo=50)
        page = await browser.new_page()
        for tld, country in domains:
            url = (
                f"https://{tld}.indeed.com/jobs?q={quote_plus(title)}"
                f"&l={quote_plus(country)}&fromage=14"
            )
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                body = (await page.content()).lower()
                if "captcha" in body or "verify" in body:
                    captcha = True
                    break
                cards = page.locator(".job_seen_beacon, .jobsearch-SerpJobCard")
                n = min(await cards.count(), 15)
                for i in range(n):
                    card = cards.nth(i)
                    try:
                        t = (await card.locator("h2, .jobTitle").first.inner_text()).strip()
                        company = (await card.locator(".companyName").first.inner_text()).strip()
                        link_el = card.locator("h2 a, a.jcs-JobTitle").first
                        href = await link_el.get_attribute("href")
                        if not href:
                            continue
                        if href.startswith("/"):
                            href = f"https://{tld}.indeed.com{href}"
                        if not is_relevant_listing(title=t, description="", keywords=cfg.relevance_keywords):
                            continue
                        scraped.append(
                            ScrapedJob(
                                title=t,
                                company=company,
                                location=country,
                                description="",
                                linkedin_url="",
                                external_apply_url=href,
                                is_easy_apply=False,
                                source="indeed",
                                metadata={"scrape_source": "indeed", "country": country},
                            )
                        )
                    except Exception:
                        continue
            except Exception:
                continue
        await browser.close()

    inserted = save_scraped_jobs(scraped, default_source="indeed")
    notify_scrape_complete(
        found=len(scraped),
        inserted=inserted,
        skipped_easy_apply=0,
        captcha=captcha,
        source="Indeed EU",
    )
    return IndeedResult(
        found=len(scraped),
        inserted=inserted,
        message=f"Indeed EU: {inserted} jobs" + (" (CAPTCHA — partial)" if captcha else ""),
        captcha=captcha,
    )


def run_indeed_scraper_sync(cfg: ScraperConfig) -> dict:
    send_telegram_message("<b>ProjectEagle — Indeed EU scan started</b>")
    return asdict(asyncio.run(_scrape_indeed(cfg)))
