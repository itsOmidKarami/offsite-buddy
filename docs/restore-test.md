# Restore Test

For a `photos_to_bob` job, list the available snapshots first:

```bash
sudo /etc/offsitebuddy/jobs/photos_to_bob/snapshots.sh
```

Restore an older snapshot into an existing, empty target:

```bash
sudo mkdir -p /tmp/offsitebuddy-restore-old
sudo /etc/offsitebuddy/jobs/photos_to_bob/restore.sh \
  --snapshot e78ad23c /tmp/offsitebuddy-restore-old
```

To restore only configured backup paths or descendants, repeat `--include`:

```bash
sudo mkdir -p /tmp/offsitebuddy-restore-selective
sudo /etc/offsitebuddy/jobs/photos_to_bob/restore.sh \
  --snapshot latest \
  --include /srv/photos/2026 \
  --include /srv/photos/catalog.json \
  /tmp/offsitebuddy-restore-selective
```

The compatible wrapper still restores the latest snapshot:

```bash
sudo mkdir -p /tmp/offsitebuddy-restore-latest
sudo /etc/offsitebuddy/jobs/photos_to_bob/restore-latest.sh \
  /tmp/offsitebuddy-restore-latest
```

Every restore target must already exist and be empty. OffsiteBuddy does not
delete a target after a failed or interrupted restore; inspect and empty it
before retrying. Open the restored files and confirm the data you need is
present.
