import json
from pathlib import Path

import pandas as pd

from .config import ROOT_DIR


def _resolve_path(filepath):
    path = Path(filepath)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def load_weekly_points(filepaths):
    rows = []
    for fp in filepaths:
        with open(_resolve_path(fp)) as f:
            week = json.load(f)
        for pid, rec in week["playerStats"].items():
            rows.append({
                "player_id": int(pid),
                "name": rec["name"],
                "team": rec["team"],
                "position": rec["position"],
                "week_start": week["weekStart"],
                "week_end": week["weekEnd"],
                "week_points": rec["points"],
                "week_games_played": rec["games_played"],
            })
    return pd.DataFrame(rows)


def load_season_snapshot(filepath, season_label):
    with open(_resolve_path(filepath)) as f:
        data = json.load(f)
    rows = []
    for pid, rec in data["players"].items():
        rows.append({
            "player_id": int(pid),
            "name": rec["name"],
            "team": rec["team"],
            "position": rec["position"],
            "season": season_label,
            "season_points": rec["points"],
            "ppg": rec["ppg"],
            "games_played": rec["games_played"],
            "weeksPoints": rec["weeksPoints"],
        })
    return pd.DataFrame(rows)


def load_peripherals(filepath, season_label, week_label=None):
    with open(_resolve_path(filepath)) as f:
        data = json.load(f)

    if isinstance(data, list):
        payload = data
        processed_weeks = []
    elif isinstance(data, dict):
        payload = data.get("players", [])
        processed_weeks = data.get("processed_weeks", [])
    else:
        raise TypeError(f"Unsupported peripherals payload type: {type(data)!r}")

    if payload is None:
        payload = []

    df = pd.DataFrame(payload)
    if df.empty:
        df = pd.DataFrame(columns=["player_id", "id", "name", "team", "position"])

    if "id" in df.columns and "player_id" not in df.columns:
        df = df.rename(columns={"id": "player_id"})
    if "playerId" in df.columns and "player_id" not in df.columns:
        df = df.rename(columns={"playerId": "player_id"})

    if "player_id" in df.columns:
        df["player_id"] = pd.to_numeric(df["player_id"], errors="coerce").astype("Int64")

    df["season"] = season_label
    df["week"] = week_label
    df.attrs["processed_weeks"] = processed_weeks
    return df


def split_skaters_goalies(df, position_col="position"):
    skaters = df[df[position_col].isin({"C", "L", "R", "D"})].copy()
    goalies = df[df[position_col] == "G"].copy()
    return skaters, goalies
