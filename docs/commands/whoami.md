# whoami

Show the currently signed-in Openbase Cloud account.

Prints your account email. The command forces a token refresh first, so it also
validates that your session is still good; if you are not signed in it tells you
to run `openbase login`.

## Usage

```bash
openbase whoami
```

## Related

- [`account`](account.md) — fuller account details (balance, subscription)
- [`login`](login.md) — sign in
