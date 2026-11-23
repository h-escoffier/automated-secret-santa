import csv, json, logging, smtplib, ssl

import cssutils
from premailer import Premailer
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


cssutils.log.setLevel(logging.CRITICAL)

ASSIGNMENTS_PATH = "automated_secret_santa/data_secret/santa_assignments.json"


def load_participants(path="data/participants.csv"):
    participants = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for line_no, row in enumerate(csv.reader(f), start=1):
            if not row or not "".join(row).strip() or row[0].strip().startswith("#"):
                continue
            if len(row) < 2:
                raise ValueError(f"{path}, line {line_no}: expected 'name,email'")
            name, addr = row[0].strip(), row[1].strip().lower()
            if "@" not in addr:
                raise ValueError(f"{path}, line {line_no}: invalid email '{addr}' for {name}")
            participants.append([name, addr])

    names = [name for name, _ in participants]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"{path}: duplicated names {duplicates} - names must be unique")
    return participants


def load_config(path='data/mail_config.json'):
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    missing = [key for key in ("from_email", "password") if key not in config]
    if missing:
        raise ValueError(f"{path}: missing keys {missing}")
    return config


def inline_css(html_body):
    out = Premailer(html_body).transform(pretty_print=False)
    if not out.lstrip().lower().startswith("<!doctype"):
        out = "<!DOCTYPE html>\n" + out
    return out


def send_email(to_addr, subject, text_body, html_body, config, attachments=None):
    root = MIMEMultipart("mixed")
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(text_body, "plain", "utf-8"))
    alt.attach(MIMEText(inline_css(html_body), "html", "utf-8"))
    root.attach(alt)

    for filename, mimetype, data in attachments or []:
        maintype, _, subtype = mimetype.partition("/")
        if maintype == "image":
            part = MIMEImage(data, _subtype=subtype)
        elif maintype == "text":
            part = MIMEText(data.decode(errors="replace"), subtype, "utf-8")
        else:
            part = MIMEApplication(data, _subtype=subtype or "octet-stream")
        part.add_header("Content-Disposition", "attachment", filename=("utf-8", "", filename))
        root.attach(part)

    from_email = config["from_email"]
    root["Subject"] = Header(subject, "utf-8")
    root["From"] = formataddr((config.get("from_name", ""), from_email))
    root["To"] = to_addr
    root["Date"] = formatdate(localtime=True)
    root["Message-ID"] = make_msgid(domain=from_email.split("@")[-1])

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(config.get("smtp_host", "smtp.gmail.com"), config.get("smtp_port", 465),
                          context=context, timeout=30) as server:
        server.login(from_email, config["password"])
        server.send_message(root)