# Monitoring With Uptime Kuma

OffsiteBuddy does not create Uptime Kuma monitors.

Create Uptime Kuma push monitors yourself, then paste their push URLs into the job heartbeat fields:

```yaml
heartbeat:
  start_url: "{{ vault_uptime_kuma_start_url | default('') }}"
  success_url: "{{ vault_uptime_kuma_success_url }}"
  failure_url: "{{ vault_uptime_kuma_failure_url }}"
```

Use separate push URLs when you want Uptime Kuma to distinguish started, succeeded, and failed events. OffsiteBuddy calls each configured URL as-is with `curl -fsS`.
