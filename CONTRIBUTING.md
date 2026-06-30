# Contributing

Keep v0.1 focused on restic, rest-server, Docker Compose, Tailscale, existing quota-managed paths, and systemd timers.

Run these before submitting changes:

```bash
ansible-lint
yamllint .
molecule test
ansible-galaxy collection build --force
```
