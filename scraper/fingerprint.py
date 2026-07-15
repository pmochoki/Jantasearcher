"""Stable listing fingerprints for deduplication."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_STRIP_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "mc_", "ref", "source")


def normalize_listing_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", (text or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_external_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return (url or "").strip().lower()
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not any(k.lower().startswith(prefix) for prefix in _STRIP_QUERY_PREFIXES)
    ]
    path = parsed.path.rstrip("/") or "/"
    normalized = parsed._replace(
        netloc=parsed.netloc.lower(),
        path=path,
        query=urlencode(sorted(query)),
        fragment="",
    )
    return urlunparse(normalized).lower()


def compute_listing_fingerprint(
    *,
    company: str,
    title: str,
    external_url: str,
    source_job_id: str | None = None,
    scrape_source: str | None = None,
) -> str:
    """Deterministic fingerprint for cross-source dedup within a user account."""
    if source_job_id and scrape_source:
        raw = f"{scrape_source}:{source_job_id}"
    elif source_job_id:
        raw = f"id:{source_job_id}"
    else:
        raw = "|".join(
            [
                normalize_listing_text(company),
                normalize_listing_text(title),
                normalize_external_url(external_url),
            ]
        )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
