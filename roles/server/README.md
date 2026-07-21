# server

Configures OffsiteBuddy rest-server storage for friends.

The role creates per-friend rest-server Compose projects with Tailscale sidecars,
credentials, managed-stack markers, and optional quota-backed paths.

## Requirements

- Docker with the Compose plugin
- Tailscale auth keys for Tailscale-backed rest-server access
- Python passlib and requests packages

## Role Variables

- `offsitebuddy_server_root`: Root directory for generated server files.
- `offsitebuddy_friends`: List of friend storage definitions.
- `offsitebuddy_rest_server_image`: rest-server container image.
- `offsitebuddy_tailscale_image`: Tailscale container image.
- `offsitebuddy_start_services`: Start generated services after writing files.
- `offsitebuddy_cleanup_stale`: Remove generated files for deleted friends.

## Stale Cleanup

Stale cleanup is opt-in (`offsitebuddy_cleanup_stale: true`) and requires runtime
management with `offsitebuddy_start_services: true`. It stops a stale friend's
Compose project before removing the managed directory, including its Tailscale
state. External quota data is never removed, and directories without a direct
`.offsitebuddy-managed` marker are ignored.

Version 1 names each Compose project `offsitebuddy-friend-<name>`. If a legacy
generic `<name>` project still has containers or networks, the role fails rather
than removing it, before friend-specific files change. Inspect and stop that
project explicitly, then rerun the role:

```shell
docker compose --project-name <friend-name> --file <managed-compose-path>/compose.yaml down
```

## Example Playbook

```yaml
- hosts: servers
  roles:
    - role: itsomidkarami.offsitebuddy.server
```

## License

MIT
