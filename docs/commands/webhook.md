# webhook

Manage the server pool's **release-notification webhook**.

When set, every deploy run on the pool (and its apps) that reaches a terminal
state — `SUCCEEDED` or `FAILED`, for any operation — POSTs a signed JSON payload
to your URL. Bridge it to Slack (or anything) to get release success/failure
updates per project.

The webhook is **per server pool**, so apps sharing a pool share one webhook.

## Usage

```bash
openbase webhook -a my-app                                 # show URL + secret
openbase webhook set -a my-app https://hooks.me/openbase   # set (auto-secret)
openbase webhook set -a my-app https://hooks.me/x --secret s3cr3t
openbase webhook unset -a my-app                           # remove
```

Only the pool **owner** can view or change the webhook.

## Payload & signature

The POST body is JSON with the run's `status`, `operation`, `summary`, `reason`,
`commit_sha`, `git_ref`, a `log_excerpt`, and the `stack`/`resource`. It is
signed with your secret over the raw body:

```
X-Openbase-Event: deployment_run.terminal
X-Openbase-Signature: sha256=<hex HMAC-SHA256 of the body with your secret>
```

Verify by recomputing the HMAC over the exact bytes received and comparing with
a constant-time check.

## Subcommands

| Command | Description |
|---|---|
| `webhook` | Show the current URL and signing secret |
| `webhook set URL [--secret S]` | Set the URL; secret is auto-generated if omitted |
| `webhook unset` | Remove the webhook |

## Options

| Option | Description |
|---|---|
| `-a`, `--app NAME` | Target app (or set `OPENBASE_APP`) |
| `--secret` | (set only) Signing secret; omit to auto-generate |

## Related

- [`releases`](releases.md) — deploy run history
- [`ps`](ps.md) — stack status
