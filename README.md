# OffsiteBuddy

OffsiteBuddy is an Ansible Galaxy collection for friend-to-friend off-site NAS backups.

The v0.1 stack uses restic on the client side, rest-server on the storage side, Docker Compose, Tailscale sidecar containers, one append-only repository per friend, and hard quota-backed storage paths.

## What It Does

- Creates one isolated rest-server stack per friend.
- Runs restic client jobs in short-lived containers.
- Schedules backups with host systemd timers.
- Supports Uptime Kuma and Healthchecks-style push URLs.
- Requires hard quota assertion for existing quota-managed paths.

## What It Does Not Protect Against

- A storage host deleting repository files directly.
- Disk failure without server-side snapshots or replication.
- A leaked restic repository password.
- Backups that never get restore-tested.

## Quick Start

See `docs/getting-started.md`.
