#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def require(condition, message, failures):
    if not condition:
        failures.append(message)


def main():
    failures = []

    backup = read("roles/client/templates/backup.sh.j2")
    for field in ("start", "success", "failure"):
        require(
            "ping_url {{ job.heartbeat.%s_url | default('') | quote }} \"%s\""
            % (field, field)
            in backup,
            "heartbeat %s URL must be shell-quoted" % field,
            failures,
        )

    validate = read("roles/client/tasks/validate.yml")
    for snippet in (
        "regex_search('^([01][0-9]|2[0-3]):[0-5][0-9]$')",
        "item.backup_paths | type_debug == 'list'",
        "select('match', '^/')",
        "map(attribute='name')",
        "unique",
    ):
        require(snippet in validate, "missing client validation: %s" % snippet, failures)

    docs = read("docs/append-only-maintenance.md").lower()
    require("retention is metadata only" in docs, "retention must be documented as metadata-only", failures)
    require("does not enforce retention" in docs, "retention non-enforcement must be explicit", failures)

    server_compose = read("roles/server/templates/compose.yaml.j2")
    require("TS_USERSPACE: \"false\"" in server_compose, "tailscale must use kernel networking", failures)
    require("devices:" in server_compose, "tailscale must map /dev/net/tun as a device", failures)
    require("NET_RAW" in server_compose, "tailscale should include NET_RAW capability", failures)

    server_tasks = read("roles/server/tasks/rest_server.yml")
    require("python3-passlib" in server_tasks, "server role must install passlib for htpasswd", failures)

    server_validate = read("roles/server/tasks/validate.yml")
    require("offsitebuddy_friends | map(attribute='name')" in server_validate, "server friend names must be unique", failures)

    verify = read("molecule/default/verify.yml")
    for snippet in (
        "bash -n",
        "from_yaml",
        "docker compose --project-directory",
        "systemd-analyze verify",
        "TS_USERSPACE",
    ):
        require(snippet in verify, "missing Molecule artifact check: %s" % snippet, failures)

    require(
        not (ROOT / ".superpowers/sdd/task-5-report.md").exists(),
        "internal .superpowers report should not be tracked",
        failures,
    )

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        raise SystemExit(1)

    print("review fix checks passed")


if __name__ == "__main__":
    main()
