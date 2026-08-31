# releases

List recent deploy runs (releases) for an app.

Openbase Cloud deploys are push-to-deploy: pushing to an app's connected branch
creates a run. Use `releases` to watch runs appear and see how each finished.

## Usage

```bash
openbase releases -a my-app
openbase releases -a my-app -n 30
openbase releases -a my-app --json
```

## Output

A table, newest first:

| Column | Description |
|---|---|
| WHEN | Run creation time |
| OPERATION | Deploy, rollback, sync, teardown, etc. |
| STATUS | Run status |
| REF | Git ref and short commit (e.g. `main@a1b2c3d`) |
| AGENT | Who triggered the run — an agent/thread UUID, or `human` |
| SUMMARY | Short run summary, when present |

Attribution comes from the caller's agent/thread ID. Codex is detected
automatically, and other callers can set `OPENBASE_AGENT_ID` explicitly (see
[Configuration](../configuration.md)); mutations made without an available ID
are recorded as `human`.

## Options

| Option | Description | Default |
|---|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) | — |
| `-n`, `--num N` | Maximum number of runs to show | `15` |
| `--json` | Output the raw runs JSON | — |

## Related

- [`ps`](ps.md) — current status, including the latest run
- [`logs`](logs.md) — app logs during and after a deploy
