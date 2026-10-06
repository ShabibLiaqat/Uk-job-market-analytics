"""Run structural and value checks on dated live extracts without printing row data."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
from pathlib import Path

from src.data_model import CSV_FIELDS


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "snapshots"
ALLOWED_ROLES = {"Data Analyst", "BI Analyst", "MI Analyst", "Other analyst", "Other / review"}
ALLOWED_PERIODS = {"annual", "hourly", "weekly", "monthly", "unspecified"}


def validate(path: Path) -> tuple[int, Counter[str]]:
    checks: Counter[str] = Counter()
    errors = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing_columns = set(CSV_FIELDS) - columns
        if missing_columns:
            print(f"FAIL {path.name}: expected schema columns are missing ({len(missing_columns)}).")
            return 1, checks

        seen: set[tuple[str, str]] = set()
        for row in reader:
            checks["rows"] += 1
            key = (row["posting_id"].strip(), row["retrieved_on"].strip())
            if not key[0] or not key[1]:
                checks["missing required values"] += 1
            if key in seen:
                checks["duplicate advert-date keys"] += 1
            seen.add(key)

            try:
                date.fromisoformat(row["retrieved_on"])
            except (ValueError, TypeError):
                checks["invalid retrieval dates"] += 1
            if row["posted_date"].strip():
                try:
                    date.fromisoformat(row["posted_date"])
                except (ValueError, TypeError):
                    checks["invalid posting dates"] += 1

            if not row["title"].strip() or not row["region"].strip() or not row["matched_search_families"].strip():
                checks["missing required values"] += 1
            if row["role_family"] not in ALLOWED_ROLES:
                checks["unknown role categories"] += 1
            if row["salary_period"] not in ALLOWED_PERIODS:
                checks["unknown salary periods"] += 1
            if row["salary_is_predicted"].casefold() not in {"true", "false", "1", "0", "yes", "no"}:
                checks["invalid predicted-salary flags"] += 1

            bounds: list[float | None] = []
            for field in ("salary_min", "salary_max"):
                raw = row[field].strip()
                try:
                    value = float(raw) if raw else None
                except ValueError:
                    value = None
                    checks["invalid salary values"] += 1
                if value is not None and value < 0:
                    checks["negative salary values"] += 1
                bounds.append(value)
            if bounds[0] is not None and bounds[1] is not None and bounds[0] > bounds[1]:
                checks["reversed salary ranges"] += 1

    issue_count = sum(value for key, value in checks.items() if key != "rows")
    errors += issue_count
    region_unknown = checks["rows"]
    with path.open(newline="", encoding="utf-8") as handle:
        region_unknown = sum(1 for row in csv.DictReader(handle) if row.get("region") == "Unclassified")
    unknown_share = (100 * region_unknown / checks["rows"]) if checks["rows"] else 0
    status = "PASS" if errors == 0 else "FAIL"
    print(
        f"{status} {path.name}: {checks['rows']} rows; {errors} structural/value issues; "
        f"{unknown_share:.1f}% of regions unclassified."
    )
    if errors:
        details = ", ".join(f"{name}: {count}" for name, count in checks.items() if name != "rows")
        print(f"  Issue counts: {details}")
    return errors, checks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=SNAPSHOT_DIR, help="A dated CSV or folder of snapshots")
    args = parser.parse_args()
    paths = [args.path] if args.path.is_file() else sorted(args.path.glob("jobs_*.csv"))
    if not paths:
        raise SystemExit("No dated snapshots found to validate.")

    failures = 0
    for path in paths:
        found, _ = validate(path)
        failures += found
    if failures:
        raise SystemExit(f"Validation found {failures} structural/value issue(s).")
    print("Validation passed. Coverage gaps remain visible for analysis; they are not structural errors.")


if __name__ == "__main__":
    main()
