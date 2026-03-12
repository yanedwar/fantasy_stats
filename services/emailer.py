import os
import smtplib
import json
from email.message import EmailMessage
from analysis.stats_calc import top_ppg_defence, top_ppg_forwards, top_ppg_goalies, three_hot_streak, hottest_players, heating_up_players
from services.leaderboard import top_goalies, top_defence, top_forwards

with open("config/scoring_settings.json", "r") as f:
    SETTINGS = json.load(f)

def send_weekly_email(body_text: str):
    sender = os.environ["EMAIL_SENDER"]
    password = os.environ["EMAIL_PASSWORD"]

    raw_recipients = os.getenv("EMAIL_RECIPIENTS", "")
    recipients = [
        r.strip()
        for r in raw_recipients.replace("\n", ",").split(",")
        if r.strip()
    ]

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = "Weekly Costco Hotdogs NHL Fantasy Results"
    msg.set_content(body_text)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)

    print("Email sent successfully!")

def build_email_body(players, start_date, end_date, games_played):
    lines = []

    lines.append(f"For the week of {start_date} to {end_date}:")
    lines.append(f"Total number of games this week: {games_played}")
    lines.append("=" * 40)
    lines.append("")

    lines.append(top_players(players))

    lines.append(top_ppg())

    lines.append(hot_streaks())

    lines.append(heating_up())

    return "\n".join(lines)

def top_players(players):
    lines = []

    top_f = top_forwards(players)[:SETTINGS["topForwards"]]   
    top_d = top_defence(players)[:SETTINGS["topDefence"]]
    top_g = top_goalies(players)[:SETTINGS["topGoalies"]]

    lines.append(f"Top {len(top_f)} forwards of the week:")
    for p in top_f:
        lines.append(f"{p.name:<20} ({p.team} | {p.position}) - {p.points} pts in {p.games_played} games")

    lines.append("")
    lines.append(f"Top {len(top_d)} defence of the week:")
    for p in top_d:
        lines.append(f"{p.name:<20} ({p.team} | {p.position}) - {p.points} pts in {p.games_played} games")

    lines.append("")
    lines.append(f"Top {len(top_g)} goalies of the week:")
    for p in top_g:
        lines.append(f"{p.name:<20} ({p.team} | {p.position}) - {p.points} pts in {p.games_played} games")

    lines.append("")

    return "\n".join(lines)

def top_ppg():
    lines = []

    top_f = top_ppg_forwards()[:SETTINGS["topForwards"]]  
    top_d = top_ppg_defence()[:SETTINGS["topDefence"]]
    top_g = top_ppg_goalies()[:SETTINGS["topGoalies"]]

    lines.append(f"Top {len(top_f)} forwards by ppg:")
    for p in top_f:
        name = p["name"]
        team = p["team"]
        position = p["position"]
        ppg = p["ppg"]
        gp = p["games_played"]
        lines.append(f"{name:<20} ({team} | {position}) - {ppg} ppg in {gp} games played")

    lines.append("")
    lines.append(f"Top {len(top_d)} defence by ppg:")
    for p in top_d:
        name = p["name"]
        team = p["team"]
        position = p["position"]
        ppg = p["ppg"]
        gp = p["games_played"]
        lines.append(f"{name:<20} ({team} | {position}) - {ppg} ppg in {gp} games played")

    lines.append("")
    lines.append(f"Top {len(top_g)} goalies by ppg:")
    for p in top_g:
        name = p["name"]
        team = p["team"]
        position = p["position"]
        ppg = p["ppg"]
        gp = p["games_played"]
        lines.append(f"{name:<20} ({team} | {position}) - {ppg} ppg in {gp} games played")

    lines.append("")

    return "\n".join(lines)

def hot_streaks():
    lines = []

    hottest = hottest_players()
    lines.append(f"Top {len(hottest)} players on a hot streak from the last three weeks:")

    for player in hottest:
        weeks = sorted(player["weeksPoints"])
        last3 = [player["weeksPoints"][w] for w in weeks[-3:]]
        name = player["name"]
        position = player["position"]
        team = player["team"]
        lines.append(f"{name:<20} ({team} | {position}) → {last3} avg: {round(three_hot_streak(player), 2)}")
    
    lines.append("")

    return "\n".join(lines)    

def heating_up():
    lines = []

    heating = heating_up_players()
    lines.append(f"Top {len(heating)} players heating up over the last three weeks:")

    for player in heating:
        weeks = sorted(player["weeksPoints"])
        #last3 = [player["weeksPoints"][w] for w in weeks[-3:]]
        name = player["name"]
        position = player["position"]
        ppg = player["ppg"]
        team = player["team"]
        lines.append(f"{name:<20} ({team} | {position}) season avg: {ppg} → latest 3 weeks avg: {round(three_hot_streak(player), 2)}")
    
    lines.append("")

    return "\n".join(lines) 

