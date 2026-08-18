# health-check

View or set the HTTP path used to health-check an app's web service.

The platform probes this path during zero-downtime rollouts — from the host
proxy's active health checks and the container health check — and only shifts
traffic to a new release once it responds. The path must return `200` without
authentication. When unset, the platform default (`/api/csrf/`, present on all
Openbase server apps) is used.

The setting applies to the app's whole server pool and takes effect on the
pool's next infrastructure apply.

## Usage

```bash
openbase health-check -a my-app             # show the current path
openbase health-check /healthz -a my-app    # set a custom path
openbase health-check --unset -a my-app     # revert to the platform default
```

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |
| `--unset` | Clear the custom path and revert to the platform default |

## Related

- [`ps`](ps.md) — stack status
- [`releases`](releases.md) — deploy runs
