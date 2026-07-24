# Retention Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make append-only maintenance refuse ambiguous Docker ownership, remain fail-closed through restarts and signals, and require every repository writer to be paused.

**Architecture:** Extend the existing server identity preflight with an exact Docker label inspection for every configured friend's maintenance project. Repeat that inspection in the generated helper immediately before changing projects, then use the existing helper harness and Molecule identity-shadow fixture for regression coverage.

**Tech Stack:** Ansible, Docker Compose, Bash, Molecule, Python static checks

## Global Constraints

- Never remove an existing maintenance Compose project automatically.
- Run the Ansible Docker-state guard before maintenance files can be changed.
- Run the helper Docker-state guard before the ordinary append-only project is stopped.
- Keep destructive retention manual and operator-controlled.
- Add no dependency, framework, lock service, or automatic prune behavior.

---

### Task 1: Refuse existing maintenance Compose projects during convergence

**Files:**
- Modify: `tests/test_review_fixes.py`
- Modify: `molecule/cleanup/side_effect.yml`
- Modify: `roles/server/tasks/project_identity_preflight.yml`

**Interfaces:**
- Consumes: `offsitebuddy_friends[*].name` and Docker resources labeled `com.docker.compose.project=offsitebuddy-maintenance-friend-<name>`
- Produces: `offsitebuddy_server_maintenance_compose_summaries`, containing only friend name, project name, container count, and network count

- [ ] **Step 1: Add failing static assertions**

Add this after `server_tasks` is loaded in `tests/test_review_fixes.py`:

```python
    identity_preflight = read("roles/server/tasks/project_identity_preflight.yml")
    for snippet in (
        "Check current maintenance Compose projects",
        "offsitebuddy_server_maintenance_compose_inspections",
        "offsitebuddy_server_maintenance_compose_summaries",
        "Refuse active or foreign maintenance Compose projects",
        "com.docker.compose.project=offsitebuddy-maintenance-friend-",
    ):
        assert snippet in identity_preflight
    maintenance_query = identity_preflight.split(
        "- name: Check current maintenance Compose projects", 1
    )[1].split("- name: Initialize current maintenance Compose summaries", 1)[0]
    assert "offsitebuddy_friends | map(attribute='name')" in maintenance_query
    identity_import_index = server_tasks.index(
        "- name: Check server Compose project identity ownership"
    )
    maintenance_removal_index = server_tasks.index(
        "- name: Remove maintenance files for read-write friends"
    )
    assert identity_import_index < maintenance_removal_index
```

- [ ] **Step 2: Convert the maintenance identity-shadow fixture to a Docker-only collision**

In `molecule/cleanup/side_effect.yml`, remove `.offsitebuddy-managed` from the
fixture file loop, set the invoked friend's mode to `read_write`, expect the
new refusal task, and remove the deleted marker from the later assertions:

```yaml
        - name: Create server maintenance identity shadow sentinel
          ansible.builtin.copy:
            dest: "{{ server_maintenance_shadow_path }}/sentinel"
            content: preserved
            mode: "0600"
```

```yaml
                    rest_server:
                      mode: read_write
                      username: cleanup-server-shadow
                      password: cleanup-server-shadow-fixture
```

```yaml
                  - >-
                    ansible_failed_task.name is search(
                      'Refuse active or foreign maintenance Compose projects'
                    )
```

The post-refusal stat loop and assertion become:

```yaml
          loop:
            - >-
              {{
                server_maintenance_shadow_root ~ '/friends/' ~
                server_shadow_current
              }}
            - "{{ server_maintenance_shadow_path }}/sentinel"
            - "{{ server_maintenance_shadow_path }}/compose.yaml"
          register: server_maintenance_shadow_files

        - name: Verify server maintenance identity shadow refusal
          ansible.builtin.assert:
            that:
              - not server_maintenance_shadow_files.results[0].stat.exists
              - server_maintenance_shadow_files.results[1].stat.exists
              - >-
                server_maintenance_shadow_files.results[2].stat.checksum ==
                server_maintenance_shadow_compose_before.stat.checksum
```

- [ ] **Step 3: Run the focused checks and verify RED**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --locked python tests/test_review_fixes.py
```

Expected: FAIL because `project_identity_preflight.yml` does not inspect exact
maintenance Docker identities.

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --locked molecule test -s cleanup --no-report
```

Expected: FAIL with `Server maintenance identity shadow unexpectedly passed preflight.`

- [ ] **Step 4: Implement the exact Docker-state preflight**

Prepend this to `roles/server/tasks/project_identity_preflight.yml`:

```yaml
---
- name: Check current maintenance Compose projects
  community.docker.docker_host_info:
    containers: true
    containers_all: true
    containers_filters:
      label: >-
        com.docker.compose.project=offsitebuddy-maintenance-friend-{{
        maintenance_friend_name }}
    networks: true
    networks_filters:
      label: >-
        com.docker.compose.project=offsitebuddy-maintenance-friend-{{
        maintenance_friend_name }}
  loop: "{{ offsitebuddy_friends | map(attribute='name') | list }}"
  loop_control:
    loop_var: maintenance_friend_name
    label: "{{ maintenance_friend_name }}"
  register: offsitebuddy_server_maintenance_compose_inspections
  no_log: true

- name: Initialize current maintenance Compose summaries
  ansible.builtin.set_fact:
    offsitebuddy_server_maintenance_compose_summaries: []
  no_log: true

- name: Project current maintenance Compose inspections
  ansible.builtin.set_fact:
    offsitebuddy_server_maintenance_compose_summaries: >-
      {{
        offsitebuddy_server_maintenance_compose_summaries +
        [{
          'friend_name': maintenance_inspection.maintenance_friend_name,
          'project_name':
            'offsitebuddy-maintenance-friend-' ~
            maintenance_inspection.maintenance_friend_name,
          'container_count': maintenance_inspection.containers | length,
          'network_count': maintenance_inspection.networks | length
        }]
      }}
  loop: >-
    {{
      offsitebuddy_server_maintenance_compose_inspections.results |
      default([])
    }}
  loop_control:
    loop_var: maintenance_inspection
    label: >-
      {{ maintenance_inspection.maintenance_friend_name | default('skipped') }}
  when: not maintenance_inspection.skipped | default(false)
  no_log: true

- name: Refuse active or foreign maintenance Compose projects
  ansible.builtin.assert:
    that:
      - maintenance_project.container_count == 0
      - maintenance_project.network_count == 0
    fail_msg: >-
      Maintenance Compose project {{ maintenance_project.project_name }} exists
      ({{ maintenance_project.container_count }} containers,
      {{ maintenance_project.network_count }} networks). Complete its owning
      maintenance window or inspect and remove it with its owning Compose
      definition before rerunning; OffsiteBuddy will not remove it
      automatically.
  loop: >-
    {{ offsitebuddy_server_maintenance_compose_summaries | default([]) }}
  loop_control:
    loop_var: maintenance_project
    label: "{{ maintenance_project.friend_name }}"
```

Keep the existing marker-based preflight tasks immediately after this block,
without a second YAML document marker.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --locked python tests/test_review_fixes.py
UV_CACHE_DIR=.uv-cache uv run --locked molecule test -s cleanup --no-report
```

Expected: both PASS, and the Molecule refusal reports the new exact-identity
guard while preserving the foreign fixture.

- [ ] **Step 6: Commit**

```bash
git add tests/test_review_fixes.py molecule/cleanup/side_effect.yml roles/server/tasks/project_identity_preflight.yml
git commit -m "fix: refuse active maintenance projects"
```

### Task 2: Keep the helper fail-closed

**Files:**
- Modify: `tests/maintenance-endpoint.sh`
- Modify: `tests/test_review_fixes.py`
- Modify: `roles/server/templates/maintenance-endpoint.sh.j2`
- Modify: `roles/server/templates/compose.maintenance.yaml.j2`

**Interfaces:**
- Consumes: Docker CLI resource labels for the rendered maintenance project
- Produces: exit status `1` without stopping the ordinary project when the exact maintenance identity already exists

- [ ] **Step 1: Add failing helper-harness cases**

Add this helper to `tests/maintenance-endpoint.sh`:

```bash
assert_log_excludes() {
  local unexpected="$1"
  ! grep -Fqx "$unexpected" "$docker_log" ||
    fail "unexpected command in Docker log: $unexpected"
}
```

Before the fake Docker script exits, add:

```bash
if [ "${FAKE_DOCKER_EXISTING_MAINTENANCE_PROJECT:-}" = 1 ] &&
  [ "${1:-}" = ps ]; then
  printf 'existing-maintenance-container\n'
fi

if [ "${FAKE_DOCKER_SIGNAL_DURING_MAINTENANCE_DOWN:-}" = 1 ] &&
  [ "$#" -ge 3 ] &&
  [[ "${@: -3:1}" == */compose.maintenance.yaml ]] &&
  [ "${@: -2:1}" = down ] &&
  [ "${@: -1}" = --remove-orphans ]; then
  kill -TERM "$PPID"
fi
```

Add these cases after the normal-exit case:

```bash
render_helper collision
: > "$docker_log"
collision_ordinary_down="$(compose_command "$job_dir/compose.yaml" down)"
set +e
printf '\n' | PATH="$fake_bin:$PATH" FAKE_DOCKER_LOG="$docker_log" \
  FAKE_DOCKER_EXISTING_MAINTENANCE_PROJECT=1 \
  "$job_dir/maintenance-endpoint.sh" >/dev/null 2>&1
collision_status=$?
set -e
assert_eq "$collision_status" 1
assert_log_excludes "$collision_ordinary_down"

render_helper cleanup-term
: > "$docker_log"
set +e
printf '\n' | PATH="$fake_bin:$PATH" FAKE_DOCKER_LOG="$docker_log" \
  FAKE_DOCKER_SIGNAL_DURING_MAINTENANCE_DOWN=1 \
  "$job_dir/maintenance-endpoint.sh" >/dev/null
cleanup_term_status=$?
set -e
assert_eq "$cleanup_term_status" 0
cleanup_term_restore="$(compose_command "$job_dir/compose.yaml" up -d)"
assert_eq "$(command_line)" "$cleanup_term_restore"
assert_eq "$(ordinary_restore_count)" 1
```

- [ ] **Step 2: Add failing static assertions**

Add beside the existing maintenance template assertions in
`tests/test_review_fixes.py`:

```python
    assert maintenance_compose.count('restart: "no"') == 2
    assert "restart: unless-stopped" not in maintenance_compose
    assert 'maintenance_project="offsitebuddy-maintenance-friend-' in maintenance_helper
    assert 'docker ps --all --quiet --filter "$project_filter"' in maintenance_helper
    assert 'docker network ls --quiet --filter "$project_filter"' in maintenance_helper
    assert "trap '' HUP INT TERM" in maintenance_helper
```

- [ ] **Step 3: Run the focused checks and verify RED**

Run:

```bash
bash tests/maintenance-endpoint.sh
UV_CACHE_DIR=.uv-cache uv run --locked python tests/test_review_fixes.py
```

Expected: the harness FAILS because the collision is accepted or cleanup exits
`143`; the Python check FAILS because automatic restart and the missing
just-in-time guard remain.

- [ ] **Step 4: Implement the minimal helper and Compose changes**

In `roles/server/templates/maintenance-endpoint.sh.j2`, change cleanup trap
setup to:

```bash
  trap - EXIT
  trap '' HUP INT TERM
```

Add this immediately before the ordinary `docker compose ... down`:

```bash
maintenance_project="offsitebuddy-maintenance-friend-{{ maintenance_item.0.name }}"
project_filter="label=com.docker.compose.project=$maintenance_project"
maintenance_containers="$(
  docker ps --all --quiet --filter "$project_filter"
)"
maintenance_networks="$(
  docker network ls --quiet --filter "$project_filter"
)"
if [ -n "$maintenance_containers$maintenance_networks" ]; then
  printf 'Maintenance Compose project %s already exists; refusing to replace it.\n' \
    "$maintenance_project" >&2
  exit 1
fi
```

In `roles/server/templates/compose.maintenance.yaml.j2`, replace both restart
policies with:

```yaml
    restart: "no"
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
bash tests/maintenance-endpoint.sh
UV_CACHE_DIR=.uv-cache uv run --locked python tests/test_review_fixes.py
```

Expected: both PASS. The collision case never logs the ordinary project down,
and the cleanup-signal case restores it exactly once.

- [ ] **Step 6: Commit**

```bash
git add tests/maintenance-endpoint.sh tests/test_review_fixes.py roles/server/templates/maintenance-endpoint.sh.j2 roles/server/templates/compose.maintenance.yaml.j2
git commit -m "fix: keep maintenance helper fail closed"
```

### Task 3: Pause every repository user

**Files:**
- Modify: `tests/test_review_fixes.py`
- Modify: `docs/append-only-maintenance.md`

**Interfaces:**
- Consumes: operator knowledge of every job and host targeting the selected repository
- Produces: an explicit preflight requirement to pause all matching backup and check units

- [ ] **Step 1: Add the failing documentation assertion**

Add after the existing runbook text assertions in `tests/test_review_fixes.py`:

```python
    for text in (
        "every backup and check job",
        "including jobs on other hosts",
        "same repository",
        "repeat these commands for each matching job",
    ):
        assert text in docs
    assert "do not combine friends or jobs in one window" not in docs
```

- [ ] **Step 2: Run the focused check and verify RED**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --locked python tests/test_review_fixes.py
```

Expected: FAIL because the runbook only pauses the selected job.

- [ ] **Step 3: Clarify the runbook**

Replace the opening scope with:

```markdown
OffsiteBuddy does not enforce retention. It keeps the normal rest-server
append-only. Retention is manual maintenance: use one approved window for one
friend and its repository. Do not schedule an automatic prune.

The commands use friend `alice`, client job `photos_to_alice`, and the default
roots `/srv/offsitebuddy` and `/etc/offsitebuddy/jobs`. Substitute the one
reviewed friend/repository and the configured `offsitebuddy_server_root` and
`offsitebuddy_client_root`; do not combine friends or repositories in one
window.
```

Replace the first preflight paragraph with:

```markdown
Identify every backup and check job that targets the same repository,
including jobs on other hosts. Pause all of them. The commands below show one
job; repeat these commands for each matching job. Run the check-unit lines only
when that job has a generated check unit. Disabling a timer does not stop an
in-flight service, so wait until every matching service is inactive before
continuing:
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --locked python tests/test_review_fixes.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_review_fixes.py docs/append-only-maintenance.md
git commit -m "docs: pause every retention repository user"
```

### Task 4: Full verification and final review

**Files:**
- Verify only: all files changed in Tasks 1-3

**Interfaces:**
- Consumes: completed Task 1-3 commits
- Produces: clean local validation evidence and a reviewable final diff

- [ ] **Step 1: Run formatting and static validation**

```bash
ANSIBLE_HOME=.ansible \
ANSIBLE_COLLECTIONS_PATH=.ansible/collections:collections \
UV_CACHE_DIR=.uv-cache \
uv run --locked pre-commit run --all-files
```

Expected: all hooks PASS.

- [ ] **Step 2: Run focused runtime checks**

```bash
bash tests/maintenance-endpoint.sh
UV_CACHE_DIR=.uv-cache uv run --locked molecule test -s cleanup --no-report
```

Expected: both PASS.

- [ ] **Step 3: Run the default Molecule validation**

```bash
UV_CACHE_DIR=.uv-cache uv run --locked molecule converge --no-report
UV_CACHE_DIR=.uv-cache uv run --locked molecule verify --no-report
```

Expected: both PASS.

- [ ] **Step 4: Build the collection and check the diff**

```bash
UV_CACHE_DIR=.uv-cache uv run --locked ansible-galaxy collection build --force
git diff --check origin/main...HEAD
git status --short --branch
```

Expected: collection build succeeds, diff check is silent, and the worktree is
clean.

- [ ] **Step 5: Re-review the exact final diff**

Review:

```bash
git diff --stat 41f344103e0ec062dd046c9b856b4117169e7c4f...HEAD
git diff 41f344103e0ec062dd046c9b856b4117169e7c4f...HEAD
```

Expected: only the approved design, focused regressions, three fixes, and
runbook clarification are present; no unresolved P1/P2 finding remains.
