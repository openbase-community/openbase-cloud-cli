"""``openbase workspaces`` — list your cloud dev workspaces (devspaces)."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.context import err, handle_errors, make_client, out


@click.command(name="workspaces")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def workspaces(as_json: bool) -> None:
    """List your Openbase Cloud dev workspaces and their status."""
    spaces = make_client().devspaces()
    if as_json:
        out.print_json(jsonlib.dumps(spaces))
        return
    if not spaces:
        err.print("No workspaces found.")
        return
    table = Table(box=None, pad_edge=False)
    table.add_column("ID", style="bold")
    table.add_column("KIND")
    table.add_column("STATUS")
    table.add_column("TYPE")
    table.add_column("HOURS (mo)", justify="right")
    table.add_column("SPEND (mo)", justify="right")
    for s in spaces:
        hours = s.get("monthly_usage_hours")
        spend = s.get("monthly_spend_cents")
        table.add_row(
            str(s.get("id", "") or "—"),
            str(s.get("kind", "") or "—"),
            str(s.get("status", "") or "—"),
            str(s.get("instance_type", "") or "—"),
            f"{float(hours):.1f}" if isinstance(hours, (int, float)) else "—",
            f"${int(spend) / 100:,.2f}" if isinstance(spend, int) else "—",
        )
    out.print(table)
