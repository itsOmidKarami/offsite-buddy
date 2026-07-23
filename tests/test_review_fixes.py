#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def assert_secret_loops_are_redacted(path, collection_variable):
    for task in yaml.safe_load(read(path)):
        loop = str(task.get("loop", ""))
        if collection_variable not in loop:
            continue
        safe_name_projection = "map(attribute='name')" in loop
        behaviorally_redacted = (
            task.get("name") == "Validate friend rest-server access modes"
        )
        assert (
            task.get("no_log") is True
            or safe_name_projection
            or behaviorally_redacted
        ), (
            "%s loops over %s without no_log or a safe projection: %s"
            % (path, collection_variable, task["name"])
        )


def run_playbook(path):
    env = os.environ.copy()
    env["ANSIBLE_LOCAL_TEMP"] = str(ROOT / ".ansible/tmp")
    result = subprocess.run(
        [
            "ansible-playbook",
            "-i",
            "localhost,",
            "-c",
            "local",
            path,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    return result, output


def assert_server_mode_validation_output_is_redacted():
    result, output = run_playbook("tests/validation-negative.yml")
    assert result.returncode == 0, "negative validation playbook must pass"
    assert "rest_server.mode must be append_only or read_write" in output, (
        "access-mode validation must retain its safe failure message"
    )
    for secret in (
        "mode-validation-tailscale-secret",
        "mode-validation-rest-server-secret",
    ):
        assert secret not in output, "Ansible output leaked %s" % secret


def assert_client_validation_output_is_redacted():
    result, output = run_playbook("tests/secret-redaction.yml")
    assert result.returncode != 0, "secret redaction play must fail on the missing path"
    assert "secret_output" in output, "failure must retain the safe job name"
    assert "missing-source" in output, "failure must retain the safe backup path"
    for secret in (
        "output-rest-password",
        "output-restic-password",
        "output-tailscale-auth-key",
        "repository:",
        "password:",
        "auth_key:",
    ):
        assert secret not in output, "Ansible output leaked %s" % secret


def main():
    ansible_cfg = read("ansible.cfg")
    assert "stdout_callback = yaml" not in ansible_cfg, (
        "removed community.general.yaml callback must not be selected"
    )
    assert "stdout_callback = default" in ansible_cfg, (
        "Ansible output should use the built-in default callback"
    )
    assert "callback_result_format = yaml" in ansible_cfg, (
        "YAML-like output should use the built-in callback option"
    )

    backup = read("roles/client/templates/backup.sh.j2")
    for field in ("start", "success", "failure"):
        expected = (
            "ping_url {{ job.heartbeat.%s_url | default('') | quote }} \"%s\""
            % (field, field)
        )
        assert expected in backup, "heartbeat %s URL must be shell-quoted" % field
    assert "redacted" in backup, "heartbeat failure logs must not expose URLs"

    validate = read("roles/client/tasks/validate.yml")
    for snippet in (
        "regex_search('^([01][0-9]|2[0-3]):[0-5][0-9]$')",
        "item.backup_paths | type_debug == 'list'",
        "select('match', '^/')",
        "map(attribute='name')",
        "unique",
        "offsitebuddy_client_backup_path_stats",
        "item.2.exists",
        "item.2.isdir",
        "systemd-analyze calendar",
        "url-encoded",
        "offsitebuddy_client_supported_repository_schemes",
        "Validate local repository paths do not overlap backup paths",
        "Validate excludes do not cover backup paths",
        "item.excludes | type_debug == 'list'",
        "offsitebuddy_client_root | regex_search('^/') is not none",
        "item.repository | length > 0",
        "'..' not in item.repository.split('/')",
        "item.repository != '/'",
        "item.repository is not match('^.+/$')",
        "item.password is string",
        "item.password | length > 0",
        "item.backup_paths | select('string') | list | length",
        "item.backup_paths | reject('equalto', '/')",
        "item.backup_paths | reject('match', '^.+/$')",
        "item.backup_paths | reject('search', '(^|/)\\.\\.(/|$)')",
        "item.excludes | reject('equalto', '/')",
        "item.excludes | reject('match', '^.+/$')",
        "item.excludes | reject('search', '(^|/)\\.\\.(/|$)')",
        "item.excludes | reject('search', '[*?\\[]')",
        "managed client root",
    ):
        assert snippet in validate, "missing client validation: %s" % snippet
    assert "not offsitebuddy_cleanup_stale | bool or" in validate
    assert "offsitebuddy_manage_systemd | bool" in validate
    assert "offsitebuddy-client-" in validate
    assert "intersect" in validate
    stat_task = validate.split("- name: Stat client backup paths", 1)[1].split(
        "- name: Assert client backup paths exist and are directories", 1
    )[0]
    assert "no_log: true" in stat_task, "backup path stat must hide full job items"
    path_assert_task = validate.split(
        "- name: Assert client backup paths exist and are directories", 1
    )[1].split("- name: Validate local repository paths", 1)[0]
    assert "offsitebuddy_client_backup_path_checks" in path_assert_task, (
        "backup path assertions must loop over sanitized results"
    )
    assert "item.item.0" not in path_assert_task, (
        "backup path assertions must not retain the full job object"
    )

    docs = read("docs/append-only-maintenance.md").lower()
    assert "does not enforce retention" in docs, "retention non-enforcement must be explicit"
    assert "manual maintenance" in docs, "manual retention maintenance must be explicit"
    for text in (
        "--dry-run",
        "--keep-within",
        "maintenance-endpoint.sh",
        "forget --prune",
        "restic check",
        "restore-latest.sh",
        "append-only",
    ):
        assert text in docs
    for command in (
        "-f /srv/offsitebuddy/friends/alice/compose.yaml",
        "-f /srv/offsitebuddy/friends/alice/compose.maintenance.yaml",
        "while sudo systemctl is-active --quiet offsitebuddy-backup-photos_to_alice.service",
        "while sudo systemctl is-active --quiet offsitebuddy-check-photos_to_alice.service",
        "preflight_restore=\"$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-preflight.xxxxxx)\"",
        "post_prune_restore=\"$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-post-prune.xxxxxx)\"",
        "label=com.docker.compose.project=offsitebuddy-maintenance-friend-alice",
        "grep '^options=.*--append-only'",
    ):
        assert command in docs
    assert "offsitebuddy_server_root" in docs
    assert "offsitebuddy_client_root" in docs
    post_close_docs = docs.split("## restore append-only operation", 1)[1].split(
        "## failure handling", 1
    )[0]
    assert post_close_docs.index("offsitebuddy-maintenance-friend-alice") < (
        post_close_docs.index('label=com.docker.compose.project=offsitebuddy-friend-alice"')
    ) < post_close_docs.index("options=.*--append-only") < post_close_docs.index(
        "/etc/offsitebuddy/jobs/photos_to_alice/check.sh"
    )
    failure_docs = docs.split("## failure handling", 1)[1]
    assert failure_docs.index("compose.maintenance.yaml down --remove-orphans") < (
        failure_docs.index("compose.yaml up -d")
    )

    endpoint_docs = read("docs/tailnet-endpoints.md").lower().replace("\n", " ")
    assert "tailnet ip | supported reliable default for cross-tailnet docker jobs." in endpoint_docs
    assert "full magicdns fqdn | supported after successful resolution in the generated restic path." in endpoint_docs
    assert "generated one-shot restic container, whose in-container dns" in endpoint_docs
    assert "is an alternative only after it resolves successfully in this generated restic execution path" in endpoint_docs
    assert "checking resolution only from the tailscale sidecar is insufficient." in endpoint_docs
    assert "after any re-enrollment or loss of persistent tailscale state, even if the ip appears unchanged" in endpoint_docs
    assert "first stop and disable the affected job's backup timer and, if present, check timer." in endpoint_docs
    assert "rediscover the ip and converge the client with `offsitebuddy_start_services: false` so the timers remain paused." in endpoint_docs
    assert "without printing the repository url, run that job's `snapshots.sh` and `check.sh`." in endpoint_docs
    assert "only after both succeed, run normal client convergence to enable and resume timers." in endpoint_docs
    assert "public internet exposure is unsupported by default." in endpoint_docs
    assert "do not echo, log, or paste a complete credential-bearing repository url" in endpoint_docs

    endpoint_example = read("examples/group_vars/backup_clients.yml").lower()
    active_repository = endpoint_example.split("    repository: >-\n", 1)[1].split(
        "    # a full magicdns fqdn", 1
    )[0]
    assert "offsitebuddy_alice_server_tailnet_ip" in active_repository
    assert "vault_rest_server_password" in active_repository
    assert "urlencode" in active_repository
    for literal in ("tskey-", "password123", "correcthorsebatterystaple"):
        assert literal not in endpoint_example

    server_compose = read("roles/server/templates/compose.yaml.j2")
    assert 'name: "offsitebuddy-friend-{{ friend.name }}"' in server_compose
    assert "TS_USERSPACE: \"false\"" in server_compose, "tailscale must use kernel networking"
    assert "devices:" in server_compose, "tailscale must map /dev/net/tun as a device"
    assert "NET_RAW" in server_compose, "tailscale should include NET_RAW capability"
    assert "type: bind" in server_compose, "server volumes should use long-form bind mounts"
    maintenance_compose = read("roles/server/templates/compose.maintenance.yaml.j2")
    maintenance_helper = read("roles/server/templates/maintenance-endpoint.sh.j2")
    maintenance_verify = read("molecule/default/verify.yml")
    assert (
        'name: "offsitebuddy-maintenance-friend-{{ friend.name }}"'
        in maintenance_compose
    )
    assert 'name: "offsitebuddy-friend-{{ friend.name }}-maintenance"' not in maintenance_compose
    ordinary_collision_project = "offsitebuddy-friend-alice-maintenance"
    maintenance_alice_project = "offsitebuddy-maintenance-friend-alice"
    assert ordinary_collision_project != maintenance_alice_project
    assert "--append-only" not in maintenance_compose
    assert "friend.quota.path" in maintenance_compose
    assert "./htpasswd" in maintenance_compose
    assert "trap cleanup EXIT" in maintenance_helper
    for signal in ("HUP", "INT", "TERM"):
        assert signal in maintenance_helper
    assert 'compose.yaml" up -d' in maintenance_helper
    assert "exit \"$restore_status\"" in maintenance_helper
    assert "artifact_status=$?" in maintenance_helper
    assert "exit \"$artifact_status\"" in maintenance_helper
    maintenance_validation = maintenance_verify.split(
        "- name: Validate maintenance Compose configuration", 1
    )[1].split("- name: Parse generated Compose files", 1)[0]
    assert "--project-name" not in maintenance_validation
    assert "maintenance-endpoint.sh" in read("roles/server/tasks/rest_server.yml")
    server_tasks = read("roles/server/tasks/rest_server.yml")
    server_cleanup = read("roles/server/tasks/cleanup.yml")
    assert 'project_name: "offsitebuddy-friend-{{ friend_name }}"' in server_tasks
    assert (
        'project_name: "offsitebuddy-friend-{{ stale_friend_name }}"'
        in server_cleanup
    )
    assert "community.docker.docker_host_info" in server_tasks
    assert "community.docker.docker_host_info" in server_cleanup
    dependency_index = server_tasks.index(
        "- name: Ensure server Python dependencies are installed"
    )
    legacy_query_index = server_tasks.index(
        "- name: Check for legacy generic friend Compose projects"
    )
    legacy_refusal_index = server_tasks.index(
        "- name: Refuse to replace legacy generic friend Compose projects"
    )
    first_friend_write_index = server_tasks.index(
        "- name: Ensure friend stack directories exist"
    )
    assert dependency_index < legacy_query_index
    assert legacy_query_index < legacy_refusal_index < first_friend_write_index
    current_legacy_query = server_tasks.split(
        "- name: Check for legacy generic friend Compose projects", 1
    )[1].split("- name: Project current legacy Compose inspections", 1)[0]
    current_legacy_init = server_tasks.split(
        "- name: Initialize current legacy Compose summaries", 1
    )[1].split("- name: Project current legacy Compose inspections", 1)[0]
    current_legacy_projection = server_tasks.split(
        "- name: Project current legacy Compose inspections", 1
    )[1].split(
        "- name: Refuse to replace legacy generic friend Compose projects", 1
    )[0]
    current_legacy_refusal = server_tasks.split(
        "- name: Refuse to replace legacy generic friend Compose projects", 1
    )[1].split("- name: Ensure friend stack directories exist", 1)[0]
    assert "no_log: true" in current_legacy_query
    assert "no_log: true" in current_legacy_projection
    assert "offsitebuddy_start_services" not in current_legacy_query
    assert "when:" not in current_legacy_init
    assert "offsitebuddy_server_legacy_compose_inspections" in current_legacy_query
    assert "offsitebuddy_server_legacy_compose_inspections" in (
        current_legacy_projection
    )
    assert "offsitebuddy_server_legacy_compose_summaries" in current_legacy_refusal
    assert "offsitebuddy_server_legacy_compose_inspections" not in current_legacy_refusal
    assert "--project-name {{ legacy_project.friend_name }}" in current_legacy_refusal
    assert "offsitebuddy_server_root ~ '/friends/' ~ legacy_project.friend_name" in (
        current_legacy_refusal
    )
    assert "'/compose.yaml'" in current_legacy_refusal

    stale_legacy_query = server_cleanup.split(
        "- name: Check stale friends for legacy generic Compose projects", 1
    )[1].split("- name: Project stale legacy Compose inspections", 1)[0]
    stale_legacy_init = server_cleanup.split(
        "- name: Initialize stale legacy Compose summaries", 1
    )[1].split("- name: Project stale legacy Compose inspections", 1)[0]
    stale_legacy_projection = server_cleanup.split(
        "- name: Project stale legacy Compose inspections", 1
    )[1].split(
        "- name: Refuse to remove stale friends with legacy generic Compose projects",
        1,
    )[0]
    stale_legacy_refusal = server_cleanup.split(
        "- name: Refuse to remove stale friends with legacy generic Compose projects",
        1,
    )[1].split("- name: Stop stale friend server stacks", 1)[0]
    assert "no_log: true" in stale_legacy_query
    assert "no_log: true" in stale_legacy_projection
    assert "when:" not in stale_legacy_init
    assert "offsitebuddy_stale_legacy_compose_inspections" in stale_legacy_query
    assert "offsitebuddy_stale_legacy_compose_inspections" in (
        stale_legacy_projection
    )
    assert "offsitebuddy_stale_legacy_compose_summaries" in stale_legacy_refusal
    assert "offsitebuddy_stale_legacy_compose_inspections" not in stale_legacy_refusal
    assert "--project-name {{ legacy_project.friend_name }}" in stale_legacy_refusal
    assert "offsitebuddy_server_root ~ '/friends/' ~ legacy_project.friend_name" in (
        stale_legacy_refusal
    )
    assert "'/compose.yaml'" in stale_legacy_refusal
    assert "python3-passlib" in server_tasks, "server role must install passlib for htpasswd"
    assert ".offsitebuddy-managed" in server_tasks, "server role must mark managed stacks"
    assert "offsitebuddy_cleanup_stale" in server_cleanup, "server role must support stale cleanup"
    assert "state: absent" in server_cleanup, "server stale cleanup must stop old stacks"
    assert "state: restarted" not in server_tasks, (
        "changed server files must converge with Compose up, not restart"
    )
    converge_task = server_tasks.split(
        "- name: Converge per-friend server stacks", 1
    )[1]
    assert "state: present" in converge_task, "server stacks must converge with up -d"
    assert "pull: missing" in converge_task, "server convergence must retain pull behavior"
    server_find = server_cleanup.split("- name: Find managed friend stack markers", 1)[1].split(
        "- name: Stop stale friend server stacks", 1
    )[0]
    assert "recurse: true" in server_find
    assert "depth: 2" in server_find
    assert "hidden: true" in server_find
    assert (
        "item.path | dirname | dirname == offsitebuddy_server_root ~ '/friends'"
        in server_cleanup
    )
    assert server_cleanup.index("Stop stale friend server stacks") < server_cleanup.index(
        "Remove stale friend stack directories"
    )
    stale_stop_task = server_cleanup.split(
        "- name: Stop stale friend server stacks", 1
    )[1].split("- name: Remove stale friend stack directories", 1)[0]
    assert "files:" in stale_stop_task
    assert "- compose.yaml" in stale_stop_task
    assert server_tasks.index(
        "Refuse to replace legacy generic friend Compose projects"
    ) < server_tasks.index("cleanup.yml")
    assert server_tasks.index("cleanup.yml") < server_tasks.index(
        "project_identity_preflight.yml"
    )
    assert server_tasks.index("project_identity_preflight.yml") < server_tasks.index(
        "Ensure friend stack directories exist"
    )
    server_identity_preflight = read(
        "roles/server/tasks/project_identity_preflight.yml"
    )
    assert "Find managed friend markers for Compose identity preflight" in (
        server_identity_preflight
    )
    assert "managed_friend_name not in current_project_names" in (
        server_identity_preflight
    )
    assert "offsitebuddy_cleanup_stale" not in server_identity_preflight

    server_readme = read("roles/server/README.md")
    assert "before friend-specific files change" in server_readme
    assert (
        "docker compose --project-name <friend-name> --file "
        "<managed-compose-path>/compose.yaml down"
    ) in server_readme

    cleanup_prepare = read("molecule/cleanup/prepare.yml")
    cleanup_prepare_query = cleanup_prepare.split(
        "- name: Check cleanup fixture project names are unused", 1
    )[1].split("- name: Initialize cleanup fixture project summaries", 1)[0]
    cleanup_prepare_projection = cleanup_prepare.split(
        "- name: Project cleanup fixture inspections", 1
    )[1].split("- name: Refuse to overwrite existing cleanup fixture projects", 1)[0]
    assert "no_log: true" in cleanup_prepare_query
    assert "no_log: true" in cleanup_prepare_projection
    assert "container_count" in cleanup_prepare_projection
    assert "network_count" in cleanup_prepare_projection

    cleanup_side_effect = read("molecule/cleanup/side_effect.yml")
    assert "tskey-auth-" not in cleanup_side_effect, (
        "Molecule fixtures must not resemble Tailscale API keys"
    )
    assert "legacy_teardown_root" in cleanup_side_effect
    assert cleanup_side_effect.count(
        'project_src: "{{ legacy_teardown_root }}"'
    ) == 6
    assert "Require server identity shadow refusal with cleanup disabled" in (
        cleanup_side_effect
    )
    assert "Require client identity shadow refusal with cleanup disabled" in (
        cleanup_side_effect
    )
    assert "Exercise stale client generic Compose refusal before deletion" in (
        cleanup_side_effect
    )

    cleanup_molecule = read("molecule/cleanup/molecule.yml")
    cleanup_playbook = read("molecule/cleanup/cleanup.yml")
    assert "cleanup: cleanup.yml" in cleanup_molecule
    assert "offsitebuddy.cleanup-fixture" in cleanup_playbook
    assert "offsitebuddy.cleanup-fixture" in cleanup_prepare
    assert cleanup_side_effect.count("offsitebuddy.cleanup-fixture") == 12

    server_validate = read("roles/server/tasks/validate.yml")
    assert "offsitebuddy_friends | map(attribute='name')" in server_validate, "server friend names must be unique"
    assert "map(attribute='quota.path')" in server_validate, "server quota paths must be unique"
    assert "map(attribute='tailscale.hostname')" in server_validate, "server hostnames must be unique"
    assert "item.quota.path | regex_search('^/')" in server_validate, (
        "server quota paths must be absolute"
    )
    assert "'..' not in item.quota.path.split('/')" in server_validate, (
        "server quota paths must reject traversal segments"
    )
    for snippet in (
        "offsitebuddy_server_root | regex_search('^/') is not none",
        "item.quota.path != '/'",
        "item.quota.path is not match('^.+/$')",
        "managed server root",
        "item.tailscale.auth_key is string",
        "item.rest_server.username is string",
        "item.rest_server.password is string",
        "item.rest_server.port is not defined or",
        "item.rest_server.port | string is match('^[0-9]+$')",
        "Validate friend quota paths do not overlap each other",
    ):
        assert snippet in server_validate, "missing server validation: %s" % snippet
    assert "not offsitebuddy_cleanup_stale | bool or offsitebuddy_start_services | bool" in server_validate
    assert "offsitebuddy-friend-" in server_validate
    assert "intersect" in server_validate

    quota_validate = read("roles/quota/tasks/main.yml")
    assert "item.path | regex_search('^/')" in quota_validate, (
        "quota role paths must be absolute"
    )
    assert "'..' not in item.path.split('/')" in quota_validate, (
        "quota role paths must reject traversal segments"
    )
    assert "item.path != '/'" in quota_validate, "quota role paths must reject root"
    assert "item.path is not match('^.+/$')" in quota_validate, (
        "quota role paths must reject trailing slashes"
    )

    getting_started = read("docs/getting-started.md").lower()
    assert "client-side tailscale\n   sidecar" in getting_started, (
        "client Tailscale sidecar setup must be explicit"
    )
    assert "untagged tailscale auth key" in getting_started, (
        "client sidecar auth keys must work with cross-tailnet sharing"
    )
    assert "<hostname>.<server-tailnet>.ts.net" in getting_started, (
        "cross-tailnet shares must use the shared machine FQDN"
    )
    assert "do not mutually share the client device" in getting_started, (
        "Tailscale sharing should stay one-way for backup access"
    )
    assert "debian-family" in getting_started, "supported OS family must be explicit"
    assert "url-encoded" in getting_started, "REST URL credentials must be documented as URL-encoded"
    assert "ansible-galaxy collection install" in getting_started, (
        "collection installation path must be documented"
    )
    assert "127.0.0.11" in getting_started, (
        "Docker embedded DNS failure mode must be documented"
    )
    assert "tailscale ip" in getting_started, (
        "Tailnet IP repository fallback must be documented"
    )

    workflow = read(".github/workflows/ci.yml")
    expected_trigger = "  pull_request:\n  push:\n    branches:\n      - main"
    assert expected_trigger in workflow, (
        "CI should run on PRs and only on pushes to main"
    )
    assert "actions/checkout@v7" in workflow, (
        "CI checkout action should use a Node 24 runtime"
    )
    assert "actions/setup-python@v7" in workflow, (
        "CI setup-python action should use a Node 24 runtime"
    )
    assert "actions/checkout@v4" not in workflow
    assert "actions/setup-python@v5" not in workflow
    assert "tests/validation-negative.yml" in workflow, (
        "CI must reject unsafe validation inputs"
    )
    assert "tests/client-sidecar-render.yml" in workflow, (
        "CI must render the client Tailscale sidecar path"
    )
    assert "tests/e2e-local.yml" in workflow, "CI must exercise local backup and restore"
    assert "git config --global init.defaultBranch main" in workflow, (
        "CI checkout should avoid git init default-branch warnings"
    )
    assert "MOLECULE_GLOB: molecule/*/molecule.yml" in workflow, (
        "CI should avoid Molecule collection migration warnings"
    )
    for snippet in (
        "Validate PR title",
        "${{ github.event.pull_request.title }}",
        "feat|fix|perf|revert|docs|test|ci|chore|refactor",
        "PR title must be a conventional commit",
    ):
        assert snippet in workflow, "missing PR title release gate: %s" % snippet
    assert "uv run molecule converge --no-report" in workflow, (
        "Molecule converge should avoid end-of-run warning summaries"
    )
    assert "uv run molecule verify --no-report" in workflow, (
        "Molecule verify should avoid end-of-run warning summaries"
    )
    assert "printf '%s%s  Driver docker does not provide a schema.' WARN ING" in workflow, (
        "CI should filter Molecule docker plugin schema warning noise"
    )
    assert 'grep -v -F "$molecule_schema_filter"' in workflow, (
        "CI should keep the literal warning text out of echoed commands"
    )

    release_workflow = read(".github/workflows/release.yml")
    release_please = read("release-please-config.json")
    assert "googleapis/release-please-action@v5" in release_workflow, (
        "release-please action should use the supported Node 24 runtime"
    )
    assert "googleapis/release-please-action@v4" not in release_workflow
    assert "  contents: write" in release_workflow
    assert "  pull-requests: write" in release_workflow
    assert "GH_TOKEN: ${{ github.token }}" in release_workflow
    assert "RELEASE_PLEASE_TOKEN" not in release_workflow, (
        "release PRs must be authored by github-actions so the owner can approve them"
    )
    assert '"draft": true' in release_please, (
        "release-please must leave releases mutable until artifacts are attached"
    )
    assert '"force-tag-creation": true' in release_please, (
        "draft releases must still create tags for workflow checkout"
    )
    for snippet in (
        "--json isDraft,isImmutable,assets",
        "gh release create \"$tag\" \"$artifact\"",
        "gh release upload \"$tag\" \"$artifact\"",
        "gh release edit \"$tag\"",
        "--draft=false",
        "Release $tag already has $artifact",
        "Immutable releases cannot be modified",
        "Ship a new version tag instead",
    ):
        assert snippet in release_workflow, "missing release artifact flow: %s" % snippet

    validation_negative = read("tests/validation-negative.yml")
    assert "rescue:" not in validation_negative, (
        "negative validation checks must not print rescued task failures"
    )
    assert "ansible_failed_task" not in validation_negative, (
        "negative validation checks must avoid Ansible failure annotations"
    )
    assert "ansible_python_interpreter" in validation_negative, (
        "negative validation checks should avoid interpreter discovery warnings"
    )

    verify = read("molecule/default/verify.yml")
    for snippet in (
        "bash -n",
        "from_yaml",
        "Normalize rendered server Compose files",
        "systemd-analyze verify",
        "TS_USERSPACE",
    ):
        assert snippet in verify, "missing Molecule artifact check: %s" % snippet
    generated_files = verify.split(
        "- name: Read per-entry generated files", 1
    )[1].split("- name: Index generated file content", 1)[0]
    client_outputs = verify.split(
        "- name: Stat client job outputs", 1
    )[1].split("- name: Stat secret files", 1)[0]
    helper_syntax = verify.split(
        "- name: Verify helper script syntax", 1
    )[1].split("- name: Normalize rendered server Compose files", 1)[0]
    for name, job in (
        ("photos", "photos_to_bob"),
        ("documents", "documents_to_alice"),
    ):
        restore_path = "/etc/offsitebuddy/jobs/%s/restore.sh" % job
        wrapper_path = "/etc/offsitebuddy/jobs/%s/restore-latest.sh" % job
        assert "name: %s_restore\n          path: %s" % (
            name,
            restore_path,
        ) in generated_files
        assert restore_path in client_outputs
        assert wrapper_path in client_outputs
    for helper in ("'restore.sh'", "'restore-latest.sh'"):
        assert helper in helper_syntax
    client_tasks = read("roles/client/tasks/restic.yml")
    client_task_defs = {
        task["name"]: task for task in yaml.safe_load(client_tasks)
    }
    repository_check_task = client_task_defs[
        "Check for existing restic repositories"
    ]
    assert "community.docker.docker_compose_v2_run" in repository_check_task
    assert repository_check_task["changed_when"] is False
    assert repository_check_task["failed_when"] == (
        "offsitebuddy_restic_repository_check.rc not in [0, 10]"
    )

    repository_init_task = client_task_defs[
        "Initialize missing restic repositories"
    ]
    assert "community.docker.docker_compose_v2_run" in repository_init_task
    assert any(
        "offsitebuddy_restic_repository_check.results[job_index].rc" in condition
        and "== 10" in condition
        for condition in repository_init_task["when"]
    )
    assert ".offsitebuddy-managed" in client_tasks, "client role must mark managed jobs"
    assert "no_log: true" in client_tasks.split("- name: Initialize missing restic repositories")[0], (
        "helper script templating must hide heartbeat URLs"
    )
    init_task = client_tasks.split(
        "- name: Initialize missing restic repositories", 1
    )[1].split("- name: Run initial backup", 1)[0]
    assert "no_log: true" in init_task, "repository init must hide repository URLs"

    initial_backup_result, initial_backup_output = run_playbook(
        "tests/initial-backup-regression.yml"
    )
    assert initial_backup_result.returncode == 0, initial_backup_output

    client_cleanup = read("roles/client/tasks/cleanup.yml")
    assert "LoadState" in client_cleanup
    assert "ActiveState" in client_cleanup
    assert "not-found" in client_cleanup
    client_find = client_cleanup.split("- name: Find managed client job markers", 1)[1].split(
        "- name: Query stale client unit states", 1
    )[0]
    assert "offsitebuddy_cleanup_stale" in client_cleanup, "client role must support stale cleanup"
    assert "{'kind': 'backup', 'unit_type': 'timer'}" in client_cleanup, (
        "stale backup timers must be checked and stopped"
    )
    assert "state: absent" in client_cleanup, "stale unit files must be removed"
    assert "recurse: true" in client_cleanup
    assert "depth: 2" in client_cleanup
    assert "hidden: true" in client_find
    assert "item.path | dirname | dirname == offsitebuddy_client_root" in client_cleanup
    assert "failed_when: false" not in client_cleanup
    assert client_cleanup.index("Stop loaded stale client units") < client_cleanup.index(
        "Remove stale client job directories"
    )
    assert client_cleanup.index("Stop stale client Compose projects") < (
        client_cleanup.index("Remove stale client job directories")
    )
    assert 'project_name: "offsitebuddy-client-{{ stale_job_name }}"' in (
        client_cleanup
    )
    assert "Refuse to remove stale jobs with legacy generic Compose projects" in (
        client_cleanup
    )
    assert "Stop unloaded active stale client units" in client_cleanup
    assert "systemctl" in client_cleanup
    assert "stop" in client_cleanup
    assert "Verify stale client units are inactive" in client_cleanup
    inactive_verify = client_cleanup.split(
        "- name: Verify stale client units are inactive", 1
    )[1].split("- name: Check stale jobs for legacy generic Compose projects", 1)[0]
    assert "rc != 0" in inactive_verify

    client_main = read("roles/client/tasks/main.yml")
    assert "compose_preflight.yml" in client_main
    assert client_main.index("compose_preflight.yml") < client_main.index("cleanup.yml")
    assert client_main.index("cleanup.yml") < client_main.index(
        "project_identity_preflight.yml"
    )
    assert client_main.index("project_identity_preflight.yml") < client_main.index(
        "restic.yml"
    )
    client_identity_preflight = read(
        "roles/client/tasks/project_identity_preflight.yml"
    )
    assert "Find managed client markers for Compose identity preflight" in (
        client_identity_preflight
    )
    assert "managed_job_name not in current_project_names" in (
        client_identity_preflight
    )
    assert "offsitebuddy_cleanup_stale" not in client_identity_preflight
    client_preflight = read("roles/client/tasks/compose_preflight.yml")
    assert "community.docker.docker_host_info" in client_preflight
    assert "/etc/debian_version" in client_preflight
    client_dependency_install = client_preflight.split(
        "- name: Ensure client Python dependencies are installed", 1
    )[1].split("- name: Check for legacy generic client Compose projects", 1)[0]
    assert "become: true" in client_dependency_install
    assert "offsitebuddy_client_debian.stat.exists" in client_dependency_install
    assert "Refuse to replace legacy generic client Compose projects" in (
        client_preflight
    )
    assert "offsitebuddy-backup-{{ legacy_project.job_name }}.timer" in (
        client_preflight
    )
    assert "offsitebuddy-check-{{ legacy_project.job_name }}.timer" in (
        client_preflight
    )
    assert "services are inactive" in client_preflight
    assert "no_log: true" in client_preflight
    client_readme = read("roles/client/README.md")
    assert "before job-specific files change" in client_readme
    assert "backup sources" in client_readme.lower()
    assert "repository data are never removed" in client_readme.lower()
    assert "stop and disable any existing backup/check timers" in (
        client_readme.lower()
    )
    assert (
        "docker compose --project-name <job-name> --file "
        "<managed-compose-path>/compose.yaml down"
    ) in client_readme
    timer_guidance = " ".join(client_readme.split())
    assert "A missed `Persistent=true` timer can run after boot." in timer_guidance
    assert (
        "Each backup start is delayed by up to "
        "`offsitebuddy_backup_randomized_delay_sec` through `RandomizedDelaySec`."
    ) in timer_guidance
    assert "Disabling an optional check leaves its backup timer enabled." in timer_guidance
    assert (
        "Set `check.read_data: true` only when needed: it reads repository data "
        "and may be I/O-intensive."
    ) in timer_guidance

    default_molecule = read("molecule/default/molecule.yml")
    assert "DOCKER_SOCKET_VOLUME" in default_molecule
    cleanup_molecule = read("molecule/cleanup/molecule.yml")
    assert "/var/run/docker.sock:/docker.sock" in cleanup_molecule
    for cleanup_playbook in (
        "molecule/cleanup/prepare.yml",
        "molecule/cleanup/converge.yml",
        "molecule/cleanup/side_effect.yml",
        "molecule/cleanup/verify.yml",
    ):
        assert "default('unix:///docker.sock', true)" in read(cleanup_playbook)
    assert "current_client_legacy_job" in cleanup_side_effect
    assert "Refuse to replace legacy generic client Compose projects" in (
        cleanup_side_effect
    )
    current_client_migration = cleanup_side_effect.split(
        "- name: Exercise current client generic Compose refusal before job writes",
        1,
    )[1].split(
        "- name: Exercise current generic Compose refusal before friend writes",
        1,
    )[0]
    assert "offsitebuddy_start_services: true" in current_client_migration
    assert "offsitebuddy_manage_systemd: true" in current_client_migration
    assert "cleanup_fixture_project_names" in cleanup_side_effect

    for path, collection_variable in (
        ("roles/client/tasks/validate.yml", "offsitebuddy_client_jobs"),
        ("roles/client/tasks/restic.yml", "offsitebuddy_client_jobs"),
        ("roles/client/tasks/systemd.yml", "offsitebuddy_client_jobs"),
        ("roles/server/tasks/validate.yml", "offsitebuddy_friends"),
        ("roles/server/tasks/rest_server.yml", "offsitebuddy_friends"),
    ):
        assert_secret_loops_are_redacted(path, collection_variable)

    assert_server_mode_validation_output_is_redacted()
    assert_client_validation_output_is_redacted()

    client_compose = read("roles/client/templates/compose.yaml.j2")
    assert 'name: "offsitebuddy-client-{{ job.name }}"' in client_compose
    assert "type: bind" in client_compose, "client volumes should use long-form bind mounts"
    for snippet in (
        "image: \"{{ offsitebuddy_tailscale_image }}\"",
        "TS_AUTHKEY: \"${TS_AUTHKEY}\"",
        "TS_HOSTNAME: \"{{ job.tailscale.hostname }}\"",
        "TS_USERSPACE: \"false\"",
        "./tailscale-state:/var/lib/tailscale",
        "/dev/net/tun:/dev/net/tun",
        "NET_ADMIN",
        "NET_RAW",
        "network_mode: service:tailscale",
    ):
        assert snippet in client_compose, "missing client Tailscale sidecar: %s" % snippet
    assert "job.repository is match('^/')" in client_compose, (
        "local repository paths must be mounted for e2e backup/restore"
    )

    client_defaults = read("roles/client/defaults/main.yml")
    assert "offsitebuddy_tailscale_image: tailscale/tailscale:stable" in client_defaults, (
        "client role must provide its own Tailscale image default"
    )

    server_compose = read("roles/server/templates/compose.yaml.j2")
    assert "friend.rest_server.port | default(8000) | int" in server_compose, (
        "server compose must render normalized integer ports"
    )

    restore_latest = read("roles/client/templates/restore-latest.sh.j2")
    assert "if [[ $# -ne 1 ]]; then" in restore_latest
    assert 'exec "$job_dir/restore.sh" --snapshot latest "$1"' in restore_latest
    assert '"$@"' not in restore_latest

    restore = read("roles/client/templates/restore.sh.j2")
    for snippet in (
        "Restore target must be an absolute path",
        "Restore target must not be /",
        "Restore target must not end with /",
        "Restore target must not overlap backup source",
        "Restore target must be an existing empty directory",
    ):
        assert snippet in restore, "missing restore target guard: %s" % snippet

    for snippet in ("--snapshot", "--include", "args=(restore", "--target", "--verbose=2"):
        assert snippet in restore
    assert "--target)" not in restore, "restore target CLI must remain positional"
    assert re.search(r"\beval\b", restore) is None

    e2e = read("tests/e2e-local.yml")
    for snippet in (
        "ansible_python_interpreter",
        "init_if_missing: true",
        "run_initial_backup: true",
        "snapshots.sh",
        "check.sh",
        "restore.sh",
        "restore-latest.sh",
        "proof.txt",
        "second-only.txt",
        "third-only.txt",
        "offsitebuddy_e2e_snapshot_list",
        "--json",
        "--snapshot",
        "--include",
    ):
        assert snippet in e2e, "missing e2e backup/restore check: %s" % snippet

    assert not (ROOT / ".superpowers/sdd/task-5-report.md").exists(), (
        "internal .superpowers report should not be tracked"
    )

    for role_dir in (ROOT / "roles").iterdir():
        if role_dir.is_dir():
            assert (role_dir / "README.md").exists(), (
                "Galaxy import requires role README: %s" % role_dir.name
            )

    galaxy = read("galaxy.yml")
    assert 'community.docker: ">=3.13.0"' in galaxy
    for ignored in (
        ".venv",
        ".uv-cache",
        "*.tar.gz",
        "**/.DS_Store",
        ".release-please-manifest.json",
        "release-please-config.json",
    ):
        assert ignored in galaxy, "collection build must ignore %s" % ignored

    assert '"include-component-in-tag": false' in release_please, (
        "release tags must be plain vX.Y.Z tags for the publish workflow"
    )
    assert '"type": "generic"' in release_please, (
        "release-please must update galaxy.yml without rewriting YAML formatting"
    )
    assert "x-release-please-version" in galaxy, (
        "galaxy.yml must mark the version line for release-please"
    )

    contributing = read("CONTRIBUTING.md")
    pr_template = read(".github/pull_request_template.md")
    requirements_dev = read("requirements-dev.yml")
    assert 'name: community.docker\n    version: ">=3.13.0"' in requirements_dev
    assert "ansible.posix" in requirements_dev, (
        "Molecule Docker create uses ansible.posix.synchronize"
    )
    for release_doc in (contributing, pr_template):
        assert "release-worthy" in release_doc, (
            "release docs should distinguish release-worthy PR titles"
        )
        assert "fix:" in release_doc and "feat:" in release_doc, (
            "release docs should name release-triggering prefixes"
        )
    for command in (
        "uv run --locked pre-commit run --all-files",
        "uv run molecule converge",
        "uv run molecule verify",
        "uv run ansible-playbook -i localhost, -c local tests/validation-negative.yml",
        "uv run ansible-playbook -i localhost, -c local tests/client-sidecar-render.yml",
        "uv run ansible-playbook -i localhost, -c local tests/e2e-local.yml",
    ):
        assert command in contributing, "CONTRIBUTING missing %s" % command
        assert command in pr_template, "PR template missing %s" % command

    dependabot = read(".github/dependabot.yml")
    assert "package-ecosystem: uv" in dependabot, (
        "Dependabot should track uv/Python dev deps"
    )

    print("review fix checks passed")


if __name__ == "__main__":
    main()
