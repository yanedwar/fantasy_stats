import numpy as np
import pandas as pd


def weekly_trend_and_consistency(weeks_points: dict):
    if not weeks_points:
        return pd.Series({
            "weekly_std": np.nan, "weekly_cv": np.nan, "trend_slope": np.nan,
            "first_half_avg": np.nan, "second_half_avg": np.nan,
        })
    dates = sorted(weeks_points.keys())
    values = np.array([weeks_points[d] for d in dates], dtype=float)
    mean = values.mean()
    std = values.std(ddof=0)
    cv = std / mean if mean > 0 else np.nan
    if len(values) >= 2:
        trend_slope = np.polyfit(np.arange(len(values)), values, 1)[0]
    else:
        trend_slope = np.nan
    mid = len(values) // 2
    first_half_avg = values[:mid].mean() if mid > 0 else np.nan
    second_half_avg = values[mid:].mean() if len(values) - mid > 0 else np.nan
    return pd.Series({
        "weekly_std": std, "weekly_cv": cv, "trend_slope": trend_slope,
        "first_half_avg": first_half_avg, "second_half_avg": second_half_avg,
    })


def build_skater_season_features(season_snapshot_df, peripherals_season_df):
    trend_feats = season_snapshot_df["weeksPoints"].apply(weekly_trend_and_consistency)
    base = pd.concat([season_snapshot_df.drop(columns=["weeksPoints"]), trend_feats], axis=1)

    required_cols = ["player_id", "goals", "assists", "shots", "hits",
                     "blocks", "pm", "takeaways", "sh_goals"]
    per = peripherals_season_df.copy()
    for col in required_cols:
        if col not in per.columns:
            per[col] = np.nan
    per = per[required_cols].copy()
    merged = base.merge(per, on="player_id", how="left")

    gp = merged["games_played"].replace(0, np.nan)
    merged["goals_per_gp"] = merged["goals"] / gp
    merged["assists_per_gp"] = merged["assists"] / gp
    merged["shots_per_gp"] = merged["shots"] / gp
    merged["shooting_pct"] = merged["goals"] / merged["shots"].replace(0, np.nan)
    merged["hits_per_gp"] = merged["hits"] / gp
    merged["blocks_per_gp"] = merged["blocks"] / gp
    merged["takeaways_per_gp"] = merged["takeaways"] / gp
    merged["pm_per_gp"] = merged["pm"] / gp
    return merged


def build_goalie_season_features(season_snapshot_df, peripherals_season_df):
    trend_feats = season_snapshot_df["weeksPoints"].apply(weekly_trend_and_consistency)
    base = pd.concat([season_snapshot_df.drop(columns=["weeksPoints"]), trend_feats], axis=1)

    required_cols = ["player_id", "win", "otl", "shutout", "saves", "g_against", "nine_one"]
    per = peripherals_season_df.copy()
    for col in required_cols:
        if col not in per.columns:
            per[col] = np.nan
    per = per[required_cols].copy()
    merged = base.merge(per, on="player_id", how="left")

    gp = merged["games_played"].replace(0, np.nan)
    merged["wins_per_gp"] = merged["win"] / gp
    merged["saves_per_gp"] = merged["saves"] / gp
    merged["shutouts_per_gp"] = merged["shutout"] / gp
    merged["goals_against_per_gp"] = merged["g_against"] / gp
    merged["quality_start_rate"] = merged["nine_one"] / gp
    return merged


SKATER_FEATURE_COLS = [
    "ppg", "games_played", "weekly_std", "weekly_cv", "trend_slope",
    "first_half_avg", "second_half_avg",
    "goals_per_gp", "assists_per_gp", "shots_per_gp", "shooting_pct",
    "hits_per_gp", "blocks_per_gp", "takeaways_per_gp", "pm_per_gp",
]

GOALIE_FEATURE_COLS = [
    "ppg", "games_played", "weekly_std", "weekly_cv", "trend_slope",
    "first_half_avg", "second_half_avg",
    "wins_per_gp", "saves_per_gp", "shutouts_per_gp",
    "goals_against_per_gp", "quality_start_rate",
]

SKATER_PERIPHERAL_RAW_COLS = [
    "goals", "assists", "shots", "hits", "blocks", "pm", "takeaways", "sh_goals",
]
