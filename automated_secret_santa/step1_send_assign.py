import os, sys, random, json
from rich.console import Console

from automated_secret_santa.helpers import load_config, load_participants, send_email, ASSIGNMENTS_PATH
from automated_secret_santa.email_template import create_email1, check_language


console = Console()

SUBJECTS = {
    "en": "🎄 You have received a message from Santa Claus!",
    "fr": "🎄 Tu as reçu un message du Père Noël !",
}


def assign_secret_santa(participants, exclusion_rules, max_attempts=10000):
    names = [name.strip() for name, _ in participants]
    if len(names) < 2:
        console.print("[red] Error: At least 2 participants are needed.[/red]")
        sys.exit(1)
    shuffled = names[:]

    for _ in range(max_attempts):
        random.shuffle(shuffled)
        valid = True
        for giver, receiver in zip(names, shuffled):
            if giver == receiver: 
                valid = False
                break
            for group in exclusion_rules:
                if giver in group and receiver in group:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            return dict(zip(names, shuffled))
    console.print("[red] Error: Failed to assign Secret Santa within max attempts - Your exclusion rules might be impossible to satisfy.[/red]")
    sys.exit(1)


def exclusion_rules(participants, path="data/exclusion_rules.csv"):
    """One group per line (e.g. a couple): 'Alice,Bob'. Members of a group can't draw each other."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except FileNotFoundError:
        # print("No exclusion rules found.")
        return []

    participants_names = [name for name, _ in participants]
    groups = []
    for line in lines:
        group = [person.strip() for person in line.split(",") if person.strip()]
        for person in group:
            if person not in participants_names:
                console.print(f"[yellow] Warning: {person} in exclusion rules not in participants list.[/yellow]")
        if len(group) > 1:
            groups.append(group)
    return groups


def run_part1(budget: str, language: str, overwrite: bool = True) -> None:
    """
    Assign Secret Santa and send emails to participants.

    Parameters:
        budget (str): Budget for the Secret Santa gift.
        language (str): Language code for email templates: 'en' for English, 'fr' for French.
        overwrite (bool): Allow replacing an existing assignments file. Default True

    Returns:
        None
    """
    check_language(language)

    participants = load_participants()
    groups = exclusion_rules(participants)

    config = load_config()

    if os.path.exists(ASSIGNMENTS_PATH) and not overwrite:
        console.print(f"[red] Error: {ASSIGNMENTS_PATH} already exists - participants may already have their assignment. "
                      f"Delete the file or call run_part1(..., overwrite=True) to draw again.[/red]")
        sys.exit(1)

    assignments = assign_secret_santa(participants, groups)

    os.makedirs(os.path.dirname(ASSIGNMENTS_PATH), exist_ok=True)
    with open(ASSIGNMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)

    emails = dict(participants)
    failed = []

    for santa, santa_of in assignments.items():
        santa_email = emails[santa]

        text_body_en = f"Ho ho ho {santa} ! You are the secret Santa for {santa_of}. Budget : {budget}. Reply to this email with your wishlist."
        text_body_fr = f"Ho ho ho {santa} ! Tu es le Père Noël secret de {santa_of}. Budget : {budget}. Réponds à ce mail avec ta liste d'envies."
        text_body = text_body_fr if language == 'fr' else text_body_en

        body_html = create_email1(santa, santa_of, budget, language)

        try:
            send_email(santa_email, SUBJECTS[language], text_body, body_html, config)
        except Exception as e:  # one failure must not stop the others
            console.print(f"[red] Error: could not send email to {santa} ({santa_email}): {e}[/red]")
            failed.append(santa)

    if failed:
        console.print(f"[red] {len(failed)} email(s) failed: {', '.join(failed)} - the assignments are saved in {ASSIGNMENTS_PATH}.[/red]")


if __name__ == "__main__":
    print('start - part1')
    run_part1('5€', 'fr')
    print('end - part1')