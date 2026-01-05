from datetime import date, timedelta
from models import PlayerStats
from api.schedule import get_week_schedule
from api.gamecenter import get_boxscore
from emailer import send_weekly_email
from services.games import get_games
from services.goalie_points import get_goalie_points
from scoring import get_skater, get_goalie

def build_email_body(players, start_date, end_date, games_played):
    lines = []

    sorted_players = sorted(players.values(), key=lambda p: p.points, reverse = True)
    top_30 = sorted_players[:30]    
    lines.append(f"For the week of {start_date} to {end_date}:")
    lines.append("=" * 40)
    lines.append("")

    for p in top_30:
        lines.append(f"{p.name:<20} ({p.team} | {p.position}) - {p.points} pts in {p.games_played} games")

    lines.append(f"Total number of games this week: {games_played}")

    return "\n".join(lines)

def get_last_sunday(today=None):
    if today is None:
        today = date.today()
    return today - timedelta(days=(today.weekday() + 1) % 7)

def main():
    ## START DATE
    start_date = date(2025, 12, 27)
    #start_date = get_last_sunday()

    ## GAMES
    sch_data = get_week_schedule(start_date)
    games_week = get_games(sch_data)

    end_date = start_date + timedelta(days=6)

    ## PLAYERS
    players = {}

    ## PROCESS THE GAMES
    for game in games_week:
        game_data = get_boxscore(game.id)

        for side in ("homeTeam", "awayTeam"):
        
            team_players = game_data.get("playerByGameStats", {}).get(side)
            for forward in team_players["forwards"] + team_players["defense"]:
                player_id = forward.get("playerId")
                name = forward["name"]["default"]
                team = game_data.get(side, {}).get("abbrev")
                position = forward["position"]

                if player_id not in players:
                    players[player_id] =  PlayerStats(player_id, name, team, position)

                goals = forward.get("goals", 0)
                assists = forward.get("assists", 0)
                shots = forward.get("sog", 0)
                hits = forward.get("hits", 0)
                blocks = forward.get("blockedShots", 0)
                pm = forward.get("plusMinus", 0)
                takeaways = forward.get("takeaways", 0)

                sh_goals = 0
                if len(game.shg_scorers) > 0:
                    for scorer in game.shg_scorers:
                        if scorer == player_id:
                            sh_goals += 1

                get_skater(players[player_id], goals, assists, shots, sh_goals, hits, blocks, pm, takeaways)

            for goalie in team_players["goalies"]:
                if goalie.get("toi") != "00:00":
                    player_id = goalie.get("playerId")
                    name = goalie["name"]["default"]
                    team = game_data.get(side, {}).get("abbrev")
                    position = goalie["position"]

                    if player_id not in players:
                        players[player_id] =  PlayerStats(player_id, name, team, position)

                    points = get_goalie_points(game.id, player_id)
                    goals = points["goals"]
                    assists = points["assists"]
                    
                    sh_goals = 0
                    if len(game.shg_scorers) > 0:
                        for scorer in game.shg_scorers:
                            if scorer == player_id:
                                sh_goals += 1

                    win = 0
                    otl = 0
                    shutout = 0
                    saves = goalie.get("saves", 0)
                    g_against = goalie.get("goalsAgainst", 0)
                    nine_one = 0

                    if goalie.get("decision") == "W":
                        win = 1
                    elif goalie.get("decision") == "O":
                        otl = 1
                    
                    if goalie.get("savePctg") >= 0.91:
                        nine_one = 1
                        if goalie.get("savePctg") == 1.0:
                            shutout = 1

                    get_goalie(players[player_id], goals, assists, sh_goals, win, otl, shutout, saves, g_against, nine_one)

    email_body = build_email_body(players, start_date, end_date, len(games_week))
    send_weekly_email(email_body)

if __name__ == "__main__":
    main()