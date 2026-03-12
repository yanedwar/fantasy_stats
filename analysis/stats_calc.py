import json
import statistics

with open("data/season/season_2025_2026.json", "r") as f:
    STATS = json.load(f)

players = STATS["players"]

def top_ppg_forwards(min_games=5):
    forwards = [p for p in players.values() if p["position"] in ("C", "L", "R") and p["games_played"] > min_games]
    forwards.sort(key=lambda p: p["ppg"], reverse = True)
    return forwards

def top_ppg_defence(min_games=5):
    defence = [p for p in players.values() if p["position"] == "D"and p["games_played"] > min_games]
    defence.sort(key=lambda p: p["ppg"], reverse = True)
    return defence

def top_ppg_goalies(min_games=5):
    goalies = [p for p in players.values() if p["position"] == "G" and p["games_played"] > min_games]
    goalies.sort(key=lambda p: p["ppg"], reverse = True)
    return goalies

def three_hot_streak(player, n=3):
    weeks = sorted(player["weeksPoints"])
    last = [player["weeksPoints"][w] for w in weeks[-n:]]
    return sum(last) / len(last)

def hottest_players(n=15):
    eligible = [p for p in players.values() if len(p["weeksPoints"]) >= 3]

    ranked = sorted(eligible, key=lambda p: three_hot_streak(p), reverse = True)

    return ranked[:n]

def heating(player):
    return three_hot_streak(player) - player["ppg"]

def heating_up_players(n=10):
    eligible = [p for p in players.values() if len(p["weeksPoints"]) >= 3]

    ranked = sorted(eligible, key=lambda p: heating(p), reverse = True)

    return ranked[:n]

