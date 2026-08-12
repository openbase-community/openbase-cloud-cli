"""``openbase projects`` — list your Openbase Cloud projects."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.context import err, handle_errors, make_client, out


@click.command(name="projects")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def projects(as_json: bool) -> None:
    """List your Openbase Cloud projects."""
    found = make_client().projects()
    if as_json:
        out.print_json(jsonlib.dumps(found))
        return
    if not found:
        err.print("No projects found.")
        return
    table = Table(box=None, pad_edge=False)
    table.add_column("IDENTIFIER", style="bold")
    table.add_column("TITLE")
    table.add_column("REPO")
    table.add_column("CREATED")
    for p in found:
        table.add_row(
            str(p.get("identifier", "") or "—"),
            str(p.get("title", "") or "—"),
            str(p.get("github_repo_name", "") or "—"),
            str(p.get("created_at", "") or "—"),
        )
    out.print(table)
