import imaplib, email, json, asyncio, re

from email.header import decode_header, make_header
from email.utils import parseaddr
from rich.console import Console
from bs4 import BeautifulSoup

from automated_secret_santa.helpers import load_config, load_participants, send_email, ASSIGNMENTS_PATH
from automated_secret_santa.email_template import create_email2, check_language


console = Console()

SUBJECTS = {
    "en": "🎄 Santa Claus wants to forward you a message!",
    "fr": "🎄 Le Père Noël souhaite te transmettre un message !",
}


def load_assignments(filename=ASSIGNMENTS_PATH):
    with open(filename, encoding="utf-8") as f:
        return json.load(f)


def decode_part(part):
    payload = part.get_payload(decode=True)
    if not payload:
        return ""
    try:
        return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def get_text_part(msg):
    if not msg.is_multipart():
        text = decode_part(msg)
        return html_to_text(text) if msg.get_content_type() == "text/html" else text
    plain, html_part = None, None
    for part in msg.walk():
        if part.is_multipart() or part.get_content_disposition() == "attachment":
            continue
        ctype = part.get_content_type()
        if ctype == "text/plain" and plain is None:
            plain = decode_part(part)
        elif ctype == "text/html" and html_part is None:
            html_part = decode_part(part)
    if plain and plain.strip():
        return plain
    return html_to_text(html_part or "")


def html_to_text(html_str):
    soup = BeautifulSoup(html_str, "html.parser")
    for tag in soup(["style", "script", "head"]):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for tag in soup.find_all(["p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"]):
        tag.append("\n")  # keep line breaks between blocks
    text = soup.get_text().replace("\xa0", " ")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def get_inbox_emails(config):
    imap = imaplib.IMAP4_SSL(config.get("imap_host", "imap.gmail.com"))
    mails = []
    try:
        imap.login(config["from_email"], config["password"])
        imap.select("INBOX")

        # Check unseen emails
        _, messages = imap.uid("search", None, "UNSEEN")
        for uid in messages[0].split():
            _, msg_data = imap.uid("fetch", uid, "(BODY.PEEK[])")
            if not msg_data or not msg_data[0]:
                continue
            mails.append((uid, email.message_from_bytes(msg_data[0][1])))
    finally:
        imap.logout()
    return mails


def mark_as_seen(config, uids):
    if not uids:
        return
    imap = imaplib.IMAP4_SSL(config.get("imap_host", "imap.gmail.com"))
    try:
        imap.login(config["from_email"], config["password"])
        imap.select("INBOX")
        for uid in uids:
            imap.uid("store", uid, "+FLAGS", "\\Seen")
    finally:
        imap.logout()


def decode_filename(filename):
    try:
        return str(make_header(decode_header(filename)))
    except Exception:
        return filename


def get_attachments(msg):
    atts = []
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        dispo = part.get_content_disposition()
        filename = part.get_filename()

        if ctype in ("text/plain", "text/html") and dispo != "attachment":
            continue
        data = part.get_payload(decode=True)
        if not data:
            continue
        if dispo == "attachment":
            atts.append((decode_filename(filename) if filename else "attachment", ctype, data))
        elif ctype.startswith("image/"): 
            atts.append((decode_filename(filename) if filename else "image", ctype, data))
    return atts


# Reply markers (FR + EN)
ATTRIBUTION_REGEX = re.compile(r"^\s*(Le|On)\s+.{5,250}?\s(a\s+écrit|wrote)\s*:\s*$", re.IGNORECASE)
REPLY_MARKERS = [
    r"^\s*(From|De|Von)\s*:\s+.*@.*$",
    r"^\s*-{2,}\s*Original Message\s*-{2,}\s*$",
    r"^\s*-{2,}\s*Message d['’]origine\s*-{2,}\s*$",
    r"^\s*-{2,}.*(Forwarded message|Message transféré).*-{2,}\s*$",
]
REPLY_REGEX = re.compile("|".join(f"({m})" for m in REPLY_MARKERS), flags=re.IGNORECASE)
MOBILE_SIGNATURE_REGEX = re.compile(r"^\s*(Envoyé de mon|Envoyé depuis|Sent from my|Get Outlook for)\b.*$", re.IGNORECASE)


def extract_first_email_message(body: str) -> str:
    if not body:
        return ""

    lines = body.splitlines()

    cleaned = []
    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else ""

        if (REPLY_REGEX.match(line)
                or ATTRIBUTION_REGEX.match(line)
                or ATTRIBUTION_REGEX.match(f"{line} {next_line}")):
            break

        if line.strip().startswith(">"):
            break

        cleaned.append(line)

    while cleaned and (not cleaned[-1].strip() or MOBILE_SIGNATURE_REGEX.match(cleaned[-1])):
        cleaned.pop()

    result = "\n".join(cleaned).strip()
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def run_part2(language: str) -> None:
    check_language(language)

    participants = load_participants()
    try:
        assignments = load_assignments()
    except FileNotFoundError:
        console.print(f"[red] Error: {ASSIGNMENTS_PATH} not found - run part 1 first.[/red]")
        return
    config = load_config()

    emails = dict(participants)
    name_by_email = {mail: name for name, mail in participants}
    santa_by_giftee = {santa_of: santa for santa, santa_of in assignments.items()}

    mails = get_inbox_emails(config)

    if not mails:
        return

    handled = []

    for uid, msg in mails:

        from_addr = parseaddr(msg.get("From", ""))[1].lower()

        sender_name = name_by_email.get(from_addr)
        if not sender_name:
            console.print(f"[yellow] Warning - no participant with email {from_addr}[/yellow]")
            handled.append(uid)
            continue

        target_name = santa_by_giftee.get(sender_name)
        if not target_name:
            console.print(f"[yellow] Warning - no assignment found for {sender_name}[/yellow]")
            handled.append(uid)
            continue

        target_email = emails.get(target_name)
        if not target_email:
            console.print(f"[yellow] Warning - {target_name} not found[/yellow]")
            handled.append(uid)
            continue

        body = get_text_part(msg)
        body_cleaned = extract_first_email_message(body)

        atts = get_attachments(msg)
        text_body_en = f"Message from {sender_name} forwarded by Santa Claus."
        text_body_fr = f"Message de {sender_name} transmis par le Père Noël."
        text_body = text_body_fr if language == 'fr' else text_body_en
        if body_cleaned:
            text_body += f"\n\n{body_cleaned}"

        html_body = create_email2(target_name, sender_name, body_cleaned, language)

        try:
            send_email(target_email, SUBJECTS[language], text_body, html_body, config, attachments=atts)
            handled.append(uid)
        except Exception as e: 
            console.print(f"[red] Error: could not forward {sender_name}'s message to {target_name}: {e}[/red]")

    mark_as_seen(config, handled)


async def auto_forward_wishlists(language: str):
    check_language(language)
    while True:
        try:
            await asyncio.to_thread(run_part2, language)  
        except Exception as e:  
            console.print(f"[red] Error while forwarding wishlists: {e}[/red]")
        await asyncio.sleep(86400)


if __name__ == "__main__":
    print("start - part2")
    run_part2('en')
    print("end - part2")