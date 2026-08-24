# access

View and manage who can collaborate on an app's server pool.

Access is per **server pool**: a collaborator can deploy, view logs and status,
run one-off commands, and manage config vars and secrets for every app on the
pool. Adding and removing collaborators is owner-only; any member can view the
access list. The same controls are in the
[dashboard](https://app.openbase.cloud) (pool page → Collaborators).

## Usage

```bash
openbase access -a my-app                      # owner, collaborators, invites
openbase access -a my-app --json               # raw JSON
openbase access add -a my-app erik@example.com     # invite (owner only)
openbase access remove -a my-app erik@example.com  # remove or revoke (owner only)
```

`add` emails an invitation; the invitee signs in with the invited address and
accepts, at which point they become a collaborator. Invitations expire after
14 days; re-running `add` resends one. `remove` removes an accepted
collaborator, or revokes a still-pending invitation, matching by email.

## Subcommands

| Command | Description |
|---|---|
| `access` | List the pool owner, collaborators, and pending invitations |
| `access add EMAIL` | Invite EMAIL to collaborate on the pool (owner only) |
| `access remove EMAIL` | Remove EMAIL's access or revoke their invitation (owner only) |

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |
| `--json` | (list only) Raw JSON: owner, collaborators, invitations |

## Related

- [`config`](config.md) — config vars and secrets collaborators can manage
- [`apps`](apps.md) — apps you own or collaborate on
