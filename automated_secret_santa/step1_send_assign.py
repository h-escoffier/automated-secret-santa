import random, json
from rich.console import Console

from automated_secret_santa.helpers import load_config, load_participants, send_email
from automated_secret_santa.email_template import create_email1


console = Console()

def assign_secret_santa(participants, exclusion_rules, max_attempts=10000):
    names = [name for name, _ in participants]
    shuffled = names[:]

    for _ in range(max_attempts):
        random.shuffle(shuffled)
        valid = True
        for giver, receiver in zip(names, shuffled):
            if giver == receiver: # No auto-assignment
                valid = False
                break
            if exclusion_rules != []: 
                for group in exclusion_rules:
                    if giver in group and receiver in group:
                        valid = False
                        break
            if not valid:
                break
        if valid:
            return dict(zip(names, shuffled))
    console.print("[red] Error: Failed to assign Secret Santa within max attempts - Your exclusion rules might be impossible to satisfy.[/red]")
    exit()


def exclusion_rules(participants, path="data/exclusion_rules.csv"): 
    try:
        with open(path, "r") as f:
            content = f.read().strip().split('\n')
        groups = [line.split(',') for line in content]
        if groups == [['']]:
            # print("No exclusion rules found.")
            return []
        # Check that all persons in exclusion rules are in participants
        participants_names = [name for name, _ in participants]
        for group in groups: 
            for person in group: 
                if person not in participants_names: 
                    console.print(f"[yellow] Warning: {person} in exclusion rules not in participants list.[/yellow]")
        return groups
    except FileNotFoundError:
        # print("No exclusion rules found.")
        return []


def run_part1(budget: str,language: str) -> None:
    """
    Assign Secret Santa and send emails to participants.

    Parameters:
        budget (str): Budget for the Secret Santa gift.
        language (str): Language code for email templates: 'en' for English, 'fr' for French.
    
    Returns:
        None
    """
    participants = load_participants()
    groups = exclusion_rules(participants)

    config = load_config()

    assignments = assign_secret_santa(participants, groups)

    with open("secret_data/santa_assignments.json", "w") as f:
        json.dump(assignments, f, indent=2)

    for santa, santa_of in assignments.items():
        for nom, email in participants: 
            if nom == santa: 
                santa_email = email
                break       
        
        if language != 'fr' and language != 'en':
            console.print(f"[red] Error: Language {language} not supported. - Only 'en' and 'fr' are supported.[/red]")
            exit()

        body_html = create_email1(santa, santa_of, budget, language)  
        
        if language == 'en':    
            send_email(santa_email, "🎄 You have received a message from Santa Claus!", body_html, config)
        elif language == 'fr':
            send_email(santa_email, "🎄 Vous avez reçu un message du Père Noël !", body_html, config)


if __name__ == "__main__":
    print('start - part1')
    run_part1('5€', 'fr')
    print('end - part1')
