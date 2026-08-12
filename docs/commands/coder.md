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

## Requirements

The `openbase-coder` CLI must be installed; this command invokes its executable.
See the [Openbase Coder docs](https://docs.openbase.cloud).

## Related

- [`login`](login.md) — also delegates to `openbase-coder`
- [`workspaces`](workspaces.md) — read-only devspace status from `openbase`
