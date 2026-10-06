"""Shared, documented transformations for job advert records."""

from __future__ import annotations

import re
from datetime import date
from typing import Any


ROLE_SEARCHES = {
    "Data Analyst": "Data Analyst",
    "BI Analyst": "Business Intelligence Analyst",
    "MI Analyst": "MI Analyst",
}
CSV_FIELDS = [
    "posting_id", "title", "employer", "location", "region", "role_family",
    "role_taxonomy_version", "matched_search_families",
    "posted_date", "retrieved_on", "salary_min", "salary_max", "salary_period",
    "salary_is_predicted", "contract_type", "skills", "skill_taxonomy_version",
    "source", "is_synthetic",
]
SKILL_TAXONOMY_VERSION = "1.0"
ROLE_TAXONOMY_VERSION = "2.0"

SKILLS = {
    "SQL": (r"\bsql\b",),
    "Power BI": (r"\bpower\s?bi\b",),
    "Excel": (r"\bexcel\b",),
    "Python": (r"\bpython\b",),
    "Tableau": (r"\btableau\b",),
    "Microsoft Fabric": (r"\bfabric\b", r"\bmicrosoft fabric\b"),
    "Azure": (r"\bazure\b",),
    "DAX": (r"\bdax\b",),
    "Power Query": (r"\bpower query\b",),
    "Stakeholder communication": (r"\bstakeholder(?:s)?\b",),
}

# A region is assigned only when a recognised UK region/nation appears in the
# location hierarchy returned by the API. We do not guess from an arbitrary city.
REGIONS = {
    "north west": "North West", "north east": "North East",
    "north west england": "North West", "north east england": "North East",
    "yorkshire and the humber": "Yorkshire and the Humber",
    "yorkshire": "Yorkshire and the Humber", "east midlands": "East Midlands",
    "east midlands england": "East Midlands", "west midlands england": "West Midlands",
    "west midlands": "West Midlands", "east of england": "East of England",
    "east of england region": "East of England",
    "london": "London", "south east": "South East", "south west": "South West",
    "south east england": "South East", "south west england": "South West",
    "scotland": "Scotland", "wales": "Wales",
    "northern ireland": "Northern Ireland",
}

COUNTY_REGIONS = {
    "cumbria": "North West", "lancashire": "North West", "cheshire": "North West",
    "merseyside": "North West", "greater manchester": "North West",
    "northumberland": "North East", "tyne and wear": "North East",
    "county durham": "North East", "cleveland": "North East",
    "north yorkshire": "Yorkshire and the Humber", "west yorkshire": "Yorkshire and the Humber",
    "south yorkshire": "Yorkshire and the Humber", "east riding of yorkshire": "Yorkshire and the Humber",
    "derbyshire": "East Midlands", "leicestershire": "East Midlands",
    "lincolnshire": "East Midlands", "nottinghamshire": "East Midlands",
    "northamptonshire": "East Midlands", "herefordshire": "West Midlands",
    "shropshire": "West Midlands", "staffordshire": "West Midlands",
    "warwickshire": "West Midlands", "worcestershire": "West Midlands",
    "bedfordshire": "East of England", "cambridgeshire": "East of England",
    "essex": "East of England", "hertfordshire": "East of England",
    "norfolk": "East of England", "suffolk": "East of England",
    "berkshire": "South East", "buckinghamshire": "South East",
    "east sussex": "South East", "hampshire": "South East", "isle of wight": "South East",
    "kent": "South East", "oxfordshire": "South East", "surrey": "South East",
    "west sussex": "South East", "cornwall": "South West", "devon": "South West",
    "dorset": "South West", "gloucestershire": "South West", "somerset": "South West",
    "wiltshire": "South West", "bristol": "South West",
}

ANNUAL_PAY = re.compile(r"\b(?:per\s+annum|per\s+year|a\s+year|annually|annual(?:ly)?|yearly|p\.a\.)\b", re.I)
HOURLY_PAY = re.compile(r"\b(?:per\s+hour|an\s+hour|hourly|\bph\b)\b", re.I)
WEEKLY_PAY = re.compile(r"\b(?:per\s+week|a\s+week|weekly)\b", re.I)
MONTHLY_PAY = re.compile(r"\b(?:per\s+month|a\s+month|monthly)\b", re.I)


def classify_role(title: str) -> str:
    """Classify from advert title only; search terms are not evidence of role."""
    text = title.casefold()
    if ("business intelligence" in text or re.search(r"\bbi\b", text)) and re.search(r"\banalysts?\b", text):
        return "BI Analyst"
    if re.search(r"\bmi\b|management information", text) and re.search(r"\banalysts?\b", text):
        return "MI Analyst"
    if re.search(r"\bdata\s+analysts?\b", text):
        return "Data Analyst"
    if re.search(r"\banalysts?\b", text):
        return "Other analyst"
    return "Other / review"


def classify_region(area: list[str] | str | None) -> str:
    labels = area if isinstance(area, list) else [area or ""]
    normalised = [str(label).strip().casefold() for label in labels]
    for label in normalised:
        if label in REGIONS:
            return REGIONS[label]
    for label in normalised:
        if label in COUNTY_REGIONS:
            return COUNTY_REGIONS[label]
    return "Unclassified"


def salary_period(text: str) -> str:
    """Return only an explicit pay period; avoid inferring units from the amount."""
    if ANNUAL_PAY.search(text):
        return "annual"
    if HOURLY_PAY.search(text):
        return "hourly"
    if WEEKLY_PAY.search(text):
        return "weekly"
    if MONTHLY_PAY.search(text):
        return "monthly"
    return "unspecified"


def extract_skill_tags(text: str) -> str:
    found = []
    folded = text.casefold()
    for skill, patterns in SKILLS.items():
        if any(re.search(pattern, folded, flags=re.I) for pattern in patterns):
            found.append(skill)
    return "|".join(found)


def normalise_advert(
    advert: dict[str, Any], searched_role: str, retrieved_on: date
) -> dict[str, Any]:
    """Shape one API record; retain only selected fields and derived skill tags."""
    description = str(advert.get("description") or "")
    title = str(advert.get("title") or "").strip()
    location = advert.get("location") or {}
    if not isinstance(location, dict):
        location = {}
    area = location.get("area") or []
    created = str(advert.get("created") or "")
    posted_date = created[:10] if created else ""
    if posted_date:
        date.fromisoformat(posted_date)

    minimum = advert.get("salary_min")
    maximum = advert.get("salary_max")
    company = advert.get("company") or {}
    if not isinstance(company, dict):
        company = {}
    return {
        "posting_id": str(advert.get("id") or ""),
        "title": title,
        "employer": str(company.get("display_name") or "Not stated"),
        "location": str(location.get("display_name") or "Not stated"),
        "region": classify_region(area),
        "role_family": classify_role(title),
        "role_taxonomy_version": ROLE_TAXONOMY_VERSION,
        "matched_search_families": searched_role,
        "posted_date": posted_date,
        "retrieved_on": retrieved_on.isoformat(),
        "salary_min": minimum,
        "salary_max": maximum,
        "salary_period": salary_period(f"{title} {description}"),
        "salary_is_predicted": bool(advert.get("salary_is_predicted", False)),
        "contract_type": str(advert.get("contract_type") or "Not stated"),
        "skills": extract_skill_tags(f"{title} {description}"),
        "skill_taxonomy_version": SKILL_TAXONOMY_VERSION,
        "source": "Adzuna API",
        "is_synthetic": False,
    }
