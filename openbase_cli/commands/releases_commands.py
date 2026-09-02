"""``openbase releases`` — inspect and wait for app deploy runs."""

from __future__ import annotations

import json as jsonlib
import re
import time
from typing import Any

import click
from rich.table import Table

from openbase_cli.apps import require_stack_id, resolve_app
from openbase_cli.context import (
    app_option,
    err,
    handle_errors,
    make_client,
    out,
    sanitize_remote_text,
)

_TERMINAL_STATUSES = {"succeeded", "failed", "superseded"}
_WAITABLE_OPERATIONS = ["deploy", "frontend_deploy"]
_FULL_COMMIT_SHA = re.compile(r"[0-9a-fA-F]{40}")


def _validate_commit_sha(
    _ctx: click.Context,
    _param: click.Parameter,
    value: str,
) -> str:
    value = value.strip().lower()
    if not _FULL_COMMIT_SHA.fullmatch(value):
        raise click.BadParameter("must be a full 40-character hexadecimal Git commit SHA")
    return value


@click.group(invoke_without_command=True)
@click.pass_context
@app_option
@click.option(
    "-n",
    "--num",
    "limit",
    type=int,
    default=15,
    show_default=True,
    help="Maximum number of runs to show.",
)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@handle_errors
def releases(ctx: click.Context, app_name: str | None, limit: int, as_json: bool) -> None:
    """List recent deploy runs for an app, or wait for a specific release."""
    if ctx.invoked_subcommand is not None:
        return
    client = make_client()
    app = resolve_app(client, app_name or "")
    runs = client.resource_runs(app.resource_id)[:limit]

    if as_json:
        out.print_json(jsonlib.dumps(runs))
        return
    if not runs:
        err.print(f"No deploy runs recorded for '{app.name}' yet.")
        return
    table = Table(box=None, pad_edge=False)
    table.add_column("WHEN")
    table.add_column("OPERATION", style="bold")
    table.add_column("STATUS")
    table.add_column("REF")
    table.add_column("AGENT")
    table.add_column("SUMMARY")
    for run in runs:
        table.add_row(
            str(run.get("created_at", "") or "—"),
            str(run.get("operation", "") or "—"),
            str(run.get("status", "") or "—"),
            _ref(run),
            str(run.get("agent_id", "") or "—"),
            str(run.get("summary", "") or ""),
        )
    out.print(table)


@releases.command("wait")
@app_option
@click.option(
    "--commit",
    "commit_sha",
    required=True,
    callback=_validate_commit_sha,
    help="Full commit SHA to wait for.",
)
@click.option(
    "--operation",
    type=click.Choice(_WAITABLE_OPERATIONS),
    required=True,
    help="Release operation triggered by the commit.",
)
@click.option(
    "--verify-rollout",
    is_flag=True,
    help="After release success, wait for every live ECS service to finish rolling out.",
)
@click.option(
    "--timeout",
    type=click.FloatRange(min=1),
    default=1800.0,
    show_default=True,
    metavar="SECONDS",
    help="Maximum time to wait.",
)
@click.option(
    "--poll-interval",
    type=click.FloatRange(min=0.1),
    default=10.0,
    show_default=True,
    metavar="SECONDS",
    help="Delay between API checks.",
)
@handle_errors
def wait_for_release(
    app_name: str | None,
    commit_sha: str,
    operation: str,
    verify_rollout: bool,
    timeout: float,
    poll_interval: float,
) -> None:
    """Wait until one commit's release succeeds or fails.

    Rollout verification is for server deploys. It refreshes live stack status
    after CodeBuild succeeds and waits until every reported ECS service is
    stable, preventing an asynchronous circuit-breaker rollback from looking
    like a successful release.
    """
    if verify_rollout and operation != "deploy":
        raise click.UsageError("--verify-rollout is only valid with --operation deploy.")
    client = make_client()
    app = resolve_app(client, app_name or "")
    stack_id = require_stack_id(app) if verify_rollout else None
    deadline = time.monotonic() + timeout
    last_progress = ""

    while True:
        runs = client.resource_runs(app.resource_id)
        run, newer_run = _target_release(runs, commit_sha=commit_sha, operation=operation)
        if newer_run:
            newer_sha = str(newer_run.get("commit_sha") or "")[:12] or "unknown"
            raise click.ClickException(
                f"Release {commit_sha[:12]} was overtaken by newer {operation} release {newer_sha}."
            )

        progress = "waiting for the webhook-created run"
        if run:
            status = str(run.get("status") or "unknown")
            progress = f"release {run.get('id') or commit_sha[:12]!s} is {status}"
            if status in {"failed", "superseded"}:
                summary = _release_summary(run)
                raise click.ClickException(
                    f"Release {commit_sha[:12]} {status}: {summary}"
                )
            if status == "succeeded":
                if not verify_rollout:
                    out.print(f"Release {commit_sha[:12]} succeeded ({operation}).")
                    return
                stack = client.stack_status(stack_id or "")
                rollout_state, rollout_detail = _rollout_verification(stack)
                progress = rollout_detail
                if rollout_state == "failed":
                    raise click.ClickException(rollout_detail)
                if rollout_state == "succeeded":
                    # Re-read the run after the live AWS check. The rollout
                    # verifier may have changed a previously successful run to
                    # failed while stack status was being refreshed.
                    confirmed_runs = client.resource_runs(app.resource_id)
                    confirmed, newer_confirmed = _target_release(
                        confirmed_runs,
                        commit_sha=commit_sha,
                        operation=operation,
                    )
                    if newer_confirmed:
                        newer_sha = str(newer_confirmed.get("commit_sha") or "")[:12]
                        raise click.ClickException(
                            f"Release {commit_sha[:12]} was overtaken by newer "
                            f"{operation} release {newer_sha or 'unknown'}."
                        )
                    confirmed_status = str((confirmed or {}).get("status") or "missing")
                    if confirmed_status == "succeeded":
                        out.print(
                            f"Release {commit_sha[:12]} succeeded ({operation}); "
                            "ECS rollout is stable."
                        )
                        return
                    if confirmed_status in _TERMINAL_STATUSES:
                        summary = _release_summary(confirmed or {})
                        raise click.ClickException(
                            f"Release {commit_sha[:12]} became {confirmed_status}: {summary}"
                        )

        if progress != last_progress:
            click.echo(f"Waiting: {progress}.", err=True)
            last_progress = progress
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise click.ClickException(
                f"Timed out after {timeout:g}s waiting for {operation} release {commit_sha[:12]}."
            )
        time.sleep(min(poll_interval, remaining))


def _target_release(
    runs: list[dict[str, Any]],
    *,
    commit_sha: str,
    operation: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return the target run and any newer run that overtook it.

    The API returns newest first. A newer run for the same operation and ref
    means live state no longer belongs to the requested commit, even if that
    older run once succeeded.
    """
    target_index = next(
        (
            index
            for index, run in enumerate(runs)
            if run.get("commit_sha") == commit_sha and run.get("operation") == operation
        ),
        None,
    )
    if target_index is None:
        return None, None
    target = runs[target_index]
    target_ref = str(target.get("git_ref") or "")
    newer = next(
        (
            run
            for run in runs[:target_index]
            if run.get("operation") == operation
            and str(run.get("git_ref") or "") == target_ref
            and run.get("commit_sha") != commit_sha
        ),
        None,
    )
    return target, newer


def _rollout_verification(stack: dict[str, Any]) -> tuple[str, str]:
    expected_image_tag = str(stack.get("expected_image_tag") or "")
    if not expected_image_tag:
        return "waiting", "waiting for the expected image tag"
    payload = stack.get("last_status_payload") or {}
    services = payload.get("services") if isinstance(payload, dict) else None
    if not isinstance(services, list) or not services:
        return "waiting", "waiting for live ECS rollout status"
    if not any(service.get("component") == "web" for service in services):
        return "waiting", "waiting for the web service rollout"

    for service in services:
        component = str(service.get("component") or service.get("service") or "service")
        rollout_state = str(service.get("rollout_state") or "UNKNOWN")
        if rollout_state == "FAILED":
            return "failed", f"ECS {component} rollout failed"
        if rollout_state != "COMPLETED":
            return "waiting", f"ECS {component} rollout is {rollout_state.lower()}"
        if service.get("running") != service.get("desired") or service.get("pending") != 0:
            return "waiting", f"ECS {component} tasks have not stabilized"
        live_image_tag = str(service.get("image_tag") or "")
        if live_image_tag != expected_image_tag:
            return (
                "waiting",
                f"ECS {component} is running image {live_image_tag or 'unknown'}, "
                f"waiting for {expected_image_tag}",
            )
    return "succeeded", "ECS rollout is stable"


def _release_summary(run: dict[str, Any]) -> str:
    summary = run.get("summary") or "Release did not succeed."
    return sanitize_remote_text(summary)[:1000]


def _ref(run: dict) -> str:
    sha = str(run.get("commit_sha", "") or "")
    ref = str(run.get("git_ref", "") or "")
    short = sha[:7] if sha else ""
    if ref and short:
        return f"{ref}@{short}"
    return ref or short or "—"
