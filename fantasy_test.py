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
        self.points = 0
        self.games_played = 0

    def skater(self, goals, assists, shots, sh_goals, hits, blocks, pm, takeaways):
        self.games_played += 1
        self.points += 6*goals + 2*sh_goals + 4*assists + 0.9*shots + 2*pm + 0.4*hits + 0.6*blocks + 0.6*takeaways
        if goals >= 3: #hat trick
            self.points += 2
        self.points = round(self.points, 1)
    
    def goalie(self, goals, assists, sh_goals, win, otl, shutout, saves, g_against, nine_one):
        self.games_played += 1
        self.points += 20*goals + 4*assists + 2*sh_goals + 5*win + 2*otl + 5*shutout + 0.6*saves - 3*g_against + 3*nine_one
        self.points = round(self.points, 1)

games_week = []
players = {}

sch_url = f"https://api-web.nhle.com/v1/schedule/2025-12-21"

sch_response = requests.get(sch_url, timeout=10)

print("Status code:", sch_response.status_code)

if sch_response.status_code != 200 or not sch_response.text.strip():
    print("No data returned")
    exit()

sch_data = sch_response.json()

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


## TODO: figure out which game is missing - C. McDavid played 3 games in Dec 21-27, but program only recongizes 2. Does it count 21 or 27? 

for game in games_week:
    box_url = f"https://api-web.nhle.com/v1/gamecenter/{game.id}/boxscore"
    box_response = requests.get(box_url, timeout=10)
    print("Status code:", box_response.status_code)
    if box_response.status_code != 200 or not box_response.text.strip():
        print("No data returned")
        exit()
    game_data = box_response.json()
    home_players = game_data.get("playerByGameStats", {}).get("homeTeam")
    for forward in home_players["forwards"]:
        player_id = forward.get("playerId")
        name = forward["name"]["default"]
        team = game_data.get("homeTeam", {}).get("abbrev")
        position = forward["position"]

        if player_id not in players:
            players[player_id] =  PlayerStats(player_id, name, team, position)

        goals = forward.get("goals", 0)
        assists = forward.get("assists", 0)
        shots = forward.get("sog", 0)
        sh_goals = 0 #complete logic later
        hits = forward.get("hits", 0)
        blocks = forward.get("blockedShots", 0)
        pm = forward.get("plusMinus", 0)
        takeaways = forward.get("takeaways", 0)

        players[player_id].skater(goals, assists, shots, sh_goals, hits, blocks, pm, takeaways)

sorted_players = sorted(players.values(), key=lambda p: p.points, reverse = True)
top_10 = sorted_players[:10]

for p in top_10:
    print(f"{p.name} ({p.team}) - {p.points} pts in {p.games_played} games")

print(f"Total number of games this week: {len(games_week)}")
    