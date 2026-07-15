"""Per-source enable toggles from environment."""

from __future__ import annotations

import os


def _enabled(name: str, *, default: bool) -> bool:
    raw = os.getenv(f"{name}_ENABLED", str(default).lower())
    return raw.lower() in ("1", "true", "yes")


def eures_enabled() -> bool:
    return _enabled("EURES", default=True)


def arbeitnow_enabled() -> bool:
    return _enabled("ARBEITNOW", default=True)


def remoteok_enabled() -> bool:
    return _enabled("REMOTEOK", default=True)


def indeed_enabled() -> bool:
    return _enabled("INDEED", default=True)


def adzuna_enabled() -> bool:
    return _enabled("ADZUNA", default=False)


def adzuna_configured() -> bool:
    return bool(os.getenv("ADZUNA_APP_ID", "").strip() and os.getenv("ADZUNA_APP_KEY", "").strip())
