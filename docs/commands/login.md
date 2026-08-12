# login

Sign in to Openbase Cloud.

`openbase login` delegates to `openbase-coder login`, which owns the shared
browser sign-in and writes credentials to `~/.openbase/auth.json`. Because both
CLIs read that file, signing in here signs you in for `openbase-coder` too.

## Usage

```bash
openbase login [ARGS...]
```

Any extra arguments are passed straight through to `openbase-coder login`.

## Requirements

The `openbase-coder` CLI must be installed — `openbase login` invokes its
executable. See the [Openbase Coder docs](https://docs.openbase.cloud) to
install it.

## Related

- [`logout`](logout.md) — remove the shared credentials
- [`whoami`](whoami.md) — confirm who you are signed in as
- [`coder`](coder.md) — run other `openbase-coder` commands
