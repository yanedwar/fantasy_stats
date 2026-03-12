import statistics

def three_hot_streak(player, n=3):
    weeks = sorted(player["weeksPoints"])
    last = [player["weeksPoints"][w] for w in weeks[-n:]]
    return sum(last) / len(last)

def hottest_players(players, n=15):
    eligible = [p for p in players.values() if len(p["weeksPoints"]) >= 3]

    ranked = sorted(eligible, key=lambda p: three_hot_streak(p), reverse = True)

    return ranked[:n]



