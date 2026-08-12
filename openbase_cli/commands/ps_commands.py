"""``openbase-deploy ps`` / ``status`` — show an app's current stack status."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.apps import require_stack_id, resolve_app
from openbase_cli.context import app_option, handle_errors, make_client, out


def _status_impl(app_name: str | None, as_json: bool) -> None:
    client = make_client()
    app = resolve_app(client, app_name or "")
    stack_id = require_stack_id(app)
    stack = client.stack_status(stack_id)

    if as_json:
        out.print_json(jsonlib.dumps(stack))
        return

    latest_run = stack.get("latest_run") or {}
    rows = [
        ("App", app.name),
        ("Project", app.project),
        ("Type", app.resource_type),
        ("Status", str(stack.get("status", "") or "—")),
        ("Region", str(stack.get("aws_region", "") or "—")),
        ("URL", app.web_url or "—"),
        ("Last run", _run_summary(latest_run)),
        ("Updated", str(stack.get("updated_at", "") or "—")),
    ]
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column(style="bold")
    table.add_column()
    for label, value in rows:
        table.add_row(label, value)
    out.print(table)


def _run_summary(run: dict) -> str:
    if not run:
        return "—"
    parts = [str(run.get("operation", "")), str(run.get("status", ""))]
    summary = run.get("summary")
    label = " ".join(p for p in parts if p)
    return f"{label} — {summary}" if summary else (label or "—")


@click.command()
@app_option
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def ps(app_name: str | None, as_json: bool) -> None:
    """Show the current status of an app's stack."""
    _status_impl(app_name, as_json)


@click.command()
@app_option
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def status(app_name: str | None, as_json: bool) -> None:
    """Alias for `ps`: show the current status of an app's stack."""
    _status_impl(app_name, as_json)
