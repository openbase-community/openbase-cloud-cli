# config

View, set, and unset an app's config vars, Heroku-style.

Vars you set with `config set` are plaintext and read back with `config`.
Pass `--secret` to store values write-only instead: secret values are never
returned by the API (they show as `(secret — value hidden)` in the table,
`null` in `--json`). Secrets can also be managed in the
[dashboard](https://app.openbase.cloud).

## Usage

```bash
openbase config -a my-app                      # list
openbase config -a my-app --json               # {key: value}, secrets null
openbase config set -a my-app DEBUG=false      # set (overwrites) one or more
openbase config set -a my-app A=1 B=2          # multiple at once
openbase config set --secret -a my-app API_KEY=…   # store write-only secret(s)
openbase config unset -a my-app DEBUG A        # remove one or more
```

`set` and `unset` change the deployed environment, so they trigger a new
release. `set` overwrites a key that already exists. Platform-reserved keys
(e.g. `DEPLOYMENT_*`, `DATABASE_URL`) are rejected by the server.

Both the pool owner and [collaborators](access.md) can manage config vars and
secrets.

## Subcommands

| Command | Description |
|---|---|
| `config` | List vars (`KEY` / `VALUE`, sorted by key; secrets masked) |
| `config set KEY=VALUE...` | Create or overwrite vars, then redeploy |
| `config unset KEY...` | Remove vars, then redeploy |

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |
| `--secret` | (set only) Store the value(s) as write-only secrets |
| `--json` | (list only) Emit a `{key: value}` object; secret values are `null` |

## Related

- [`access`](access.md) — pool collaborators
- [`ps`](ps.md) — stack status
- [`releases`](releases.md) — deploy runs
