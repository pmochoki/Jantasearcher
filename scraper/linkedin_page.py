"""Shared LinkedIn page detection helpers."""

from __future__ import annotations


async def detect_captcha(page) -> bool:
    body_text = (await page.content()).lower()
    return (
        "captcha" in body_text
        or "security verification" in body_text
        or "let's do a quick security check" in body_text
        or "checkpoint" in page.url.lower()
    )


async def session_looks_authenticated(page) -> bool:
    if await page.locator("#username").count() > 0:
        return False
    url = page.url.lower()
    return "feed" in url or "/jobs" in url or "mynetwork" in url
