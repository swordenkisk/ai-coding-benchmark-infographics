import unittest

import pandas as pd

from benchmark_data import DataValidationError, load_and_validate


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "model": "Argon",
                "benchmark": "Example benchmark",
                "benchmark_version": "v1",
                "score": 80,
                "score_unit": "points",
                "higher_is_better": "true",
                "evaluated_on": "2026-01-10",
                "source_url": "https://example.com/results",
            }
        ]
    )


class BenchmarkDataTests(unittest.TestCase):
    def test_valid_row_is_normalized(self) -> None:
        result = load_and_validate(sample_frame())
        self.assertEqual(result.loc[0, "model"], "Argon")
        self.assertEqual(result.loc[0, "higher_is_better"], True)
        self.assertEqual(result.loc[0, "evaluated_on"], "2026-01-10")
        self.assertIn("input_usd_per_1m_tokens", result.columns)

    def test_missing_column_is_rejected(self) -> None:
        frame = sample_frame().drop(columns=["source_url"])
        with self.assertRaises(DataValidationError):
            load_and_validate(frame)

    def test_invalid_source_url_is_rejected(self) -> None:
        frame = sample_frame()
        frame.loc[0, "source_url"] = "not-a-url"
        with self.assertRaises(DataValidationError):
            load_and_validate(frame)

    def test_inconsistent_score_direction_is_rejected(self) -> None:
        frame = pd.concat([sample_frame(), sample_frame()], ignore_index=True)
        frame.loc[1, "model"] = "Other model"
        frame.loc[1, "higher_is_better"] = "false"
        with self.assertRaises(DataValidationError):
            load_and_validate(frame)


if __name__ == "__main__":
    unittest.main()
