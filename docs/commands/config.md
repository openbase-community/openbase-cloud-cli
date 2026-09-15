# config

View, set, and unset an app's config vars, Heroku-style.

Vars you set with `config set` are plaintext and read back with `config get`
or the full listing. Pass `--secret` to store values write-only instead:
secret values are never returned by the API (they show as
`(secret — value hidden)`, `null` in `--json`). Secrets can also be managed
in the [dashboard](https://app.openbase.cloud).

**Prefer `config get KEY` when you know which keys you need.** It retrieves
only those values, so nothing else can end up in your terminal, logs, shell
history, or anything you paste elsewhere. The full listing dumps every var —
including all plaintext values — in one output, so it asks for confirmation
first; pass `--confirm` to skip the prompt. Non-interactive runs (scripts,
agents) without `--confirm` currently proceed with a deprecation warning on
stderr; in a future release `--confirm` will be required there.

## Usage

```bash
openbase config get -a my-app DEBUG            # one value, bare (pipe-friendly)
openbase config get -a my-app DEBUG API_URL    # several, as KEY=VALUE lines
openbase config get -a my-app --json DEBUG     # {key: value}, secrets null
openbase config -a my-app                      # full listing (asks: are you sure?)
openbase config -a my-app --confirm            # full listing, no prompt
openbase config -a my-app --confirm --json     # full {key: value}, secrets null
openbase config set -a my-app DEBUG=false      # set (overwrites) one or more
openbase config set -a my-app A=1 B=2          # multiple at once
openbase config set --secret -a my-app API_KEY=…   # store write-only secret(s)
openbase config unset -a my-app DEBUG A        # remove one or more
```

`config get` with a single key prints the bare value; with several keys it
prints `KEY=VALUE` lines. Keys that are not set are reported on stderr and
the command exits non-zero, so `openbase config get -a my-app SOME_KEY` is
also the way to check whether a var is set at all.

`set` and `unset` change the deployed environment, so they trigger a new
release. `set` overwrites a key that already exists. Platform-reserved keys
(e.g. `DEPLOYMENT_*`, `DATABASE_URL`) are rejected by the server.

Both the pool owner and [collaborators](access.md) can manage config vars and
secrets.

## Subcommands

| Command | Description |
|---|---|
| `config get KEY...` | Print only the requested values (preferred) |
| `config` | List ALL vars (`KEY` / `VALUE`, sorted; secrets masked; asks for confirmation) |
| `config set KEY=VALUE...` | Create or overwrite vars, then redeploy |
| `config unset KEY...` | Remove vars, then redeploy |

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |
| `--secret` | (set only) Store the value(s) as write-only secrets |
| `--confirm` | (list only) Skip the full-listing confirmation prompt |
| `--json` | (list/get) Emit a `{key: value}` object; secret values are `null` |

## Why the full listing asks for confirmation

A single full-listing output holds every plaintext value the app has. Copied
into a chat message, a CI log, or a bug report, one accidental paste exposes
them all at once — whereas `config get` bounds any such accident to the keys
you actually asked for. The prompt exists to push routine usage toward
`config get`; `--confirm` keeps deliberate full listings scriptable. For
backwards compatibility, non-interactive listings without `--confirm` still
run today (with a deprecation warning) — update scripts now, before the
warning becomes an error.

## Related

- [`access`](access.md) — pool collaborators
- [`ps`](ps.md) — stack status
- [`releases`](releases.md) — deploy runs
