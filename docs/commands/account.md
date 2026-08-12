# account

Show details for the signed-in Openbase Cloud account.

## Usage

```bash
openbase account [--json]
```

## Output

A table with:

| Field | Description |
|---|---|
| Email | Account email |
| Name | First and last name, when set |
| Balance | Current account balance |
| Subscription | `active` or `none` |
| Email verified | `yes` or `no` |

## Options

| Option | Description |
|---|---|
| `--json` | Output the raw account JSON from the API |

## Related

- [`whoami`](whoami.md) — just the email
- [`usage`](usage.md) — this month's spend and limits
