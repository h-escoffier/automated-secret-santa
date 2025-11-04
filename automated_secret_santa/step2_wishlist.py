import imaplib, email, json, asyncio
from rich.console import Console

from automated_secret_santa.helpers import load_config, load_participants, send_email
from automated_secret_santa.email_template import create_email2


console = Console()


def load_assignments(filename="secret_data/santa_assignments.json"):
    with open(filename) as f:
        return json.load(f)
    

def get_inbox_emails(config):
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(config["from_email"], config["password"])
    imap.select("INBOX")

    # Check unseen emails
    _, messages = imap.search(None, '(UNSEEN)')
    mail_ids = messages[0].split()
    mails = []

    for mail_id in mail_ids:
        _, msg_data = imap.fetch(mail_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        mails.append(msg)

    imap.logout()
    return mails


def run_part2(language: str) -> None:
    participants = load_participants()
    assignments = load_assignments()
    config = load_config()

    mails = get_inbox_emails(config)

    if not mails:
        return

    for msg in mails:

        from_addr = email.utils.parseaddr(msg["From"])[1].lower()
        
        for name, mail in participants: 
            if mail == from_addr: 
                sender_name = name 
                break 

        if not sender_name:
            console.print(f"[yellow] Warning - {name} not found[/yellow]")
            continue
        
        for santa, santa_of in assignments.items(): 
            if sender_name == santa_of: 
                target_name = santa
                break 

        target_email = None

        for name, mail in participants:
            if name == target_name:
                target_email = mail
                break

        if not target_email:
            console.print(f"[yellow] Warning - {target_name} not found[/yellow]")
            continue

        if msg.is_multipart():
            body = ""
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
        
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        # Gmail / Mail 
        lines = [line for line in body.split("\n") if line.strip() and not line.startswith(">")]

        # Outlook
        try:
            index = next(i for i, line in enumerate(lines) if "hyper.super.secret.santa@gmail.com" in line)
            lines = lines[:index]
        except StopIteration:
            pass
        
        body_cleaned = "<br>".join(lines)

        if language != 'fr' and language != 'en':
            console.print(f"[red] Error: Language {language} not supported. - Only 'en' and 'fr' are supported.[/red]")
            exit()

        html_body = create_email2(target_name, sender_name, body_cleaned, language)

        if language == 'fr':
            send_email(target_email, "🎄 Le Père Noël souhaite vous transmettre un message !", html_body, config)
        elif language == 'en':
            send_email(target_email, "🎄 Santa Claus wants to forward you a message!", html_body, config)


async def auto_forward_wishlists(language: str):
    while True:
        run_part2(language)
        await asyncio.sleep(86400) # 24 hours


if __name__ == "__main__":
    print("start - part2")
    run_part2('en')
    print("end - part2")
