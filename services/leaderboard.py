import json

with open("config/scoring_settings.json", "r") as f:
    SETTINGS = json.load(f)

def top_forwards(players):
    forwards = [p for p in players.values() if p.position == "C" or p.position == "R" or p.position == "L"]
    forwards.sort(key=lambda p: p.points, reverse = True)
    return forwards[:SETTINGS["topForwards"]]

def top_defence(players):
    defence = [p for p in players.values() if p.position == "D"]
    defence.sort(key=lambda p: p.points, reverse = True)
    return defence[:SETTINGS["topDefence"]]

def top_goalies(players):
    goalies = [p for p in players.values() if p.position == "G"]
    goalies.sort(key=lambda p: p.points, reverse = True)
    return goalies[:SETTINGS["topGoalies"]]

