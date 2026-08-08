import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .config import SKATER_SCORING_WEIGHTS


def compute_value_composition(features_df, weights=None):
    if weights is None:
        weights = SKATER_SCORING_WEIGHTS
    if not isinstance(weights, pd.Series):
        weights = pd.Series(weights, dtype=float)

    peripheral_cols = list(weights.index)
    df = features_df.copy()
    for col in peripheral_cols:
        if col not in df.columns:
            df[col] = 0

    contributions = df[peripheral_cols].fillna(0).mul(weights, axis=1)
    total = contributions.sum(axis=1).replace(0, np.nan)
    shares = contributions.div(total, axis=0)
    shares.columns = [f"{c}_share" for c in shares.columns]

    out = pd.concat([
        df[["player_id", "name", "position"]].reset_index(drop=True),
        shares.reset_index(drop=True),
    ], axis=1)
    scoring_cols = [c for c in ["goals_share", "assists_share"] if c in out.columns]
    out["scoring_share"] = out[scoring_cols].sum(axis=1)
    out["peripheral_share"] = 1 - out["scoring_share"]
    return out


def cluster_player_archetypes(features_df, feature_cols=None, n_clusters=5, random_state=42):
    feature_cols = feature_cols or [
        "goals_per_gp", "assists_per_gp", "shots_per_gp", "hits_per_gp",
        "blocks_per_gp", "takeaways_per_gp",
    ]
    df = features_df.dropna(subset=feature_cols).copy()
    scaler = StandardScaler()
    X = scaler.fit_transform(df[feature_cols])
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df["cluster"] = km.fit_predict(X)
    return df, km, scaler


def describe_clusters(clustered_df, feature_cols):
    return clustered_df.groupby("cluster")[feature_cols].mean().round(3)
