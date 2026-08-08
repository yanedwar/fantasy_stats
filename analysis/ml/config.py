import json
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
SEASON_DIR = DATA_DIR / "season"
PERIPHERALS_DIR = DATA_DIR / "peripherals"
SCORING_SETTINGS_PATH = ROOT_DIR / "config" / "scoring_settings.json"

with open(SCORING_SETTINGS_PATH, "r", encoding="utf-8") as f:
    SCORING_SETTINGS = json.load(f)

SKATER_SCORING_WEIGHTS = pd.Series({
    "goals": SCORING_SETTINGS["skaterScoring"]["goal"],
    "assists": SCORING_SETTINGS["skaterScoring"]["assist"],
    "shots": SCORING_SETTINGS["skaterScoring"]["shot"],
    "sh_goals": SCORING_SETTINGS["skaterScoring"]["shortHandedGoal"],
    "hits": SCORING_SETTINGS["skaterScoring"]["hit"],
    "blocks": SCORING_SETTINGS["skaterScoring"]["block"],
    "pm": SCORING_SETTINGS["skaterScoring"]["pm"],
    "takeaways": SCORING_SETTINGS["skaterScoring"]["takeaway"],
}, dtype=float)

GOALIE_SCORING_WEIGHTS = pd.Series({
    "goals": SCORING_SETTINGS["goalieScoring"]["goal"],
    "assists": SCORING_SETTINGS["goalieScoring"]["assist"],
    "sh_goals": SCORING_SETTINGS["goalieScoring"]["shortHandedGoal"],
    "win": SCORING_SETTINGS["goalieScoring"]["win"],
    "otl": SCORING_SETTINGS["goalieScoring"]["otl"],
    "shutout": SCORING_SETTINGS["goalieScoring"]["shutout"],
    "saves": SCORING_SETTINGS["goalieScoring"]["save"],
    "g_against": SCORING_SETTINGS["goalieScoring"]["goalAgainst"],
    "nine_one": SCORING_SETTINGS["goalieScoring"]["nineOne"],
}, dtype=float)
