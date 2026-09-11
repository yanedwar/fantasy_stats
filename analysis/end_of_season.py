import argparse
import json
import matplotlib.pyplot as plt
from aggregation import build_season_totals, save_season_totals
from stats_calc import order_season_by_points, order_season_by_ppg

def save_points_leaders(season):
    points_leaders = order_season_by_points(season)
    with open("data/season/points_leaders.json", "w") as f:
        json.dump(points_leaders, f, indent=2)

def save_points_per_game_leaders(season):
    ppg_leaders = order_season_by_ppg(season)
    with open("data/season/ppg_leaders.json", "w") as f:
        json.dump(ppg_leaders, f, indent=2)

def plot_points_vs_ppg(season):
    points = [p["points"] for p in season.values()]
    ppg = [p["ppg"] for p in season.values()]

    plt.scatter(points, ppg)
    plt.xlabel("Total Points")
    plt.ylabel("Points Per Game")
    plt.title("Total Points vs Points Per Game")
    plt.grid()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Build and save a season snapshot")
    parser.add_argument("--season", help="Season label such as 2024-2025")
    parser.add_argument("--plot", action="store_true", help="Show a points vs ppg scatter plot")
    args = parser.parse_args()

    season = build_season_totals(args.season)
    save_season_totals(season, args.season)

    if args.plot:
        plot_points_vs_ppg(season)


if __name__ == "__main__":
    main()