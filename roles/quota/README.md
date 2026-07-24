# quota

Manages hard quota-backed directories for OffsiteBuddy storage paths.

The role validates absolute existing quota paths for each entry in
`offsitebuddy_quota_items`; it does not create or configure the quota backend.

The role's write probe proves current writability only. It does not prove the
configured numeric quota or future capacity; configure and enforce those in
the storage provider.

## Requirements

- An externally provisioned quota-backed path on the target host.

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
