import os
import smtplib
from email.message import EmailMessage

def send_weekly_email(body_text: str):
    sender = os.environ["EMAIL_SENDER"]
    password = os.environ["EMAIL_PASSWORD"]

    recipients = [
        email.strip()
        for email in os.environ["EMAIL_RECIPIENTS"].split(",")
        if email.strip()
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
