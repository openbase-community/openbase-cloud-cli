# workspaces

List your Openbase Cloud dev workspaces (devspaces) and their status.

This is a quick terminal readout. Devspaces — what they are, how to create and
connect to them, and the coding agents that run inside them — are documented in
the [Openbase Coder docs](https://docs.openbase.cloud).

## Usage

```bash
openbase workspaces
openbase workspaces --json
```

## Output

| Column | Description |
|---|---|
| ID | Workspace id |
| KIND | Workspace kind |
| STATUS | Current status |
| TYPE | Instance type |
| HOURS (mo) | Hours used this month |
| SPEND (mo) | Spend this month |

## Options

| Option | Description |
|---|---|
| `--json` | Output the raw workspaces JSON |

## Related

- [`coder`](coder.md) — drive devspaces via `openbase coder <args>`
- [Openbase Coder docs](https://docs.openbase.cloud) — full devspace workflow
