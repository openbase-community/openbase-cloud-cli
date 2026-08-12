# logs

Display recent logs for an app, Heroku-style, with optional tailing.

Openbase Cloud currently surfaces recent error-level lines from the app's server
stack. Without `--tail`, this prints one snapshot and exits.

## Usage

```bash
openbase logs -a my-app                 # last 15 minutes, one snapshot
openbase logs -a my-app -n 60           # last 60 minutes
openbase logs -a my-app --tail          # stream new lines (Ctrl-C to stop)
```

## Options

| Option | Description | Default |
|---|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) | — |
| `-n`, `--num MINUTES` | Show lines from the last `MINUTES` minutes | `15` |
| `-t`, `--tail` | Continuously stream new lines until Ctrl-C | off |

## How Tailing Works

The logs endpoint is a windowed pull, not a live stream. With `--tail`, the CLI
re-queries every few seconds and prints only lines it has not shown yet,
de-duplicating on a rolling window so repeated windows do not reprint. Press
Ctrl-C to stop.

## Related

- [`ps`](ps.md) — current stack status
- [`releases`](releases.md) — recent deploy runs
