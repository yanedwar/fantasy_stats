class PlayerStats:
    def __init__(self, player_id, name, team, position):
        self.id = player_id
        self.name = name
        self.team = team
        self.position = position
        self.points = 0.0
        self.games_played = 0

    def store(self):
        return {
            "player_id": self.id,
            "name": self.name,
            "team": self.team,
            "position": self.position,
            "points": round(self.points, 2),
            "games_played": self.games_played
        }