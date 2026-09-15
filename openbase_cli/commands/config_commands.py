"""``openbase config`` — view, set, and unset an app's config vars."""

from __future__ import annotations

import json as jsonlib
import sys

import click
from rich.table import Table

from openbase_cli.apps import App, resolve_app
from openbase_cli.context import (
    app_option,
    err,
    handle_errors,
    make_client,
    out,
    sanitize_remote_text,
)

_SECRET_PLACEHOLDER = "(secret — value hidden)"

_FULL_LISTING_WARNING = (
    "This dumps EVERY config var for the app in one output — including all "
    "plaintext values — which is rarely what you need and is easy to leak "
    "into logs, chat, or shell history. If you only need specific keys, use "
    "`openbase config get KEY...` instead."
)


def _stdin_is_interactive() -> bool:
    return sys.stdin.isatty()


@click.group(invoke_without_command=True)
@app_option
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.option(
    "--confirm",
    "confirmed",
    is_flag=True,
    help="Skip the full-listing confirmation prompt (required when non-interactive).",
)
@click.pass_context
@handle_errors
def config(ctx: click.Context, app_name: str | None, as_json: bool, confirmed: bool) -> None:
    """View or change an app's config vars.

    With no subcommand, lists ALL the vars — prefer ``config get KEY`` for
    specific values. Values set with ``config set`` are plaintext and read
    back here; values set with ``config set --secret`` (or as secrets in the
    dashboard) are write-only and show as a placeholder.

    The full listing asks for confirmation (pass ``--confirm`` to skip, which
    is required when running non-interactively).
    """
    if ctx.invoked_subcommand is not None:
        return
    if not confirmed:
        if _stdin_is_interactive():
            err.print(f"[yellow]{_FULL_LISTING_WARNING}[/yellow]")
            if not click.confirm("Are you SURE you want the full listing?"):
                raise click.Abort()
        else:
            raise click.UsageError(
                _FULL_LISTING_WARNING + " To list everything anyway, pass --confirm."
            )
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


@config.command("get")
@app_option
@click.option("--json", "as_json", is_flag=True, help="Output a {key: value} JSON object.")
@click.argument("keys", nargs=-1, required=True, metavar="KEY...")
@handle_errors
def config_get(app_name: str | None, as_json: bool, keys: tuple[str, ...]) -> None:
    """Print the value of one or more specific config vars.

    Prefer this over the full ``openbase config`` listing whenever you know
    which keys you need: it retrieves only those values, so nothing else can
    end up in your output, logs, or shell history.

    With a single KEY, prints the bare value (pipe-friendly). With several,
    prints ``KEY=VALUE`` lines. Secrets are write-only and show as a
    placeholder (``null`` in ``--json``). Keys that are not set are reported
    on stderr and the command exits non-zero.
    """
    client = make_client()
    app = resolve_app(client, app_name or "")
    variables = {
        str(v.get("key")): v for v in client.resource_config_vars(app.resource_id) if v.get("key")
    }
    missing = [k for k in keys if k not in variables]

    def value_of(key: str) -> str:
        v = variables[key]
        if v.get("is_secret"):
            return _SECRET_PLACEHOLDER
        return sanitize_remote_text(v.get("value") or "")

    if as_json:
        out.print_json(
            jsonlib.dumps(
                {
                    k: (None if variables[k].get("is_secret") else variables[k].get("value"))
                    for k in keys
                    if k in variables
                }
            )
        )
    elif len(keys) == 1 and not missing:
        out.print(value_of(keys[0]), markup=False, highlight=False)
    else:
        for k in keys:
            if k in variables:
                out.print(f"{k}={value_of(k)}", markup=False, highlight=False)
    for k in missing:
        err.print(f"[yellow]{k} is not set on {app.name}.[/yellow]")
    if missing:
        raise SystemExit(1)


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
@click.option(
    "--secret-stdin",
    "secret_stdin_key",
    metavar="KEY",
    help="Read one write-only secret from standard input instead of process arguments.",
)
@click.argument("pairs", nargs=-1, metavar="KEY=VALUE...")
@handle_errors
def config_set(
    app_name: str | None,
    is_secret: bool,
    secret_stdin_key: str | None,
    pairs: tuple[str, ...],
) -> None:
    """Set one or more config vars (KEY=VALUE), then redeploy.

    Overwrites a key that already exists. Values are plaintext and readable
    back with ``openbase config`` unless ``--secret`` is passed, in which case
    they are stored write-only (shown only as a placeholder afterwards). Use
    ``--secret-stdin KEY`` to keep one secret value out of process arguments.
    """
    if secret_stdin_key and (is_secret or pairs):
        raise click.UsageError("--secret-stdin cannot be combined with --secret or KEY=VALUE")
    if not secret_stdin_key and not pairs:
        raise click.UsageError("Provide KEY=VALUE or --secret-stdin KEY")

    parsed: list[tuple[str, str]] = []
    if secret_stdin_key:
        key = secret_stdin_key.strip()
        if not key:
            raise click.UsageError("--secret-stdin requires a non-empty key")
        value = click.get_text_stream("stdin").read()
        if value.endswith("\n"):
            value = value[:-1]
            if value.endswith("\r"):
                value = value[:-1]
        if not value:
            raise click.UsageError("No secret value was received on standard input")
        parsed.append((key, value))
        is_secret = True

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
