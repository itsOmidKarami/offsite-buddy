# Append-Only Maintenance

OffsiteBuddy does not enforce retention. It keeps the normal rest-server
append-only. Retention is manual maintenance: use one approved window for one
friend and its matching client job. Do not schedule an automatic prune.

The commands below use friend `alice` and client job `photos_to_alice`. Replace
both names with the one reviewed pair; do not combine friends or jobs in a
maintenance window.

## Preflight

Pause the selected job's writers before changing retention. Pause its optional
check timer too when it is configured:

```sh
sudo systemctl disable --now offsitebuddy-backup-photos_to_alice.timer
sudo systemctl disable --now offsitebuddy-check-photos_to_alice.timer
```

Confirm the latest completed `check.sh` and a representative
`restore-latest.sh` are recorded as successful. Record the current
append-only server container state before opening the window:

```sh
sudo journalctl --unit offsitebuddy-check-photos_to_alice.service --no-pager
sudo docker compose --project-directory /srv/offsitebuddy/friends/alice \
  -f compose.yaml ps
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

The helper removes itself after every window. If it is absent, rerun normal
server convergence for the selected friend before continuing. On the server,
open only that friend's helper and keep this terminal open:

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

Return to the helper terminal and press Enter. It closes the maintenance
endpoint and restores the ordinary stack. Confirm the ordinary Compose file
contains `--append-only`, then run `restic check` through the selected job and
perform a representative latest restore into an existing empty directory:

```sh
sudo docker compose --project-directory /srv/offsitebuddy/friends/alice \
  -f compose.yaml config | grep -- --append-only
sudo /etc/offsitebuddy/jobs/photos_to_alice/check.sh
sudo mkdir -p /tmp/offsitebuddy-restore-photos-to-alice
sudo /etc/offsitebuddy/jobs/photos_to_alice/restore-latest.sh \
  /tmp/offsitebuddy-restore-photos-to-alice
```

Resume the selected job's backup timer, and its configured check timer, only
after both `restic check` and `restore-latest.sh` succeed:

```sh
sudo systemctl enable --now offsitebuddy-backup-photos_to_alice.timer
sudo systemctl enable --now offsitebuddy-check-photos_to_alice.timer
```

## Failure handling

If the helper cannot restore the ordinary stack automatically, keep the
selected job's writers paused. Inspect both Compose projects, restore the
ordinary stack explicitly, and rerun the check and representative restore
above before resuming either timer:

```sh
sudo docker ps -a \
  --filter label=com.docker.compose.project=offsitebuddy-friend-alice-maintenance
sudo docker ps -a \
  --filter label=com.docker.compose.project=offsitebuddy-friend-alice
sudo docker compose --project-directory /srv/offsitebuddy/friends/alice \
  -f compose.yaml up -d
```

If either verification fails, leave the timers disabled and investigate the
selected friend and job; do not reopen writers to an unchecked repository.
