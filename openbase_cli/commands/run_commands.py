"""``openbase run`` — execute a one-off command in an app container."""

from __future__ import annotations

import click

from openbase_cli.apps import require_stack_id, resolve_app
from openbase_cli.context import app_option, err, handle_errors, make_client, print_remote_line


# ignore_unknown_options lets unknown flags flow into COMMAND;
# allow_interspersed_args=False stops click from also claiming *known* options
# (-a, --memory, --shell-bin) that appear after the command starts, so
# `openbase run -a api ./script --memory 512` passes --memory to the script
# instead of silently resizing the task. CLI options must precede COMMAND.
@click.command(
    "run",
    context_settings={"ignore_unknown_options": True, "allow_interspersed_args": False},
)
@app_option
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@click.option("--shell-bin", default="/bin/sh", show_default=True)
@click.option(
    "--memory",
    default=256,
    show_default=True,
    type=int,
    help="Hard memory limit in MiB for the temporary task.",
)
@handle_errors
def run_command(
    app_name: str | None, command: tuple[str, ...], shell_bin: str, memory: int
) -> None:
    """Run COMMAND in a temporary copy of the app's web container."""
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise click.UsageError("Missing COMMAND. Example: openbase run -a my-app bash")
    client = make_client()
    app = resolve_app(client, app_name or "")
    stack_id = require_stack_id(app)
    err.print(f"[dim]Running command on {app.name}...[/dim]")
    result = client.stack_run(
        stack_id,
        command=list(command),
        shell_bin=shell_bin,
        memory=memory,
    )
    for line in result.get("lines", []) or []:
        print_remote_line(line)
    exit_code = result.get("exit_code")
    if exit_code != 0:
        # exit_code None means the container never reported one — the task
        # failed to place or was killed before the command ran. That is a
        # failure, not a silent success.
        stopped_reason = str(result.get("stopped_reason") or "")
        detail = f": {stopped_reason}" if stopped_reason else ""
        label = (
            f"exit code {exit_code}"
            if exit_code is not None
            else "no exit code (the task did not run to completion)"
        )
        raise click.ClickException(f"Command failed with {label}{detail}")
