"""Collect a bounded Adzuna sample and save selected fields, never raw descriptions."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import tempfile
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.data_model import CSV_FIELDS, ROLE_SEARCHES, normalise_advert
from src.validate_extract import validate


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "processed" / "jobs.csv"
SNAPSHOT_DIR = ROOT / "data" / "snapshots"
BASE_URL = "https://api.adzuna.com/v1/api/jobs/gb/search"
MIN_SECONDS_BETWEEN_REQUESTS = 2.5


def load_local_env(path: Path) -> None:
    """Load simple KEY=VALUE lines without printing or overriding the process environment."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        name = name.strip()
        value = value.strip().strip("\"'")
        if name:
            os.environ.setdefault(name, value)


def collect(app_id: str, app_key: str, pages: int, days: int) -> list[dict]:
    rows: dict[str, dict] = {}
    last_request_at: float | None = None
    for role, query in ROLE_SEARCHES.items():
        for page in range(1, pages + 1):
            if last_request_at is not None:
                elapsed = time.monotonic() - last_request_at
                time.sleep(max(0, MIN_SECONDS_BETWEEN_REQUESTS - elapsed))

            parameters = urlencode({
                "app_id": app_id,
                "app_key": app_key,
                "what": query,
                "max_days_old": days,
                "results_per_page": 50,
                "sort_by": "date",
                "content-type": "application/json",
            })
            request = Request(
                f"{BASE_URL}/{page}?{parameters}",
                headers={"Accept": "application/json", "User-Agent": "UK-Data-Careers-Observatory/0.1"},
            )
            try:
                with urlopen(request, timeout=30) as response:
                    response_body = response.read()
                last_request_at = time.monotonic()
            except HTTPError as exc:
                raise RuntimeError(
                    f"Adzuna returned HTTP {exc.code}. Check credentials, endpoint access and account limits."
                ) from None
            except (URLError, TimeoutError, OSError):
                raise RuntimeError(
                    "Adzuna request failed because of a network or timeout error. Credentials were not displayed."
                ) from None

            try:
                payload = json.loads(response_body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise RuntimeError("Adzuna returned an unreadable response; no response text was displayed.") from None
            if not isinstance(payload, dict):
                raise RuntimeError("Adzuna returned an unexpected response format; response contents were not displayed.")
            for advert in payload.get("results", []):
                shaped = normalise_advert(advert, role, date.today())
                if shaped["posting_id"]:
                    existing = rows.get(shaped["posting_id"])
                    if existing is None:
                        rows[shaped["posting_id"]] = shaped
                    else:
                        # Preserve overlap provenance while counting each advert once.
                        matched = set(existing["matched_search_families"].split("|"))
                        matched.add(role)
                        existing["matched_search_families"] = "|".join(sorted(matched))
    return list(rows.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=int, default=1, help="Pages per role search (maximum 8, within the default per-minute limit).")
    parser.add_argument("--days", type=int, default=30, help="Include adverts from the last 1–90 days.")
    args = parser.parse_args()
    if not 1 <= args.pages <= 8:
        parser.error("--pages must be between 1 and 8")
    if not 1 <= args.days <= 90:
        parser.error("--days must be between 1 and 90")

    load_local_env(ROOT / ".env")
    app_id = os.getenv("ADZUNA_APP_ID", "").strip()
    app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
    if not app_id or not app_key:
        parser.error("Add ADZUNA_APP_ID and ADZUNA_APP_KEY to your local .env file first.")

    rows = collect(app_id, app_key, args.pages, args.days)
    if not rows:
        raise SystemExit("Adzuna returned no adverts. Refresh failed; existing extracts were preserved.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = SNAPSHOT_DIR / f"jobs_{date.today().isoformat()}.csv"
    # Validate before replacing any usable extract, including same-day reruns.
    staged = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", suffix=".csv", dir=OUTPUT.parent, delete=False) as handle:
            staged = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        errors, _ = validate(staged)
        if errors:
            raise SystemExit("Collected extract failed validation; existing extracts were preserved.")
        # Use sibling temporary files so each replacement is atomic.
        with tempfile.NamedTemporaryFile(mode="wb", dir=SNAPSHOT_DIR, delete=False) as handle:
            staged_snapshot = Path(handle.name)
            handle.write(staged.read_bytes())
        try:
            staged_snapshot.replace(snapshot)
        finally:
            staged_snapshot.unlink(missing_ok=True)
        staged.replace(OUTPUT)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
    print(f"Saved {len(rows)} unique adverts to {OUTPUT.relative_to(ROOT)}")
    print(f"Saved today's snapshot to {snapshot.relative_to(ROOT)}")
    print("Search overlap is recorded separately from title-based role classification.")
    print("Descriptions were processed for skill tags and discarded.")


if __name__ == "__main__":
    main()
