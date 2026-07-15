"""Job status transition rules and history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database.models import JobStatus

ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    "new": {"queued", "skipped", "failed", "needs_answer"},
    "queued": {"applied", "failed", "needs_answer", "skipped", "new"},
    "needs_answer": {"queued", "skipped", "failed", "new"},
    "failed": {"new", "queued", "skipped"},
    "skipped": {"new", "queued"},
    "applied": {"failed", "skipped"},
}


def can_transition(current: JobStatus, new_status: JobStatus) -> bool:
    if current == new_status:
        return True
    return new_status in ALLOWED_TRANSITIONS.get(current, set())


def append_status_history(
    metadata: dict[str, Any],
    *,
    from_status: JobStatus,
    to_status: JobStatus,
    reason: str | None = None,
) -> dict[str, Any]:
    history = list(metadata.get("status_history") or [])
    history.append(
        {
            "from": from_status,
            "to": to_status,
            "at": datetime.now(timezone.utc).isoformat(),
            "reason": reason or "",
        }
    )
    updated = dict(metadata)
    updated["status_history"] = history[-20:]
    updated["last_status_change_at"] = history[-1]["at"]
    return updated
