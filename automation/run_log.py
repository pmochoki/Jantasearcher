"""Append structured run history to automation state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from automation.state import AutomationState


def append_run_log(
    state: AutomationState,
    kind: str,
    message: str,
    *,
    ok: bool = True,
    details: dict[str, Any] | None = None,
) -> AutomationState:
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "message": message,
        "ok": ok,
        "details": details or {},
    }
    history = list(getattr(state, "run_history", None) or [])
    history.insert(0, entry)
    state.run_history = history[:100]
    return state


def log_and_save(
    kind: str,
    message: str,
    *,
    ok: bool = True,
    details: dict[str, Any] | None = None,
) -> None:
    state = AutomationState.load()
    append_run_log(state, kind, message, ok=ok, details=details)
    state.save()
