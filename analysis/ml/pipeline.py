from .config import DATA_DIR, GOALIE_SCORING_WEIGHTS, SKATER_SCORING_WEIGHTS
from .features import build_goalie_season_features, build_skater_season_features
from .io import load_peripherals, load_season_snapshot, split_skaters_goalies


def build_projection_inputs_for_repo():
    season_files = sorted((DATA_DIR / "season").glob("season_*.json"))
    if not season_files:
        raise FileNotFoundError("No season snapshot files were found in data/season")

    season_path = season_files[-1]
    season_label = season_path.stem.replace("season_", "").replace("_", "-")
    snapshot_df = load_season_snapshot(season_path, season_label)
    peripherals_df = load_peripherals(DATA_DIR / "peripherals" / "season_peripherals.json", season_label)

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
        "skater_features": skater_features,
        "goalie_features": goalie_features,
        "skater_scoring_weights": SKATER_SCORING_WEIGHTS,
        "goalie_scoring_weights": GOALIE_SCORING_WEIGHTS,
    }


def main():
    data = build_projection_inputs_for_repo()
    print(f"Loaded season {data['season_label']}")
    print(f"Skater feature rows: {len(data['skater_features'])}")
    print(f"Goalie feature rows: {len(data['goalie_features'])}")


if __name__ == "__main__":
    main()
