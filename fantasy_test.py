import json
import requests

## TODO: 
# goalie goal + assist logic

with open("config/scoring_settings.json", "r") as f:
    SETTINGS = json.load(f)

SKATER_SET = SETTINGS["skaterScoring"]
GOALIE_SET = SETTINGS["goalieScoring"]

class Game:
    def __init__(self, game_id, date, away_team, home_team, shg_scorers):
        self.id = game_id
        self.date = date
        self.ateam = away_team
        self.hteam = home_team
        self.shg_scorers = shg_scorers

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
        self.points += (
            SKATER_SET["goal"] * goals + 
            SKATER_SET["assist"] * assists + 
            SKATER_SET["shot"] * shots + 
            SKATER_SET["shortHandedGoal"] * sh_goals +
            SKATER_SET["hit"] * hits + 
            SKATER_SET["block"] * blocks + 
            SKATER_SET["pm"] * pm +
            SKATER_SET["takeaway"] * takeaways
        )
        if goals >= 3: #hat trick
            self.points += SKATER_SET["hatTrick"]
        self.points = round(self.points, 1)
    
    def goalie(self, goals, assists, sh_goals, win, otl, shutout, saves, g_against, nine_one):
        self.games_played += 1
        self.points += (
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
        self.points = round(self.points, 1)

def short_handed_goals(game_id, ateam_id, hteam_id):
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    response = requests.get(url, timeout=10)
    if response.status_code != 200 or not response.text.strip():
        print("No data returned")
        exit()
    data = response.json()

    shg_scorers = []

    plays = data.get("plays")
    for play in plays:
        event = play.get("typeDescKey")
        s_code = play.get("situationCode")

        if event == "goal" and s_code == "1451":
            if play.get("details", {}).get("eventOwnerTeamId") == ateam_id:
                scorer = play.get("details", {}).get("scoringPlayerId")
                shg_scorers.append(scorer)

        if event == "goal" and s_code == "1541":
            if play.get("details", {}).get("eventOwnerTeamId") == hteam_id:
                scorer = play.get("details", {}).get("scoringPlayerId")
                shg_scorers.append(scorer)    
    
    return shg_scorers

games_week = []
players = {}

## LOG GAMES PLAYED THIS WEEK
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
        away_team_id = game.get("awayTeam", {}).get("id")
        home_team = game.get("homeTeam", {}).get("commonName",{}).get("default")
        home_team_id = game.get("homeTeam", {}).get("id")
        shg_scorers = short_handed_goals(game_id, away_team_id, home_team_id)
        new_game = Game(game_id, date, away_team, home_team, shg_scorers)
        games_week.append(new_game)

week_start = games_week[0].date
week_end = games_week[-1].date

#for game in games_week:
games_testing = games_week[:6] #testing so computer doesn't blow up

## POINTS CALCULATION
for game in games_week:
    box_url = f"https://api-web.nhle.com/v1/gamecenter/{game.id}/boxscore"
    box_response = requests.get(box_url, timeout=10)
    if box_response.status_code != 200 or not box_response.text.strip():
        print("No data returned")
        exit()
    if box_response.status_code == 200:
        matchup = f"{game.ateam} vs. {game.hteam} on {game.date}"
        print(f"{matchup:<45} | game id: {game.id}")
    game_data = box_response.json()

## HOME
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
        hits = forward.get("hits", 0)
        blocks = forward.get("blockedShots", 0)
        pm = forward.get("plusMinus", 0)
        takeaways = forward.get("takeaways", 0)

        sh_goals = 0
        if len(game.shg_scorers) > 0:
            for scorer in game.shg_scorers:
                if scorer == player_id:
                    sh_goals += 1

        players[player_id].skater(goals, assists, shots, sh_goals, hits, blocks, pm, takeaways)

    for defense in home_players["defense"]:
        player_id = defense.get("playerId")
        name = defense["name"]["default"]
        team = game_data.get("homeTeam", {}).get("abbrev")
        position = defense["position"]

        if player_id not in players:
            players[player_id] =  PlayerStats(player_id, name, team, position)

        goals = defense.get("goals", 0)
        assists = defense.get("assists", 0)
        shots = defense.get("sog", 0)
        hits = defense.get("hits", 0)
        blocks = defense.get("blockedShots", 0)
        pm = defense.get("plusMinus", 0)
        takeaways = defense.get("takeaways", 0)

        sh_goals = 0
        if len(game.shg_scorers) > 0:
            for scorer in game.shg_scorers:
                if scorer == player_id:
                    sh_goals += 1   

        players[player_id].skater(goals, assists, shots, sh_goals, hits, blocks, pm, takeaways)

    for goalie in home_players["goalies"]:
        if goalie.get("toi") != "00:00":
            player_id = goalie.get("playerId")
            name = goalie["name"]["default"]
            team = game_data.get("homeTeam", {}).get("abbrev")
            position = goalie["position"]

            if player_id not in players:
                players[player_id] =  PlayerStats(player_id, name, team, position)

            goals = 0 #complete logic later
            assists = 0 #complete logic later

            sh_goals = 0
            if len(game.shg_scorers) > 0:
                for scorer in game.shg_scorers:
                    if scorer == player_id:
                        sh_goals += 1    

            wins = 0
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

            players[player_id].goalie(goals, assists, sh_goals, win, otl, shutout, saves, g_against, nine_one)
            print(f"{players[player_id].name}: {players[player_id].points}")

## AWAY
    away_players = game_data.get("playerByGameStats", {}).get("awayTeam")
    for forward in away_players["forwards"]:
        player_id = forward.get("playerId")
        name = forward["name"]["default"]
        team = game_data.get("awayTeam", {}).get("abbrev")
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

        players[player_id].skater(goals, assists, shots, sh_goals, hits, blocks, pm, takeaways)
    
    for defense in away_players["defense"]:
        player_id = defense.get("playerId")
        name = defense["name"]["default"]
        team = game_data.get("awayTeam", {}).get("abbrev")
        position = defense["position"]

        if player_id not in players:
            players[player_id] =  PlayerStats(player_id, name, team, position)

        goals = defense.get("goals", 0)
        assists = defense.get("assists", 0)
        shots = defense.get("sog", 0)
        hits = defense.get("hits", 0)
        blocks = defense.get("blockedShots", 0)
        pm = defense.get("plusMinus", 0)
        takeaways = defense.get("takeaways", 0)

        sh_goals = 0
        if len(game.shg_scorers) > 0:
            for scorer in game.shg_scorers:
                if scorer == player_id:
                    sh_goals += 1

        players[player_id].skater(goals, assists, shots, sh_goals, hits, blocks, pm, takeaways)

    for goalie in away_players["goalies"]:
        if goalie.get("toi") != "00:00":
            player_id = goalie.get("playerId")
            name = goalie["name"]["default"]
            team = game_data.get("homeTeam", {}).get("abbrev")
            position = goalie["position"]

            if player_id not in players:
                players[player_id] =  PlayerStats(player_id, name, team, position)

            goals = 0 #complete logic later
            assists = 0 #complete logic later
            
            sh_goals = 0
            if len(game.shg_scorers) > 0:
                for scorer in game.shg_scorers:
                    if scorer == player_id:
                        sh_goals += 1

            wins = 0
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

            players[player_id].goalie(goals, assists, sh_goals, win, otl, shutout, saves, g_against, nine_one)
            print(f"{players[player_id].name}: {players[player_id].points}")

sorted_players = sorted(players.values(), key=lambda p: p.points, reverse = True)
top_10 = sorted_players[:10]

print(f"For the week of {week_start} to {week_end}:")
for p in top_10:
    print(f"{p.name:<20} ({p.team} | {p.position}) - {p.points} pts in {p.games_played} games")

print(f"Total number of games this week: {len(games_week)}")
    