# OffsiteBuddy

OffsiteBuddy is an Ansible Galaxy collection for friend-to-friend off-site NAS backups.

The v0.1 stack uses restic on the client side, rest-server on the storage side, Docker Compose, Tailscale sidecar containers, one append-only repository per friend, and hard quota-backed storage paths.

## Quick Start

See `docs/getting-started.md`.

## Monitoring

Uptime Kuma and Healthchecks.io are supported through generic push URLs. OffsiteBuddy does not create monitors in external services.

## Restore Test

See `docs/restore-test.md`. A backup that has not been restored is only a backup attempt.

## Security

See `SECURITY.md` and `docs/append-only-maintenance.md`.
