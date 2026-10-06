"""Load the latest live extract into a small local SQLite warehouse."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from src.data_model import CSV_FIELDS


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "jobs.csv"
SNAPSHOT_DIR = ROOT / "data" / "snapshots"
DATABASE = ROOT / "data" / "careers_observatory.sqlite"
SCHEMA = ROOT / "sql" / "schema.sql"


def main() -> None:
    snapshot_files = sorted(SNAPSHOT_DIR.glob("jobs_*.csv"))
    inputs = snapshot_files or ([INPUT] if INPUT.exists() else [])
    if not inputs:
        raise SystemExit("No live extract found. Run python -m src.collect_adzuna first.")

    records = []
    for path in inputs:
        with path.open(newline="", encoding="utf-8") as handle:
            for source_row in csv.DictReader(handle):
                row = {field: source_row.get(field, "") for field in CSV_FIELDS}
                for field in ("posted_date", "salary_min", "salary_max"):
                    row[field] = row[field] or None
                for field in ("salary_min", "salary_max"):
                    row[field] = float(row[field]) if row[field] is not None else None
                for field in ("salary_is_predicted", "is_synthetic"):
                    row[field] = int(str(row[field]).casefold() in {"true", "1", "yes"})
                records.append(tuple(row[field] for field in CSV_FIELDS))

    with sqlite3.connect(DATABASE) as connection:
        # The dated CSV snapshots are the rebuildable source of truth.
        connection.execute("DROP TABLE IF EXISTS jobs")
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        columns = ", ".join(CSV_FIELDS)
        placeholders = ", ".join("?" for _ in CSV_FIELDS)
        connection.execute("DELETE FROM jobs")
        connection.executemany(
            f"INSERT INTO jobs ({columns}) VALUES ({placeholders})", records
        )
    print(f"Loaded {len(records)} observations from {len(inputs)} extract(s) into {DATABASE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
