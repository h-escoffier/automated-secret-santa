import json, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Helper functions


def load_participants(path="data/participants.csv"):
    with open(path) as f:
        content = f.read().strip().split('\n')
    return [line.split(',') for line in content]


def load_config(path='data/mail_config.json'): 
    with open(path) as f:
        config = json.load(f)
    return config


def send_email(to_addr, subject, body, config):
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["from_email"]
    msg["To"] = to_addr

    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(config["from_email"], config["password"])
        server.send_message(msg)
