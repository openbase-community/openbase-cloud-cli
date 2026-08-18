"""``openbase health-check`` — view or set an app's web health-check path."""

from __future__ import annotations

import click

from openbase_cli.apps import require_stack_id, resolve_app
from openbase_cli.context import app_option, handle_errors, make_client, out

PLATFORM_DEFAULT_PATH = "/api/csrf/"


@click.command(name="health-check")
@click.argument("path", required=False)
@click.option(
    "--unset",
    is_flag=True,
    help="Clear the custom path and revert to the platform default.",
)
@app_option
@handle_errors
def health_check(path: str | None, unset: bool, app_name: str | None) -> None:
    """Show or set the HTTP path used to health-check the app's web service.

    With no PATH, prints the current setting. The path is probed by the
    platform's zero-downtime rollout checks and must return 200 without
    authentication. Changes take effect on the app's next infrastructure
    apply.
    """
    client = make_client()
    app = resolve_app(client, app_name or "")
    stack_id = require_stack_id(app)

    if unset:
        path = ""
    elif path is None:
        current = client.stack_status(stack_id).get("web_health_check_path") or ""
        if current:
            out.print(current)
        else:
            out.print(f"{PLATFORM_DEFAULT_PATH} (platform default)")
        return

    updated = client.stack_update(stack_id, {"web_health_check_path": path})
    effective = updated.get("web_health_check_path") or ""
    if effective:
        out.print(f"Health-check path for '{app.name}' set to {effective}.")
    else:
        out.print(
            f"Health-check path for '{app.name}' reset to the platform "
            f"default ({PLATFORM_DEFAULT_PATH})."
        )
    out.print("Takes effect on the next infrastructure apply.")
