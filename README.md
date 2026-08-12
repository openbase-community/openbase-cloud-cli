# openbase-deploy

The command line for the **[Openbase Cloud](https://openbase.cloud)** PaaS.
Log in once, then read your apps' **logs**, **status**, **config**, and
**releases** right from your terminal. Heroku-style, over HTTPS — no cloud
credentials to configure.

## Install

```bash
pip install openbase-cli
```

This installs the `openbase-deploy` command. (Prefer [uv](https://docs.astral.sh/uv/)?
`uv tool install openbase-cli`.)

## Log in

```bash
openbase-deploy login
```

This opens your browser to sign in and saves your credentials locally. It
shares a session with the [Openbase Coder](https://openbase.cloud) CLI — if
you're already signed in there, you're ready to go here too, and vice versa.

```bash
openbase-deploy whoami     # show the signed-in account
openbase-deploy logout     # sign out
```

## Everyday commands

Address an app with `-a/--app NAME`, or set `OPENBASE_APP` once.

```bash
openbase-deploy apps                    # list your apps
openbase-deploy logs -a my-app          # recent logs
openbase-deploy logs -a my-app --tail   # stream new lines (Ctrl-C to stop)
openbase-deploy logs -a my-app -n 60    # last 60 minutes
openbase-deploy ps -a my-app            # current status (alias: status)
openbase-deploy config -a my-app        # config vars (secret values hidden)
openbase-deploy releases -a my-app      # recent deploys
openbase-deploy open -a my-app          # open the app in your browser
```

Add `--json` to most commands for scripting.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENBASE_APP` | Default app for `-a` | — |
| `OPENBASE_API_URL` | Override the Openbase Cloud base URL | `https://app.openbase.cloud` |
| `OPENBASE_HOST` | Alias for `OPENBASE_API_URL` | — |

## Notes

- `logs` shows recent lines from your app's server logs; `--tail` keeps polling
  and prints new lines as they arrive.
- Secret config values are never sent back over the API — manage them from the
  Openbase Cloud dashboard.

## Development

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
```

## License

MIT — see [LICENSE](LICENSE).
