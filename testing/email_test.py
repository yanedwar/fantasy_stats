import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.emailer import build_email_body
from models import PlayerStats
from scoring import get_skater, get_goalie

with open("data/weeks/2026-03-01.json", "r") as f:
    TEST = json.load(f)

if __name__ == "__main__":
    players_dict = {}
    players = TEST["playerStats"]
    start_date = TEST["weekStart"]
    end_date = TEST["weekEnd"]
    games_played = TEST["gamesPlayed"]
    for player in players.values():
        name = player["name"]
        position = player["position"]
        team = player["team"]
        points = player["points"]
        games_played = player["games_played"]
        players_dict[player["player_id"]] = PlayerStats(player["player_id"], name, team, position)
        players_dict[player["player_id"]].points = points
        players_dict[player["player_id"]].games_played = games_played
    email_body = build_email_body(players_dict, start_date, end_date, games_played)
    print(email_body)
