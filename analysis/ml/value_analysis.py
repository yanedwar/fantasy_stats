import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .config import SKATER_SCORING_WEIGHTS

def format_value_composition(composition_df, n=None, decimals=1, sort_by="peripheral_share",
                              min_total_value=None):
    """
    Presentation-ready view of compute_value_composition()'s output:
    converts fractions to percentages, renames to short column headers,
    drops player_id, and sorts by whichever share you want to spotlight
    (default: peripheral_share, to surface "hits a lot, doesn't score
    much" types first -- pass sort_by="grinder_share" to specifically
    surface physical players, or sort_by="offensive_volume_share" for
    high-shot-volume players, since those two get lumped together inside
    peripheral_share otherwise). Pass min_total_value to filter out
    trivial/replacement-level players (e.g. min_total_value=50) so the
    top of the sorted list is genuinely valuable peripheral specialists
    rather than zero-goal black-aces who trivially hit 100% peripheral_share.
    """
    cols = {
        "name": "Player", "position": "Pos", "total_value": "TotalVal",
        "goals_share": "Goals%", "assists_share": "Assists%",
        "shots_share": "Shots%", "hits_share": "Hits%",
        "blocks_share": "Blocks%", "takeaways_share": "TA%",
        "pm_share": "PM%", "sh_goals_share": "SHG%",
        "scoring_share": "Scoring%", "peripheral_share": "Peripheral%",
        "offensive_volume_share": "OffVol%", "grinder_share": "Grinder%",
    }
    available = {k: v for k, v in cols.items() if k in composition_df.columns}
    out = composition_df[list(available.keys())].rename(columns=available).copy()

    pct_cols = [c for c in out.columns if c not in ("Player", "Pos", "TotalVal")]
    for c in pct_cols:
        out[c] = (out[c] * 100).round(decimals)
    if "TotalVal" in out.columns:
        out["TotalVal"] = out["TotalVal"].round(decimals)
        if min_total_value is not None:
            out = out[out["TotalVal"] >= min_total_value]

    sort_col = cols.get(sort_by, sort_by)
    if sort_col in out.columns:
        out = out.sort_values(sort_col, ascending=False)
    if n:
        out = out.head(n)
    return out.reset_index(drop=True)

def compute_value_composition(features_df, weights: pd.Series, min_games_played=20,
                               min_total_value=100):
    """
    Breaks each player's point value down by category as a % share, using
    the weights from recover_scoring_weights (or loaded directly from
    your league's scoring config). Produces a `scoring_share` (goals +
    assists), `peripheral_share` (everything else), and `total_value`
    (the player's total weighted contribution).

    min_games_played: excludes players without a meaningful sample size
    (raised from 10 -> 20; 10 games still lets brief call-ups through).

    min_total_value: excludes players whose total weighted contribution
    is too small in ABSOLUTE terms for the % shares to mean anything.
    This matters even for players who clear min_games_played, because a
    low-usage player's total can still be small or flip sign (a run of
    negative plus/minus can outweigh a handful of hits at this league's
    2.0/PM weight) -- dividing by a small-but-nonzero denominator still
    distorts every share, just less dramatically than dividing by exactly
    zero. 100 is a reasonable "clearly rostered" floor given weights that
    award 6/goal, but check the total_value distribution in your own data
    and adjust -- it should scale with how your league weights things.
    """
    peripheral_cols = list(weights.index)
    df = features_df.copy()
    if "games_played" in df.columns:
        df = df[df["games_played"] >= min_games_played]

    contributions = df[peripheral_cols].mul(weights, axis=1)
    total = contributions.sum(axis=1, skipna=False)
    shares = contributions.div(total.where(total.abs() >= min_total_value, np.nan), axis=0)
    shares.columns = [f"{c}_share" for c in shares.columns]

    out = pd.concat([df[["player_id", "name", "position"]].reset_index(drop=True),
                      shares.reset_index(drop=True)], axis=1)
    out["total_value"] = total.reset_index(drop=True)
    scoring_cols = [c for c in ["goals_share", "assists_share"] if c in out.columns]
    out["scoring_share"] = out[scoring_cols].sum(axis=1, skipna=False)
    out["peripheral_share"] = 1 - out["scoring_share"]

    # Two named slices of peripheral_share, since "everything that isn't a
    # goal or assist" bundles two genuinely different playstyles together:
    # offensive_volume_share is still offense -- pucks on net that haven't
    # (yet) counted as a goal -- while grinder_share is the physical/
    # possession game (hits, blocks, takeaways) that has nothing to do
    # with shooting the puck. A player can be high-peripheral for either
    # reason, or both, and those are very different rosters decisions.
    # pm_share is deliberately in neither: plus-minus reflects on-ice
    # context (linemates, matchups, team results) more than an individual
    # skill in either bucket, so folding it into one would misattribute
    # it. That also means scoring_share + offensive_volume_share +
    # grinder_share + pm_share = 1.0, not just the first three.
    offense_cols = [c for c in ["shots_share", "sh_goals_share"] if c in out.columns]
    out["offensive_volume_share"] = out[offense_cols].sum(axis=1, skipna=False)
    grinder_cols = [c for c in ["hits_share", "blocks_share", "takeaways_share"] if c in out.columns]
    out["grinder_share"] = out[grinder_cols].sum(axis=1, skipna=False)

    # drop players whose denominator was too unstable for the shares
    # above to mean anything, instead of returning distorted rows
    out = out[out["total_value"].abs() >= min_total_value].reset_index(drop=True)
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

def find_peripheral_value_picks(ranked_df, composition_df, top_n_per_position=60,
                                 min_peripheral_share=0.5):
    """
    Combines project_and_rank()'s output (proj_expected, position_rank)
    with compute_value_composition()'s output to surface players who are
    BOTH draftable (ranked within a realistic startable range at their
    position) AND whose value leans peripheral -- as opposed to sorting
    composition alone, which surfaces low-value players regardless of
    whether they're actually worth a roster spot. Tune
    top_n_per_position to your league's actual roster size (e.g. a
    12-team league starting 4 D needs roughly top-48-60 D to be relevant).
    """
    merged = ranked_df.merge(
        composition_df[["player_id", "peripheral_share", "scoring_share", "total_value",
                         "offensive_volume_share", "grinder_share"]],
        on="player_id", how="inner")
    qualified = merged[merged["position_rank"] <= top_n_per_position]
    qualified = qualified[qualified["peripheral_share"] >= min_peripheral_share]
    return qualified.sort_values("proj_expected", ascending=False)

def label_clusters(clustered_df, feature_cols):
    """
    Auto-generates a short descriptive label per cluster based on which
    stat(s) sit furthest above the population average, relative to that
    stat's spread (z-score). Returns {cluster_id: label_string}. Purely
    descriptive shorthand -- cross-check against describe_clusters()'s
    actual numbers before trusting a label, especially with few clusters
    or overlapping archetypes.
    """
    means = clustered_df.groupby("cluster")[feature_cols].mean()
    grand_mean = clustered_df[feature_cols].mean()
    grand_std = clustered_df[feature_cols].std()
    z = (means - grand_mean) / grand_std
    return {
        cid: " + ".join(
            row.sort_values(ascending=False).head(2).index
            .str.replace("_per_gp", "").str.replace("_", " ").str.title()
        )
        for cid, row in z.iterrows()
    }


def get_player_cluster(clustered_df, player_name, feature_cols, cluster_labels=None, ranked_df=None):
    """
    Look up which archetype cluster a specific player belongs to, by
    (partial, case-insensitive) name match -- e.g. "hathaway" matches
    "G. Hathaway". Returns their cluster id/label and stat line, and --
    if you pass ranked_df (project_and_rank()'s output) -- their
    proj_expected and position_rank too, so you see the archetype AND
    whether they're actually worth drafting in one row.
    """
    matches = clustered_df[clustered_df["name"].str.contains(player_name, case=False, na=False)]
    if matches.empty:
        return matches
    cols = ["player_id", "name", "position", "cluster"] + feature_cols
    out = matches[cols].copy()
    if cluster_labels:
        out["archetype"] = out["cluster"].map(cluster_labels)
    if ranked_df is not None:
        out = out.merge(
            ranked_df[["player_id", "proj_expected", "position_rank", "overall_rank"]],
            on="player_id", how="left")
    return out


def list_cluster_members(clustered_df, cluster_id, feature_cols, cluster_labels=None,
                          ranked_df=None, n=None):
    """
    Lists every player assigned to a given cluster. Pass ranked_df to
    sort by proj_expected descending -- this is what actually answers
    "is this archetype worth drafting, and who's the best example of it,"
    rather than just listing cluster members in arbitrary order.
    """
    members = clustered_df[clustered_df["cluster"] == cluster_id].copy()
    cols = ["player_id", "name", "position"] + feature_cols
    out = members[cols].copy()
    if cluster_labels:
        out["archetype"] = cluster_labels.get(cluster_id, str(cluster_id))
    if ranked_df is not None:
        out = out.merge(
            ranked_df[["player_id", "proj_expected", "position_rank", "overall_rank"]],
            on="player_id", how="left")
        out = out.sort_values("proj_expected", ascending=False)
    if n:
        out = out.head(n)
    return out.reset_index(drop=True)