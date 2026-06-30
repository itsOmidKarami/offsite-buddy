# Task 1 Report: Collection Skeleton And Static Tooling

## Implemented
- Added `.gitignore` with required ignore entries.
- Added Ansible collection/tooling config files: `ansible.cfg`, `galaxy.yml`, `requirements-dev.yml`.
- Added repository docs and policy files: `README.md`, `SECURITY.md`, `CONTRIBUTING.md`.
- Added playbook examples: `playbooks/server.yml`, `playbooks/client.yml`.
- Added sample inventory: `examples/inventory.ini`.
- Added CI workflow: `.github/workflows/ci.yml`.

## Verification
- Ran `ansible-galaxy collection build --force`
  - Result: `command not found` (`zsh:1: command not found: ansible-galaxy`)
- Ran `ansible-lint`
  - Result: `command not found` (`zsh:1: command not found: ansible-lint`)
  - Expected earlier failure for missing roles could not be reached because `ansible-lint` is not installed in this environment.

## Files Changed
- `.gitignore`
- `ansible.cfg`
- `galaxy.yml`
- `README.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `requirements-dev.yml`
- `playbooks/server.yml`
- `playbooks/client.yml`
- `examples/inventory.ini`
- `.github/workflows/ci.yml`

## Self-Review
- Scope stayed within Task 1 files only.
- No roles, Molecule scenarios, or non-Task-1 implementation files were added.
- File contents match the brief verbatim.
- `build_ignore` in `galaxy.yml` excludes `.github` (including CI) and `docs/superpowers`, matching requirements.

## Concerns
- Verification tooling is not installed in this workspace, so command-based validation could not execute.
