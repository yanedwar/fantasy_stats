import pandas as pd
from sklearn.metrics import mean_absolute_error

from .training import baseline_projection, build_training_panel, train_ridge


def evaluate_model(model, df, feature_cols, target_col="target_next_season_points"):
    df = df.dropna(subset=[target_col]).copy()
    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df[target_col]
    preds = model.predict(X)
    return mean_absolute_error(y, preds)


def evaluate_forward_chaining(season_features_by_year, feature_cols,
                               target_col="target_next_season_points"):
    seasons_sorted = sorted(season_features_by_year.keys())
    results = []
    for i in range(2, len(seasons_sorted)):
        train_years = seasons_sorted[:i]
        test_pair = (seasons_sorted[i - 1], seasons_sorted[i])

        train_panel = build_training_panel(
            {y: season_features_by_year[y] for y in train_years})
        test_panel = build_training_panel(
            {y: season_features_by_year[y] for y in test_pair})

        ridge = train_ridge(train_panel, feature_cols)
        mae_ridge = evaluate_model(ridge, test_panel, feature_cols)

        valid = test_panel.dropna(subset=[target_col])
        naive_pred = baseline_projection(valid)
        mae_naive = mean_absolute_error(valid[target_col], naive_pred)

        results.append({
            "test_season": test_pair[1],
            "n_players": len(valid),
            "mae_naive_baseline": round(mae_naive, 2),
            "mae_ridge": round(mae_ridge, 2),
        })
    return pd.DataFrame(results)
