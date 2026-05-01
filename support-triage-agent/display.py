from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich import box
from tools import TriageState

console = Console()

PRIORITY_COLORS = {
    "CRITICAL": "bold red",
    "HIGH": "bold yellow",
    "MEDIUM": "bold cyan",
    "LOW": "dim green",
}

PRIORITY_ICONS = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}


def print_banner() -> None:
    console.print(
        Panel.fit(
            "[bold white]support-triage-agent[/bold white]\n"
            "[dim]AI-powered support ticket triage[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()


def print_separator() -> None:
    console.print(Rule(style="dim"))


def print_triage_report(state: TriageState, ticket_text: str = "") -> None:
    if ticket_text:
        preview = ticket_text[:200].replace("\n", " ").strip()
        if len(ticket_text) > 200:
            preview += "…"
        console.print(
            Panel(
                f"[dim]{preview}[/dim]",
                title="[bold]Ticket[/bold]",
                border_style="dim",
                padding=(0, 2),
            )
        )
        console.print()

    priority_color = PRIORITY_COLORS.get(state.priority or "LOW", "white")
    priority_icon = PRIORITY_ICONS.get(state.priority or "LOW", "")

    overview = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    overview.add_column("Field", style="bold dim", no_wrap=True)
    overview.add_column("Value")

    overview.add_row("Category", state.category or "—")
    overview.add_row(
        "Priority",
        Text(
            f"{priority_icon}  {state.priority}  (SLA: {state.sla_hours}h)",
            style=priority_color,
        ),
    )
    overview.add_row("Route to", f"[bold]{state.team}[/bold]")
    if state.cc_teams:
        overview.add_row("CC", ", ".join(state.cc_teams))
    if state.tags:
        overview.add_row("Tags", "  ".join(f"[cyan]#{t}[/cyan]" for t in state.tags))

    console.print(
        Panel(overview, title="[bold]Triage Overview[/bold]", border_style="cyan", padding=(0, 1))
    )

    if state.priority_justification:
        console.print(
            Panel(
                f"[italic]{state.priority_justification}[/italic]",
                title="[bold]Priority Reasoning[/bold]",
                border_style=priority_color,
                padding=(0, 2),
            )
        )

    if state.routing_notes:
        console.print(
            Panel(
                state.routing_notes,
                title=f"[bold]Notes for {state.team}[/bold]",
                border_style="yellow",
                padding=(0, 2),
            )
        )

    if state.response_subject and state.response_body:
        console.print(
            Panel(
                f"[bold]Subject:[/bold] {state.response_subject}\n\n{state.response_body}",
                title="[bold]Draft Customer Response[/bold]",
                border_style="green",
                padding=(1, 2),
            )
        )

    if state.summary:
        console.print(
            Panel(
                state.summary,
                title="[bold]Executive Summary[/bold]",
                border_style="magenta",
                padding=(0, 2),
            )
        )

    if state.internal_notes:
        console.print(
            Panel(
                f"[dim]{state.internal_notes}[/dim]",
                title="[bold]Internal Notes[/bold]",
                border_style="dim",
                padding=(0, 2),
            )
        )

    console.print()
    status = "✓ Triage complete" if state.finalized else "⚠ Triage incomplete"
    status_color = "bold green" if state.finalized else "bold yellow"
    console.print(f"[{status_color}]{status}[/{status_color}]")
