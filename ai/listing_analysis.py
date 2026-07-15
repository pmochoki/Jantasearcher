"""Claude analysis: summary, English listing text, and fit probability."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from ai.client import get_claude_client, get_model
from ai.text_utils import strip_html
from ai.usage import AiUsage, extract_usage

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)


@dataclass(frozen=True)
class ListingAnalysis:
    summary: str
    description_en: str
    fit_probability: int
    fit_rationale: str
    usage: AiUsage | None = None


def _clamp_percent(value: Any) -> int:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, n))


def _parse_analysis(
    raw: str,
    *,
    fallback_description: str,
    usage: AiUsage | None = None,
) -> ListingAnalysis:
    match = _JSON_BLOCK_RE.search(raw)
    if match:
        try:
            data = json.loads(match.group(0))
            return ListingAnalysis(
                summary=str(data.get("summary", "")).strip(),
                description_en=str(data.get("description_en", "")).strip() or fallback_description,
                fit_probability=_clamp_percent(data.get("fit_probability")),
                fit_rationale=str(data.get("fit_rationale", "")).strip(),
                usage=usage,
            )
        except json.JSONDecodeError:
            pass
    return ListingAnalysis(
        summary=raw.strip()[:2000],
        description_en=fallback_description,
        fit_probability=0,
        fit_rationale="Could not parse structured analysis.",
        usage=usage,
    )


def analyze_listing(
    *,
    profile: dict[str, Any],
    title: str,
    company: str,
    location: str,
    description: str,
    opportunity_type: str = "job",
) -> ListingAnalysis:
    """Summarize, translate to English, and estimate fit % for the signed-in user's profile."""
    plain = strip_html(description)
    if not plain.strip():
        plain = description.strip()

    contact = profile.get("contact") or {}
    applicant = {
        "name": contact.get("full_name"),
        "location": contact.get("location"),
        "summary": profile.get("summary"),
        "skills": profile.get("skills"),
        "education": profile.get("education"),
        "experience": profile.get("experience"),
        "projects": profile.get("projects"),
    }
    kind = "scholarship or funded programme" if opportunity_type == "scholarship" else "job"

    system = """You help a mechatronics engineering graduate review job and scholarship listings.

Rules:
- Use ONLY facts from the listing and the applicant profile JSON. Never invent credentials.
- fit_probability is 0-100: realistic chance THIS applicant gets an interview or offer (not generic job difficulty).
- description_en: full listing translated to clear English plain text (no HTML, no markdown).
- summary: 3-5 bullet lines starting with "•", under 150 words, English only.
- fit_rationale: one short English sentence explaining the percentage.
- Respond with ONLY valid JSON, no markdown fences:
{"fit_probability": 45, "fit_rationale": "...", "summary": "• ...\\n• ...", "description_en": "..."}"""

    user_prompt = f"""Analyze this {kind} for the applicant.

Listing title: {title}
Organization: {company}
Location: {location or "Not stated"}

Applicant profile (JSON):
{json.dumps(applicant, ensure_ascii=False)[:8000]}

Listing text (may be German or other language):
{plain[:14000]}"""

    client = get_claude_client()
    response = client.messages.create(
        model=get_model(),
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise RuntimeError("Claude returned no analysis text")

    fallback = plain[:12000]
    usage = extract_usage(response, operation="analyze_listing")
    return _parse_analysis(text_blocks[0], fallback_description=fallback, usage=usage)
