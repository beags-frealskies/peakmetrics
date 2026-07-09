import unittest

import pandas as pd

from parser import sanitize_for_excel


class TestExcelSanitization(unittest.TestCase):
    def test_removes_timezone_from_datetime_values(self) -> None:
        df = pd.DataFrame(
            {
                "start_time": [pd.Timestamp("2026-06-29 15:30:42", tz="UTC")],
            }
        )

        cleaned = sanitize_for_excel(df)

        self.assertFalse(pd.api.types.is_datetime64tz_dtype(cleaned["start_time"]))
        self.assertEqual(cleaned.iloc[0, 0], pd.Timestamp("2026-06-29 15:30:42"))


if __name__ == "__main__":
    unittest.main()
