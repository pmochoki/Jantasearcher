"""Map Europe location names to EURES ISO country codes."""

from __future__ import annotations

from scraper.europe_locations import EUROPE_JOB_LOCATIONS

NAME_TO_EURES: dict[str, str] = {
    "Albania": "al",
    "Andorra": "ad",
    "Austria": "at",
    "Belarus": "by",
    "Belgium": "be",
    "Bosnia and Herzegovina": "ba",
    "Bulgaria": "bg",
    "Croatia": "hr",
    "Cyprus": "cy",
    "Czech Republic": "cz",
    "Denmark": "dk",
    "Estonia": "ee",
    "Finland": "fi",
    "France": "fr",
    "Germany": "de",
    "Greece": "gr",
    "Hungary": "hu",
    "Budapest": "hu",
    "Iceland": "is",
    "Ireland": "ie",
    "Italy": "it",
    "Kosovo": "xk",
    "Latvia": "lv",
    "Liechtenstein": "li",
    "Lithuania": "lt",
    "Luxembourg": "lu",
    "Malta": "mt",
    "Moldova": "md",
    "Monaco": "mc",
    "Montenegro": "me",
    "Netherlands": "nl",
    "North Macedonia": "mk",
    "Norway": "no",
    "Poland": "pl",
    "Portugal": "pt",
    "Romania": "ro",
    "San Marino": "sm",
    "Serbia": "rs",
    "Slovakia": "sk",
    "Slovenia": "si",
    "Spain": "es",
    "Sweden": "se",
    "Switzerland": "ch",
    "Turkey": "tr",
    "Ukraine": "ua",
    "United Kingdom": "uk",
}


def eures_codes_for_locations(locations: tuple[str, ...] | list[str]) -> list[str]:
    codes: list[str] = []
    seen: set[str] = set()
    for name in locations:
        code = NAME_TO_EURES.get(name)
        if code and code not in seen:
            seen.add(code)
            codes.append(code)
    return codes


def all_eures_codes() -> list[str]:
    return eures_codes_for_locations(EUROPE_JOB_LOCATIONS)
