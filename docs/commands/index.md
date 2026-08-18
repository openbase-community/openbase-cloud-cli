# Commands Overview

Command structure:

```bash
openbase [OPTIONS] COMMAND [ARGS]
```

Many of these operations also have equivalents in the
[Openbase Cloud dashboard](https://app.openbase.cloud); the CLI is the fast
terminal path to the same account and apps.

## Global Options

| Option | Description |
|---|---|
| `-V`, `--version` | Print CLI version and exit |
| `-h`, `--help` | Show help |
| `-a`, `--app NAME` | Target app for app-scoped commands (or set `OPENBASE_APP`) |
| `--json` | JSON output (most read commands) |

## Account

| Command | Description |
|---|---|
| [`login`](login.md) | Sign in to Openbase Cloud (delegates to `openbase-coder login`) |
| [`logout`](logout.md) | Sign out and remove the shared credentials |
| [`whoami`](whoami.md) | Show the signed-in account email |
| [`account`](account.md) | Account details: balance, subscription, verification |

## Apps & Deploys

| Command | Description |
|---|---|
| [`apps`](apps.md) | List Openbase Cloud apps you can access |
| [`open`](open.md) | Open an app's primary URL in your browser |
| [`logs`](logs.md) | Display and tail recent app logs |
| [`run`](run.md) | Run a one-off command in an app container |
| [`ps`](ps.md) | Show an app's current stack status (alias: `status`) |
| [`config`](config.md) | List an app's config vars (secrets hidden) |
| [`health-check`](health-check.md) | View or set the web health-check path |
| [`releases`](releases.md) | List recent deploy runs (releases) for an app |

## Account-Wide Resources

| Command | Description |
|---|---|
| [`usage`](usage.md) | This month's spend and usage limits |
| [`projects`](projects.md) | List your Openbase Cloud projects |
| [`workspaces`](workspaces.md) | List your cloud dev workspaces (devspaces) |

## Escape Hatch

| Command | Description |
|---|---|
| [`coder`](coder.md) | Run any `openbase-coder` command: `openbase coder <args>` |

## Common Examples

```bash
# Sign in and confirm
openbase login
openbase whoami

# List and inspect apps
openbase apps
openbase ps -a my-app
openbase logs -a my-app --tail
openbase run -a my-app python manage.py check
openbase config -a my-app
openbase releases -a my-app

# Account-wide
openbase usage
openbase projects
openbase workspaces

# Scripting
openbase apps --json
```
