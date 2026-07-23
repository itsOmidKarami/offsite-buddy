# client

Configures OffsiteBuddy backup jobs on client hosts.

The role renders restic helper scripts, Docker Compose files, and optional
systemd units for each entry in `offsitebuddy_client_jobs`.

## Cross-Tailnet Endpoint

Use the shared server sidecar's Tailnet IP in `repository` for cross-tailnet
Docker jobs. A full MagicDNS FQDN is supported only after it resolves in the
generated restic execution path; short hostnames and public addresses are not
supported defaults. See [Tailnet endpoint guidance](../../docs/tailnet-endpoints.md).

## Requirements

- Docker with the Compose plugin
- systemd when `offsitebuddy_manage_systemd` is true
- Tailscale auth keys for jobs with Tailscale sidecars

## Role Variables

- `offsitebuddy_client_root`: Directory for generated job files.
- `offsitebuddy_client_jobs`: List of backup job definitions.
- `offsitebuddy_restic_image`: restic container image.
- `offsitebuddy_tailscale_image`: Tailscale container image.
- `offsitebuddy_start_services`: Start generated services after writing files.
- `offsitebuddy_cleanup_stale`: Remove generated files for deleted jobs.

## Restores

Each job provides `snapshots.sh`, `restore.sh`, and the compatible
`restore-latest.sh <target>` wrapper. `restore.sh` requires
`--snapshot <id|latest>` and accepts repeated `--include` paths. Restore targets
must be existing empty directories. See [restore testing](../../docs/restore-test.md)
for concrete snapshot and selective-restore commands.

## Timers and Checks

A missed `Persistent=true` timer can run after boot. Each backup start is delayed
by up to `offsitebuddy_backup_randomized_delay_sec` through
`RandomizedDelaySec`. Disabling an optional check leaves its backup timer
enabled. Set `check.read_data: true` only when needed: it reads repository data
and may be I/O-intensive.

## Stale Cleanup

Stale cleanup is opt-in (`offsitebuddy_cleanup_stale: true`) and requires runtime
management with `offsitebuddy_start_services: true` and
`offsitebuddy_manage_systemd: true`. It stops a stale job's timers and services
and verifies its `offsitebuddy-client-<job-name>` Compose project is down before
removing the managed directory, including its Tailscale state. Backup sources
and repository data are never removed, and directories without a direct
`.offsitebuddy-managed` marker are ignored.

Missing optional check units are safe to skip. Any real systemd query or stop
error remains fatal and preserves the stale managed directory for inspection.

Older releases used the generic job name as the Compose project name. The role
detects those projects before job-specific files change and refuses to migrate
them automatically. Stop and disable any existing backup/check timers, stop
active backup/check services, and verify those services are inactive. Then
inspect the reported project and stop it explicitly with
`docker compose --project-name <job-name> --file <managed-compose-path>/compose.yaml down`
before rerunning the role.

## Example Playbook

```yaml
- hosts: clients
  roles:
    - role: itsomidkarami.offsitebuddy.client
```

## License

MIT
