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

This repo uses release-please. Use conventional commit prefixes so it can choose
the next version:

- `fix:` for patch releases
- `feat:` for minor releases
- `feat!:` or `BREAKING CHANGE:` for major releases

One-time setup:

1. Confirm the lower-case `itsomidkarami` namespace is available in Ansible
   Galaxy.
2. Add `ANSIBLE_GALAXY_API_TOKEN` as a repository secret.
3. Add `RELEASE_PLEASE_TOKEN` as a repository secret. Use a fine-grained GitHub
   token with contents, pull request, and issue write access for this repository.

To publish, merge the release-please PR. The release workflow creates the tag and
GitHub Release, builds the collection, attaches the tarball to the release, and
publishes it to Ansible Galaxy.
