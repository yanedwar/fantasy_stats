import json

with open("config/scoring_settings.json", "r") as f:
    SETTINGS = json.load(f)

GOALIE_SET = SETTINGS["goalieScoring"]

def get_goalie(player, goals, assists, sh_goals, win, otl, shutout, saves, g_against, nine_one):
        player.games_played += 1
        player.points += (
            GOALIE_SET["goal"] * goals + 
            GOALIE_SET["assist"] * assists + 
            GOALIE_SET["shortHandedGoal"] * sh_goals + 
            GOALIE_SET["win"] * win + 
            GOALIE_SET["otl"] * otl + 
            GOALIE_SET["shutout"] * shutout + 
            GOALIE_SET["save"] * saves + 
            GOALIE_SET["goalAgainst"] * g_against + 
            GOALIE_SET["nineOne"] * nine_one
        )
        player.points = round(player.points, 1)