import tempfile
import unittest
from pathlib import Path

from parser import discover_fit_files


class TestFitDiscovery(unittest.TestCase):
    def test_discover_fit_files_and_extract_distance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "2026-06-29.fit").write_text("Distance:\n10.2 mi\n", encoding="utf-8")
            (folder / "2026-06-30.fit").write_text("Distance:\n8.0 mi\n", encoding="utf-8")

            runs = discover_fit_files(folder)

            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]["name"], "2026-06-29.fit")
            self.assertEqual(runs[0]["distance"], 10.2)
            self.assertEqual(runs[1]["name"], "2026-06-30.fit")
            self.assertEqual(runs[1]["distance"], 8.0)


if __name__ == "__main__":
    unittest.main()
