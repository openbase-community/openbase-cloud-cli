"""``openbase config`` — view, set, and unset an app's config vars."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.apps import App, resolve_app
from openbase_cli.context import app_option, err, handle_errors, make_client, out

_SECRET_PLACEHOLDER = "(secret — value hidden)"


@click.group(invoke_without_command=True)
@app_option
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
@handle_errors
def config(ctx: click.Context, app_name: str | None, as_json: bool) -> None:
    """View or change an app's config vars.

    With no subcommand, lists the vars. Values set with ``config set`` are
    plaintext and read back here; values set with ``config set --secret`` (or
    as secrets in the dashboard) are write-only and show as a placeholder.
    """
    if ctx.invoked_subcommand is not None:
        return
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


def _config_var_index(client, app: App) -> dict[str, str]:
    """Map existing config-var key -> its id, for upsert/unset."""
    return {
        str(v.get("key")): str(v.get("id"))
        for v in client.resource_config_vars(app.resource_id)
        if v.get("key") and v.get("id")
    }


@config.command("set")
@app_option
@click.option(
    "--secret",
    "is_secret",
    is_flag=True,
    help="Store the value(s) as write-only secrets instead of plaintext vars.",
)
@click.argument("pairs", nargs=-1, required=True, metavar="KEY=VALUE...")
@handle_errors
def config_set(app_name: str | None, is_secret: bool, pairs: tuple[str, ...]) -> None:
    """Set one or more config vars (KEY=VALUE), then redeploy.

    Overwrites a key that already exists. Values are plaintext and readable
    back with ``openbase config`` unless ``--secret`` is passed, in which case
    they are stored write-only (shown only as a placeholder afterwards).
    """
    parsed: list[tuple[str, str]] = []
    for pair in pairs:
        key, sep, value = pair.partition("=")
        key = key.strip()
        if not sep or not key:
            raise click.UsageError(f"Invalid KEY=VALUE pair: {pair!r}")
        parsed.append((key, value))

    client = make_client()
    app = resolve_app(client, app_name or "")
    existing = _config_var_index(client, app)
    for key, value in parsed:
        # No update endpoint exists; overwrite an existing key by removing the
        # old var first, then creating the new one.
        if key in existing:
            client.delete_config_var(existing[key])
        client.set_config_var(app.resource_id, key=key, value=value, is_secret=is_secret)
        kind = "secret" if is_secret else "config var"
        err.print(f"[dim]Set {kind} {key} on {app.name}[/dim]")
    noun = "secret(s)" if is_secret else "config var(s)"
    err.print(f"Set {len(parsed)} {noun} on {app.name}. A new release is deploying.")


@config.command("unset")
@app_option
@click.argument("keys", nargs=-1, required=True, metavar="KEY...")
@handle_errors
def config_unset(app_name: str | None, keys: tuple[str, ...]) -> None:
    """Remove one or more config vars, then redeploy."""
    client = make_client()
    app = resolve_app(client, app_name or "")
    existing = _config_var_index(client, app)
    removed = 0
    for key in keys:
        if key not in existing:
            err.print(f"[yellow]{key} is not set on {app.name}; skipping.[/yellow]")
            continue
        client.delete_config_var(existing[key])
        err.print(f"[dim]Unset {key} on {app.name}[/dim]")
        removed += 1
    if removed:
        err.print(f"Unset {removed} config var(s) on {app.name}. A new release is deploying.")
