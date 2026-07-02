#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def main():
    backup = read("roles/client/templates/backup.sh.j2")
    for field in ("start", "success", "failure"):
        expected = (
            "ping_url {{ job.heartbeat.%s_url | default('') | quote }} \"%s\""
            % (field, field)
        )
        assert expected in backup, "heartbeat %s URL must be shell-quoted" % field

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
    ):
        assert snippet in validate, "missing client validation: %s" % snippet

    docs = read("docs/append-only-maintenance.md").lower()
    assert "does not enforce retention" in docs, "retention non-enforcement must be explicit"
    assert "manual maintenance" in docs, "manual retention maintenance must be explicit"

    server_compose = read("roles/server/templates/compose.yaml.j2")
    assert "TS_USERSPACE: \"false\"" in server_compose, "tailscale must use kernel networking"
    assert "devices:" in server_compose, "tailscale must map /dev/net/tun as a device"
    assert "NET_RAW" in server_compose, "tailscale should include NET_RAW capability"

    server_tasks = read("roles/server/tasks/rest_server.yml")
    assert "python3-passlib" in server_tasks, "server role must install passlib for htpasswd"

    server_validate = read("roles/server/tasks/validate.yml")
    assert "offsitebuddy_friends | map(attribute='name')" in server_validate, "server friend names must be unique"
    assert "map(attribute='quota.path')" in server_validate, "server quota paths must be unique"
    assert "map(attribute='tailscale.hostname')" in server_validate, "server hostnames must be unique"

    getting_started = read("docs/getting-started.md").lower()
    assert "tailscale must be running on the client host" in getting_started, (
        "client Tailscale prerequisite must be explicit"
    )
    assert "debian-family" in getting_started, "supported OS family must be explicit"

    verify = read("molecule/default/verify.yml")
    for snippet in (
        "bash -n",
        "from_yaml",
        "docker compose --project-directory",
        "systemd-analyze verify",
        "TS_USERSPACE",
    ):
        assert snippet in verify, "missing Molecule artifact check: %s" % snippet

    assert not (ROOT / ".superpowers/sdd/task-5-report.md").exists(), (
        "internal .superpowers report should not be tracked"
    )

    print("review fix checks passed")


if __name__ == "__main__":
    main()
