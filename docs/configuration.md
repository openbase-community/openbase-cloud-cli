# Configuration

The `openbase` CLI is configured with a few environment variables and a couple
of global flags. Credentials are stored on disk by the shared sign-in flow.

## Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENBASE_APP` | Default app for `-a/--app`, so you can omit the flag | — |
| `OPENBASE_API_URL` | Override the Openbase Cloud base URL | `https://app.openbase.cloud` |
| `OPENBASE_HOST` | Alias for `OPENBASE_API_URL` | — |
| `OPENBASE_AGENT_ID` | Attribute mutations to an agent; set it to the agent/thread UUID | — |

Set a default app for a shell session:

```bash
export OPENBASE_APP=my-app
openbase logs --tail        # no -a needed
```

## Agent Attribution

Every mutation (config changes, deploys, restarts, hostname edits, teardowns)
is recorded against whoever made it. An agent driving the CLI exports its
agent/thread UUID so its actions are attributed to it:

```bash
export OPENBASE_AGENT_ID=cac5ccd4-2499-4784-a2a6-05e3b2caa98b
openbase config set -a my-app FEATURE_FLAG=on
```

The CLI sends this as the `X-Openbase-Agent-Id` header. When it is unset the CLI
sends nothing and Openbase Cloud records the mutation as `human`. Attribution
shows up in the AGENT column of [`openbase releases`](commands/releases.md) and
in release webhook notifications.

## Credentials

Sign-in is delegated to the `openbase-coder` CLI and writes to a shared file:

```text
~/.openbase/auth.json
```

Both `openbase` and `openbase-coder` read this file, so signing in with either
tool authenticates both. `openbase logout` removes it. See
[`login`](commands/login.md) and [`logout`](commands/logout.md).

## Global Flags

| Flag | Description |
| --- | --- |
| `-V`, `--version` | Print the CLI version and exit |
| `-h`, `--help` | Show help for the CLI or any subcommand |
| `-a`, `--app NAME` | Target app for app-scoped commands (or `OPENBASE_APP`) |
| `--json` | Machine-readable JSON output (supported by most read commands) |

## JSON Output

Most read commands accept `--json` for scripting. Secret config values are never
returned by the API; in `openbase config --json` they appear as `null`.

```bash
openbase apps --json
openbase config -a my-app --json
openbase usage --json
```

## Talking to a Different Backend

Point the CLI at a non-production Openbase Cloud API (for example a staging
environment) with `OPENBASE_API_URL`:

```bash
OPENBASE_API_URL=https://app-staging.openbase.cloud openbase apps
```
