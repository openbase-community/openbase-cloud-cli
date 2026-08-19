"""``openbase webhook`` — manage a server pool's release-notification webhook."""

from __future__ import annotations

import click

from openbase_cli.apps import require_stack_id, resolve_app
from openbase_cli.context import app_option, err, handle_errors, make_client, out


@click.group(invoke_without_command=True)
@app_option
@click.pass_context
@handle_errors
def webhook(ctx: click.Context, app_name: str | None) -> None:
    """View or change the app's release-notification webhook.

    The webhook is per server pool: every run on the pool (and its apps) that
    reaches a terminal state POSTs a signed JSON payload to the URL. Verify the
    ``X-Openbase-Signature: sha256=<hmac>`` header with the shown secret.
    """
    if ctx.invoked_subcommand is not None:
        return
    client = make_client()
    app = resolve_app(client, app_name or "")
    data = client.get_stack_webhook(require_stack_id(app))
    url = (data or {}).get("url") or ""
    if not url:
        err.print(f"No release webhook set for '{app.name}'.")
        return
    out.print(f"URL:    {url}")
    out.print(f"Secret: {(data or {}).get('secret') or ''}")


@webhook.command("set")
@app_option
@click.argument("url")
@click.option(
    "--secret",
    default=None,
    help="Signing secret. Omit to auto-generate (shown on success).",
)
@handle_errors
def webhook_set(app_name: str | None, url: str, secret: str | None) -> None:
    """Set the pool's release webhook URL (and optional signing secret)."""
    client = make_client()
    app = resolve_app(client, app_name or "")
    data = client.set_stack_webhook(require_stack_id(app), url=url, secret=secret)
    out.print(f"Release webhook set for '{app.name}'.")
    out.print(f"URL:    {(data or {}).get('url') or url}")
    out.print(f"Secret: {(data or {}).get('secret') or ''}")
    err.print(
        "[dim]Payloads are signed HMAC-SHA256 over the body (X-Openbase-Signature: sha256=…).[/dim]"
    )


@webhook.command("unset")
@app_option
@handle_errors
def webhook_unset(app_name: str | None) -> None:
    """Remove the pool's release webhook."""
    client = make_client()
    app = resolve_app(client, app_name or "")
    client.unset_stack_webhook(require_stack_id(app))
    err.print(f"Release webhook removed for '{app.name}'.")
