from analysis.ml.config import SKATER_SCORING_WEIGHTS
from analysis.ml.features import SKATER_FEATURE_COLS, SKATER_FEATURE_COLS_P
from analysis.ml.pipeline import train_models_from_seasons
from analysis.ml.training import project_and_rank
from analysis.ml.value_analysis import (find_peripheral_value_picks, format_value_composition, compute_value_composition, cluster_player_archetypes, describe_clusters, label_clusters)

results = train_models_from_seasons(["2018-2019", "2019-2020", "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"])

latest = results["latest_skater_features"]
weights = SKATER_SCORING_WEIGHTS
print("\nScoring weights loaded from config/scoring_settings.json:\n", weights.to_string())

skater_board = project_and_rank(
    results["skater_quantiles"],
    results["latest_skater_features"],
    SKATER_FEATURE_COLS_P,
)


composition = compute_value_composition(latest, weights)
peripheral_value = find_peripheral_value_picks(skater_board, composition)
print("\nTop 10 peripheral value picks (ranked by projected points):")
print(format_value_composition(peripheral_value, n=10, sort_by="proj_expected"))
 
clustered, kmeans_model, scaler = cluster_player_archetypes(latest, n_clusters=4)
print("\nArchetype cluster profiles:")
print(describe_clusters(clustered, ["goals_per_gp", "assists_per_gp", "shots_per_gp",
                                     "hits_per_gp", "blocks_per_gp", "takeaways_per_gp"]))
print(label_clusters(clustered, ["goals_per_gp", "assists_per_gp", "shots_per_gp",
                                     "hits_per_gp", "blocks_per_gp", "takeaways_per_gp"]))