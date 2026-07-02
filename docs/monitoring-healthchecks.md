# Monitoring With Healthchecks.io

OffsiteBuddy supports Healthchecks-style push URLs.

Configure the URLs in the job:

```yaml
heartbeat:
  start_url: "{{ vault_healthchecks_start_url | default('') }}"
  success_url: "{{ vault_healthchecks_success_url }}"
  failure_url: "{{ vault_healthchecks_failure_url }}"
```

OffsiteBuddy calls each URL as-is. Put provider-specific suffixes or query strings directly in the URL variable.
