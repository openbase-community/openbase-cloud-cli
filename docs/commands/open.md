# open

Open an app's primary URL in your browser.

## Usage

```bash
openbase open -a my-app
# or, with OPENBASE_APP set:
openbase open
```

Resolves the app, then opens its primary hostname with your default browser. If
the app has no hostname yet, the command says so and exits non-zero.

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |

## Related

- [`apps`](apps.md) — find app names and URLs
- [`ps`](ps.md) — status, including the URL
