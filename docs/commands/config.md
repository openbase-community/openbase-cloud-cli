# config

View, set, and unset an app's config vars, Heroku-style.

Vars you set with `config set` are plaintext and read back with `config`.
Secret values are managed only in the [dashboard](https://app.openbase.cloud) —
they are never returned by the API (they show as `(secret — set in dashboard)`
in the table, `null` in `--json`) and cannot be set from the CLI.

## Usage

```bash
openbase config -a my-app                      # list
openbase config -a my-app --json               # {key: value}, secrets null
openbase config set -a my-app DEBUG=false      # set (overwrites) one or more
openbase config set -a my-app A=1 B=2          # multiple at once
openbase config unset -a my-app DEBUG A        # remove one or more
```

`set` and `unset` change the deployed environment, so they trigger a new
release. `set` overwrites a key that already exists. Platform-reserved keys
(e.g. `DEPLOYMENT_*`, `DATABASE_URL`) are rejected by the server.

## Subcommands

| Command | Description |
|---|---|
| `config` | List vars (`KEY` / `VALUE`, sorted by key; secrets masked) |
| `config set KEY=VALUE...` | Create or overwrite plaintext vars, then redeploy |
| `config unset KEY...` | Remove vars, then redeploy |

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |
| `--json` | (list only) Emit a `{key: value}` object; secret values are `null` |

## Related

- [`ps`](ps.md) — stack status
- [`releases`](releases.md) — deploy runs
