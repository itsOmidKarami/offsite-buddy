# Contributing

Keep v0.1 focused on restic, rest-server, Docker Compose, Tailscale, existing quota-managed paths, and systemd timers.

Run these before submitting changes:

```bash
uv run --locked pre-commit run --all-files
uv run molecule converge
uv run molecule verify
uv run ansible-playbook -i localhost, -c local tests/validation-negative.yml
uv run ansible-playbook -i localhost, -c local tests/client-sidecar-render.yml
uv run ansible-playbook -i localhost, -c local tests/e2e-local.yml
uv run ansible-galaxy collection build --force
```

## Release

This repo uses release-please. Because the repository uses squash merges, the PR
title becomes the commit on `main`. Use conventional commit prefixes in PR titles
so release-please can choose the next version:

- For user-facing or package changes, use `fix:` or `feat:` in the PR title.
- For non-release changes, use `docs:`, `test:`, `ci:`, `chore:`, or
  `refactor:`.
- While version is `0.x`, `fix:`, `feat:`, and `perf:` create patch releases,
  and breaking changes create minor releases.
- From `1.0.0` onward, `fix:` creates patch releases, `feat:` creates minor
  releases, and breaking changes create major releases.

CI rejects PR titles that do not start with one of those conventional prefixes.
If release-worthy changes already merged without a release prefix, open a tiny
follow-up PR titled `fix: release <summary>` or `feat: release <summary>` and
merge it through the normal flow. Keep that follow-up PR small; it exists only
to put the missed release summary into release-please history.

To publish, merge the release-please PR. The release workflow creates the tag and
draft GitHub Release, builds the collection, attaches the tarball, publishes the
GitHub Release, and publishes it to Ansible Galaxy.

If publishing fails after the GitHub Release is published with its tarball,
rerun the `Release` workflow manually with the existing tag. If a published
immutable release is missing the tarball, ship a new patch release; GitHub does
not allow attaching assets or recreating a release for that tag after deletion.
