from analysis.ml.pipeline import train_models_from_seasons
from analysis.ml.training import project_and_rank, format_projection_board
from analysis.ml.features import SKATER_FEATURE_COLS, GOALIE_FEATURE_COLS

results = train_models_from_seasons(["2018-2019","2019-2020", "2020-2021","2021-2022", "2022-2023","2023-2024","2024-2025", "2025-2026"])

skater_board = project_and_rank(
    results["skater_quantiles"],
    results["latest_skater_features"],
    SKATER_FEATURE_COLS,
)

goalie_board = project_and_rank(
    results["goalie_quantiles"],
    results["latest_goalie_features"],
    GOALIE_FEATURE_COLS,
)

print("Skater Projections:")
print(format_projection_board(skater_board, n=10).to_string(index=False))
 
print("\nGoalie Projections:")
print(format_projection_board(goalie_board, n=50).to_string(index=False))