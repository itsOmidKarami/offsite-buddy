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

## Preflight

From a controlled matching client, prove the current repository still works.
Use a new private target and retain it for comparison until the window closes:

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
   matching client's repository URL from that same raw Vault value with `urlencode`;
   do not paste an encoded password into Vault. Keep all Ansible tasks that
   handle either raw or derived credential form under `no_log: true`.
2. Apply the server role for Alice. Then restart rest-server so it deterministically
   reloads its credentials without restarting Tailscale:

   ```sh
   sudo docker compose --project-name offsitebuddy-friend-alice \
     --project-directory /srv/offsitebuddy/friends/alice \
     -f /srv/offsitebuddy/friends/alice/compose.yaml restart rest-server
   ```

3. Apply every matching client host with the newly derived repository URL.
4. On one controlled client, run fresh authentication, check, backup, and
   restore gates in a second private target. Confirm the ordinary server
   project is running:

   ```sh
   cutover_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-cutover.XXXXXX)"
   sudo chmod 700 "$cutover_restore"
   sudo /etc/offsitebuddy/jobs/photos_to_alice/snapshots.sh
   sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
   sudo /etc/offsitebuddy/jobs/photos_to_alice/backup.sh
   sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$cutover_restore"
   sudo docker compose --project-name offsitebuddy-friend-alice \
     --project-directory /srv/offsitebuddy/friends/alice \
     -f /srv/offsitebuddy/friends/alice/compose.yaml ps
   ```

   Inspect the restored files. On failure, leave all affected timers disabled
   and services inactive; use a new private target for another restore attempt.

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

## Rollback

Perform rollback as the reverse cutover while all writers remain paused:

1. Restore Alice's old server Vault value and converge the server role.
2. Restart only `rest-server` with the same explicit `offsitebuddy-friend-alice`
   project name and `/srv/offsitebuddy/friends/alice` project directory command
   above; do not restart Tailscale.
3. Restore every matching client's old Vault-derived repository value and
   converge every matching client host. Keep raw and derived credential values
   under `no_log: true`.
4. Rerun the same authentication, `snapshots.sh`, `check.sh`, `backup.sh`, and
   fresh `restore-latest.sh` gates. Inspect the fresh restore and confirm the
   ordinary server project is running.
5. Resume only the timers that were previously enabled.

If any rollback gate fails, keep every affected timer disabled and every
service inactive. Never reuse a partial restore target.
