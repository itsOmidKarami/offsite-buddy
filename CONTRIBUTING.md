# Contributing

Keep v0.1 focused on restic, rest-server, Docker Compose, Tailscale, existing quota-managed paths, and systemd timers.

Run these before submitting changes:

```bash
uv run --locked pre-commit run --all-files
uv run molecule converge
uv run molecule verify
uv run ansible-playbook -i localhost, -c local tests/validation-negative.yml
uv run ansible-playbook -i localhost, -c local tests/e2e-local.yml
uv run ansible-galaxy collection build --force
```

## Release

Before the first release, create the `offsitebuddy` namespace on Ansible Galaxy
and add a repository secret named `ANSIBLE_GALAXY_API_TOKEN`.

To publish, update the version in `galaxy.yml` and `pyproject.toml`, merge to
`main`, then publish a GitHub Release tagged `vX.Y.Z`. The release workflow
builds the collection, attaches the tarball to the GitHub Release, and publishes
it to Ansible Galaxy.
