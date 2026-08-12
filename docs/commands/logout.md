# logout

Sign out and remove the shared Openbase Cloud credentials.

Deletes `~/.openbase/auth.json`. Since that file is shared with
`openbase-coder`, this signs you out of both CLIs. If you are not signed in, the
command reports that and does nothing.

## Usage

```bash
openbase logout
```

## Related

- [`login`](login.md) — sign back in
- [`whoami`](whoami.md) — check current sign-in state
