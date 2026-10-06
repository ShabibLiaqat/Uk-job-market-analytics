"""Create a deterministic, fictional preview dataset for the dashboard."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from src.data_model import CSV_FIELDS, ROLE_TAXONOMY_VERSION, classify_role


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "sample_jobs.csv"
ROLES = [
    ("Data Analyst", ["Data Analyst", "Junior Data Analyst", "Senior Data Analyst", "Reporting Analyst"]),
    ("BI Analyst", ["BI Analyst", "Business Intelligence Analyst", "Power BI Analyst"]),
    ("MI Analyst", ["MI Analyst", "Management Information Analyst", "MI Reporting Analyst"]),
]
REGIONS = ["North West", "London", "South East", "West Midlands", "Scotland", "Yorkshire and the Humber", "East of England", "Wales", "South West", "Northern Ireland"]
PLACES = {
    "North West": ["Preston", "Manchester", "Liverpool"],
    "London": ["London"], "South East": ["Reading", "Brighton", "Southampton"],
    "West Midlands": ["Birmingham", "Coventry"], "Scotland": ["Glasgow", "Edinburgh"],
    "Yorkshire and the Humber": ["Leeds", "Sheffield"], "East of England": ["Cambridge", "Norwich"],
    "Wales": ["Cardiff", "Swansea"], "South West": ["Bristol", "Exeter"],
    "Northern Ireland": ["Belfast", "Derry"],
}
SKILL_SETS = [
    "SQL|Excel|Power BI", "SQL|Power BI|DAX|Power Query", "Excel|SQL|Python",
    "SQL|Tableau|Python", "Excel|Power BI|Stakeholder communication",
    "SQL|Microsoft Fabric|Azure|Power BI", "Excel|DAX|Power BI",
]
EMPLOYERS = [f"Example Employer {letter}" for letter in "ABCDEFGHIJ"]


def main() -> None:
    rows = []
    job_index = 0
    for month_offset in range(12):
        year = 2025 + ((month_offset + 9) // 12)
        month = ((month_offset + 9) % 12) + 1
        for within_month in range(5):
            role_index = (month_offset + within_month) % len(ROLES)
            family, titles = ROLES[role_index]
            region_index = (job_index * 3 + month_offset) % len(REGIONS)
            region = REGIONS[region_index]
            place = PLACES[region][job_index % len(PLACES[region])]
            skills = SKILL_SETS[(job_index * 2 + within_month) % len(SKILL_SETS)]
            title = titles[(job_index + within_month) % len(titles)]
            salary_period = "annual" if job_index % 5 != 0 else ("hourly" if job_index % 10 == 0 else "unspecified")
            salary_min = salary_max = ""
            if salary_period == "annual":
                salary_min = 26_000 + (job_index % 9) * 2_000
                salary_max = salary_min + 7_000 + (job_index % 4) * 1_000
            elif salary_period == "hourly":
                salary_min, salary_max = 14.5, 19.5
            elif job_index % 2 == 0:
                salary_min, salary_max = 30_000, 38_000
            day = 2 + within_month * 5
            posted = date(year, month, min(day, 28)).isoformat()
            rows.append({
                "posting_id": f"DEMO-{job_index + 1:03}",
                "title": title,
                "employer": EMPLOYERS[job_index % len(EMPLOYERS)],
                "location": f"{place}, {region}",
                "region": region,
                "role_family": classify_role(title),
                "role_taxonomy_version": ROLE_TAXONOMY_VERSION,
                "matched_search_families": family,
                "posted_date": posted,
                "retrieved_on": "2026-09-29",
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_period": salary_period,
                "salary_is_predicted": "false",
                "contract_type": "Permanent",
                "skills": skills,
                "skill_taxonomy_version": "1.0",
                "source": "Fictional preview data",
                "is_synthetic": "true",
            })
            job_index += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} clearly synthetic preview rows to {OUTPUT.name}")


if __name__ == "__main__":
    main()
