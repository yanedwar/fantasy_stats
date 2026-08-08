import json
from datetime import date
from pathlib import Path
from api.schedule import get_week_schedule
from api.gamecenter import get_boxscore
from services.games import get_games
from services.goalie_points import get_goalie_points


def _season_str_from_date(d):
    if d.month >= 7:
        start = d.year
    else:
        start = d.year - 1
    return f"{start}-{start + 1}"


def _peripherals_dir_for_date(d: date) -> Path:
    season = _season_str_from_date(d)
    p = Path("data") / season / "peripherals"
    p.mkdir(parents=True, exist_ok=True)
    return p

class SkaterPeripherals:
    def __init__(self, player_id, name, team, position):
        self.id = player_id
        self.name = name
        self.team = team
        self.position = position
        self.goals = 0
        self.assists = 0
        self.shots = 0
        self.hits = 0
        self.blocks = 0
        self.pm = 0
        self.takeaways = 0
        self.sh_goals = 0

class GoaliePeripherals:
    def __init__(self, player_id, name, team, position):
        self.id = player_id
        self.name = name
        self.team = team
        self.position = position
        self.goals = 0
        self.assists = 0
        self.sh_goals = 0
        self.win = 0
        self.otl = 0
        self.shutout = 0
        self.saves = 0
        self.g_against = 0
        self.nine_one = 0

def get_week_peripherals(start_date):
    peripherals = {}

    sch_data = get_week_schedule(start_date)
    games_week = get_games(sch_data)

    for game in games_week:
        game_data = get_boxscore(game.id)

        for side in ("homeTeam", "awayTeam"):
        
            team_players = game_data.get("playerByGameStats", {}).get(side, {})
            for skater in team_players.get("forwards", []) + team_players.get("defense", []):
                player_id = skater.get("playerId")
                name = skater["name"]["default"]
                team = game_data.get(side, {}).get("abbrev")
                position = skater["position"]

                if player_id not in peripherals:
                    peripherals[player_id] = SkaterPeripherals(player_id, name, team, position)

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

                    if player_id not in peripherals:
                        peripherals[player_id] = GoaliePeripherals(player_id, name, team, position)

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
                    
                    peripherals[player_id].goals += goals
                    peripherals[player_id].assists += assists
                    peripherals[player_id].sh_goals += sh_goals
                    peripherals[player_id].win += win
                    peripherals[player_id].otl += otl
                    peripherals[player_id].shutout += shutout
                    peripherals[player_id].saves += saves
                    peripherals[player_id].g_against -= g_against
                    peripherals[player_id].nine_one += nine_one

    return peripherals

def serialize_peripheral_player(stats):
    if stats.position in ("G", "Goalie"):
        return {
            "id": stats.id,
            "name": stats.name,
            "team": stats.team,
            "position": stats.position,
            "goals": stats.goals,
            "assists": stats.assists,
            "sh_goals": stats.sh_goals,
            "win": stats.win,
            "otl": stats.otl,
            "shutout": stats.shutout,
            "saves": stats.saves,
            "g_against": stats.g_against,
            "nine_one": stats.nine_one
        }

    return {
        "id": stats.id,
        "name": stats.name,
        "team": stats.team,
        "position": stats.position,
        "goals": stats.goals,
        "assists": stats.assists,
        "shots": stats.shots,
        "hits": stats.hits,
        "blocks": stats.blocks,
        "pm": stats.pm,
        "takeaways": stats.takeaways,
        "sh_goals": stats.sh_goals
    }

def append_peripherals_to_season(peripherals, start_date):
    dirpath = _peripherals_dir_for_date(start_date)
    week_key = str(start_date)

    existing_players = []
    processed_weeks = []

    season_file = dirpath / "season_peripherals.json"

    if season_file.exists():
        with open(season_file, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []

        # Backward compatible with old format where season file was a plain list.
        if isinstance(existing_data, list):
            existing_players = existing_data
        elif isinstance(existing_data, dict):
            players_data = existing_data.get("players", [])
            weeks_data = existing_data.get("processed_weeks", [])

            if isinstance(players_data, list):
                existing_players = players_data
            if isinstance(weeks_data, list):
                processed_weeks = weeks_data

    if week_key in processed_weeks:
        return False

    totals_by_id = {
        player.get("id"): player
        for player in existing_players
        if isinstance(player, dict) and player.get("id") is not None
    }

    for stats in peripherals.values():
        player = serialize_peripheral_player(stats)
        player_id = player["id"]

        if player_id not in totals_by_id:
            totals_by_id[player_id] = player
            continue

        existing = totals_by_id[player_id]
        existing["name"] = player["name"]
        existing["team"] = player["team"]
        existing["position"] = player["position"]

        for key, value in player.items():
            if key in ("id", "name", "team", "position"):
                continue
            existing[key] = existing.get(key, 0) + value

    players = list(totals_by_id.values())
    players.sort(key=lambda p: (p.get("position", ""), p.get("name", "")))
    processed_weeks.append(week_key)

    with open(season_file, "w", encoding="utf-8") as f:
        json.dump({
            "processed_weeks": processed_weeks,
            "players": players
        }, f, indent=2)

    return True

def save_week_peripherals(peripherals, start_date):
    dirpath = _peripherals_dir_for_date(start_date)
    players = []

    for _, stats in peripherals.items():
        players.append(serialize_peripheral_player(stats))

    with open(dirpath / f"{start_date}.json", "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2)



start_date = date(2024, 10, 6)
week_peripherals = get_week_peripherals(start_date)
save_week_peripherals(week_peripherals, start_date)
append_peripherals_to_season(week_peripherals, start_date)

