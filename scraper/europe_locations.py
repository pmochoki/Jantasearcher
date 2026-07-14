"""LinkedIn-friendly location names for job searches across Europe."""

from __future__ import annotations

# Sovereign states and common LinkedIn location labels — Hungary is searched first via HU_JOB_LOCATIONS.
EUROPE_JOB_LOCATIONS: tuple[str, ...] = (
    "Albania",
    "Andorra",
    "Austria",
    "Belarus",
    "Belgium",
    "Bosnia and Herzegovina",
    "Bulgaria",
    "Croatia",
    "Cyprus",
    "Czech Republic",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Iceland",
    "Ireland",
    "Italy",
    "Kosovo",
    "Latvia",
    "Liechtenstein",
    "Lithuania",
    "Luxembourg",
    "Malta",
    "Moldova",
    "Monaco",
    "Montenegro",
    "Netherlands",
    "North Macedonia",
    "Norway",
    "Poland",
    "Portugal",
    "Romania",
    "San Marino",
    "Serbia",
    "Slovakia",
    "Slovenia",
    "Spain",
    "Sweden",
    "Switzerland",
    "Turkey",
    "Ukraine",
    "United Kingdom",
)

# Scholarships: same countries plus broad EU label for LinkedIn keyword searches.
EUROPE_SCHOLARSHIP_LOCATIONS: tuple[str, ...] = ("European Union",) + EUROPE_JOB_LOCATIONS
