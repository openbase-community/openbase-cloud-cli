"""``openbase access`` — manage who can collaborate on an app's server pool."""

from __future__ import annotations

import json as jsonlib

import click
from rich.table import Table

from openbase_cli.apps import require_stack_id, resolve_app
from openbase_cli.context import app_option, err, handle_errors, make_client, out


@click.group(invoke_without_command=True)
@app_option
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
@handle_errors
def access(ctx: click.Context, app_name: str | None, as_json: bool) -> None:
    """View or change who has access to the app's server pool.

    Access is per server pool: collaborators can deploy, view logs, and manage
    config vars and secrets for every app on the pool. Only the pool owner can
    add or remove collaborators. With no subcommand, lists the owner, accepted
    collaborators, and pending invitations.
    """
    if ctx.invoked_subcommand is not None:
        return
    client = make_client()
    app = resolve_app(client, app_name or "")
    data = client.stack_access(require_stack_id(app))
    collaborators = data.get("collaborators", []) or []
    invitations = data.get("invitations", []) or []
    owner_email = (app.stack or {}).get("owner_email") or ""

    if as_json:
        out.print_json(
            jsonlib.dumps(
                {
                    "owner": owner_email,
                    "collaborators": collaborators,
                    "invitations": invitations,
                }
            )
        )
        return
    table = Table(box=None, pad_edge=False)
    table.add_column("EMAIL", style="bold")
    table.add_column("ROLE")
    table.add_column("STATUS")
    if owner_email:
        table.add_row(owner_email, "owner", "")
    for collaborator in collaborators:
        table.add_row(str(collaborator.get("email", "")), "collaborator", "")
    for invitation in invitations:
        table.add_row(str(invitation.get("email", "")), "collaborator", "invited")
    out.print(table)


@access.command("add")
@app_option
@click.argument("email")
@handle_errors
def access_add(app_name: str | None, email: str) -> None:
    """Invite EMAIL to collaborate on the app's server pool.

    Sends an invitation email; the invitee signs in with that address and
    accepts. Re-running resends the invitation. Owner only.
    """
    client = make_client()
    app = resolve_app(client, app_name or "")
    client.create_stack_invitation(require_stack_id(app), email=email)
    err.print(f"Invited {email} to collaborate on '{app.name}'. Invitation email sent.")


@access.command("remove")
@app_option
@click.argument("email")
@handle_errors
def access_remove(app_name: str | None, email: str) -> None:
    """Remove EMAIL's access (or revoke a pending invitation). Owner only."""
    client = make_client()
    app = resolve_app(client, app_name or "")
    data = client.stack_access(require_stack_id(app))
    lowered = email.strip().lower()
    removed = False
    for collaborator in data.get("collaborators", []) or []:
        if str(collaborator.get("email", "")).lower() == lowered and collaborator.get("id"):
            client.delete_stack_collaborator(str(collaborator["id"]))
            err.print(f"Removed collaborator {email} from '{app.name}'.")
            removed = True
    for invitation in data.get("invitations", []) or []:
        if str(invitation.get("email", "")).lower() == lowered and invitation.get("id"):
            client.delete_stack_invitation(str(invitation["id"]))
            err.print(f"Revoked pending invitation for {email} on '{app.name}'.")
            removed = True
    if not removed:
        raise click.ClickException(f"{email} has no access or pending invitation on '{app.name}'.")
