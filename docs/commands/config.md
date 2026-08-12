# config

List an app's config vars.

Secret values are never returned by the Openbase Cloud API. In the table they
show as `(secret — set in dashboard)`; in `--json` they are `null`. Set and edit
config vars and secrets in the [dashboard](https://app.openbase.cloud).

## Usage

```bash
openbase config -a my-app
openbase config -a my-app --json
```

## Output

A table of `KEY` / `VALUE`, sorted by key. Secret values are masked.

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |
| `--json` | Emit a `{key: value}` object; secret values are `null` |

## Related

- [`ps`](ps.md) — stack status
- [`releases`](releases.md) — deploy runs
