import json
import os

def build_season_totals():
    season = {}

    weeks_dir = "data/weeks"
    for fname in sorted(os.listdir(weeks_dir)):
        if not fname.endswith(".json"):
            continue

        with open(os.path.join(weeks_dir, fname)) as f:
            week = json.load(f)

        for pid, pdata in week["playerStats"].items():
            if pid not in season:
                season[pid] = {
                    "id": pid,
                    "name": pdata["name"],
                    "team": pdata["team"],
                    "position": pdata["position"],
                    "points": 0.0,
                    "ppg": 0.0,
                    "games_played": 0,
                    "weeksPoints": {}
                }

            season[pid]["points"] += pdata["points"]

            season[pid]["points"] = round(season[pid]["points"], 2)
            season[pid]["games_played"] += pdata["games_played"]

            season[pid]["ppg"] = season[pid]["points"] / season[pid]["games_played"]
            season[pid]["ppg"] = round(season[pid]["ppg"], 2)

            season[pid]["weeksPoints"][week["weekStart"]] = round(pdata["points"], 2)

    return season

def save_season_totals(season):
    payload = {
        "season": "2025-2026",
        "players": season
    }

    with open("data/season/season_2025_2026.json", "w") as f:
        json.dump(payload, f, indent=2)