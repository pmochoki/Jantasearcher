from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _parse_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class ScraperConfig:
    linkedin_email: str
    linkedin_password: str
    job_title: str
    location: str
    experience_level: str
    date_posted: str
    max_pages: int
    delay_min_seconds: int
    delay_max_seconds: int
    headless: bool
    public_mode: bool
    eu_job_locations: tuple[str, ...]
    scholarship_keywords: tuple[str, ...]
    exclude_locations: tuple[str, ...]

    @staticmethod
    def from_env() -> "ScraperConfig":
        return ScraperConfig(
            linkedin_email=os.getenv("LINKEDIN_EMAIL", ""),
            linkedin_password=os.getenv("LINKEDIN_PASSWORD", ""),
            job_title=os.getenv("JOB_SEARCH_TITLE", "Mechatronics Engineer"),
            location=os.getenv("JOB_SEARCH_LOCATION", "European Union"),
            experience_level=os.getenv("JOB_SEARCH_EXPERIENCE_LEVEL", "entry"),
            date_posted=os.getenv("JOB_SEARCH_DATE_POSTED", "past_month"),
            max_pages=int(os.getenv("SCRAPER_MAX_PAGES", "3")),
            delay_min_seconds=int(os.getenv("SCRAPER_DELAY_MIN", "3")),
            delay_max_seconds=int(os.getenv("SCRAPER_DELAY_MAX", "15")),
            headless=os.getenv("SCRAPER_HEADLESS", "true").lower() == "true",
            public_mode=os.getenv("SCRAPER_PUBLIC_MODE", "false").lower() == "true",
            eu_job_locations=tuple(
                _parse_csv(
                    os.getenv(
                        "EU_JOB_LOCATIONS",
                        "Germany,Netherlands,Sweden,Austria,Denmark,Ireland,Belgium,"
                        "Czech Republic,Poland,Portugal,Spain,Italy,France,Finland,Switzerland",
                    )
                )
            ),
            scholarship_keywords=tuple(
                _parse_csv(
                    os.getenv(
                        "SCHOLARSHIP_SEARCH_KEYWORDS",
                        "mechatronics masters scholarship,robotics graduate scholarship,"
                        "engineering master funding Europe,Erasmus Mundus mechatronics,"
                        "DAAD scholarship engineering",
                    )
                )
            ),
            exclude_locations=tuple(
                _parse_csv(os.getenv("EXCLUDE_LOCATIONS", "Hungary,Budapest"))
            ),
        )

    def with_overrides(self, **kwargs: object) -> "ScraperConfig":
        return replace(self, **kwargs)

    def location_is_excluded(self, location: str) -> bool:
        normalized = location.lower()
        return any(excluded.lower() in normalized for excluded in self.exclude_locations)

    def validate(self) -> None:
        if self.public_mode:
            self.validate_scrape_only()
            return
        if not self.linkedin_email or not self.linkedin_password:
            raise ValueError(
                "Missing LINKEDIN_EMAIL or LINKEDIN_PASSWORD in .env "
                "(or set SCRAPER_PUBLIC_MODE=true for guest search)"
            )
        self.validate_scrape_only()

    def validate_scrape_only(self) -> None:
        if self.delay_min_seconds < 1 or self.delay_max_seconds < self.delay_min_seconds:
            raise ValueError("Invalid scraper delay range")
        if self.max_pages < 1:
            raise ValueError("SCRAPER_MAX_PAGES must be >= 1")


def review_before_submit() -> bool:
    """Default ON: pause before final ATS submit for manual approval."""
    return os.getenv("REVIEW_BEFORE_SUBMIT", "true").lower() != "false"
