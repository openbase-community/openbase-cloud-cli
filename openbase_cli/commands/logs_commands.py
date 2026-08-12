"""``openbase-deploy logs`` — read (and tail) app logs, Heroku-style."""

from __future__ import annotations

import time

import click

from openbase_cli.apps import require_stack_id, resolve_app
from openbase_cli.context import app_option, err, handle_errors, make_client, out

# How long to sleep between polls when tailing. The logs endpoint is a
# windowed pull, not a stream, so we re-query and print only unseen lines.
_TAIL_INTERVAL_SECONDS = 3.0


@click.command()
@app_option
@click.option(
    "-n",
    "--num",
    "since_minutes",
    type=int,
    default=15,
    show_default=True,
    metavar="MINUTES",
    help="Show log lines from the last MINUTES minutes.",
)
@click.option(
    "-t", "--tail", is_flag=True, help="Continuously stream new log lines (Ctrl-C to stop)."
)
@handle_errors
def logs(app_name: str | None, since_minutes: int, tail: bool) -> None:
    """Display recent logs for an app.

    Openbase Cloud currently surfaces recent error-level lines from the app's
    server stack. Without --tail this prints one snapshot and exits.
    """
    client = make_client()
    app = resolve_app(client, app_name or "")
    stack_id = require_stack_id(app)

    lines = client.stack_logs(stack_id, since_minutes=since_minutes)
    for line in lines:
        out.print(line, markup=False, highlight=False)

    if not tail:
        if not lines:
            err.print(f"No log lines in the last {since_minutes} minute(s).")
        return

    err.print("[dim]Tailing logs. Press Ctrl-C to stop.[/dim]")
    # Track the tail of what we have shown so repeated windows don't re-print
    # lines. Log lines are not guaranteed unique, so we de-dupe on a rolling
    # window rather than a set.
    seen = list(lines)
    try:
        while True:
            time.sleep(_TAIL_INTERVAL_SECONDS)
            current = client.stack_logs(stack_id, since_minutes=max(since_minutes, 5))
            fresh = _new_lines(seen, current)
            for line in fresh:
                out.print(line, markup=False, highlight=False)
            if fresh:
                seen = current[-500:]
    except KeyboardInterrupt:
        err.print("\n[dim]Stopped tailing.[/dim]")


def _new_lines(previous: list[str], current: list[str]) -> list[str]:
    """Return the suffix of ``current`` that follows the overlap with ``previous``.

    Finds the largest ``k`` such that the last ``k`` previously-seen lines are a
    prefix of ``current``; everything after that is new. Falls back to the whole
    window when there is no overlap (e.g. after a gap).
    """
    if not previous:
        return current
    max_overlap = min(len(previous), len(current))
    for k in range(max_overlap, 0, -1):
        if previous[-k:] == current[:k]:
            return current[k:]
    return current
