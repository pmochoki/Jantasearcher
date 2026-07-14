"""Hungary-first job discovery — always scan HU while rotating the rest of Europe."""

from __future__ import annotations

import os

from scraper.config import ScraperConfig


def hungary_focus_enabled() -> bool:
    return os.getenv("HUNGARY_FOCUS", "true").lower() in ("1", "true", "yes")


def hu_location_set(cfg: ScraperConfig) -> set[str]:
    return {loc.lower() for loc in cfg.hu_job_locations}


def is_hungary_location(location: str | None) -> bool:
    if not location:
        return False
    loc = location.lower()
    return any(x in loc for x in ("hungary", "budapest", "magyar", "debrecen", "szeged", "győr", "gyor", "pecs", "pécs"))


def eu_locations_excluding_hungary(cfg: ScraperConfig) -> list[str]:
    """European locations for rotation — Hungary handled separately every cycle."""
    hu = hu_location_set(cfg)
    seen: set[str] = set()
    ordered: list[str] = []
    for loc in cfg.eu_job_locations:
        key = loc.lower()
        if key in hu or key in seen:
            continue
        seen.add(key)
        ordered.append(loc)
    return ordered


def merge_hungary_into_batch(cfg: ScraperConfig, locations: list[str]) -> list[str]:
    """Prepend HU locations to every LinkedIn / API batch."""
    if not hungary_focus_enabled():
        return locations
    seen: set[str] = set()
    merged: list[str] = []
    for loc in (*cfg.hu_job_locations, *locations):
        key = loc.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(loc)
    return merged


def eures_country_batch(cfg: ScraperConfig, batch: list[str]) -> list[str]:
    """Ensure Hungary (hu) is in every EURES country batch."""
    if not hungary_focus_enabled():
        return batch
    out = ["hu"]
    for code in batch:
        if code and code.lower() != "hu" and code not in out:
            out.append(code)
    return out[: max(len(batch), 1)]


def hungary_match_boost(job) -> int:
    """Extra apply-queue priority for Hungary listings."""
    if not hungary_focus_enabled():
        return 0
    boost = 0
    meta = job.metadata or {}
    if meta.get("scrape_source") == "profession_hu" or getattr(job, "source", "") == "profession_hu":
        boost += 20
    if is_hungary_location(getattr(job, "location", None)):
        boost += 25
    return boost
