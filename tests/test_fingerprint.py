from __future__ import annotations

from scraper.fingerprint import compute_listing_fingerprint, normalize_external_url, normalize_listing_text


def test_normalize_listing_text():
    assert normalize_listing_text("  Mechatronics — Engineer! ") == "mechatronics engineer"


def test_normalize_external_url_strips_tracking():
    raw = "https://Example.com/jobs/123?utm_source=linkedin&id=abc"
    normalized = normalize_external_url(raw)
    assert "utm_source" not in normalized
    assert "example.com/jobs/123" in normalized


def test_fingerprint_stable_for_same_listing():
    kwargs = dict(
        company="ACME Robotics",
        title="Mechatronics Engineer",
        external_url="https://example.com/jobs/1?utm_medium=cpc",
    )
    assert compute_listing_fingerprint(**kwargs) == compute_listing_fingerprint(**kwargs)


def test_fingerprint_uses_source_id_when_present():
    fp1 = compute_listing_fingerprint(
        company="ACME",
        title="Engineer",
        external_url="https://example.com/1",
        source_job_id="abc-123",
        scrape_source="adzuna",
    )
    fp2 = compute_listing_fingerprint(
        company="Other Co",
        title="Different title",
        external_url="https://example.com/2",
        source_job_id="abc-123",
        scrape_source="adzuna",
    )
    assert fp1 == fp2
    fp3 = compute_listing_fingerprint(
        company="ACME",
        title="Engineer",
        external_url="https://example.com/1",
        source_job_id="other-id",
        scrape_source="adzuna",
    )
    assert fp1 != fp3
