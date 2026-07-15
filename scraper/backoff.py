"""Exponential backoff helpers for scraper auth and retries."""

from __future__ import annotations


def backoff_seconds(
    attempt: int,
    *,
    base: float = 60.0,
    cap: float = 3600.0,
) -> float:
    """Seconds to wait after `attempt` consecutive failures (1-based)."""
    if attempt < 1:
        return 0.0
    return min(base * (2 ** (attempt - 1)), cap)


def scale_delay_max(base_max: float, failures: int, *, factor: float = 0.5) -> float:
    """Stretch human delay upper bound after auth failures."""
    if failures <= 0:
        return base_max
    return base_max * (1.0 + failures * factor)
