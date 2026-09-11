import argparse
import json
from datetime import date, timedelta
from get_peripherals import GoaliePeripherals, SkaterPeripherals, append_peripherals_to_season, save_week_peripherals
from models import PlayerStats
from analysis.aggregation import build_season_totals, save_season_totals, season_from_date
from api.schedule import get_week_schedule
from api.gamecenter import get_boxscore
from services.emailer import send_weekly_email, build_email_body
from services.games import get_games
from services.goalie_points import get_goalie_points
from services.store import store_week, week_exists
from scoring import get_skater, get_goalie

def parse_date(value):
    return date.fromisoformat(value)

def get_last_week(today=None):
    if today is None:
        today = date.today()

    return today - timedelta(days=7)

def get_last_last_sunday(today=None):
    if today is None:
        today = date.today()
    subtract = (today.weekday() + 1) % 7
    return today - timedelta(days=7+subtract)

def process_week(start_date, args, send_email=False, overwrite=False):
    season = season_from_date(start_date)

    ## GAMES
    sch_data = get_week_schedule(start_date)
    games_week = get_games(sch_data)

    end_date = start_date + timedelta(days=6)

    ## PLAYERS
    players = {}

    ## PERIPHERALS
    peripherals = {}

    ## PROCESS THE GAMES
    for game in games_week:
        game_data = get_boxscore(game.id)

        for side in ("homeTeam", "awayTeam"):
            
            team_players = game_data.get("playerByGameStats", {}).get(side, {})
            for skater in team_players.get("forwards", []) + team_players.get("defense", []):
                player_id = skater.get("playerId")
                name = skater["name"]["default"]
                team = game_data.get(side, {}).get("abbrev")
                position = skater["position"]

                if player_id not in players:
                    players[player_id] =  PlayerStats(player_id, name, team, position)

                goals = skater.get("goals", 0)
                assists = skater.get("assists", 0)
                shots = skater.get("sog", 0)
                hits = skater.get("hits", 0)
                blocks = skater.get("blockedShots", 0)
                pm = skater.get("plusMinus", 0)
                takeaways = skater.get("takeaways", 0)

                sh_goals = 0
                if len(game.shg_scorers) > 0:
                    for scorer in game.shg_scorers:
                        if scorer == player_id:
                            sh_goals += 1

                get_skater(players[player_id], goals, assists, shots, sh_goals, hits, blocks, pm, takeaways)
                
                if player_id not in peripherals:
                    peripherals[player_id] = SkaterPeripherals(player_id, name, team, position)

                peripherals[player_id].goals += goals
                peripherals[player_id].assists += assists
                peripherals[player_id].shots += shots
                peripherals[player_id].hits += hits
                peripherals[player_id].blocks += blocks
                peripherals[player_id].pm += pm
                peripherals[player_id].takeaways += takeaways
                peripherals[player_id].sh_goals += sh_goals

            for goalie in team_players.get("goalies", []):
                if goalie.get("toi") != "00:00":
                    if goalie.get("savePctg") is None:
                        continue

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

                    if player_id not in peripherals:
                        peripherals[player_id] = GoaliePeripherals(player_id, name, team, position)
                    
                    peripherals[player_id].goals += goals
                    peripherals[player_id].assists += assists
                    peripherals[player_id].sh_goals += sh_goals
                    peripherals[player_id].win += win
                    peripherals[player_id].otl += otl
                    peripherals[player_id].shutout += shutout
                    peripherals[player_id].saves += saves
                    peripherals[player_id].g_against -= g_against
                    peripherals[player_id].nine_one += nine_one

    if len(games_week) > 0:
        try:
            if week_exists(start_date) and not overwrite:
                print(f"Week {start_date} already processed. Skipping save.")
                saved = None
            else:
                file_path = store_week(players, start_date, end_date, len(games_week), overwrite=overwrite)
                save_week_peripherals(peripherals, start_date)
                append_peripherals_to_season(peripherals, start_date)
                print(f"Saved weekly data to {file_path}")
                saved = file_path

            season_totals = build_season_totals(season)
            save_season_totals(season_totals, season)

            email_body = build_email_body(players, start_date, end_date, len(games_week))
            if args.print_data or not send_email:
                print(email_body)
            else:
                if not args.print_email:
                    send_weekly_email(email_body)

            return saved
        except FileExistsError:
            print(f"Weekly data for {start_date} already exists and overwrite=False; skipping.")
            return None

    else:
        print(f"No games found for the week of {start_date} to {end_date}. No data saved or email sent.")
        return None


def process_season(season_str, args):
    parts = season_str.split("-")
    if len(parts) != 2:
        raise ValueError("Season must be in the form YYYY-YYYY, e.g. 2025-2026")
    start_year = int(parts[0])
    end_year = int(parts[1])

    start = date(start_year, 7, 1)
    end = date(end_year, 6, 30)

    # find first Sunday on or after start
    days_to_sunday = (6 - start.weekday()) % 7
    current = start + timedelta(days=days_to_sunday)

    saved_files = []
    while current <= end:
        print(f"Processing week starting {current}")
        saved = process_week(current, args, send_email=False, overwrite=args.overwrite)
        if saved:
            saved_files.append(str(saved))
        current = current + timedelta(days=7)

    season_totals = build_season_totals(season_str)
    save_season_totals(season_totals, season_str)
    print(f"Processed season {season_str}; saved {len(saved_files)} weeks.")
    return saved_files

def main():
    parser = argparse.ArgumentParser(
        prog='NHL fantasy stats',
        description='Run NHL fantasy stats or add arguments for testing')
    parser.add_argument('-e', '--print_email', action='store_true', help='Print only email body for testing')
    parser.add_argument('-d', '--print_data', action='store_true', help='Run data collection and print email body for testing')
    parser.add_argument('--start-date', type=parse_date, help='Override the week start date in YYYY-MM-DD format')
    parser.add_argument('--season', help='Process an entire season, e.g. 2022-2023')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing week files when processing a season')
    args = parser.parse_args()

    email = False

    if args.start_date:
        start_date = args.start_date
    elif args.print_data:
        start_date = get_last_last_sunday()
    else:
        start_date = get_last_week()
        email = True

    if args.print_email:
        with open(f"data/weeks/{start_date}.json", "r") as f:
            TEST = json.load(f)
        players_dict = {}
        players = TEST["playerStats"]
        start_date = TEST["weekStart"]
        end_date = TEST["weekEnd"]
        games_played_week = TEST["gamesPlayed"]
        for player in players.values():
            name = player["name"]
            position = player["position"]
            team = player["team"]
            points = player["points"]
            games_played = player["games_played"]
            players_dict[player["player_id"]] = PlayerStats(player["player_id"], name, team, position)
            players_dict[player["player_id"]].points = points
            players_dict[player["player_id"]].games_played = games_played
        email_body = build_email_body(players_dict, start_date, end_date, games_played_week)
        print(email_body)
        return 0

    if args.season:
        process_season(args.season, args)
        return 0
    
    process_week(start_date, args, send_email=email, overwrite=False)
    return 0

if __name__ == "__main__":
    main()