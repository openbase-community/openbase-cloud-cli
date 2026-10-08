# coder

Run the Openbase Coder CLI through `openbase`.

`openbase coder <args>` is a thin passthrough to the separate `openbase-coder`
executable — the voice-first coding runtime that also owns sign-in, devspaces,
and agents. Anything not covered by the `openbase` CLI can be run this way.

## Usage

```bash
openbase coder <args>...

# examples
openbase coder --help
openbase coder devspaces status
```

## Agent sessions: `openbase codex` and `openbase claude`

`openbase codex [args]` and `openbase claude [args]` forward to
`openbase-coder codex` / `openbase-coder claude`, which start Codex or Claude
Code with Openbase's session profile so the session shows up in the Openbase
app and on your phone, and can be steered from there. On a laptop paired with
an always-on hub through Openbase Sync, a session started in a synced folder
runs on the hub and your terminal attaches to it; `--local` or `--remote`
(first) force either. Other arguments go to the agent unchanged, and plain
`codex` / `claude` are never changed. Details:
[Codex and Claude Code from your terminal](https://docs.openbase.cloud/agent-launchers/).

```bash
openbase codex "fix the failing test"
openbase claude -c
```

## Requirements

The `openbase-coder` CLI must be installed; this command invokes its executable.
See the [Openbase Coder docs](https://docs.openbase.cloud).

## Related

- [`login`](login.md) — also delegates to `openbase-coder`
- [`workspaces`](workspaces.md) — read-only devspace status from `openbase`
