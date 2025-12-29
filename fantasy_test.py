import requests

class Game:
    def __init__(self, game_id, date, away_team, home_team):
        self.id = game_id
        self.date = date
        self.ateam = away_team
        self.hteam = home_team

class PlayerStats:
    def __init__(self, player_id, name, team, position):
        self.id = player_id
        self.name = name
        self.team = team
        self.position = position

        self.games_played = 0
        self.goals = 0
        self.assists = 0
        self.shots = 0
        self.hits = 0
        self.blocks = 0
        self.pm = 0
        self.takeaways = 0

class GoalieStats:
    def __init__(self, player_id, name, team):
        self.id = player_id
        self.name = name
        self.team = team

        self.games_played = 0
        self.goals = 0
        self.assists = 0
        self.wins = 0
        self.saves = 0
        self.save_pct = 0



sch_url = f"https://api-web.nhle.com/v1/schedule/2025-12-21"

sch_response = requests.get(sch_url, timeout=10)

print("Status code:", sch_response.status_code)

if sch_response.status_code != 200 or not sch_response.text.strip():
    print("No data returned")
    exit()

sch_data = sch_response.json()

games_week = []

for day in sch_data.get("gameWeek", []):
    date = day.get("date", {})
    for game in day.get("games", []):
        game_id = game.get("id")
        away_team = game.get("awayTeam", {}).get("commonName",{}).get("default")
        home_team = game.get("homeTeam", {}).get("commonName",{}).get("default")
        new_game = Game(game_id, date, away_team, home_team)
        games_week.append(new_game)

#for game in games_week:
games_testing = games_week[:6] #testing so computer doesn't blow up

for game in games_testing:
    box_url = f"https://api-web.nhle.com/v1/gamecenter/{game.id}/boxscore"
    box_response = requests.get(box_url, timeout=10)
    print("Status code:", box_response.status_code)
    if box_response.status_code != 200 or not box_response.text.strip():
        print("No data returned")
        exit()
    game_data = box_response.json()
    home_players = game_data.get("playerByGameStats", {}).get("homeTeam")

    