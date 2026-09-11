import importlib.util
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import QuantileRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_training_panel(season_features_by_year: dict, target_col="season_points"):
    seasons_sorted = sorted(season_features_by_year.keys())
    panels = []
    skipped = []
    for prev_s, next_s in zip(seasons_sorted[:-1], seasons_sorted[1:]):
        # zip() only guarantees these are adjacent in the sorted list, not
        # adjacent on the calendar. A caller passing in a season list with
        # a gap (e.g. skipping a lockout/pandemic-shortened year) would
        # otherwise silently get paired as if it were a normal one-year-ahead
        # transition, training on a multi-year jump labeled as a single year.
        prev_start = int(prev_s.split("-")[0])
        next_start = int(next_s.split("-")[0])
        if next_start != prev_start + 1:
            skipped.append((prev_s, next_s))
            continue
        prev_df = season_features_by_year[prev_s].copy()
        next_df = season_features_by_year[next_s][["player_id", target_col]].rename(
            columns={target_col: "target_next_season_points"})
        merged = prev_df.merge(next_df, on="player_id", how="inner")
        merged["feature_season"] = prev_s
        merged["target_season"] = next_s
        panels.append(merged)
    if skipped:
        warnings.warn(
            f"build_training_panel: skipped non-consecutive season pairs {skipped} "
            "-- these seasons were passed in but aren't calendar-adjacent, so "
            "pairing them as a one-year-ahead transition would be wrong.",
            RuntimeWarning,
            stacklevel=2,
        )
    if not panels:
        return pd.DataFrame(columns=["player_id", "target_next_season_points"])
    return pd.concat(panels, ignore_index=True)


def baseline_projection(df, ppg_col="ppg", games_col="games_played",
                         league_avg_games=82, shrink_games=20):
    pos_mean = df.groupby("position")["ppg"].transform("mean")
    weight = df[games_col] / (df[games_col] + shrink_games)
    shrunk_ppg = weight * df[ppg_col] + (1 - weight) * pos_mean
    return shrunk_ppg * league_avg_games


def train_ridge(panel_df, feature_cols, target_col="target_next_season_points", alpha=5.0):
    df = panel_df.dropna(subset=[target_col]).copy()
    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df[target_col]
    model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
    model.fit(X, y)
    return model


def train_quantile_gbm(panel_df, feature_cols, target_col="target_next_season_points",
                        quantiles=(0.1, 0.5, 0.9), random_state=42):
    if importlib.util.find_spec("lightgbm") is not None:
        lgb = __import__("lightgbm")
    else:
        lgb = None
        warnings.warn(
            "lightgbm is not installed -- falling back to sklearn's "
            "GradientBoostingRegressor. This is NOT an equivalent substitute: "
            "at ~900+ skaters it produces visibly coarser, less-resolved "
            "predictions (many players sharing the exact same floor/ceiling "
            "value), and that coarseness gets WORSE, not better, as more "
            "training seasons are added. `pip install lightgbm` before "
            "trusting any board built on this fallback.",
            RuntimeWarning,
            stacklevel=2,
        )

    df = panel_df.dropna(subset=[target_col]).copy()
    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df[target_col]
    models = {}

    if lgb is not None:
        for q in quantiles:
            m = lgb.LGBMRegressor(
                objective="quantile", alpha=q, n_estimators=450, learning_rate=0.0075,
                max_depth=3, num_leaves=7, min_child_samples=25, verbosity=-1,
                random_state=random_state, deterministic=True, n_jobs=1,
            )
            m.fit(X, y)
            models[q] = m
        return models

    for q in quantiles:
        m = GradientBoostingRegressor(
            loss="quantile",
            alpha=q,
            n_estimators=200,
            learning_rate=0.03,
            max_depth=3,
            min_samples_split=25,
            random_state=random_state,
        )
        m.fit(X, y)
        models[q] = m
    return models

def train_quantile_linear(panel_df, feature_cols, target_col="target_next_season_points",
                           quantiles=(0.1, 0.5, 0.9), alpha=0.01):
    """
    Linear alternative to train_quantile_gbm -- much lower variance at
    small sample sizes (a single season-pair of ~700-800 skaters), since
    it's a smooth function of the features rather than a small number of
    step-function leaves. USE THIS as your primary model until you have
    3+ seasons of real data; switch back to comparing against the GBM
    once evaluate_forward_chaining can actually validate which one wins.
    """
    df = panel_df.dropna(subset=[target_col]).copy()
    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df[target_col]
    models = {}
    for q in quantiles:
        m = Pipeline([
            ("scale", StandardScaler()),
            ("q", QuantileRegressor(quantile=q, alpha=alpha, solver="highs")),
        ])
        m.fit(X, y)
        models[q] = m
    return models


def project_and_rank(models, current_season_features, feature_cols):
    df = current_season_features.copy()
    X = df[feature_cols].fillna(df[feature_cols].median())
    df["proj_floor"] = models[min(models)].predict(X)
    df["proj_expected"] = models[0.5].predict(X) if 0.5 in models else np.nan
    df["proj_ceiling"] = models[max(models)].predict(X)

    # Each quantile above is its own independently-fit model, so nothing
    # stops them from disagreeing on ordering for a given player -- e.g.
    # the "ceiling" (0.9) model predicting a lower number than the
    # "expected" (0.5) model predicts for that same player ("quantile
    # crossing"). Rare (a handful of players out of ~900+), but when it
    # happens it produces a visibly nonsensical line like a ceiling below
    # the projection. Sorting each player's three predicted values
    # (floor <= expected <= ceiling) is the standard fix for this
    # (Chernozhukov et al. 2010's rearrangement approach) -- it's a
    # no-op for every row that wasn't crossed, and just relabels which
    # number is "floor" vs "ceiling" for the rows that were.
    quantile_cols = ["proj_floor", "proj_expected", "proj_ceiling"]
    df[quantile_cols] = np.sort(df[quantile_cols].to_numpy(), axis=1)

    df["boom_bust_range"] = df["proj_ceiling"] - df["proj_floor"]

    df["position_rank"] = df.groupby("position")["proj_expected"].rank(
        ascending=False, method="min")
    df["overall_rank"] = df["proj_expected"].rank(ascending=False, method="min")

    # trailing_ppg/career_peak_ppg/seasons_of_history all lean on the same
    # thing: multi-season history. For a player with 0-1 prior seasons,
    # those columns are either a copy of this year's own ppg (see
    # add_career_trailing_features's NaN fallback) or a single thin season
    # -- not the stabilizing signal they are for a 5-6 year veteran. The
    # model has very few training examples of "immediate-impact player
    # breaks out further in year 2" to learn from (there are only three
    # such players in this dataset, and turning one into a special case
    # in a global feature didn't backtest as an improvement -- see
    # skater_notes.md), so rather than quietly guess, flag it: treat
    # these projections as lower-confidence and worth a manual look.
    df["limited_history"] = df["seasons_of_history"] <= 1

    return df.sort_values("proj_expected", ascending=False)

def format_projection_board(ranked_df, n=None, decimals=1):
    """
    Presentation-ready view of project_and_rank()'s output: just the
    columns you'd want at the draft table, renamed, rounded, and reset to
    a clean index. Pass n to limit to the top N rows. Works directly with
    df.to_string(index=False) for a terminal table, .to_csv() for a
    spreadsheet, or plain display in a notebook.
    """
    cols = {
        "overall_rank": "Rank", "position_rank": "PosRk", "name": "Player",
        "team": "Team", "position": "Pos", "proj_floor": "Floor",
        "proj_expected": "Projected", "proj_ceiling": "Ceiling",
        "boom_bust_range": "Range", "limited_history": "Flag",
    }
    out = ranked_df[list(cols.keys())].rename(columns=cols)
    out[["Rank", "PosRk"]] = out[["Rank", "PosRk"]].astype(int)
    for c in ["Floor", "Projected", "Ceiling", "Range"]:
        out[c] = out[c].round(decimals)
    out["Flag"] = out["Flag"].map({True: "LTD HIST", False: ""})
    if n:
        out = out.head(n)
    return out.reset_index(drop=True)