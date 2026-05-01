#!/usr/bin/env python3
"""
support-triage-agent — AI-powered terminal tool for triaging support tickets.

Usage:
  python main.py                  Interactive session (type or paste tickets)
  python main.py --file FILE      Triage a ticket from a file
  python main.py --stdin          Read ticket from stdin (pipe-friendly)
  python main.py --verbose        Show agent tool calls as they happen
"""

import argparse
import sys
from agent import run_triage
from display import print_banner, print_triage_report, print_separator, console


def triage_from_text(text: str, verbose: bool) -> None:
    text = text.strip()
    if not text:
        console.print("[yellow]Empty ticket — skipping.[/yellow]")
        return

    console.print("\n[bold cyan]Analyzing ticket…[/bold cyan]")
    state = run_triage(text, verbose=verbose)
    print_triage_report(state, ticket_text=text)


def interactive_session(verbose: bool) -> None:
    print_banner()
    console.print(
        "[dim]Type or paste a support ticket, then press Enter twice to submit. "
        "Type [bold]exit[/bold] to quit.[/dim]\n"
    )

    while True:
        console.print("[bold green]▶ New ticket[/bold green] (blank line to submit, 'exit' to quit):")
        lines = []
        try:
            while True:
                line = input()
                if line.lower() in ("exit", "quit"):
                    console.print("\n[dim]Goodbye.[/dim]")
                    return
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            return

        ticket = "\n".join(lines).strip()
        triage_from_text(ticket, verbose)
        print_separator()
        console.print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="support-triage-agent — AI-powered support ticket triage"
    )
    parser.add_argument("--file", metavar="FILE", help="Path to a text file containing the ticket")
    parser.add_argument("--stdin", action="store_true", help="Read ticket from stdin")
    parser.add_argument("--verbose", action="store_true", help="Show agent tool calls")
    args = parser.parse_args()

    if args.stdin:
        ticket = sys.stdin.read()
        triage_from_text(ticket, args.verbose)
    elif args.file:
        try:
            with open(args.file, "r") as f:
                ticket = f.read()
        except FileNotFoundError:
            console.print(f"[red]File not found: {args.file}[/red]")
            sys.exit(1)
        triage_from_text(ticket, args.verbose)
    else:
        interactive_session(args.verbose)


if __name__ == "__main__":
    main()
