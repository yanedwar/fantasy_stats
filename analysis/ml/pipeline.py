from pathlib import Path

from .config import DATA_DIR, GOALIE_SCORING_WEIGHTS, SKATER_SCORING_WEIGHTS
from .evaluation import evaluate_model
from .features import (
    GOALIE_FEATURE_COLS,
    SKATER_FEATURE_COLS,
    SKATER_FEATURE_COLS_P,
    build_goalie_season_features,
    build_skater_season_features,
    add_career_trailing_features
)
from .io import load_peripherals, load_season_snapshot, split_skaters_goalies
from .training import build_training_panel, train_quantile_gbm, train_quantile_linear, train_ridge


def _season_paths(season_label):
    season_root = DATA_DIR / season_label
    if season_root.exists():
        snapshot_path = season_root / "season" / f"season_{season_label.replace('-', '_')}.json"
        peripherals_path = season_root / "peripherals" / "season_peripherals.json"
        if snapshot_path.exists() and peripherals_path.exists():
            return snapshot_path, peripherals_path

    snapshot_path = DATA_DIR / "season" / f"season_{season_label.replace('-', '_')}.json"
    peripherals_path = DATA_DIR / "peripherals" / f"season_peripherals.json"
    return snapshot_path, peripherals_path


def load_season_bundle(season_label):
    snapshot_path, peripherals_path = _season_paths(season_label)
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Season snapshot not found for {season_label}: {snapshot_path}")
    if not peripherals_path.exists():
        raise FileNotFoundError(f"Peripheral file not found for {season_label}: {peripherals_path}")

    snapshot_df = load_season_snapshot(snapshot_path, season_label)
    peripherals_df = load_peripherals(peripherals_path, season_label)
    skaters_df, goalies_df = split_skaters_goalies(peripherals_df)

    skater_features = build_skater_season_features(
        snapshot_df[snapshot_df["position"].isin({"C", "L", "R", "D"})].copy(),
        skaters_df,
    )
    goalie_features = build_goalie_season_features(
        snapshot_df[snapshot_df["position"] == "G"].copy(),
        goalies_df,
    )

    return {
        "season_label": season_label,
        "snapshot": snapshot_df,
        "peripherals": peripherals_df,
        "skater_features": skater_features,
        "goalie_features": goalie_features,
        "skater_scoring_weights": SKATER_SCORING_WEIGHTS,
        "goalie_scoring_weights": GOALIE_SCORING_WEIGHTS,
    }


def build_projection_inputs_for_repo():
    season_files = sorted((DATA_DIR / "season").glob("season_*.json"))
    if not season_files:
        raise FileNotFoundError("No season snapshot files were found in data/season")

    season_label = season_files[-1].stem.replace("season_", "").replace("_", "-")
    return load_season_bundle(season_label)


def build_season_feature_map(season_labels):
    bundles = {season_label: load_season_bundle(season_label) for season_label in season_labels}
    return {
        "skaters": {season_label: bundle["skater_features"] for season_label, bundle in bundles.items()},
        "goalies": {season_label: bundle["goalie_features"] for season_label, bundle in bundles.items()},
        "bundles": bundles,
    }


def train_models_from_seasons(season_labels):
    feature_map = build_season_feature_map(season_labels)

    feature_map["skaters"] = add_career_trailing_features(feature_map["skaters"])
    feature_map["goalies"] = add_career_trailing_features(feature_map["goalies"])

    skater_panel = build_training_panel(feature_map["skaters"])
    goalie_panel = build_training_panel(feature_map["goalies"])

    skater_ridge = train_ridge(skater_panel, SKATER_FEATURE_COLS)
    goalie_ridge = train_ridge(goalie_panel, GOALIE_FEATURE_COLS)

    skater_quantiles = train_quantile_gbm(skater_panel, SKATER_FEATURE_COLS)
    goalie_quantiles = train_quantile_gbm(goalie_panel, GOALIE_FEATURE_COLS)

    #skater_quantiles = train_quantile_linear(skater_panel, SKATER_FEATURE_COLS)
    #goalie_quantiles = train_quantile_linear(goalie_panel, GOALIE_FEATURE_COLS)

    latest_label = sorted(season_labels)[-1]
    latest_bundle = feature_map["bundles"][latest_label]

    skater_mae = evaluate_model(skater_ridge, skater_panel, SKATER_FEATURE_COLS)
    goalie_mae = evaluate_model(goalie_ridge, goalie_panel, GOALIE_FEATURE_COLS)

    return {
        "season_labels": season_labels,
        "latest_label": latest_label,
        "skater_panel": skater_panel,
        "goalie_panel": goalie_panel,
        "skater_ridge": skater_ridge,
        "goalie_ridge": goalie_ridge,
        "skater_quantiles": skater_quantiles,
        "goalie_quantiles": goalie_quantiles,
        "latest_skater_features": feature_map["skaters"][latest_label],
        "latest_goalie_features": feature_map["goalies"][latest_label],
        "skater_mae": skater_mae,
        "goalie_mae": goalie_mae,
    }


def main(season_labels=None):
    if season_labels is None:
        data = build_projection_inputs_for_repo()
        print(f"Loaded season {data['season_label']}")
        print(f"Skater feature rows: {len(data['skater_features'])}")
        print(f"Goalie feature rows: {len(data['goalie_features'])}")
        return data

    results = train_models_from_seasons(season_labels)
    print(f"Trained on seasons: {', '.join(results['season_labels'])}")
    print(f"Skater training MAE: {results['skater_mae']:.2f}")
    print(f"Goalie training MAE: {results['goalie_mae']:.2f}")
    return results


if __name__ == "__main__":
    import sys

    main(sys.argv[1:] or None)
