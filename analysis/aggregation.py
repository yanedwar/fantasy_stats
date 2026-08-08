import json
import os
from pathlib import Path
from datetime import datetime, date
import re


def _season_str_from_date(d: date) -> str:
    if d.month >= 7:
        start = d.year
    else:
        start = d.year - 1
    return f"{start}-{start + 1}"


def build_season_totals(season: str = None):
    season_players = {}

    # Determine which weeks directories to read.
    weeks_dirs = []
    legacy = Path("data") / "weeks"
    if legacy.exists():
        weeks_dirs.append(legacy)
    else:
        # look for season directories like '2025-2026'
        for p in sorted(Path("data").iterdir()):
            if p.is_dir() and re.match(r"^\d{4}-\d{4}$", p.name):
                w = p / "weeks"
                if w.exists():
                    if season is None or p.name == season:
                        weeks_dirs.append(w)

    for weeks_dir in weeks_dirs:
        for fname in sorted(os.listdir(weeks_dir)):
            if not fname.endswith(".json"):
                continue

            with open(weeks_dir / fname) as f:
                week = json.load(f)

            for pid, pdata in week["playerStats"].items():
                if pid not in season_players:
                    season_players[pid] = {
                        "id": pid,
                        "name": pdata.get("name"),
                        "team": pdata.get("team"),
                        "position": pdata.get("position"),
                        "points": 0.0,
                        "ppg": 0.0,
                        "games_played": 0,
                        "weeksPoints": {}
                    }

                season_players[pid]["points"] += pdata.get("points", 0)
                season_players[pid]["points"] = round(season_players[pid]["points"], 2)
                season_players[pid]["games_played"] += pdata.get("games_played", 0)

                gp = season_players[pid]["games_played"]
                if gp > 0:
                    season_players[pid]["ppg"] = round(season_players[pid]["points"] / gp, 2)
                else:
                    season_players[pid]["ppg"] = 0.0

                season_players[pid]["weeksPoints"][week["weekStart"]] = round(pdata.get("points", 0), 2)

    return season_players


def save_season_totals(season_players, season: str = None):
    # Try to infer season from player weeks if not provided.
    inferred = None
    if season is None:
        for pdata in season_players.values():
            weeks = pdata.get("weeksPoints", {})
            if weeks:
                wk = next(iter(weeks.keys()))
                try:
                    d = datetime.strptime(wk, "%Y-%m-%d").date()
                    inferred = _season_str_from_date(d)
                    break
                except Exception:
                    continue
    season_str = season or inferred or "unknown-season"

    # Prepare payload
    payload = {
        "season": season_str,
        "players": season_players
    }

    # Ensure target directory exists: data/<season>/season
    out_dir = Path("data") / season_str / "season"
    out_dir.mkdir(parents=True, exist_ok=True)

    # filename like season_2025_2026.json
    filename = out_dir / f"season_{season_str.replace('-', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return filename