from models.game import Game
from services.short_handed_goals import get_short_handed_goals

def game_info(game, date):
    game_id = game.get("id")
    away_team = game.get("awayTeam", {}).get("commonName",{}).get("default")
    away_team_id = game.get("awayTeam", {}).get("id")
    home_team = game.get("homeTeam", {}).get("commonName",{}).get("default")
    home_team_id = game.get("homeTeam", {}).get("id")
    shg_scorers = get_short_handed_goals(game_id, away_team_id, home_team_id)
    print(f"{away_team} vs {home_team} on {date}")
    return Game(game_id, date, away_team, home_team, shg_scorers)

def get_games(data):
    games_week = []
    
    for day in data.get("gameWeek", []):
        date = day.get("date", {})
        for game in day.get("games", []):
            if game["gameType"] != 2:
                continue
            games_week.append(game_info(game, date))

    return games_week