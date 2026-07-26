# REST Server Credential Rotation

Rotate one friend's REST credential in a reviewed maintenance window. The
examples use friend `alice`, client job `photos_to_alice`,
`/srv/offsitebuddy`, and `/etc/offsitebuddy/jobs`. Substitute the configured
`offsitebuddy_server_root`, `offsitebuddy_client_root`, and every matching
host before proceeding. Do not combine unrelated friends or repositories in
one window, and do not put a raw or encoded credential in an operator command.

## Inventory and pause

Record every backup and check job that uses Alice's repository, including jobs on other hosts,
plus whether each backup/check timer is enabled. Keep the old raw Vault value
in protected rollback storage. The old secret is rollback-only:
do not print it, paste it into a command, or copy it into a repository URL.

Disable and stop every matching timer on its original host, then wait for each
in-flight service to become inactive. Repeat this exact pause/wait sequence
for every matching job; run the check-unit lines only when that job has a
generated check unit:

```sh
sudo systemctl disable --now offsitebuddy-backup-photos_to_alice.timer
sudo systemctl disable --now offsitebuddy-check-photos_to_alice.timer
while sudo systemctl is-active --quiet offsitebuddy-backup-photos_to_alice.service; do
  sleep 5
done
while sudo systemctl is-active --quiet offsitebuddy-check-photos_to_alice.service; do
  sleep 5
done
```

If any timer cannot be paused or service cannot become inactive, stop. Keep
every affected timer disabled and service inactive until the window is
resolved.

## Safe convergence contract

Every server and matching client convergence in both cutover and rollback
must explicitly use these role variables. Do not rely on role defaults, which
can start the server stack or re-enable client timers:

```yaml
offsitebuddy_start_services: false
offsitebuddy_cleanup_stale: false
```

Verify writers remain paused after every convergence on every matching client
host. Each timer must report `disabled`, and each service must report
`inactive`; run the check-unit lines only for jobs with a generated check unit:

```sh
sudo systemctl is-enabled offsitebuddy-backup-photos_to_alice.timer
sudo systemctl is-enabled offsitebuddy-check-photos_to_alice.timer
sudo systemctl is-active offsitebuddy-backup-photos_to_alice.service
sudo systemctl is-active offsitebuddy-check-photos_to_alice.service
```

Stop if any writer is enabled or active. Convergence only rewrites managed
state during this window; the explicit server `rest-server` restart below is
the only service lifecycle action before all gates pass.

## Preflight

From a controlled matching client, prove the current repository still works.
Use a new private target, record its exact path and host in the window notes,
and retain it for comparison until the window closes:

```sh
preflight_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-preflight.XXXXXX)"
sudo chmod 700 "$preflight_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/snapshots.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$preflight_restore"
```

Inspect the restored files. If a gate fails, do not continue. Never retry a
restore into a partial target; create another private `mktemp -d` directory.

## Cutover

1. Update only Alice's raw `rest_server.password` Vault value. Derive every
   matching client's repository URL inline from that same raw Vault value with
   `urlencode | replace('/', '%2F')`; do not store a second encoded secret or
   paste an encoded password into Vault. Keep all Ansible tasks that handle
   either raw or derived credential form under `no_log: true`.
2. On Alice's server host, converge the server role with both safe convergence
   variables above. Then restart only `rest-server` so it deterministically
   reloads its credentials without restarting Tailscale:

   ```sh
   sudo docker compose --project-name offsitebuddy-friend-alice \
     --project-directory /srv/offsitebuddy/friends/alice \
     -f /srv/offsitebuddy/friends/alice/compose.yaml restart rest-server
   ```

3. Converge every matching client host with the newly derived repository URL
   and both safe convergence variables above. Re-run the paused-writer checks
   on every matching client before any gate.

### Forward client-side gates

On one controlled matching client, run fresh authentication, check, backup,
and restore gates in a second private target. Record the target's exact path
and host:

```sh
cutover_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-cutover.XXXXXX)"
sudo chmod 700 "$cutover_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/snapshots.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/backup.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$cutover_restore"
```

Inspect the restored files. On failure, leave all affected timers disabled
and services inactive; use a new private target for another restore attempt.

### Forward server-side runtime check

On Alice's server host, confirm the ordinary server project is running:

```sh
sudo docker compose --project-name offsitebuddy-friend-alice \
  --project-directory /srv/offsitebuddy/friends/alice \
  -f /srv/offsitebuddy/friends/alice/compose.yaml ps
```

## Resume and retention

After every gate passes, resume only the backup/check timers recorded as
previously enabled. Leave previously disabled timers disabled. Retain the old
secret only until the reviewed rollback window closes, then delete that
protected rollback copy.

```sh
sudo systemctl enable --now offsitebuddy-backup-photos_to_alice.timer
sudo systemctl enable --now offsitebuddy-check-photos_to_alice.timer
```

Repeat the applicable command on the original host for each matching timer;
the commands are examples, not permission to enable a timer that was disabled
before the window.

## Recorded private restore targets

After the restored data has been inspected and the success window closes,
remove only the exact recorded private restore targets on their original host.
Never use a glob or remove their parent `/tmp` directory:

```sh
sudo rm -rf -- "$preflight_restore" "$cutover_restore"
```

## Rollback

Perform rollback as the reverse cutover while all writers remain paused:

1. Restore Alice's old server Vault value. On Alice's server host, converge the
   server role with `offsitebuddy_start_services: false` and
   `offsitebuddy_cleanup_stale: false`.
2. On Alice's server host, restart only `rest-server`; do not restart Tailscale:

   ```sh
   sudo docker compose --project-name offsitebuddy-friend-alice \
     --project-directory /srv/offsitebuddy/friends/alice \
     -f /srv/offsitebuddy/friends/alice/compose.yaml restart rest-server
   ```

3. Restore every matching client's old Vault-derived repository value and
   converge every matching client host with `offsitebuddy_start_services:
   false` and `offsitebuddy_cleanup_stale: false`. Keep raw and derived
   credential values under `no_log: true`, then verify every writer remains
   paused.

### Rollback client-side gates

On one controlled matching client, rerun authentication, `snapshots.sh`,
`check.sh`, `backup.sh`, and a fresh `restore-latest.sh` gate. Record and
inspect the new private target:

```sh
rollback_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-rollback.XXXXXX)"
sudo chmod 700 "$rollback_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/snapshots.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/backup.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$rollback_restore"
```

### Rollback server-side runtime check

On Alice's server host, confirm the ordinary server project is running:

```sh
sudo docker compose --project-name offsitebuddy-friend-alice \
  --project-directory /srv/offsitebuddy/friends/alice \
  -f /srv/offsitebuddy/friends/alice/compose.yaml ps
```

After every rollback gate passes, resume only the timers recorded as previously
enabled, on their original hosts. Leave previously disabled timers disabled.
After inspecting the rollback restore and closing the rollback window, remove
only that exact recorded target on its original host:

```sh
sudo rm -rf -- "$rollback_restore"
```

If any rollback gate fails, keep every affected timer disabled and every
service inactive. Never reuse a partial restore target.
