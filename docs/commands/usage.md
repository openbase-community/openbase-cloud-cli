# usage

Show this month's spend and usage limits for your account.

## Usage

```bash
openbase usage
openbase usage --json
```

## Output

A header line with your monthly included limit and the billing-month start date,
then a table broken down by category:

| Column | Description |
|---|---|
| CATEGORY | `Sandbox`, `Deployment`, or `LLM` |
| SPENT | Amount spent this month |
| REMAINING | Amount left within the included limit |
| USED | Percent of the included limit used |

If pay-as-you-go is enabled, a final line shows the remaining PAYG allowance and
cap. If PAYG is supported but not enabled, that is noted instead.

## Options

| Option | Description |
|---|---|
| `--json` | Output the raw usage JSON |

## Related

- [`account`](account.md) — balance and subscription
