# Contributing

Keep v0.1 focused on restic, rest-server, Docker Compose, Tailscale, existing quota-managed paths, and systemd timers.

Run these before submitting changes:

```bash
uv run --locked pre-commit run --all-files
uv run molecule converge
uv run molecule verify
uv run ansible-playbook -i localhost, -c local tests/e2e-local.yml
uv run ansible-galaxy collection build --force
```
