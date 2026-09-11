import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.aggregation import build_season_totals, save_season_totals


class SeasonAggregationTests(unittest.TestCase):
    def test_build_and_save_use_requested_season_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            data_root = cwd / "data"
            season_2024_weeks = data_root / "2024-2025" / "weeks"
            season_2025_weeks = data_root / "2025-2026" / "weeks"
            season_2024_weeks.mkdir(parents=True)
            season_2025_weeks.mkdir(parents=True)

            (season_2024_weeks / "2024-09-29.json").write_text(
                json.dumps(
                    {
                        "weekStart": "2024-09-29",
                        "weekEnd": "2024-10-05",
                        "playerStats": {
                            "1": {
                                "name": "Test Player",
                                "team": "AAA",
                                "position": "C",
                                "points": 10,
                                "games_played": 2,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (season_2025_weeks / "2025-10-05.json").write_text(
                json.dumps(
                    {
                        "weekStart": "2025-10-05",
                        "weekEnd": "2025-10-11",
                        "playerStats": {
                            "1": {
                                "name": "Test Player",
                                "team": "AAA",
                                "position": "C",
                                "points": 99,
                                "games_played": 9,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            original_cwd = os.getcwd()
            os.chdir(cwd)
            try:
                season = build_season_totals("2024-2025")
                saved_path = cwd / save_season_totals(season, "2024-2025")
            finally:
                os.chdir(original_cwd)

            self.assertEqual(season["1"]["points"], 10.0)
            self.assertEqual(season["1"]["games_played"], 2)
            self.assertEqual(season["1"]["weeksPoints"], {"2024-09-29": 10.0})

            self.assertTrue(saved_path.exists())
            payload = json.loads(saved_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["season"], "2024-2025")
            self.assertEqual(payload["players"]["1"]["points"], 10.0)
            self.assertEqual(payload["players"]["1"]["games_played"], 2)


if __name__ == "__main__":
    unittest.main()
