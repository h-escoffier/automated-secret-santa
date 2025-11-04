#!/usr/bin/env python3

import typer, asyncio
from rich.console import Console
from rich.panel import Panel


from automated_secret_santa.step1_send_assign import run_part1
from automated_secret_santa.step2_wishlist import run_part2, auto_forward_wishlists


app = typer.Typer(
    help="Automated Secret Santa — Assign, Send and Forward Secret Santa emails !"
)
console = Console()



@app.command("send-emails")
def send_emails(
    budget: str = typer.Option(..., "--budget", "-b", help="Budget for the gift (e.g., '20€')"),
    language: str = typer.Option(..., "--language", "-l", help="Language code for email templates: 'en' for English, 'fr' for French.")
):
    """
    Sends Secret Santa emails to participants.
    """
    console.print(Panel.fit(f"Sending Secret Santa emails - language={language}, budget={budget}"))
    run_part1(budget=budget, language=language)
    console.print("[green] Emails sent successfully![/green]")


@app.command("forward-emails")
def forward_emails(
    language: str = typer.Option(..., "--language", "-l", help="Language code for email templates: 'en' for English, 'fr' for French.")
):
    """
    Forward wishlists to assigned Secret Santa.
    """
    console.print(Panel.fit(f"Forwarding wishlists. (language={language})"))
    run_part2(language=language)
    console.print("[green]Wishlists forwarded successfully![/green]")


@app.command("auto-forward")
def run_daemon(
    language: str = typer.Option(..., "--language", "-l", help="Language code for email templates: 'en' for English, 'fr' for French.")
    ):
    """
    Run 'forward-emails' function as a background daemon checking emails every 24 hours.
    """
    console.print(f"Running background email watcher every 24 hours")
    asyncio.run(auto_forward_wishlists(language=language))


if __name__ == "__main__":
    app()