import json

with open("data/season/season_2025_2026.json", "r") as f:
    STATS = json.load(f)

players = STATS["players"]

def top_ppg_forwards():
    forwards = [p for p in players.values() if p["position"] in ("C", "L", "R")]
    forwards.sort(key=lambda p: p["ppg"], reverse = True)
    return forwards

def top_ppg_defence():
    defence = [p for p in players.values() if p["position"] == "D"]
    defence.sort(key=lambda p: p["ppg"], reverse = True)
    return defence

def top_ppg_goalies():
    goalies = [p for p in players.values() if p["position"] == "G"]
    goalies.sort(key=lambda p: p["ppg"], reverse = True)
    return goalies

