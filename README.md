# openbase

The command line for **[Openbase Cloud](https://openbase.cloud)** — a
Heroku-style tool and a fast alternative to the web dashboard. Sign in once,
then manage and inspect your apps, deploys, usage, projects, and workspaces
from the terminal. It speaks only HTTPS to the Openbase Cloud API.

## Install

```bash
pip install openbase-cli    # provides the `openbase` command
# or:  uv tool install openbase-cli
```

## Sign in

```bash
openbase login
```

Login is handled by the [Openbase Coder](https://openbase.cloud) CLI
(`openbase-coder`), which the two tools share — `openbase login` runs
`openbase-coder login` and stores credentials in `~/.openbase/auth.json`, so
signing in with either tool signs you in for both. Install `openbase-coder`
first if you don't have it.

```bash
openbase whoami     # signed-in email
openbase account    # account details (balance, subscription)
openbase logout     # sign out
```

## Apps & deploys

Address an app with `-a/--app NAME`, or set `OPENBASE_APP`.

```bash
openbase apps                       # list your apps
openbase logs -a my-app             # recent logs
openbase logs -a my-app --lines 200 # more log lines
openbase logs -a my-app --tail      # stream new lines (Ctrl-C to stop)
openbase run -a my-app python manage.py migrate   # one-off command in the web container
openbase ps -a my-app               # current status (alias: status)
openbase config -a my-app           # config vars (secret values hidden)
openbase config set -a my-app K=V   # set a plaintext var (redeploys)
openbase health-check -a my-app     # web health-check path (zero-downtime probes)
openbase releases -a my-app         # recent deploys
openbase open -a my-app             # open the app in your browser
```

## Account, projects & workspaces

```bash
openbase usage        # this month's spend and limits
openbase projects     # your Openbase Cloud projects
openbase workspaces   # your cloud dev workspaces (devspaces) and status
```

## Coder passthrough

Anything not covered here can be run against the Coder CLI directly:

```bash
openbase coder <args>       # runs `openbase-coder <args>`
```

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENBASE_APP` | Default app for `-a` | — |
| `OPENBASE_API_URL` | Override the Openbase Cloud base URL | `https://app.openbase.cloud` |
| `OPENBASE_HOST` | Alias for `OPENBASE_API_URL` | — |

Add `--json` to most commands for scripting.

## Documentation

Full docs live at **[docs-cloud.openbase.cloud](https://docs-cloud.openbase.cloud)**
(built from `docs/` with [zensical](https://zensical.org)). Build or serve them
locally:

```bash
uvx zensical serve     # live preview
uvx zensical build     # static site into ./site
```

## Development

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
```

## License

MIT — see [LICENSE](LICENSE).
