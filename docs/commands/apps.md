# apps

List the Openbase Cloud apps (deployment resources) you can access.

## Usage

```bash
openbase apps [--json]
```

## Output

A table sorted by project then app name:

| Column | Description |
|---|---|
| APP | App name |
| PROJECT | Owning project |
| TYPE | Resource type |
| STATUS | Current status |
| URL | Primary hostname, when the app has one |

If you have no apps, the command points you to the
[dashboard](https://app.openbase.cloud) to create one.

## Options

| Option | Description |
|---|---|
| `--json` | Emit a JSON array of `{name, project, type, status, stack_id, url}` |

## Related

- [`ps`](ps.md) — detailed status for one app
- [`open`](open.md) — open an app's URL
- [`config`](config.md), [`releases`](releases.md), [`logs`](logs.md)
