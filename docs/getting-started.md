# Getting Started

This guide installs the `openbase` CLI, signs you in, and walks through reading
and deploying an app on the Openbase Cloud PaaS.

## Install

```bash
pip install openbase-cli        # provides the `openbase` command
# or:
uv tool install openbase-cli
```

The CLI needs Python 3.11+. It talks only to the Openbase Cloud API over HTTPS —
no AWS credentials, no local Docker.

## Sign In

Login is shared with the [Openbase Coder](https://docs.openbase.cloud) CLI
(`openbase-coder`): `openbase login` runs `openbase-coder login`, which owns the
browser sign-in and writes credentials to `~/.openbase/auth.json`. Signing in
with either tool signs you in for both.

```bash
openbase login
```

Install `openbase-coder` first if you do not have it (`openbase login` delegates
to it). Confirm you are signed in:

```bash
openbase whoami     # prints your account email
openbase account    # balance, subscription, email-verification status
```

To sign out and remove the shared credentials:

```bash
openbase logout
```

## Address an App

Most app commands take a target app. Pass it with `-a/--app`, or set a default
with the `OPENBASE_APP` environment variable so you can omit the flag.

```bash
openbase apps                   # list apps you can access
openbase ps -a my-app           # status of one app
export OPENBASE_APP=my-app      # default target for -a
openbase ps                     # same as: openbase ps -a my-app
```

## Inspect an App

```bash
openbase ps -a my-app           # current stack status (alias: status)
openbase logs -a my-app         # recent logs (last 15 min by default)
openbase logs -a my-app --tail  # stream new lines (Ctrl-C to stop)
openbase run -a my-app python manage.py migrate  # one-off command
openbase config -a my-app       # config vars (secret values hidden)
openbase releases -a my-app     # recent deploy runs
openbase open -a my-app         # open the app's URL in your browser
```

## Deploy an App

Openbase Cloud deploys are **push-to-deploy**: you connect a GitHub repository
to an app in the [dashboard](https://app.openbase.cloud), and pushing to the
connected branch triggers a deploy run. The `openbase` CLI is how you watch and
verify those runs from the terminal — it reads deploy state, it does not push
infrastructure itself.

A typical loop after connecting a repo:

```bash
git push origin main            # triggers a deploy run on Openbase Cloud
openbase releases -a my-app     # watch the new run appear and progress
openbase logs -a my-app --tail  # follow app logs during/after rollout
openbase run -a my-app python manage.py check
openbase ps -a my-app           # confirm the stack is healthy
```

Config vars and secrets are managed in the dashboard; `openbase config` shows
the non-secret values (secrets display as a placeholder).

## Account-Wide Views

```bash
openbase usage        # this month's spend and limits (sandbox, deploy, LLM)
openbase projects     # your Openbase Cloud projects
openbase workspaces   # your cloud dev workspaces (devspaces) and status
```

Devspaces are documented in depth in the
[Openbase Coder docs](https://docs.openbase.cloud); `openbase workspaces` is a
quick terminal readout of their status and spend.

## Scripting

Add `--json` to most commands for machine-readable output:

```bash
openbase apps --json
openbase ps -a my-app --json
openbase usage --json
```

See [Configuration](configuration.md) for all environment variables and the
`--json` flag.

## Next Steps

- Browse the full [Commands](commands/index.md) reference
- Set a default app and API URL in [Configuration](configuration.md)
- Run any Coder command via [`openbase coder <args>`](commands/coder.md)
