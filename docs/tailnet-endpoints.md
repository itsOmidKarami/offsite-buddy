# Tailnet endpoints

For cross-tailnet Docker backup jobs, configure the server sidecar's Tailnet IP
as the `repository` endpoint. This avoids relying on MagicDNS resolution from
the generated one-shot restic container, whose in-container DNS can use
Docker's `127.0.0.11` embedded resolver.

| Endpoint | Support |
| --- | --- |
| Tailnet IP | Supported reliable default for cross-tailnet Docker jobs. |
| Full MagicDNS FQDN | Supported after successful resolution in the generated restic path. |
| Short hostname | Unsupported across Tailnets. |
| Public address | Unsupported by default. |

Public internet exposure is unsupported by default.

## Discover and validate a Tailnet IP

On the server, change to the friend server project directory and run:

```sh
cd /srv/offsitebuddy/friends/alice
docker compose exec tailscale tailscale ip -4
```

Record only the returned IP in the client inventory. Do not echo, log, or paste
a complete credential-bearing repository URL into a terminal, ticket, or chat.
Keep repository credentials Vault-derived and URL-encoded in the repository
expression.

Converge the client, then validate the generated restic path without printing
the repository URL:

```sh
sudo /etc/offsitebuddy/jobs/photos_to_bob/snapshots.sh
```

A full MagicDNS FQDN such as
`<hostname>.<server-tailnet>.ts.net` is an alternative only after it resolves
successfully in this generated restic execution path, as demonstrated by a
successful `snapshots.sh` run. Checking resolution only from the Tailscale
sidecar is insufficient.

## Endpoint lifecycle

Persistent Tailscale state normally preserves the Tailnet IP. After any
re-enrollment or loss of persistent Tailscale state, even if the IP appears
unchanged, first stop and disable the affected job's backup timer and, if
present, check timer. Rediscover the IP and converge the client with
`offsitebuddy_start_services: false` so the timers remain paused. Without
printing the repository URL, run that job's `snapshots.sh` and `check.sh`. Only
after both succeed, run normal client convergence to enable and resume timers.
