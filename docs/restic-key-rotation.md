# Restic Repository-Key Rotation

Rotate one repository in one reviewed cutover window. The examples use client
job `photos_to_alice`, friend `alice`, `/etc/offsitebuddy/jobs`, and
`/srv/offsitebuddy`. Substitute the configured roots and every matching host;
do not combine repositories or friends in one window.

This changes only the password-wrapped repository master key. It does not
re-encrypt repository data. Keep the existing
`offsitebuddy_client_jobs[*].password` value authoritative: do not add a
second password variable, encoded value, helper, or automation.

## Cutover window

### Inventory and pause writers

Identify every backup and check job that uses this repository, including jobs
on other hosts. Record every matching timer's original host and enabled state,
and retain the old raw Vault value in protected rollback storage. Do not print,
paste, or put either password in a command, environment variable, log, shell
history, or repository URL.

Pause every matching job on its original host. Run the check-timer commands
only where a check unit exists. Disabling a timer does not stop a running
service, so wait for both services to be inactive and keep all writers paused
through every convergence and gate:

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

If any timer cannot be paused or service cannot become inactive, stop. Leave
every affected timer disabled and service inactive until the window is
resolved.

### Preflight

From a controlled matching client, record a fresh private restore target, list
snapshots, check the repository, and inspect a representative restore. Keep
the target for comparison until the reviewed rollback window closes. A failed
restore needs a different `mktemp -d` target; never reuse a partial target.

```sh
preflight_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-key-preflight.XXXXXX)"
sudo chmod 700 "$preflight_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/snapshots.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$preflight_restore"
```

### Add and prove the new key

Create a root-owned mode `0600` temporary password file without putting its
contents in shell history, arguments, environment variables, or logs. Type the
new password only at the hidden prompt; record the resulting file path in the
window notes.

```sh
rotation_new_password_file="$(sudo mktemp /root/offsitebuddy-restic-photos-to-alice-new-password.XXXXXX)"
sudo bash -c '
  set -e
  IFS= read -r -s -p "New repository password: " password
  printf "\n" >&2
  printf "%s\n" "$password" > "$1"
' bash "$rotation_new_password_file"
sudo chmod 600 "$rotation_new_password_file"
sudo test "$(sudo stat -c '%a:%U' "$rotation_new_password_file")" = '600:root'
```

While the old rendered job password is still authoritative, list the keys and
record the ID marked current as the exact `rotation_old_key_id`. Do not choose
a key by list position. Then add the new password using only the protected
file:

```bash
sudo docker compose \
  --project-name offsitebuddy-client-photos_to_alice \
  --project-directory /etc/offsitebuddy/jobs/photos_to_alice \
  -f /etc/offsitebuddy/jobs/photos_to_alice/compose.yaml \
  run --rm restic --json key list

sudo docker compose \
  --project-name offsitebuddy-client-photos_to_alice \
  --project-directory /etc/offsitebuddy/jobs/photos_to_alice \
  -f /etc/offsitebuddy/jobs/photos_to_alice/compose.yaml \
  run --rm \
  -v "$rotation_new_password_file:/run/secrets/restic-new-password:ro" \
  restic key add \
  --new-password-file /run/secrets/restic-new-password

sudo docker compose \
  --project-name offsitebuddy-client-photos_to_alice \
  --project-directory /etc/offsitebuddy/jobs/photos_to_alice \
  -f /etc/offsitebuddy/jobs/photos_to_alice/compose.yaml \
  run --rm restic --json key list
```

From the post-add command's JSON, confirm exactly two distinct IDs, confirm
the saved `rotation_old_key_id` is still current, and save the other exact ID
as `rotation_new_key_id`. Before changing Vault, prove the new file opens the
same repository:

```sh
sudo docker compose \
  --project-name offsitebuddy-client-photos_to_alice \
  --project-directory /etc/offsitebuddy/jobs/photos_to_alice \
  -f /etc/offsitebuddy/jobs/photos_to_alice/compose.yaml \
  run --rm \
  -v "$rotation_new_password_file:/run/secrets/restic-new-password:ro" \
  restic --password-file /run/secrets/restic-new-password snapshots
```

If adding or proving the key fails, leave writers paused and retain the old
Vault value. Do not change the rendered job password or delete the temporary
file until the failure is reviewed.

### Change Vault and converge safely

Update only the existing Vault value that feeds
`offsitebuddy_client_jobs[*].password` for every affected client. Keep
password-bearing Ansible tasks under `no_log: true`. While every writer remains
paused, converge every affected client with both variables explicitly set:

```yaml
offsitebuddy_start_services: false
offsitebuddy_cleanup_stale: false
```

After each convergence, verify the recorded backup/check timers remain
disabled and their services inactive. Do not resume them yet:

```sh
sudo systemctl is-enabled offsitebuddy-backup-photos_to_alice.timer
sudo systemctl is-enabled offsitebuddy-check-photos_to_alice.timer
sudo systemctl is-active offsitebuddy-backup-photos_to_alice.service
sudo systemctl is-active offsitebuddy-check-photos_to_alice.service
```

Stop if any writer is enabled or active. The generated client password file is
now the new rendered password; do not pass it to Compose or restic directly.

### Forward gates and timer resumption

Run a new snapshots/check/backup/restore sequence from a controlled matching
client. Record the fresh target and inspect the restored data. Do not retry a
failed restore in this or any earlier target.

```sh
cutover_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-key-cutover.XXXXXX)"
sudo chmod 700 "$cutover_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/snapshots.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/backup.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$cutover_restore"
```

Keep `rotation_old_key_id` through the reviewed rollback window; do not remove
it during cutover. If all gates and restore inspection pass, resume only the
timers recorded as enabled before the window, on their original hosts.
Previously disabled timers remain disabled:

```sh
sudo systemctl enable --now offsitebuddy-backup-photos_to_alice.timer
sudo systemctl enable --now offsitebuddy-check-photos_to_alice.timer
```

When the reviewed rollback window closes, securely delete only the exact
temporary password file and recorded cutover-window restore targets. Do not use
globs, delete a parent directory, or automate this closeout:

```sh
sudo shred --remove --zero -- "$rotation_new_password_file"
sudo rm -rf -- "$preflight_restore" "$cutover_restore"
```

## Rollback

Rollback is a separate decision during the rollback window. Pause every writer
again and wait for its in-flight services to be inactive, using the same
inventory and pause sequence above. Restore only the protected old Vault value
for `offsitebuddy_client_jobs[*].password`, then converge every affected client
with both safe variables:

```yaml
offsitebuddy_start_services: false
offsitebuddy_cleanup_stale: false
```

Verify every writer remains disabled and inactive. Run the same snapshots,
check, backup, and inspected restore gates in a new private target before any
timer is resumed:

```sh
rollback_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-key-rollback.XXXXXX)"
sudo chmod 700 "$rollback_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/snapshots.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/backup.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$rollback_restore"
```

After inspecting the restored data and passing all gates, resume only the
timers previously recorded as enabled. Leave the existing old key in place:
it is now the rendered current key. Remove only the exact recorded rollback
restore target after the reviewed rollback window closes:

```sh
sudo rm -rf -- "$rollback_restore"
```

If a rollback gate fails, leave writers paused and use a new private target
for every restore retry. Never retire a key until a later, separately reviewed
maintenance window has completed.

## Old-key retirement window

Retirement is separate from both cutover and rollback. Schedule a new reviewed
maintenance window only after the new Vault value is current. First inventory
and pause every writer again, preserve each timer's prior enabled state, wait
for every matching service to be inactive, and keep writers paused through all
gates.

From a controlled client using the new rendered password, run a successful
check and inspect a fresh representative restore before opening maintenance:

```sh
retirement_preflight_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-key-retirement-preflight.XXXXXX)"
sudo chmod 700 "$retirement_preflight_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$retirement_preflight_restore"
```

Confirm `rotation_old_key_id` is present and is not the ID marked current.
Use the exact ID saved during cutover; do not derive an ID from list position:

```sh
sudo docker compose \
  --project-name offsitebuddy-client-photos_to_alice \
  --project-directory /etc/offsitebuddy/jobs/photos_to_alice \
  -f /etc/offsitebuddy/jobs/photos_to_alice/compose.yaml \
  run --rm restic --json key list
```

For an append-only REST repository, open only Alice's existing maintenance
endpoint on the server and keep that terminal open. It temporarily exposes the
read-write endpoint and restores append-only operation when it closes:

```sh
sudo /srv/offsitebuddy/friends/alice/maintenance-endpoint.sh
```

While that terminal remains open, remove only the saved non-current key ID
from the controlled client. The generated password remains the new rendered
password, so no password is placed in this command:

```sh
sudo docker compose \
  --project-name offsitebuddy-client-photos_to_alice \
  --project-directory /etc/offsitebuddy/jobs/photos_to_alice \
  -f /etc/offsitebuddy/jobs/photos_to_alice/compose.yaml \
  run --rm restic key remove "$rotation_old_key_id"
```

Return to the helper terminal and press Enter. Before resuming any timers,
require the same append-only closeout gates used for retention: the maintenance
project and its network are absent, the ordinary `offsitebuddy-friend-alice`
project is running, and its `rest-server` `OPTIONS` includes `--append-only`.
If the helper cannot restore the ordinary stack, keep writers paused and use
the failure handling in [append-only maintenance](append-only-maintenance.md).

```sh
if sudo docker ps -aq \
  --filter "label=com.docker.compose.project=offsitebuddy-maintenance-friend-alice" | grep -q .; then
  echo "maintenance project is still present" >&2
  exit 1
fi
if sudo docker network ls --quiet \
  --filter "label=com.docker.compose.project=offsitebuddy-maintenance-friend-alice" | grep -q .; then
  echo "maintenance project network is still present" >&2
  exit 1
fi
ordinary_rest_server="$(sudo docker ps -q \
  --filter "label=com.docker.compose.project=offsitebuddy-friend-alice" \
  --filter "label=com.docker.compose.service=rest-server")"
test -n "$ordinary_rest_server"
sudo docker inspect --format '{{.State.Running}}' "$ordinary_rest_server" | grep -Fx true
sudo docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' \
  "$ordinary_rest_server" | grep '^OPTIONS=.*--append-only'
```

Run final ordinary-operation gates into another fresh target and inspect the
restored data:

```sh
retirement_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-key-retirement.XXXXXX)"
sudo chmod 700 "$retirement_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/backup.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$retirement_restore"
```

After all closeout, check, backup, and restore gates pass, resume only timers
recorded as enabled before this retirement window. Securely remove only the
two exact recorded retirement targets after inspection; do not use globs or
automate retirement cleanup:

```sh
sudo rm -rf -- "$retirement_preflight_restore" "$retirement_restore"
```

If any retirement gate fails, keep writers paused. Do not retry a restore in a
partial target or remove another key. Reopen and review the saved
`rotation_old_key_id`, the current-key evidence, and the maintenance closeout
before continuing.
