# Append-Only Maintenance

OffsiteBuddy does not enforce retention. It keeps the normal rest-server
append-only. Retention is manual maintenance: use one approved window for one
friend and its matching client job. Do not schedule an automatic prune.

The commands use friend `alice`, client job `photos_to_alice`, and the default
roots `/srv/offsitebuddy` and `/etc/offsitebuddy/jobs`. Substitute the one
reviewed friend/job pair and the configured `offsitebuddy_server_root` and
`offsitebuddy_client_root`; do not combine friends or jobs in one window.

## Preflight

Pause the selected job's writers. Run the check-unit lines only when that job
has a generated check unit. Disabling a timer does not stop an in-flight
service, so wait until both services are inactive before continuing:

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

Run a fresh preflight check and representative restore. `mktemp -d` creates a
new private target; record `$preflight_restore`, inspect the restored files,
and keep it for comparison until the window is complete:

```sh
preflight_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-preflight.XXXXXX)"
sudo chmod 700 "$preflight_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$preflight_restore"
sudo docker compose --project-directory /srv/offsitebuddy/friends/alice \
  -f /srv/offsitebuddy/friends/alice/compose.yaml ps
```

## Policy preview

From the controlled client, preview the exact snapshots affected by the
reviewed policy. Prefer `--keep-within*` policies for an append-only threat
model, for example:

```sh
sudo docker compose --project-directory /etc/offsitebuddy/jobs/photos_to_alice \
  run --rm restic forget --dry-run --keep-within 90d
```

A human must review the exact snapshot set printed by this command before any
prune. Adjust the reviewed retention duration before proceeding; do not add an
unreviewed policy to the prune command.

## Maintenance and prune

The helper removes itself after a successful window. If it is absent, rerun
normal server convergence for the selected friend before continuing. On the
server, open only that friend's helper and keep this terminal open:

```sh
sudo /srv/offsitebuddy/friends/alice/maintenance-endpoint.sh
```

While that terminal remains open, run the reviewed command from the controlled
client. This uses the generated client password file; never copy a repository
password to the server:

```sh
sudo docker compose --project-directory /etc/offsitebuddy/jobs/photos_to_alice \
  run --rm restic forget --prune --keep-within 90d
```

## Restore append-only operation

Return to the helper terminal and press Enter. Do not resume timers until the
maintenance project is absent, the ordinary project is running, and the
running ordinary rest-server `OPTIONS` includes `--append-only`:

```sh
if sudo docker ps -aq \
  --filter "label=com.docker.compose.project=offsitebuddy-maintenance-friend-alice" | grep -q .; then
  echo "maintenance project is still present" >&2
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

Run another check and restore into a different fresh private target. Do not
retry a failed restore into either existing directory: create a new `mktemp`
target, inspect it after success, and clean up only the recorded target:

```sh
post_prune_restore="$(sudo mktemp -d /tmp/offsitebuddy-restore-photos-to-alice-post-prune.XXXXXX)"
sudo chmod 700 "$post_prune_restore"
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh "$post_prune_restore"
# Inspect "$post_prune_restore", then remove only the recorded restore targets.
sudo rm -rf -- "$preflight_restore" "$post_prune_restore"
```

Resume the selected job's backup timer, and its configured check timer, only
after the runtime, `restic check`, and representative `restore-latest.sh`
gates succeed:

```sh
sudo systemctl enable --now offsitebuddy-backup-photos_to_alice.timer
sudo systemctl enable --now offsitebuddy-check-photos_to_alice.timer
```

## Failure handling

If the helper cannot restore the ordinary stack automatically, keep both
selected timers disabled and both services inactive. If a prior helper removed
the target maintenance artifacts, rerun normal server convergence for the
selected friend to recreate them. Inspect both projects, take down the exact
maintenance project, then start the ordinary project:

```sh
sudo docker ps -a \
  --filter "label=com.docker.compose.project=offsitebuddy-maintenance-friend-alice"
sudo docker ps -a \
  --filter "label=com.docker.compose.project=offsitebuddy-friend-alice"
sudo docker compose --project-directory /srv/offsitebuddy/friends/alice \
  -f /srv/offsitebuddy/friends/alice/compose.maintenance.yaml down --remove-orphans
sudo docker compose --project-directory /srv/offsitebuddy/friends/alice \
  -f /srv/offsitebuddy/friends/alice/compose.yaml up -d
```

Repeat the maintenance-absence, ordinary-running, runtime `OPTIONS`,
`check.sh`, and fresh post-prune `restore-latest.sh` gates above before
resuming either timer. If any gate fails, leave writers paused and use a new
private `mktemp` directory for every restore retry; never reuse a partial
restore target.
