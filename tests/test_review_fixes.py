#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


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
        "item.stat.exists",
        "item.stat.isdir",
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

    docs = read("docs/append-only-maintenance.md").lower()
    assert "does not enforce retention" in docs, "retention non-enforcement must be explicit"
    assert "manual maintenance" in docs, "manual retention maintenance must be explicit"

    server_compose = read("roles/server/templates/compose.yaml.j2")
    assert "TS_USERSPACE: \"false\"" in server_compose, "tailscale must use kernel networking"
    assert "devices:" in server_compose, "tailscale must map /dev/net/tun as a device"
    assert "NET_RAW" in server_compose, "tailscale should include NET_RAW capability"
    assert "type: bind" in server_compose, "server volumes should use long-form bind mounts"

    server_tasks = read("roles/server/tasks/rest_server.yml")
    assert "python3-passlib" in server_tasks, "server role must install passlib for htpasswd"
    assert ".offsitebuddy-managed" in server_tasks, "server role must mark managed stacks"
    assert "offsitebuddy_cleanup_stale" in server_tasks, "server role must support stale cleanup"
    assert "state: absent" in server_tasks, "server stale cleanup must stop old stacks"

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
    assert "tailscale must be running on the client host" in getting_started, (
        "client Tailscale prerequisite must be explicit"
    )
    assert "debian-family" in getting_started, "supported OS family must be explicit"
    assert "url-encoded" in getting_started, "REST URL credentials must be documented as URL-encoded"
    assert "ansible-galaxy collection install" in getting_started, (
        "collection installation path must be documented"
    )

    workflow = read(".github/workflows/ci.yml")
    expected_trigger = "  pull_request:\n  push:\n    branches:\n      - main"
    assert expected_trigger in workflow, (
        "CI should run on PRs and only on pushes to main"
    )
    assert "actions/checkout@v7" in workflow, (
        "CI checkout action should use a Node 24 runtime"
    )
    assert "actions/setup-python@v6" in workflow, (
        "CI setup-python action should use a Node 24 runtime"
    )
    assert "actions/checkout@v4" not in workflow
    assert "actions/setup-python@v5" not in workflow
    assert "tests/validation-negative.yml" in workflow, (
        "CI must reject unsafe validation inputs"
    )
    assert "tests/e2e-local.yml" in workflow, "CI must exercise local backup and restore"

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
        "docker compose --project-directory",
        "systemd-analyze verify",
        "TS_USERSPACE",
    ):
        assert snippet in verify, "missing Molecule artifact check: %s" % snippet

    client_tasks = read("roles/client/tasks/restic.yml")
    assert "(job_dir + '/backup.sh') | quote" in client_tasks, (
        "initial backup script path must be shell-quoted"
    )
    assert "marker_file | quote" in client_tasks, "initial backup marker path must be shell-quoted"
    assert ".offsitebuddy-managed" in client_tasks, "client role must mark managed jobs"
    assert "register: restic_init_result" in client_tasks, (
        "repository init must register stdout for changed_when"
    )
    assert "restic_init_result.stdout" in client_tasks, (
        "repository init changed_when must inspect registered stdout"
    )
    assert "no_log: true" in client_tasks.split("- name: Initialize missing restic repositories")[0], (
        "helper script templating must hide heartbeat URLs"
    )
    init_task = client_tasks.split(
        "- name: Initialize missing restic repositories", 1
    )[1].split("- name: Run initial backup", 1)[0]
    assert "no_log: true" in init_task, "repository init must hide repository URLs"

    client_systemd = read("roles/client/tasks/systemd.yml")
    assert "offsitebuddy_cleanup_stale" in client_systemd, "client role must support stale cleanup"
    assert "offsitebuddy-backup-{{ stale_job_name }}.timer" in client_systemd, (
        "stale backup timers must be stopped"
    )
    assert "state: absent" in client_systemd, "stale unit files must be removed"

    client_compose = read("roles/client/templates/compose.yaml.j2")
    assert "type: bind" in client_compose, "client volumes should use long-form bind mounts"
    assert "job.repository is match('^/')" in client_compose, (
        "local repository paths must be mounted for e2e backup/restore"
    )

    server_compose = read("roles/server/templates/compose.yaml.j2")
    assert "friend.rest_server.port | default(8000) | int" in server_compose, (
        "server compose must render normalized integer ports"
    )

    restore = read("roles/client/templates/restore-latest.sh.j2")
    for snippet in (
        "Restore target must be an absolute path",
        "Restore target must not be /",
        "Restore target must not end with /",
        "Restore target must not overlap backup source",
        "Restore target must be an existing empty directory",
    ):
        assert snippet in restore, "missing restore target guard: %s" % snippet

    e2e = read("tests/e2e-local.yml")
    for snippet in (
        "init_if_missing: true",
        "run_initial_backup: true",
        "snapshots.sh",
        "check.sh",
        "restore-latest.sh",
        "proof.txt",
    ):
        assert snippet in e2e, "missing e2e backup/restore check: %s" % snippet

    assert not (ROOT / ".superpowers/sdd/task-5-report.md").exists(), (
        "internal .superpowers report should not be tracked"
    )

    galaxy = read("galaxy.yml")
    for ignored in (
        ".venv",
        ".uv-cache",
        "*.tar.gz",
        "**/.DS_Store",
        ".release-please-manifest.json",
        "release-please-config.json",
    ):
        assert ignored in galaxy, "collection build must ignore %s" % ignored

    contributing = read("CONTRIBUTING.md")
    pr_template = read(".github/pull_request_template.md")
    for command in (
        "uv run --locked pre-commit run --all-files",
        "uv run molecule converge",
        "uv run molecule verify",
        "uv run ansible-playbook -i localhost, -c local tests/validation-negative.yml",
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
