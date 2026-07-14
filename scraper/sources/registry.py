"""Catalog of all job and scholarship discovery sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SourceSpec:
    id: str
    name: str
    kind: str  # jobs | scholarships | both
    description: str
    requires_playwright: bool
    automation_key: str | None  # state.last_* field suffix


JOB_SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec("linkedin_eu", "LinkedIn (all Europe)", "jobs", "Logged-in EU+Hungary search", True, "eu"),
    SourceSpec("eures", "EURES (EU official)", "jobs", "European Employment Services API", False, "eures"),
    SourceSpec("arbeitnow", "Arbeitnow", "jobs", "EU/DE job board API", False, "arbeitnow"),
    SourceSpec("remoteok", "RemoteOK", "jobs", "Remote engineer roles worldwide", False, "remoteok"),
    SourceSpec("profession_hu", "profession.hu", "jobs", "Hungary — Playwright", True, "profession"),
    SourceSpec("indeed_eu", "Indeed Europe", "jobs", "Playwright — may need CAPTCHA", True, "indeed"),
)

SCHOLARSHIP_SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec("linkedin_scholarship", "LinkedIn scholarships", "scholarships", "Keyword search all Europe", True, "scholarships"),
    SourceSpec("scholarship_feeds", "Scholarship feeds", "scholarships", "RSS/HTML aggregators", False, "scholarship_feeds"),
)

ALL_SOURCES = JOB_SOURCES + SCHOLARSHIP_SOURCES


def source_ids() -> list[str]:
    return [s.id for s in ALL_SOURCES]
