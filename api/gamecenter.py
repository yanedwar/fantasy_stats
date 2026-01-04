from api.client import get

def get_boxscore(game_id):
    return get(f"gamecenter/{game_id}/boxscore")

def get_play_by_play(game_id):
    return get(f"gamecenter/{game_id}/play-by-play")