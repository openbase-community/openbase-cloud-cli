"""Shared CLI plumbing: a Client factory, output console, and error handling."""

from __future__ import annotations

import functools
import re
from collections.abc import Callable
from typing import Any, TypeVar

import click
from rich.console import Console

from openbase_cli.api import ApiError, Client
from openbase_cli.apps import AppResolutionError
from openbase_cli.auth import AuthError, LoginRequiredError, TokenManager
from openbase_cli.coder import CoderNotInstalledError

# Data goes to stdout (pipe-friendly); human status/errors go to stderr.
out = Console()
err = Console(stderr=True)

# C0 controls (except tab), DEL, and C1 controls. Log and command output can
# contain visitor-controlled bytes (request paths, user agents, form fields);
# left unfiltered, an app's visitor could plant ANSI/OSC escape sequences that
# the developer's terminal then executes when they read logs — retitling the
# window, clearing the screen, or spoofing output. Stripping also drops color
# codes; plain text is the safe default for remote content.
_TERMINAL_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f\x80-\x9f]")


def sanitize_remote_text(value: object) -> str:
    """Strip terminal control characters from untrusted server text."""
    return _TERMINAL_CONTROL_CHARS.sub("", str(value))


def print_remote_line(line: str) -> None:
    """Print one line of remote app output (logs, run results) with terminal
    control characters stripped so remote content cannot inject escape
    sequences into the user's terminal."""
    out.print(sanitize_remote_text(line), markup=False, highlight=False)


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
        except (AuthError, ApiError, AppResolutionError, CoderNotInstalledError) as exc:
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
