"""``openbase login`` / ``logout`` / ``whoami``."""

from __future__ import annotations

import click
import httpx

from openbase_cli import config, login_flow
from openbase_cli.auth import AuthError, LoginRequiredError, TokenManager
from openbase_cli.context import err, handle_errors, out


@click.command()
@click.option(
    "--no-browser", is_flag=True, help="Print the login URL instead of opening a browser."
)
def login(no_browser: bool) -> None:
    """Log in to Openbase Cloud in your browser.

    Shares its session with the Openbase Coder CLI: credentials are written to
    ~/.openbase/auth.json, so logging in here logs you in for both.
    """
    host = config.host()
    try:
        access, refresh, expires_in = login_flow.run_browser_login(
            host=host, echo=err.print, open_browser=not no_browser
        )
    except httpx.HTTPStatusError as exc:
        err.print(f"[red]OAuth login failed:[/red] {login_flow.format_http_error(exc)}")
        raise SystemExit(1) from None
    except (RuntimeError, httpx.HTTPError) as exc:
        err.print(f"[red]OAuth login failed:[/red] {exc}")
        raise SystemExit(1) from None

    TokenManager(host).store_tokens(
        access_token=access, refresh_token=refresh, expires_in=expires_in
    )
    email = TokenManager(host).owner_email()
    suffix = f" as [bold]{email}[/bold]" if email else ""
    out.print(f"Logged in{suffix}.")


@click.command()
def logout() -> None:
    """Log out and remove the shared Openbase Cloud credentials."""
    manager = TokenManager()
    if not config.AUTH_JSON_PATH.is_file():
        out.print("Not logged in.")
        return
    manager.clear()
    out.print("Logged out. Credentials removed from ~/.openbase/auth.json.")


@click.command()
@handle_errors
def whoami() -> None:
    """Show the currently logged-in Openbase Cloud account."""
    manager = TokenManager()
    if not manager.is_logged_in:
        raise LoginRequiredError("Not logged in. Run 'openbase login' first.")
    try:
        manager.get_access_token()  # forces a refresh, validating the session
    except AuthError:
        raise
    email = manager.owner_email()
    out.print(email or "Logged in (account email unavailable).")
