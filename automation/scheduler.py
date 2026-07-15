from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone

from automation.apply_batch import maybe_apply_one
from automation.config import AutomationConfig
from automation.state import AutomationState
from notifications.telegram import send_telegram_message
from scraper.config import ScraperConfig
from scraper.hungary_focus import (
    eu_locations_excluding_hungary,
    eures_country_batch,
    hungary_focus_enabled,
    merge_hungary_into_batch,
)

logger = logging.getLogger(__name__)

_thread: threading.Thread | None = None
_stop = threading.Event()


def _hours_since(iso_ts: str | None) -> float | None:
    if not iso_ts:
        return None
    try:
        then = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - then).total_seconds() / 3600
    except ValueError:
        return None


def _rotate(items: list[str], start_index: int, count: int) -> tuple[list[str], int]:
    if not items:
        return [], 0
    picked: list[str] = []
    idx = start_index % len(items)
    for _ in range(min(count, len(items))):
        picked.append(items[idx])
        idx = (idx + 1) % len(items)
    return picked, idx


async def _linkedin_preflight(
    scraper_cfg: ScraperConfig,
    auto_cfg: AutomationConfig,
    state: AutomationState,
    *,
    batch_label: str,
) -> str | None:
    """Return skip message when LinkedIn should not run this batch."""
    from scraper.linkedin_auth import canary_before_scrape, linkedin_scrape_allowed

    allowed, block_msg = linkedin_scrape_allowed(state, auto_cfg)
    if not allowed:
        return block_msg

    if canary_before_scrape():
        from notifications.telegram import notify_canary_failure
        from scraper.canary import run_linkedin_canary

        canary = await run_linkedin_canary(scraper_cfg)
        if not canary.ok:
            notify_canary_failure("linkedin", canary.message)
            return f"{batch_label} skipped — LinkedIn DOM canary failed"
    return None


async def _run_linkedin_search(
    scraper_cfg: ScraperConfig,
    auto_cfg: AutomationConfig,
    state: AutomationState,
    loc_cfg: ScraperConfig,
    **kwargs,
):
    from scraper.linkedin_auth import consume_linkedin_search
    from scraper.linkedin_scraper import run_scraper

    if not consume_linkedin_search(state, auto_cfg):
        return None
    return await run_scraper(loc_cfg, **kwargs)


async def _run_eu_batch(scraper_cfg: ScraperConfig, auto_cfg: AutomationConfig, state: AutomationState) -> str:
    skip = await _linkedin_preflight(scraper_cfg, auto_cfg, state, batch_label="EU batch")
    if skip:
        state.last_eu_message = skip
        return skip

    eu_only = eu_locations_excluding_hungary(scraper_cfg)
    loc_batch, next_loc = _rotate(eu_only, state.eu_location_index, auto_cfg.locations_per_cycle)
    loc_batch = merge_hungary_into_batch(scraper_cfg, loc_batch)
    titles = list(scraper_cfg.job_search_titles())
    title_batch, next_title = _rotate(titles, state.eu_title_index, auto_cfg.titles_per_cycle)

    total_inserted = 0
    auth_blocked = False
    cap_hit = False
    for title in title_batch:
        for location in loc_batch:
            loc_cfg = scraper_cfg.with_overrides(
                job_title=title,
                location=location,
                max_pages=min(scraper_cfg.max_pages, 2),
            )
            result = await _run_linkedin_search(
                scraper_cfg, auto_cfg, state, loc_cfg, source="linkedin_eu"
            )
            if result is None:
                cap_hit = True
                break
            total_inserted += result.inserted
            if result.auth_blocked:
                auth_blocked = True
                break
        if auth_blocked or cap_hit:
            break

    state.eu_location_index = next_loc
    state.eu_title_index = next_title
    state.last_eu_scrape_at = datetime.now(timezone.utc).isoformat()
    msg = (
        f"EU batch: {total_inserted} new jobs "
        f"({', '.join(title_batch)} in {', '.join(loc_batch)})"
    )
    if auth_blocked:
        msg = "EU batch stopped — LinkedIn verification needed on your phone."
    elif cap_hit:
        msg = f"EU batch stopped — LinkedIn search cap ({auto_cfg.linkedin_max_searches_per_cycle}/cycle)."
    state.last_eu_message = msg
    return msg


async def _run_hungary_batch(scraper_cfg: ScraperConfig, auto_cfg: AutomationConfig, state: AutomationState) -> str:
    """Dedicated Hungary LinkedIn pass — all HU locations × multiple titles."""
    skip = await _linkedin_preflight(scraper_cfg, auto_cfg, state, batch_label="Hungary batch")
    if skip:
        state.last_hungary_message = skip
        return skip

    hu_locs = list(scraper_cfg.hu_job_locations) or ["Hungary", "Budapest"]
    titles = list(scraper_cfg.job_search_titles())
    title_count = min(len(titles), max(auto_cfg.titles_per_cycle * 2, 3))
    title_batch, next_ht = _rotate(titles, state.hungary_title_index, title_count)

    total_inserted = 0
    auth_blocked = False
    cap_hit = False

    for title in title_batch:
        for location in hu_locs:
            loc_cfg = scraper_cfg.with_overrides(
                job_title=title,
                location=location,
                max_pages=min(scraper_cfg.max_pages, 3),
            )
            result = await _run_linkedin_search(
                scraper_cfg, auto_cfg, state, loc_cfg, source="linkedin_eu"
            )
            if result is None:
                cap_hit = True
                break
            total_inserted += result.inserted
            if result.auth_blocked:
                auth_blocked = True
                break
        if auth_blocked or cap_hit:
            break

    state.hungary_title_index = next_ht
    state.last_hungary_scrape_at = datetime.now(timezone.utc).isoformat()
    msg = (
        f"Hungary batch: {total_inserted} new jobs "
        f"({', '.join(title_batch)} in {', '.join(hu_locs)})"
    )
    if auth_blocked:
        msg = "Hungary batch stopped — LinkedIn verification needed on your phone."
    elif cap_hit:
        msg = f"Hungary batch stopped — LinkedIn search cap ({auto_cfg.linkedin_max_searches_per_cycle}/cycle)."
    state.last_hungary_message = msg
    return msg


async def _run_scholarship_batch(
    scraper_cfg: ScraperConfig, auto_cfg: AutomationConfig, state: AutomationState
) -> str:
    skip = await _linkedin_preflight(scraper_cfg, auto_cfg, state, batch_label="Scholarship batch")
    if skip:
        state.last_scholarship_message = skip
        return skip

    keywords = list(scraper_cfg.scholarship_keywords)
    kw_batch, next_kw = _rotate(
        keywords, state.scholarship_keyword_index, auto_cfg.scholarship_keywords_per_cycle
    )
    if hungary_focus_enabled():
        loc_batch = list(scraper_cfg.hu_job_locations) or ["Hungary"]
        next_loc = state.scholarship_location_index
    else:
        locations = list(scraper_cfg.scholarship_search_locations())
        loc_batch, next_loc = _rotate(locations, state.scholarship_location_index, 1)

    total_inserted = 0
    auth_blocked = False
    cap_hit = False

    for keyword in kw_batch:
        for location in loc_batch:
            kw_cfg = scraper_cfg.with_overrides(
                job_title=keyword,
                location=location,
                max_pages=min(scraper_cfg.max_pages, 2),
            )
            result = await _run_linkedin_search(
                scraper_cfg,
                auto_cfg,
                state,
                kw_cfg,
                require_external_apply=False,
                source="linkedin_scholarship",
                opportunity_type="scholarship",
            )
            if result is None:
                cap_hit = True
                break
            total_inserted += result.inserted
            if result.auth_blocked:
                auth_blocked = True
                break
        if auth_blocked or cap_hit:
            break

    state.scholarship_keyword_index = next_kw
    state.scholarship_location_index = next_loc
    state.last_scholarship_scrape_at = datetime.now(timezone.utc).isoformat()
    msg = f"Scholarship batch: {total_inserted} new listings ({', '.join(kw_batch)} @ {loc_batch[0] if loc_batch else 'EU'})"
    if auth_blocked:
        msg = "Scholarship batch stopped — LinkedIn verification needed."
    elif cap_hit:
        msg = f"Scholarship batch stopped — LinkedIn search cap ({auto_cfg.linkedin_max_searches_per_cycle}/cycle)."
    state.last_scholarship_message = msg
    return msg


def run_automation_cycle(*, force_eu: bool = False, force_scholarships: bool = False, force_apply: bool = False) -> dict:
    """Run one automation cycle (EU scrape, scholarships, profession.hu, apply)."""
    import asyncio

    from scraper.linkedin_auth import reset_linkedin_cycle_search_count

    auto_cfg = AutomationConfig.from_env()
    scraper_cfg = ScraperConfig.from_env()
    state = AutomationState.load()
    reset_linkedin_cycle_search_count(state)
    results: dict[str, str] = {}

    try:
        eu_due = force_eu or _hours_since(state.last_eu_scrape_at) is None or _hours_since(
            state.last_eu_scrape_at
        ) >= auto_cfg.scrape_eu_interval_hours
        if eu_due:
            results["eu"] = asyncio.run(_run_eu_batch(scraper_cfg, auto_cfg, state))

        hu_due = hungary_focus_enabled() and (
            _hours_since(state.last_hungary_scrape_at) is None
            or _hours_since(state.last_hungary_scrape_at) >= auto_cfg.scrape_hungary_interval_hours
        )
        if hu_due:
            results["hungary"] = asyncio.run(_run_hungary_batch(scraper_cfg, auto_cfg, state))

        sch_due = force_scholarships or _hours_since(state.last_scholarship_scrape_at) is None or _hours_since(
            state.last_scholarship_scrape_at
        ) >= auto_cfg.scrape_scholarship_interval_hours
        if sch_due:
            results["scholarships"] = asyncio.run(
                _run_scholarship_batch(scraper_cfg, auto_cfg, state)
            )

        prof_due = _hours_since(state.last_profession_scrape_at) is None or _hours_since(
            state.last_profession_scrape_at
        ) >= auto_cfg.scrape_profession_interval_hours
        if prof_due:
            from scraper.profession_hu import run_profession_scraper_sync

            prof = run_profession_scraper_sync(scraper_cfg)
            state.last_profession_scrape_at = datetime.now(timezone.utc).isoformat()
            results["profession"] = f"profession.hu: {prof.get('inserted', 0)} new jobs"

        extra_due = _hours_since(state.last_eures_scrape_at) is None or _hours_since(
            state.last_eures_scrape_at
        ) >= auto_cfg.scrape_extra_interval_hours
        if extra_due:
            import os

            from scraper.arbeitnow import run_arbeitnow_scraper_sync
            from scraper.eures import run_eures_scraper_sync
            from scraper.remoteok import run_remoteok_scraper_sync
            from scraper.scholarship_feeds import run_scholarship_feeds_sync
            from scraper.source_flags import (
                adzuna_configured,
                adzuna_enabled,
                arbeitnow_enabled,
                eures_enabled,
                indeed_enabled,
                remoteok_enabled,
            )

            if eures_enabled():
                os.environ["EURES_COUNTRY_OFFSET"] = str(state.eures_country_index)
                eures = run_eures_scraper_sync(scraper_cfg, country_batch_size=3)
                state.eures_country_index = (state.eures_country_index + 3) % max(
                    1, len(scraper_cfg.all_job_search_locations())
                )
                state.last_eures_scrape_at = datetime.now(timezone.utc).isoformat()
                results["eures"] = eures.get("message", "EURES done")
            else:
                results["eures"] = "EURES skipped (EURES_ENABLED=false)"

            if arbeitnow_enabled():
                arbeit = run_arbeitnow_scraper_sync(scraper_cfg)
                state.last_arbeitnow_scrape_at = datetime.now(timezone.utc).isoformat()
                results["arbeitnow"] = arbeit.get("message", "Arbeitnow done")
            else:
                results["arbeitnow"] = "Arbeitnow skipped (ARBEITNOW_ENABLED=false)"

            if remoteok_enabled():
                remote = run_remoteok_scraper_sync(scraper_cfg)
                state.last_remoteok_scrape_at = datetime.now(timezone.utc).isoformat()
                results["remoteok"] = remote.get("message", "RemoteOK done")
            else:
                results["remoteok"] = "RemoteOK skipped (REMOTEOK_ENABLED=false)"

            if adzuna_enabled() and adzuna_configured():
                from scraper.adzuna import run_adzuna_scraper_sync

                os.environ["ADZUNA_COUNTRY_OFFSET"] = str(state.adzuna_country_index)
                adzuna = run_adzuna_scraper_sync(scraper_cfg, country_batch_size=3)
                state.adzuna_country_index = (state.adzuna_country_index + 3) % max(
                    1, len(scraper_cfg.all_job_search_locations())
                )
                state.last_adzuna_scrape_at = datetime.now(timezone.utc).isoformat()
                results["adzuna"] = adzuna.get("message", "Adzuna done")
            elif adzuna_enabled():
                results["adzuna"] = "Adzuna skipped — set ADZUNA_APP_ID and ADZUNA_APP_KEY"
            else:
                results["adzuna"] = "Adzuna skipped (ADZUNA_ENABLED=false)"

            feeds = run_scholarship_feeds_sync(scraper_cfg)
            state.last_scholarship_feeds_scrape_at = datetime.now(timezone.utc).isoformat()
            results["scholarship_feeds"] = feeds.get("message", "Feeds done")

            # Indeed every 3rd extra cycle (heavier / CAPTCHA risk)
            state.extra_source_index += 1
            if indeed_enabled() and state.extra_source_index % 3 == 0:
                from scraper.indeed_eu import run_indeed_scraper_sync

                indeed = run_indeed_scraper_sync(scraper_cfg)
                state.last_indeed_scrape_at = datetime.now(timezone.utc).isoformat()
                results["indeed"] = indeed.get("message", "Indeed done")
            elif not indeed_enabled():
                results["indeed"] = "Indeed skipped (INDEED_ENABLED=false)"

        if force_apply or auto_cfg.apply_enabled:
            results["apply"] = maybe_apply_one(auto_cfg, state)

        state.cycles_completed += 1
        state.last_error = ""
        from automation.run_log import append_run_log

        append_run_log(
            state,
            "cycle",
            "Automation cycle completed",
            ok=not results.get("error"),
            details=results,
        )
    except Exception as exc:
        state.last_error = str(exc)
        results["error"] = str(exc)
        logger.exception("Automation cycle failed")
        from automation.run_log import append_run_log

        append_run_log(state, "cycle", str(exc), ok=False, details=results)
    finally:
        state.save()

    return {"ok": not results.get("error"), "results": results, "state": state}


def automation_status() -> dict:
    from automation.urgency import urgency_status

    auto_cfg = AutomationConfig.from_env()
    state = AutomationState.load()
    urg = urgency_status()
    return {
        "enabled": auto_cfg.enabled,
        "poll_minutes": auto_cfg.poll_minutes,
        "apply_enabled": auto_cfg.apply_enabled,
        "apply_max_per_day": auto_cfg.apply_max_per_day,
        "apply_min_interval_minutes": auto_cfg.apply_min_interval_minutes,
        "scrape_eu_interval_hours": auto_cfg.scrape_eu_interval_hours,
        "scrape_hungary_interval_hours": auto_cfg.scrape_hungary_interval_hours,
        "scrape_scholarship_interval_hours": auto_cfg.scrape_scholarship_interval_hours,
        "scrape_extra_interval_hours": auto_cfg.scrape_extra_interval_hours,
        "thread_alive": bool(_thread and _thread.is_alive()),
        "urgency": {
            "active": urg.active,
            "permit_deadline": urg.permit_deadline,
            "days_remaining": urg.days_remaining,
            "message": urg.message,
        },
        "state": state,
    }


def _loop() -> None:
    while not _stop.is_set():
        cfg = AutomationConfig.from_env()
        if cfg.enabled:
            summary = run_automation_cycle()
            if summary.get("results"):
                logger.info("Automation cycle: %s", summary["results"])
        _stop.wait(cfg.poll_minutes * 60)


def start_automation_background() -> None:
    global _thread
    from automation.urgency import urgency_status

    cfg = AutomationConfig.from_env()
    if not cfg.enabled:
        return
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="automation-scheduler", daemon=True)
    _thread.start()
    urg = urgency_status()
    mode = "URGENCY" if urg.active else "Normal"
    send_telegram_message(
        f"<b>ProjectEagle — Automation started ({mode})</b>\n"
        f"{urg.message}\n\n"
        f"Check cycle: every {cfg.poll_minutes} min\n"
        f"LinkedIn Europe: every {cfg.scrape_eu_interval_hours}h (+ Hungary every {cfg.scrape_hungary_interval_hours}h)\n"
        f"Scholarships: every {cfg.scrape_scholarship_interval_hours}h\n"
        f"EURES/Arbeitnow/RemoteOK/Adzuna/feeds: every {cfg.scrape_extra_interval_hours}h\n"
        f"Apply: up to {cfg.apply_max_per_day}/day, min {cfg.apply_min_interval_minutes} min apart\n"
        f"Sources: LinkedIn, EURES, Arbeitnow, RemoteOK, Adzuna, profession.hu, Indeed, scholarship feeds"
    )


def stop_automation() -> None:
    _stop.set()
