"""Priority score 0–100 for apply queue ordering."""

from __future__ import annotations

from datetime import date, datetime, timezone

from database.models import JobRecord, detect_ats_platform

_HIGH = (
    "mechatronics",
    "robotics",
    "automation",
    "control systems",
    "embedded",
    "mechanical engineer",
)
_MED = ("manufacturing", "firmware", "graduate", "engineer", "intern")
_SCHOLARSHIP = (
    "scholarship",
    "master",
    "masters",
    "msc",
    "stipend",
    "funding",
    "erasmus",
    "daad",
    "stipendium",
)


def compute_match_score(job: JobRecord) -> int:
    meta = job.metadata or {}
    title = (job.title or "").lower()
    desc = (job.description or "").lower()
    text = f"{title}\n{desc}"
    score = 0

    if meta.get("opportunity_type") == "scholarship":
        score += 40
        for kw in _SCHOLARSHIP:
            if kw in text:
                score += 8
    else:
        for kw in _HIGH:
            if kw in text:
                score += 12
        for kw in _MED:
            if kw in text:
                score += 5

    platform = job.ats_platform or detect_ats_platform(job.external_url or "")
    if platform in ("greenhouse", "lever"):
        score += 20
    elif platform in ("workday", "smartrecruiters"):
        score += 8

    loc = (job.location or "").lower()
    if any(x in loc for x in ("hungary", "budapest", "europe", "eu", "germany", "netherlands")):
        score += 10

    posted = job.posted_date
    if posted:
        age = (date.today() - posted).days
        if age <= 3:
            score += 15
        elif age <= 7:
            score += 10
        elif age <= 14:
            score += 5

    found = job.date_found
    if found:
        if found.tzinfo is None:
            found = found.replace(tzinfo=timezone.utc)
        hours = (datetime.now(timezone.utc) - found).total_seconds() / 3600
        if hours <= 48:
            score += 5

    return min(100, score)
