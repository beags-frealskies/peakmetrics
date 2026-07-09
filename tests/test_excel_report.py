import tempfile
import unittest
from pathlib import Path

from excel_report import build_output_path


class TestOutputPath(unittest.TestCase):
    def test_returns_unique_path_when_target_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "Week_Data.xlsx"
            base_path.write_text("existing", encoding="utf-8")

            output_path = build_output_path(base_path)

            self.assertNotEqual(output_path, base_path)
            self.assertEqual(output_path.suffix, ".xlsx")
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
