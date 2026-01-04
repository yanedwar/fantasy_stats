import json

with open("config/scoring_settings.json", "r") as f:
    SETTINGS = json.load(f)

SKATER_SET = SETTINGS["skaterScoring"]

def get_skater(player, goals, assists, shots, sh_goals, hits, blocks, pm, takeaways):
        player.games_played += 1
        player.points += (
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
            player.points += SKATER_SET["hatTrick"]
        player.points = round(player.points, 1)