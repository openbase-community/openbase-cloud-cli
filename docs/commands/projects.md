# projects

List your Openbase Cloud projects.

A project groups deployable resources (apps) and is usually tied to a GitHub
repository.

## Usage

```bash
openbase projects
openbase projects --json
```

## Output

| Column | Description |
|---|---|
| IDENTIFIER | Project identifier |
| TITLE | Human-readable title |
| REPO | Connected GitHub repository name |
| CREATED | Creation timestamp |

## Options

| Option | Description |
|---|---|
| `--json` | Output the raw projects JSON |

## Related

- [`apps`](apps.md) — apps grouped by project
- [`workspaces`](workspaces.md) — cloud dev workspaces
