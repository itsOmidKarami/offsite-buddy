# client

Configures OffsiteBuddy backup jobs on client hosts.

The role renders restic helper scripts, Docker Compose files, and optional
systemd units for each entry in `offsitebuddy_client_jobs`.

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

## Example Playbook

```yaml
- hosts: clients
  roles:
    - role: itsomidkarami.offsitebuddy.client
```

## License

MIT
