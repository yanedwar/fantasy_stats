import json
from pathlib import Path
from datetime import date
import re


def _season_str_from_date(d: date) -> str:
    # Hockey seasons span two years. Dates from July-December belong to the
    # season that starts that calendar year; dates from Jan-June belong to the
    # season that started the previous year.
    if d.month >= 7:
        start = d.year
    else:
        start = d.year - 1
    return f"{start}-{start + 1}"


def _week_dir_for_date(d: date) -> Path:
    season = _season_str_from_date(d)
    p = Path("data") / season / "weeks"
    p.mkdir(parents=True, exist_ok=True)
    return p


def week_exists(start_date: date) -> bool:
    filename = f"{start_date.isoformat()}.json"
    return (_week_dir_for_date(start_date) / filename).exists()


def store_week(players, start_date: date, end_date: date, games_played, overwrite: bool = False):
    filename = _week_dir_for_date(start_date) / f"{start_date.isoformat()}.json"

    if games_played == 0:
        return None

    data = {
        "weekStart": start_date.strftime("%Y-%m-%d"),
        "weekEnd": end_date.strftime("%Y-%m-%d"),
        "gamesPlayed": games_played,
        "playerStats": {
            str(pid): player.store()
            for pid, player in players.items()
            if getattr(player, "games_played", 0) > 0
        },
    }

    if filename.exists() and not overwrite:
        raise FileExistsError(
            f"Weekly data for {start_date} already exists. Use overwrite=True to replace it."
        )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return filename
