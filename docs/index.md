# Openbase Cloud CLI

`openbase` is the command line for **[Openbase Cloud](https://openbase.cloud)** —
a Heroku-style tool and a fast alternative to the web dashboard. Sign in once,
then manage and inspect your apps, deploys, config, usage, and projects from the
terminal. It speaks only HTTPS to the Openbase Cloud API and needs no AWS
credentials.

These docs cover the `openbase` CLI and the Openbase Cloud PaaS workflow it
drives — connecting a repo, pushing to deploy, and reading app state. For the
voice-first coding product (desktop app, iPhone app, agents, devspaces), see the
separate **[Openbase Coder docs](https://docs.openbase.cloud)**.

## Which Page Do I Need?

- Installing and signing in for the first time → [Getting Started](getting-started.md)
- The full command list → [Commands](commands/index.md)
- Environment variables, default app, JSON output → [Configuration](configuration.md)
- Deploying an app to Openbase Cloud → [Getting Started](getting-started.md#deploy-an-app)

## Quick Start

```bash
pip install openbase-cli        # provides the `openbase` command
# or:  uv tool install openbase-cli

openbase login                  # shared sign-in (via openbase-coder)
openbase apps                   # list your apps
openbase logs -a my-app --tail  # stream logs
openbase ps -a my-app           # current status
```

## What You Can Do

Account:

- [`login`](commands/login.md) / [`logout`](commands/logout.md) — shared Openbase
  Cloud sign-in (delegated to the `openbase-coder` CLI)
- [`whoami`](commands/whoami.md) — the signed-in email
- [`account`](commands/account.md) — balance, subscription, verification

Apps & deploys:

- [`apps`](commands/apps.md) — list the apps you can access
- [`open`](commands/open.md) — open an app's URL in your browser
- [`logs`](commands/logs.md) — read and tail app logs
- [`ps`](commands/ps.md) (alias `status`) — an app's current stack status
- [`config`](commands/config.md) — an app's config vars
- [`releases`](commands/releases.md) — recent deploy runs

Account-wide resources:

- [`usage`](commands/usage.md) — this month's spend and limits
- [`projects`](commands/projects.md) — your Openbase Cloud projects
- [`workspaces`](commands/workspaces.md) — your cloud dev workspaces (devspaces)

Escape hatch:

- [`coder`](commands/coder.md) — run any `openbase-coder` command through
  `openbase coder <args>`

## Relationship to Openbase Coder

`openbase` and `openbase-coder` are sibling CLIs that share one login. Sign-in
and devspace/agent features live in `openbase-coder`; `openbase login` simply
runs `openbase-coder login` and both tools read the same
`~/.openbase/auth.json`. Devspaces and the coding agents are documented in the
[Openbase Coder docs](https://docs.openbase.cloud); this site stays focused on
the Openbase Cloud PaaS.
