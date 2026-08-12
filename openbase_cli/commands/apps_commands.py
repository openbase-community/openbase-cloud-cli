"""``openbase-deploy apps`` — list the apps you can access."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.apps import list_apps, resolve_app
from openbase_cli.context import app_option, err, handle_errors, make_client, out


@click.command(name="apps")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def apps(as_json: bool) -> None:
    """List Openbase Cloud apps (deployment resources) you can access."""
    found = list_apps(make_client())
    if as_json:
        out.print_json(
            jsonlib.dumps(
                [
                    {
                        "name": a.name,
                        "project": a.project,
                        "type": a.resource_type,
                        "status": a.status,
                        "stack_id": a.stack_id,
                        "url": a.web_url,
                    }
                    for a in found
                ]
            )
        )
        return
    if not found:
        err.print("No apps found. Create one in the Openbase Cloud dashboard.")
        return
    table = Table(box=None, pad_edge=False)
    table.add_column("APP", style="bold")
    table.add_column("PROJECT")
    table.add_column("TYPE")
    table.add_column("STATUS")
    table.add_column("URL", style="cyan")
    for a in sorted(found, key=lambda x: (x.project.lower(), x.name.lower())):
        table.add_row(a.name, a.project, a.resource_type, a.status, a.web_url or "—")
    out.print(table)


@click.command(name="open")
@app_option
@handle_errors
def open_app(app_name: str | None) -> None:
    """Open the app's primary URL in your browser."""
    import webbrowser

    app = resolve_app(make_client(), app_name or "")
    url = app.web_url
    if not url:
        err.print(f"App '{app.name}' has no hostname to open yet.")
        raise SystemExit(1)
    err.print(f"Opening {url}")
    webbrowser.open(url)
