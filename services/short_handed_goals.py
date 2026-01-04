from api.gamecenter import get_play_by_play

def get_short_handed_goals(game_id, ateam_id, hteam_id):
    data = get_play_by_play(game_id)
    plays = data.get("plays")
    shg_scorers = []

    for play in plays:
        event = play.get("typeDescKey")
        s_code = play.get("situationCode")

        if event == "goal" and (s_code == "1451" or s_code == "1460"):
            if play.get("details", {}).get("eventOwnerTeamId") == ateam_id:
                scorer = play.get("details", {}).get("scoringPlayerId")
                shg_scorers.append(scorer)

        if event == "goal" and (s_code == "1541" or s_code == "0641"):
            if play.get("details", {}).get("eventOwnerTeamId") == hteam_id:
                scorer = play.get("details", {}).get("scoringPlayerId")
                shg_scorers.append(scorer)    
    
    return shg_scorers