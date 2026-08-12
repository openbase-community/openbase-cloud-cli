# openbase-cloud-cli — agent notes

This repo is the **public Openbase Cloud CLI**: the `openbase` command
(`openbase_cli` package), a Heroku-style client for the Openbase Cloud PaaS and
an alternative to the web dashboard. It speaks only HTTPS to the Openbase Cloud
API — no AWS credentials, no local Docker.

- Package: `openbase_cli/` — root group in `openbase_cli/cli.py`, one module per
  command group under `openbase_cli/commands/`.
- Sign-in and devspace/agent features are **delegated** to the separate
  `openbase-coder` CLI: `openbase login` shells out to `openbase-coder login`,
  and both tools share `~/.openbase/auth.json`.
- Published to PyPI as `openbase-cli` (see `.github/workflows/publish.yml`).

## Sister project

The `openbase-coder` CLI and the broader voice-first coding product (desktop
app, iOS app, web console, devspaces, agents) live in the sister workspace
**`../../../openbase-coder-workspace`** (its own repos; the coder CLI is at
`openbase-coder-workspace/cli`). That workspace is the source of truth for
sign-in, devspaces, and agents; this CLI only reads/drives the Openbase Cloud
PaaS side and passes other work through via `openbase coder <args>`.

## Documentation

Public docs are built from `docs/` with [zensical](https://zensical.org) and
deployed to **https://docs-cloud.openbase.cloud** via GitHub Pages
(`.github/workflows/docs-pages.yml`, custom-domain CNAME). This mirrors the
coder CLI's docs setup (`openbase-coder-workspace/cli`, which publishes to
`docs.openbase.cloud`); the two doc sites are separate and cross-link each
other. Keep the docs focused on the PaaS (apps, deploys, logs, config,
releases, usage, projects); devspaces are documented in the coder docs.

Build/preview locally:

```bash
uvx zensical serve
uvx zensical build
```

When you add or rename a command in `openbase_cli/commands/`, update both the
`README.md` summary and the matching `docs/commands/*.md` page (and `nav` in
`zensical.toml`).

## Development

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
```
