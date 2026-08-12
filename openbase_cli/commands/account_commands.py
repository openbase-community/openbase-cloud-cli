"""``openbase account`` — show the signed-in account."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.context import handle_errors, make_client, out


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def account(as_json: bool) -> None:
    """Show details for the signed-in Openbase Cloud account."""
    me = make_client().me()
    if as_json:
        out.print_json(jsonlib.dumps(me))
        return
    name = " ".join(p for p in [me.get("first_name"), me.get("last_name")] if p)
    rows = [
        ("Email", me.get("email", "") or "—"),
        ("Name", name or "—"),
        ("Balance", me.get("balance", "") or "—"),
        ("Subscription", "active" if me.get("active_subscription") else "none"),
        ("Email verified", "yes" if me.get("email_verified") else "no"),
    ]
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column(style="bold")
    table.add_column()
    for label, value in rows:
        table.add_row(label, str(value))
    out.print(table)
