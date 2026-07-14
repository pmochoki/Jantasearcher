from __future__ import annotations

from typing import Any

from ai.client import get_claude_client, get_model

SYSTEM_PROMPT = """You summarize job and scholarship listings for a job seeker.

Rules:
- Use ONLY information from the listing text. Do not invent requirements, salary, or benefits.
- Write 3-5 short bullet points plus one line "Fit for you" only if the listing mentions mechatronics, automation, robotics, engineering, or graduate study.
- Keep under 180 words total.
- Output plain text bullets starting with "•", no markdown headers."""


def summarize_listing(
    *,
    title: str,
    company: str,
    location: str,
    description: str,
    opportunity_type: str = "job",
) -> str:
    """Generate a concise listing summary (cached by caller in job metadata)."""
    kind = "scholarship or funded programme" if opportunity_type == "scholarship" else "job"
    user_prompt = f"""Summarize this {kind} listing for quick review before applying.

Title: {title}
Organization: {company}
Location: {location}

Listing text:
{description[:12000]}

Format:
• What it is (role or programme)
• Key requirements or eligibility (only if stated)
• Location / work mode (only if stated)
• Application link action (apply externally / view on LinkedIn)
• Fit note (optional, only from listing keywords)"""

    client = get_claude_client()
    response = client.messages.create(
        model=get_model(),
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise RuntimeError("Claude returned no summary text")
    return text_blocks[0].strip()
