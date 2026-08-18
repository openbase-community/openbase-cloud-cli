# run

Run a one-off command in an app's web container.

## Usage

```bash
openbase run -a my-app python manage.py check
openbase run -a my-app bash -lc "python manage.py migrate --check"
```

The command runs in a temporary task based on the app's current web task
definition. The CLI waits for it to finish, prints captured task logs, and exits
non-zero when the command exits non-zero.

This is not an interactive TTY, so a bare `bash` will exit immediately with
nothing to read. Pass an explicit command; use `bash -lc "…"` when you need a
login shell (PATH/venv) or shell features like pipes and `&&`.

CLI options (`-a`, `--memory`, `--shell-bin`) must come **before** the command;
everything after the first command word is passed to the container verbatim.
The CLI waits up to ~10 minutes for the command to finish.

## Options

| Option | Description | Default |
|---|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) | — |
| `--shell-bin PATH` | Shell used to launch the command | `/bin/sh` |
| `--memory MIB` | Hard memory limit for the temporary task | `256` |

## Related

- [`logs`](logs.md) — read app logs
- [`ps`](ps.md) — current stack status
