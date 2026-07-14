"""Plain-text cleanup for scraped HTML descriptions."""

from __future__ import annotations

import html
import re


_TAG_RE = re.compile(r"<[^>]+>")
_BLOCK_BREAKS = re.compile(r"</(?:p|div|li|br|h[1-6]|tr)>|(?:<br\s*/?>)", re.I)
_WS_RE = re.compile(r"[ \t]+\n|\n[ \t]+|[ \t]{2,}")


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities to readable plain text."""
    if not text:
        return ""
    normalized = _BLOCK_BREAKS.sub("\n", text)
    normalized = _TAG_RE.sub(" ", normalized)
    normalized = html.unescape(normalized)
    normalized = _WS_RE.sub(" ", normalized)
    lines = [line.strip() for line in normalized.splitlines()]
    return "\n".join(line for line in lines if line).strip()
