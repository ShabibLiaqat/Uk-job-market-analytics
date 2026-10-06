"""Check refresh failures preserve usable extracts and successful captures publish."""

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from src import collect_adzuna
from src.data_model import normalise_advert


class CollectionPublicationTests(unittest.TestCase):
    def run_collection(self, rows, expected_failure=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "processed" / "jobs.csv"
            snapshots = root / "snapshots"
            output.parent.mkdir()
            snapshots.mkdir()
            snapshot = snapshots / f"jobs_{date.today().isoformat()}.csv"
            output.write_text("previous latest", encoding="utf-8")
            snapshot.write_text("previous snapshot", encoding="utf-8")
            with (
                patch.object(collect_adzuna, "ROOT", root),
                patch.object(collect_adzuna, "OUTPUT", output),
                patch.object(collect_adzuna, "SNAPSHOT_DIR", snapshots),
                patch.object(collect_adzuna, "collect", return_value=rows),
                patch.dict("os.environ", {"ADZUNA_APP_ID": "test", "ADZUNA_APP_KEY": "test"}),
                patch("sys.argv", ["collect_adzuna"]),
            ):
                if expected_failure:
                    with self.assertRaises(SystemExit):
                        collect_adzuna.main()
                    self.assertEqual(output.read_text(), "previous latest")
                    self.assertEqual(snapshot.read_text(), "previous snapshot")
                else:
                    collect_adzuna.main()
                    self.assertEqual(output.read_bytes(), snapshot.read_bytes())
                    self.assertIn("example advert", output.read_text())
            self.assertEqual(list(output.parent.iterdir()), [output])
            self.assertEqual(list(snapshots.iterdir()), [snapshot])

    def test_empty_results_preserve_previous_files(self):
        self.run_collection([], expected_failure=True)

    def test_invalid_results_preserve_previous_files(self):
        row = normalise_advert({"id": "test", "title": ""}, "Data Analyst", date.today())
        self.run_collection([row], expected_failure=True)

    def test_valid_results_replace_both_files(self):
        row = normalise_advert({"id": "test", "title": "Data Analyst example advert"}, "Data Analyst", date.today())
        self.run_collection([row])


if __name__ == "__main__":
    unittest.main()
