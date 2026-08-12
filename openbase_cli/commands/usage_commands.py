"""``openbase usage`` — account spend and usage limits."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.context import handle_errors, make_client, out


def _dollars(cents) -> str:
    try:
        return f"${int(cents) / 100:,.2f}"
    except (TypeError, ValueError):
        return "—"


def _percent(value) -> str:
    try:
        return f"{float(value):.0f}%"
    except (TypeError, ValueError):
        return "—"


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def usage(as_json: bool) -> None:
    """Show this month's spend and usage limits for your account."""
    data = make_client().usage()
    if as_json:
        out.print_json(jsonlib.dumps(data))
        return

    limit = data.get("monthly_limit_cents")
    out.print(
        f"[bold]Monthly included limit:[/bold] {_dollars(limit)}"
        f"   (billing month started {data.get('usage_month_start', '—')})"
    )

    table = Table(box=None, pad_edge=False)
    table.add_column("CATEGORY", style="bold")
    table.add_column("SPENT", justify="right")
    table.add_column("REMAINING", justify="right")
    table.add_column("USED", justify="right")
    for label, prefix in [("Sandbox", "sandbox"), ("Deployment", "deployment"), ("LLM", "llm")]:
        table.add_row(
            label,
            _dollars(data.get(f"{prefix}_spend_cents")),
            _dollars(data.get(f"{prefix}_remaining_cents")),
            _percent(data.get(f"{prefix}_spend_percent")),
        )
    out.print(table)

    if data.get("payg_enabled"):
        remaining = _dollars(data.get("payg_remaining_cents"))
        cap = _dollars(data.get("payg_limit_cents"))
        out.print(f"[bold]Pay-as-you-go:[/bold] enabled — {remaining} remaining of {cap} cap")
    elif data.get("payg_supported"):
        out.print("[dim]Pay-as-you-go: available (not enabled)[/dim]")
