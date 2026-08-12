# ps

Show an app's current stack status. `status` is an alias for `ps`.

## Usage

```bash
openbase ps -a my-app
openbase status -a my-app     # identical
openbase ps -a my-app --json
```

## Output

A table with:

| Field | Description |
|---|---|
| App | App name |
| Project | Owning project |
| Type | Resource type |
| Status | Current stack status |
| Region | AWS region |
| URL | Primary hostname |
| Last run | Latest deploy run: operation, status, and summary |
| Updated | Last update timestamp |

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |
| `--json` | Output the raw stack-status JSON |

## Related

- [`apps`](apps.md) — list all apps
- [`releases`](releases.md) — full deploy-run history
- [`logs`](logs.md) — app logs
