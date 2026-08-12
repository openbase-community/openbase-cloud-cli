"""``openbase login`` / ``logout`` / ``whoami`` and the ``coder`` passthrough."""

from __future__ import annotations

import click

from openbase_cli import config
from openbase_cli.auth import LoginRequiredError, TokenManager
from openbase_cli.coder import run_coder
from openbase_cli.context import handle_errors, out


@click.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@handle_errors
def login(args: tuple[str, ...]) -> None:
    """Log in to Openbase Cloud.

    Delegates to `openbase-coder login`, which owns the shared browser sign-in
    and writes credentials to ~/.openbase/auth.json (used by both CLIs).
    """
    raise SystemExit(run_coder(["login", *args]))


@click.command()
def logout() -> None:
    """Log out and remove the shared Openbase Cloud credentials."""
    if not config.AUTH_JSON_PATH.is_file():
        out.print("Not logged in.")
        return
    TokenManager().clear()
    out.print("Logged out. Credentials removed from ~/.openbase/auth.json.")


@click.command()
@handle_errors
def whoami() -> None:
    """Show the currently logged-in Openbase Cloud account."""
    manager = TokenManager()
    if not manager.is_logged_in:
        raise LoginRequiredError("Not logged in. Run 'openbase login' first.")
    manager.get_access_token()  # forces a refresh, validating the session
    email = manager.owner_email()
    out.print(email or "Logged in (account email unavailable).")


@click.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@handle_errors
def coder(args: tuple[str, ...]) -> None:
    """Run the Openbase Coder CLI: `openbase coder <args>`.

    A thin passthrough to the separate `openbase-coder` executable (devspaces,
    agents, and more). Requires openbase-coder to be installed.
    """
    raise SystemExit(run_coder(list(args)))
