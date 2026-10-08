"""``openbase codex`` / ``openbase claude``: Openbase-profile agent sessions.

Both forward to ``openbase-coder codex|claude``, which owns the launch:
Openbase's session profile, attaching to the local Openbase runtime, and on a
paired Openbase Sync edge running the session on the hub. Plain ``codex`` and
``claude`` are never changed.
"""

from __future__ import annotations

import click

from openbase_cli.coder import exec_coder
from openbase_cli.context import handle_errors

_PASSTHROUGH = {
    "ignore_unknown_options": True,
    "allow_extra_args": True,
    "allow_interspersed_args": False,
    "help_option_names": [],
}


@click.command(context_settings=_PASSTHROUGH)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@handle_errors
def codex(args: tuple[str, ...]) -> None:
    """Start Codex with Openbase's profile: `openbase codex [ARGS...]`.

    Runs `openbase-coder codex`, so the session is visible to and steerable
    from Openbase (the app, the phone, the dispatcher). Requires
    openbase-coder. `--local` / `--remote` first choose where a paired
    Openbase Sync edge runs it; other ARGS go to Codex.
    """
    raise SystemExit(exec_coder(["codex", *args]))


@click.command(context_settings=_PASSTHROUGH)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@handle_errors
def claude(args: tuple[str, ...]) -> None:
    """Start Claude Code with Openbase's profile: `openbase claude [ARGS...]`.

    Runs `openbase-coder claude`, so the session is visible to and steerable
    from Openbase. Requires openbase-coder. `--local` / `--remote` first
    choose where a paired Openbase Sync edge runs it; other ARGS go to
    Claude Code.
    """
    raise SystemExit(exec_coder(["claude", *args]))
