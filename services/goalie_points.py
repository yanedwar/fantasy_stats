from api.gamecenter import get_play_by_play

def get_goalie_points(game_id, goalie_id):
    data = get_play_by_play(game_id)
    plays = data.get("plays")
    points = {"goals": 0, "assists": 0}

    for play in plays:
        if play.get("typeDescKey") == "goal":
            if play.get("details", {}).get("scoringPlayerId") == goalie_id:
                points["goals"] += 1
            if play.get("details", {}).get("assist1PlayerId") == goalie_id or play.get("details", {}).get("assist2PlayerId") == goalie_id:
                points["assists"] += 1
    
    return points