# Task 5 Report

## What I Implemented

- Added client role task files for:
  - Docker/job root directory rendering: `roles/client/tasks/docker.yml`
  - Per-job restic runtime rendering and optional init/initial backup execution: `roles/client/tasks/restic.yml`
  - Per-job systemd unit rendering and timer enablement: `roles/client/tasks/systemd.yml`
- Added a client handler:
  - `roles/client/handlers/main.yml` reloads systemd only when `offsitebuddy_start_services` is `true`.
- Added client templates for:
  - Compose runtime: `compose.yaml.j2`
  - Secret/runtime files: `env.j2`, `excludes.j2`
  - Helper scripts: `backup.sh.j2`, `init.sh.j2`, `check.sh.j2`, `restore-latest.sh.j2`, `snapshots.sh.j2`, `stats.sh.j2`
  - Systemd units: `offsitebuddy-backup.service.j2`, `offsitebuddy-backup.timer.j2`, `offsitebuddy-check.service.j2`, `offsitebuddy-check.timer.j2`
- Updated `roles/client/tasks/main.yml` to import validate, docker, restic, and systemd tasks in order.
- Updated `molecule/default/verify.yml` to assert the Task 5 client render outputs:
  - backup helper script content includes `curl -fsS`
  - `.env` and `password` are mode `0600`
  - backup/check service and timer unit files exist

## Verification Commands And Results

### RED / expected pre-implementation failure

1. `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp molecule verify`
   - Result: `FAIL`
   - Actual boundary hit: Molecule could not reach the Docker daemon during scenario startup, so the expected missing-client-files assertion failure was not reachable in this environment.

### Static checks after implementation

1. `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp yamllint molecule/default roles/client`
   - Result: `PASS`

2. `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp ansible-playbook --syntax-check molecule/default/converge.yml`
   - Result: `PASS`

3. `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp ansible-playbook --syntax-check molecule/default/verify.yml`
   - Result: `PASS`

4. `git diff --check`
   - Result: `PASS`

### Full Molecule commands after implementation

1. `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp molecule converge`
   - Result: `FAIL`
   - Boundary: Docker daemon unavailable during Molecule create.

2. `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp molecule verify`
   - Result: `FAIL`
   - Boundary: Docker daemon unavailable before verification playbook execution.

3. `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp molecule idempotence`
   - Result: `FAIL`
   - Boundary: local `ansible-galaxy collection install --force /Users/omidkarami/Projects/offsite-buddy` crashes with `FileNotFoundError` while reinstalling `offsitebuddy.backup`, before the scenario reaches idempotence execution.

### Additional non-blocking check

1. `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp ansible-lint roles/client molecule/default/converge.yml molecule/default/verify.yml`
   - Result: `FAIL`
   - Reason: pre-existing role-prefix naming violations in both `roles/client/defaults/main.yml` and `roles/server/*`; no Task 5 functional failure surfaced there.

## Files Changed

- `molecule/default/verify.yml`
- `roles/client/handlers/main.yml`
- `roles/client/tasks/docker.yml`
- `roles/client/tasks/main.yml`
- `roles/client/tasks/restic.yml`
- `roles/client/tasks/systemd.yml`
- `roles/client/templates/backup.sh.j2`
- `roles/client/templates/check.sh.j2`
- `roles/client/templates/compose.yaml.j2`
- `roles/client/templates/env.j2`
- `roles/client/templates/excludes.j2`
- `roles/client/templates/init.sh.j2`
- `roles/client/templates/offsitebuddy-backup.service.j2`
- `roles/client/templates/offsitebuddy-backup.timer.j2`
- `roles/client/templates/offsitebuddy-check.service.j2`
- `roles/client/templates/offsitebuddy-check.timer.j2`
- `roles/client/templates/restore-latest.sh.j2`
- `roles/client/templates/snapshots.sh.j2`
- `roles/client/templates/stats.sh.j2`

## Self-Review Findings

- Stayed within Task 5 ownership: client role files plus `molecule/default/verify.yml`; no server/quota role edits.
- Kept runtime secrets at `0600` for `.env` and `password`.
- Kept helper scripts under `/etc/offsitebuddy/jobs/<job-name>/`.
- Guarded init, initial backup, systemd reload, and timer start paths behind `offsitebuddy_start_services | bool`, so Molecule render-only mode does not run init/backup/timers/Docker Compose.
- Kept `run_initial_backup` and `init_if_missing` defaults behavior at the task level with `default(true)`.
- Honored weekly-check scheduling via `job.check.schedule` with a `weekly` fallback in the timer template.
- Did not add docs/examples or extra abstractions beyond the requested Task 5 files.

## Concerns

- Full Molecule runtime validation is blocked here by missing Docker daemon access.
- `molecule idempotence` also hits a local `ansible-galaxy` reinstall bug before scenario execution.
- Heartbeat `curl` failures currently propagate through the helper script because the task brief specified direct `curl -fsS` calls; I left that behavior unchanged from the requested shape.

## Commit

- `4113bac feat: render client restic jobs and timers`

## Fix Round 2

### What I Changed

- Relaxed client job validation in `roles/client/tasks/validate.yml` so `job.check` stays required, but `check.enabled` and `check.read_data` may be omitted and default through the task/template flow.
- Added a minimal client systemd converge cleanup in `roles/client/tasks/systemd.yml`:
  - stat the check timer unit before cleanup
  - stop/disable an existing stale check timer when services are managed and `check.enabled` is false
  - remove stale check service and timer unit files when `check.enabled` is false
- Expanded `molecule/default/verify.yml` to assert the rest of the per-job client outputs exist:
  - `compose.yaml`
  - `excludes`
  - `init.sh`
  - `check.sh`
  - `restore-latest.sh`
  - `snapshots.sh`
  - `stats.sh`

### Verification

- `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH yamllint roles/client molecule/default/verify.yml`
  - PASS
- `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp ansible-playbook --syntax-check molecule/default/converge.yml`
  - PASS
- `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp ansible-playbook --syntax-check molecule/default/verify.yml`
  - PASS
- `git diff --check`
  - PASS
- `env PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/venv/bin:$PATH HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home ANSIBLE_HOME=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible ANSIBLE_GALAXY_TOKEN_PATH=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/home/.ansible/galaxy_token ANSIBLE_LOCAL_TEMP=/Users/omidkarami/Projects/offsite-buddy/.superpowers/sdd/ansible-tmp ANSIBLE_REMOTE_TEMP=/tmp/.ansible/tmp molecule verify`
  - FAIL: unable to contact the Docker daemon during Molecule sanity checks
