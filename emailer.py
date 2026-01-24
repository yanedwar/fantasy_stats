import os
import smtplib
from email.message import EmailMessage
from services.leaderboard import top_goalies, top_defence, top_forwards

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

    top_f = top_forwards(players)   
    top_d = top_defence(players)
    top_g = top_goalies(players)
    lines.append(f"For the week of {start_date} to {end_date}:")
    lines.append("=" * 40)
    lines.append("")

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
    lines.append(f"Total number of games this week: {games_played}")

    return "\n".join(lines)
