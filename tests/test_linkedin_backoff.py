from __future__ import annotations

from datetime import datetime, timedelta, timezone

from automation.config import AutomationConfig
from automation.state import AutomationState
from scraper.backoff import backoff_seconds, scale_delay_max
from scraper.linkedin_auth import (
    clear_linkedin_auth_block,
    consume_linkedin_search,
    is_linkedin_auth_blocked,
    linkedin_scrape_allowed,
    record_linkedin_auth_failure,
)


def test_backoff_seconds_exponential():
    assert backoff_seconds(1, base=60, cap=3600) == 60
    assert backoff_seconds(2, base=60, cap=3600) == 120
    assert backoff_seconds(10, base=60, cap=3600) == 3600


def test_scale_delay_max():
    assert scale_delay_max(15.0, 0) == 15.0
    assert scale_delay_max(15.0, 2) == 30.0


def test_linkedin_auth_blocked_until_expires():
    state = AutomationState()
    state.linkedin_auth_blocked_until = (
        datetime.now(timezone.utc) - timedelta(seconds=30)
    ).isoformat()
    assert is_linkedin_auth_blocked(state) is False


def test_record_and_clear_auth_failure():
    state = AutomationState()
    record_linkedin_auth_failure(state, "captcha")
    assert state.linkedin_auth_failures == 1
    assert state.linkedin_auth_blocked_until
    clear_linkedin_auth_block(state)
    assert state.linkedin_auth_failures == 0
    assert state.linkedin_auth_blocked_until is None


def test_linkedin_search_caps():
    state = AutomationState()
    auto_cfg = AutomationConfig(
        enabled=True,
        poll_minutes=30,
        scrape_eu_interval_hours=6,
        scrape_scholarship_interval_hours=8,
        scrape_profession_interval_hours=12,
        scrape_extra_interval_hours=4,
        scrape_hungary_interval_hours=4,
        locations_per_cycle=2,
        titles_per_cycle=1,
        scholarship_keywords_per_cycle=2,
        apply_enabled=True,
        apply_max_per_day=6,
        apply_min_interval_minutes=45,
        timezone="Europe/Budapest",
        linkedin_max_searches_per_cycle=2,
        linkedin_daily_search_cap=5,
    )
    assert consume_linkedin_search(state, auto_cfg) is True
    assert consume_linkedin_search(state, auto_cfg) is True
    assert consume_linkedin_search(state, auto_cfg) is False

    allowed, _ = linkedin_scrape_allowed(state, auto_cfg)
    assert allowed is True
