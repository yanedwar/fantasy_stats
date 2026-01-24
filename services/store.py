import json

from pathlib import Path

WEEK_DIR = Path("data/weeks")

def week_exists(start_date):

    filename = f"{start_date.isoformat()}.json"
    return (WEEK_DIR / filename).exists()

def store_week(players, start_date, end_date, games_played, overwrite = False):
    filename = WEEK_DIR / f"{start_date}.json"

    data = {
        "weekStart": start_date.strftime('%Y-%m-%d'),
        "weekEnd": end_date.strftime('%Y-%m-%d'),
        "gamesPlayed": games_played,
        "playerStats": {
            str(id): player.store()
            for id, player in players.items()
            if player.games_played > 0
        },
    }

    if filename.exists() and not overwrite:
        raise FileExistsError(
            f"Weekly data for {start_date} already exists. "
            "Use overwrite=True to replace it."
        )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return filename
