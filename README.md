# Openbase CLI

A Heroku-style command line for the **Openbase Cloud** PaaS. Log in once, then
read your apps' **logs**, **status**, **config**, and **releases** from the
terminal. It speaks only HTTPS to the Openbase Cloud API — no AWS credentials
required.

> This is the public, PaaS-facing CLI. The internal deployment engine (the
> Terraform app stack and the library the deploy runner uses, plus the retired
> manual `openbase-deploy` tool) lives in the separate, non-public `deploy`
> repo.

## Install

```bash
pip install openbase-cli    # provides the `openbase` command
# or, from a checkout:
uv run openbase --help
```

## Log in

```bash
openbase login
```

This opens your browser and stores credentials in `~/.openbase/auth.json`. That
file is **shared with the Openbase Coder CLI** — if you're already logged in
there, `openbase` is ready to go, and vice versa.

```bash
openbase whoami     # show the logged-in account
openbase logout     # clear credentials
```

## Everyday commands

An "app" is a deployed resource in your Openbase Cloud project. Address it with
`-a/--app NAME`, or set `OPENBASE_APP` once.

```bash
openbase apps                       # list apps you can access
openbase logs -a my-app             # recent logs
openbase logs -a my-app --tail      # stream new lines (Ctrl-C to stop)
openbase logs -a my-app -n 60       # last 60 minutes
openbase ps -a my-app               # current stack status (alias: status)
openbase config -a my-app           # config vars (secret values are hidden)
openbase releases -a my-app         # recent deploy runs
openbase open -a my-app             # open the app URL in a browser
```

Most commands accept `--json` for scripting.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENBASE_APP` | Default app for `-a` | — |
| `OPENBASE_API_URL` | Override the Openbase Cloud base URL | `https://app.openbase.cloud` |
| `OPENBASE_HOST` | Alias for `OPENBASE_API_URL` | — |

## Notes

- Logs currently surface recent **error-level** lines from an app's server
  stack. `--tail` re-queries and prints only new lines.
- Secret config values are never returned by the API; manage them in the
  Openbase Cloud dashboard.

## Development

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
```
