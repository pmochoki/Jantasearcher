"""Permit deadline countdown and urgency-mode automation presets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)


@dataclass(frozen=True)
class UrgencyStatus:
    active: bool
    permit_deadline: str | None
    days_remaining: int | None
    weeks_remaining: int | None
    message: str
    recommended_action: str


def _timezone() -> ZoneInfo:
    name = os.getenv("DAILY_SUMMARY_TIMEZONE", "Europe/Budapest")
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def permit_deadline() -> date | None:
    raw = os.getenv("PERMIT_DEADLINE", "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def urgency_mode_active() -> bool:
    if os.getenv("URGENCY_MODE", "").lower() in ("1", "true", "yes"):
        return True
    dl = permit_deadline()
    if dl is None:
        return False
    return (dl - datetime.now(_timezone()).date()).days <= 120


def urgency_status() -> UrgencyStatus:
    dl = permit_deadline()
    active = urgency_mode_active()
    if not dl:
        return UrgencyStatus(
            active=active,
            permit_deadline=None,
            days_remaining=None,
            weeks_remaining=None,
            message="Set PERMIT_DEADLINE=YYYY-MM-DD in .env to track your job-seeking permit.",
            recommended_action="Add permit deadline and keep local backend running 24/7.",
        )

    days = (dl - datetime.now(_timezone()).date()).days
    weeks = max(0, days // 7)
    if days < 0:
        msg = f"Permit deadline passed {abs(days)} days ago — prioritize manual follow-ups."
    elif days <= 14:
        msg = f"CRITICAL: {days} days left on job-seeking permit ({dl.isoformat()})."
    elif days <= 90:
        msg = f"URGENT: {days} days ({weeks} weeks) until permit expires ({dl.isoformat()})."
    else:
        msg = f"{days} days until permit expires ({dl.isoformat()})."

    action = (
        "Urgency mode ON — faster scans, more applies/day, all Europe sources rotating."
        if active
        else "Set URGENCY_MODE=true for faster automation."
    )
    return UrgencyStatus(
        active=active,
        permit_deadline=dl.isoformat(),
        days_remaining=days,
        weeks_remaining=weeks,
        message=msg,
        recommended_action=action,
    )


def urgency_overrides() -> dict[str, int | float]:
    """Automation tuning when urgency mode is active."""
    if not urgency_mode_active():
        return {}
    return {
        "poll_minutes": int(os.getenv("URGENCY_POLL_MINUTES", "15")),
        "scrape_eu_interval_hours": float(os.getenv("URGENCY_SCRAPE_EU_HOURS", "2")),
        "scrape_scholarship_interval_hours": float(os.getenv("URGENCY_SCRAPE_SCHOLARSHIP_HOURS", "3")),
        "scrape_profession_interval_hours": float(os.getenv("URGENCY_SCRAPE_PROFESSION_HOURS", "3")),
        "scrape_extra_interval_hours": float(os.getenv("URGENCY_SCRAPE_EXTRA_HOURS", "4")),
        "scrape_hungary_interval_hours": float(os.getenv("URGENCY_HUNGARY_SCRAPE_HOURS", "1")),
        "locations_per_cycle": int(os.getenv("URGENCY_LOCATIONS_PER_CYCLE", "4")),
        "titles_per_cycle": int(os.getenv("URGENCY_TITLES_PER_CYCLE", "2")),
        "scholarship_keywords_per_cycle": int(os.getenv("URGENCY_SCHOLARSHIP_KEYWORDS_PER_CYCLE", "3")),
        "apply_max_per_day": int(os.getenv("URGENCY_APPLY_MAX_PER_DAY", "10")),
        "apply_min_interval_minutes": int(os.getenv("URGENCY_APPLY_MIN_INTERVAL_MINUTES", "25")),
        "linkedin_max_searches_per_cycle": int(
            os.getenv("URGENCY_LINKEDIN_MAX_SEARCHES_PER_CYCLE", "12")
        ),
        "linkedin_daily_search_cap": int(os.getenv("URGENCY_LINKEDIN_DAILY_SEARCH_CAP", "80")),
    }
