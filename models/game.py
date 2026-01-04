class Game:
    def __init__(self, game_id, date, away_team, home_team, shg_scorers):
        self.id = game_id
        self.date = date
        self.ateam = away_team
        self.hteam = home_team
        self.shg_scorers = shg_scorers