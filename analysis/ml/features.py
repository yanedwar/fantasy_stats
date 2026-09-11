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

def add_career_trailing_features(features_by_year: dict, lookback=2, shrink_games=40):
    """
    Augments each season's feature table with trailing multi-season
    context per player: recency-weighted trailing PPG, trailing
    games-played, and career-peak PPG, across up to `lookback` prior
    seasons. Without trailing_games_played specifically, a player coming
    off an injury-shortened season has their reduced games_played taken
    completely at face value with no context for whether it's a new
    normal or a one-off -- same blind spot trailing_ppg fixes for
    scoring rate, just for durability instead.

    Also adds `ppg_shrunk`: the current season's ppg, pulled toward the
    player's own trailing_ppg, weighted by `shrink_games` against how many
    games they played this season (same shrink-toward-a-prior logic
    baseline_projection already uses against the position mean, just
    anchored on the player's own history instead). Two things this blend
    is doing, not one: it stops a small-sample season (e.g. 60 games from
    injury) from being trusted as much as a full one, AND -- via
    `shrink_games` -- it controls how much a *full, healthy* season's rate
    should still be tempered by track record. Raising shrink_games doesn't
    just protect against injury-shortened seasons anymore; it generally
    weights this season's rate less against the player's trailing level,
    for everyone. Re-backtested (forward-chaining, all season-transitions,
    with lightgbm actually installed -- see the note on train_quantile_gbm
    about why that matters) across shrink_games 20-100: overall MAE is
    flat throughout (~97.3-97.6), so there's real room to turn this up
    without a clear accuracy cost. 30 was chosen as a modest step in that
    direction rather than a large one -- individual players' predictions
    aren't perfectly monotonic in this parameter once the whole model gets
    retrained at each value (see e.g. Makar, who trends down as shrink
    increases past ~30 despite his own trailing_ppg exceeding his current
    ppg), so treat this as a real lever, not a precise dial.
    """
    seasons_sorted = sorted(features_by_year.keys())
    augmented = {}
    history = {}  # player_id -> [(season, ppg, games_played), ...] seen so far

    for season in seasons_sorted:
        df = features_by_year[season].copy()
        trailing_ppg, career_peak_ppg, trailing_gp, seasons_of_history = [], [], [], []
        for _, row in df.iterrows():
            pid = row["player_id"]
            past = history.get(pid, [])[-lookback:]
            if past:
                weights = np.linspace(0.5, 1.0, len(past))
                trailing_ppg.append(np.average([p for _, p, _ in past], weights=weights))
                trailing_gp.append(np.average([g for _, _, g in past], weights=weights))
                career_peak_ppg.append(max(p for _, p, _ in history[pid]))
            else:
                trailing_ppg.append(np.nan)
                trailing_gp.append(np.nan)
                career_peak_ppg.append(np.nan)
            seasons_of_history.append(len(history.get(pid, [])))
        df["trailing_ppg"] = trailing_ppg
        df["career_peak_ppg"] = career_peak_ppg
        df["trailing_games_played"] = trailing_gp
        df["seasons_of_history"] = seasons_of_history
        df["trailing_ppg"] = df["trailing_ppg"].fillna(df["ppg"])
        df["career_peak_ppg"] = df["career_peak_ppg"].fillna(df["ppg"])
        df["trailing_games_played"] = df["trailing_games_played"].fillna(df["games_played"])
        reliability = df["games_played"] / (df["games_played"] + shrink_games)
        df["ppg_shrunk"] = reliability * df["ppg"] + (1 - reliability) * df["trailing_ppg"]
        augmented[season] = df

        for _, row in df.iterrows():
            history.setdefault(row["player_id"], []).append(
                (season, row["ppg"], row["games_played"]))

    return augmented

SKATER_FEATURE_COLS = [
    # ppg_shrunk (not raw ppg) -- see add_career_trailing_features's
    # docstring. Backtested via forward-chaining evaluation across all
    # available season transitions before swapping this in: comparable
    # overall MAE to raw ppg, better MAE specifically on the "healthy
    # track record, injury-shortened current season" cohort (the
    # Matthews/Kaprizov-shaped cases), and it visibly stopped one bad
    # season from erasing a proven track record in the actual board.
    # Flagging honestly: that cohort is only ~20 players a season, and a
    # sweep over shrink_games showed real instability in exactly which
    # players it helps/hurts -- treat this as a real improvement, not a
    # fully solved problem. Re-check after adding more season-pairs.
    "ppg_shrunk", "games_played", "weekly_std", "weekly_cv", "trend_slope",
    "first_half_avg", "second_half_avg",
    # peripherals temporarily disabled -- pipeline.py isn't merging them
    # in right now. Uncomment once the peripheral data has been audited:
    # "goals_per_gp", "assists_per_gp", "shots_per_gp", "shooting_pct",
    # "hits_per_gp", "blocks_per_gp", "takeaways_per_gp", "pm_per_gp",
    "trailing_ppg", "career_peak_ppg", "seasons_of_history", "trailing_games_played",
]

SKATER_FEATURE_COLS_P = [
    "ppg_shrunk", "games_played", "weekly_std", "weekly_cv", "trend_slope",
    "first_half_avg", "second_half_avg",
    "goals_per_gp", "assists_per_gp", "shots_per_gp", "shooting_pct",
    "hits_per_gp", "blocks_per_gp", "takeaways_per_gp", "pm_per_gp",
    "trailing_ppg", "career_peak_ppg", "seasons_of_history", "trailing_games_played",
]

GOALIE_FEATURE_COLS = [
    # NOTE: still on raw "ppg" here, not ppg_shrunk. add_career_trailing_features
    # computes ppg_shrunk for goalies too (it's the same df), so this is a
    # one-line swap once goalie projections get the same look skaters
    # just did -- left as raw ppg for now so this pass stays scoped to
    # the skater board.
    "ppg", "games_played", "weekly_std", "weekly_cv", "trend_slope",
    "first_half_avg", "second_half_avg",
    # peripherals temporarily disabled, same as skaters above:
    # "wins_per_gp", "saves_per_gp", "shutouts_per_gp",
    # "goals_against_per_gp", "quality_start_rate",
    "trailing_ppg", "career_peak_ppg", "seasons_of_history", "trailing_games_played",
]

SKATER_PERIPHERAL_RAW_COLS = [
    "goals", "assists", "shots", "hits", "blocks", "pm", "takeaways", "sh_goals","trailing_ppg", 
    "career_peak_ppg", "seasons_of_history"
]

POINTS_ONLY_FEATURE_COLS = [
    "ppg_shrunk", "games_played", "weekly_std", "weekly_cv", "trend_slope",
    "first_half_avg", "second_half_avg",
    "trailing_ppg", "career_peak_ppg", "seasons_of_history", "trailing_games_played",
]