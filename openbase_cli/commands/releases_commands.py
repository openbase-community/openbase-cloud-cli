"""``openbase-deploy releases`` — recent deploy runs for an app."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.apps import resolve_app
from openbase_cli.context import app_option, err, handle_errors, make_client, out


@click.command()
@app_option
@click.option(
    "-n",
    "--num",
    "limit",
    type=int,
    default=15,
    show_default=True,
    help="Maximum number of runs to show.",
)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def releases(app_name: str | None, limit: int, as_json: bool) -> None:
    """List recent deploy runs (releases) for an app."""
    client = make_client()
    app = resolve_app(client, app_name or "")
    runs = client.resource_runs(app.resource_id)[:limit]

    if as_json:
        out.print_json(jsonlib.dumps(runs))
        return
    if not runs:
        err.print(f"No deploy runs recorded for '{app.name}' yet.")
        return
    table = Table(box=None, pad_edge=False)
    table.add_column("WHEN")
    table.add_column("OPERATION", style="bold")
    table.add_column("STATUS")
    table.add_column("REF")
    table.add_column("SUMMARY")
    for run in runs:
        table.add_row(
            str(run.get("created_at", "") or "—"),
            str(run.get("operation", "") or "—"),
            str(run.get("status", "") or "—"),
            _ref(run),
            str(run.get("summary", "") or ""),
        )
    out.print(table)


def _ref(run: dict) -> str:
    sha = str(run.get("commit_sha", "") or "")
    ref = str(run.get("git_ref", "") or "")
    short = sha[:7] if sha else ""
    if ref and short:
        return f"{ref}@{short}"
    return ref or short or "—"
