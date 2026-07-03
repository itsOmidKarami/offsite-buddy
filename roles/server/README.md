# server

Configures OffsiteBuddy rest-server storage for friends.

The role creates per-friend rest-server Compose projects with Tailscale sidecars,
credentials, managed-stack markers, and optional quota-backed paths.

## Requirements

- Docker with the Compose plugin
- Tailscale auth keys for Tailscale-backed rest-server access
- passlib package support for htpasswd generation

## Role Variables

- `offsitebuddy_server_root`: Root directory for generated server files.
- `offsitebuddy_friends`: List of friend storage definitions.
- `offsitebuddy_rest_server_image`: rest-server container image.
- `offsitebuddy_tailscale_image`: Tailscale container image.
- `offsitebuddy_start_services`: Start generated services after writing files.
- `offsitebuddy_cleanup_stale`: Remove generated files for deleted friends.

## Example Playbook

```yaml
- hosts: servers
  roles:
    - role: itsomidkarami.offsitebuddy.server
```

## License

MIT
