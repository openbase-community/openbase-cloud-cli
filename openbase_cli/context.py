"""Shared CLI plumbing: a Client factory, output console, and error handling."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

import click
from rich.console import Console

from openbase_cli.api import ApiError, Client
from openbase_cli.apps import AppResolutionError
from openbase_cli.auth import AuthError, LoginRequiredError, TokenManager

# Data goes to stdout (pipe-friendly); human status/errors go to stderr.
out = Console()
err = Console(stderr=True)

F = TypeVar("F", bound=Callable[..., Any])


def make_client() -> Client:
    return Client(TokenManager())


def handle_errors(func: F) -> F:
    """Turn library exceptions into concise messages and a non-zero exit.

    Keeps tracebacks out of the user's face for the expected failure modes
    (not logged in, no access, bad app name, backend down).
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except LoginRequiredError as exc:
            err.print(f"[red]{exc}[/red]")
            raise SystemExit(1) from exc
        except (AuthError, ApiError, AppResolutionError) as exc:
            err.print(f"[red]Error:[/red] {exc}")
            raise SystemExit(1) from exc

    return wrapper  # type: ignore[return-value]


def app_option(func: F) -> F:
    """Add the standard ``-a/--app`` option, defaulting to ``$OPENBASE_APP``."""
    return click.option(
        "-a",
        "--app",
        "app_name",
        envvar="OPENBASE_APP",
        metavar="APP",
        help="Openbase app (deployment resource) name. Defaults to $OPENBASE_APP.",
    )(func)
