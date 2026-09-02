# releases

List recent deploy runs (releases) for an app.

Openbase Cloud deploys are push-to-deploy: pushing to an app's connected branch creates a run. Use `releases` to inspect history or `releases wait` to block until one commit finishes.

## Usage

```bash
openbase releases -a my-app
openbase releases -a my-app -n 30
openbase releases -a my-app --json
FULL_COMMIT_SHA="$(git rev-parse HEAD)"
openbase releases wait -a my-app --commit "$FULL_COMMIT_SHA" --operation deploy
openbase releases wait -a my-app --commit "$FULL_COMMIT_SHA" --operation deploy --verify-rollout
```

`releases wait` matches the full commit SHA and operation. It exits successfully only when that release succeeds; a failed, superseded, overtaken, or timed-out release exits nonzero. Use `--operation frontend_deploy` for an attached frontend-only release.

Server deploys start ECS asynchronously after CodeBuild. Add `--verify-rollout` to wait until every reported ECS service is running the expected image, has completed its rollout, has its desired task count, and has no pending tasks.

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

Attribution comes from the caller's agent/thread ID. Codex is detected automatically, and other callers can set `AGENT_SESSION_ID` explicitly (see [Configuration](../configuration.md)); mutations made without an available ID are recorded as `human`.

## Options

| Option | Description | Default |
|---|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) | — |
| `-n`, `--num N` | Maximum number of runs to show | `15` |
| `--json` | Output the raw runs JSON | — |

### `wait` options

| Option | Description | Default |
|---|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) | — |
| `--commit SHA` | Full commit SHA to wait for | required |
| `--operation deploy\|frontend_deploy` | Release operation triggered by the commit | required |
| `--verify-rollout` | Verify the expected image and live ECS rollout after release success | off |
| `--timeout SECONDS` | Maximum wait time | `1800` |
| `--poll-interval SECONDS` | Delay between API checks | `10` |

## Related

- [`ps`](ps.md) — current stack and live service status
- [`logs`](logs.md) — application runtime logs
