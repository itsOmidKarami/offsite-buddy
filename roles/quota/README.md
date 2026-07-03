# quota

Manages hard quota-backed directories for OffsiteBuddy storage paths.

The role validates absolute quota paths and applies quota settings for each
entry in `offsitebuddy_quota_items`.

## Requirements

- A Linux filesystem and quota tooling compatible with the target host.

## Role Variables

- `offsitebuddy_quota_items`: List of quota path definitions.

## Example Playbook

```yaml
- hosts: servers
  roles:
    - role: itsomidkarami.offsitebuddy.quota
```

## License

MIT
