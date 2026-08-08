import importlib.util

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_training_panel(season_features_by_year: dict, target_col="season_points"):
    seasons_sorted = sorted(season_features_by_year.keys())
    panels = []
    for prev_s, next_s in zip(seasons_sorted[:-1], seasons_sorted[1:]):
        prev_df = season_features_by_year[prev_s].copy()
        next_df = season_features_by_year[next_s][["player_id", target_col]].rename(
            columns={target_col: "target_next_season_points"})
        merged = prev_df.merge(next_df, on="player_id", how="inner")
        merged["feature_season"] = prev_s
        merged["target_season"] = next_s
        panels.append(merged)
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
                        quantiles=(0.1, 0.5, 0.9)):
    if importlib.util.find_spec("lightgbm") is not None:
        lgb = __import__("lightgbm")
    else:
        lgb = None

    df = panel_df.dropna(subset=[target_col]).copy()
    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df[target_col]
    models = {}

    if lgb is not None:
        for q in quantiles:
            m = lgb.LGBMRegressor(
                objective="quantile", alpha=q, n_estimators=200, learning_rate=0.03,
                max_depth=3, num_leaves=7, min_child_samples=15, verbosity=-1,
            )
            m.fit(X, y)
            models[q] = m
        return models

    for q in quantiles:
        m = GradientBoostingRegressor(
            n_estimators=120,
            learning_rate=0.05,
            max_depth=2,
            random_state=42,
        )
        m.fit(X, y)
        models[q] = m
    return models


def project_and_rank(models, current_season_features, feature_cols):
    df = current_season_features.copy()
    X = df[feature_cols].fillna(df[feature_cols].median())
    df["proj_floor"] = models[min(models)].predict(X)
    df["proj_expected"] = models[0.5].predict(X) if 0.5 in models else np.nan
    df["proj_ceiling"] = models[max(models)].predict(X)
    df["boom_bust_range"] = df["proj_ceiling"] - df["proj_floor"]

    df["position_rank"] = df.groupby("position")["proj_expected"].rank(
        ascending=False, method="min")
    df["overall_rank"] = df["proj_expected"].rank(ascending=False, method="min")
    return df.sort_values("proj_expected", ascending=False)
