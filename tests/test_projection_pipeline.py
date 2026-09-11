import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.ml.io import load_peripherals


class ProjectionPipelineTests(unittest.TestCase):
    def test_load_peripherals_accepts_list_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "peripherals.json"
            payload = [
                {"id": 101, "name": "Test Player", "team": "TST", "position": "C", "goals": 2}
            ]
            path.write_text(json.dumps(payload), encoding="utf-8")

            df = load_peripherals(path, season_label="2024-2025")

            self.assertEqual(df.loc[0, "player_id"], 101)
            self.assertEqual(df.loc[0, "season"], "2024-2025")
            self.assertEqual(df.loc[0, "goals"], 2)


if __name__ == "__main__":
    unittest.main()
