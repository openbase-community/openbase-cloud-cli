"""``openbase-deploy config`` — read an app's config vars."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.apps import resolve_app
from openbase_cli.context import app_option, err, handle_errors, make_client, out

_SECRET_PLACEHOLDER = "(secret — set in dashboard)"


@click.command()
@app_option
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def config(app_name: str | None, as_json: bool) -> None:
    """List config vars for an app.

    Secret values are never returned by the API; they show as a placeholder.
    """
    client = make_client()
    app = resolve_app(client, app_name or "")
    variables = client.resource_config_vars(app.resource_id)

    if as_json:
        out.print_json(
            jsonlib.dumps(
                {v.get("key"): (None if v.get("is_secret") else v.get("value")) for v in variables}
            )
        )
        return
    if not variables:
        err.print(f"No config vars set for '{app.name}'.")
        return
    table = Table(box=None, pad_edge=False)
    table.add_column("KEY", style="bold")
    table.add_column("VALUE")
    for v in sorted(variables, key=lambda x: str(x.get("key", "")).lower()):
        value = _SECRET_PLACEHOLDER if v.get("is_secret") else (v.get("value") or "")
        table.add_row(str(v.get("key", "")), value)
    out.print(table)
