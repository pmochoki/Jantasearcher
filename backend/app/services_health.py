"""Aggregated health checks for dashboard service banner."""

from __future__ import annotations

import os
from typing import Any

from ai.client import ClaudeConfigError, get_claude_client, get_model
from database.client import SupabaseConfigError, get_supabase_client
from notifications.telegram_bot import telegram_bot_status
from scraper.config import ScraperConfig
from scraper.session import session_exists


def _service(
    *,
    ok: bool,
    detail: str = "",
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "detail": detail}
    payload.update(extra)
    return payload


def get_services_health() -> dict[str, Any]:
    """Public health snapshot — no auth required."""
    services: dict[str, dict[str, Any]] = {}

    # Supabase
    try:
        client = get_supabase_client()
        result = client.table("jobs").select("id", count="exact").limit(1).execute()
        services["supabase"] = _service(
            ok=True,
            detail="Connected",
            jobs_count=result.count,
        )
    except SupabaseConfigError as exc:
        services["supabase"] = _service(ok=False, detail=str(exc))
    except Exception as exc:
        services["supabase"] = _service(ok=False, detail=f"Query failed: {exc}")

    # Claude API key present
    try:
        get_claude_client()
        services["claude"] = _service(
            ok=True,
            detail="API key configured",
            model=get_model(),
        )
    except ClaudeConfigError as exc:
        services["claude"] = _service(ok=False, detail=str(exc), configured=False)
    else:
        services["claude"]["configured"] = True

    # LinkedIn session (local automation only on Vercel)
    on_vercel = bool(os.getenv("VERCEL"))
    cfg = ScraperConfig.from_env()
    if on_vercel:
        services["linkedin"] = _service(
            ok=True,
            detail="Scrapers run on your Mac — session not checked on Vercel",
            session_saved=False,
            local_only=True,
        )
    elif cfg.public_mode:
        services["linkedin"] = _service(
            ok=True,
            detail="Public/guest LinkedIn mode (SCRAPER_PUBLIC_MODE=true)",
            session_saved=False,
            public_mode=True,
        )
    elif session_exists():
        from automation.state import AutomationState
        from scraper.linkedin_auth import is_linkedin_auth_blocked

        state = AutomationState.load()
        blocked = is_linkedin_auth_blocked(state)
        detail = "Saved session found (data/linkedin_session.json)"
        if blocked:
            detail += f" — auth cooldown until {state.linkedin_auth_blocked_until[:19]} UTC"
        services["linkedin"] = _service(
            ok=not blocked,
            detail=detail,
            session_saved=True,
            auth_blocked=blocked,
            searches_today=state.linkedin_searches_today_count,
        )
    elif cfg.linkedin_email and cfg.linkedin_password:
        services["linkedin"] = _service(
            ok=True,
            detail="Credentials set — session will be created on first scrape",
            session_saved=False,
        )
    else:
        services["linkedin"] = _service(
            ok=False,
            detail="Set LINKEDIN_EMAIL/PASSWORD or SCRAPER_PUBLIC_MODE=true",
            session_saved=False,
        )

    # Telegram
    tg = telegram_bot_status()
    token_set = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
    chats_ok = bool(tg.get("configured"))
    if on_vercel:
        services["telegram"] = _service(
            ok=token_set and chats_ok,
            detail="Bot runs locally — "
            + (
                "token + chat ID set"
                if token_set and chats_ok
                else "set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID"
            ),
            local_only=True,
            thread_alive=False,
        )
    else:
        thread = bool(tg.get("bot_thread_alive"))
        services["telegram"] = _service(
            ok=token_set and chats_ok and thread,
            detail=(
                f"@{tg.get('bot_username')} polling"
                if thread and tg.get("bot_username")
                else tg.get("detail") or ("Polling active" if thread else "Bot not running")
            ),
            thread_alive=thread,
            token_configured=token_set,
        )

    # Automation host
    services["automation"] = _service(
        ok=not on_vercel or _automation_enabled(),
        detail=(
            "Runs on Vercel API only — start backend on Mac for 24/7 scans"
            if on_vercel
            else "Local automation available"
        ),
        vercel=on_vercel,
        enabled=_automation_enabled(),
    )

    critical_ok = services["supabase"]["ok"]
    return {
        "ok": critical_ok,
        "services": services,
        "host": "vercel" if on_vercel else "local",
    }


def _automation_enabled() -> bool:
    from automation.config import AutomationConfig

    return AutomationConfig.from_env().enabled


def probe_claude_live() -> dict[str, Any]:
    """Minimal live Claude call to verify the API key works."""
    from ai.client import get_claude_client, get_model

    client = get_claude_client()
    model = get_model()
    response = client.messages.create(
        model=model,
        max_tokens=32,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: ProjectEagle Claude OK",
            }
        ],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    usage = getattr(response, "usage", None)
    return {
        "ok": True,
        "model": model,
        "reply": text,
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
    }
