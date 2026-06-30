# Restore Test

Run a restore test after the first backup:

```bash
sudo /etc/offsitebuddy/jobs/photos_to_bob/snapshots.sh
sudo mkdir -p /tmp/offsitebuddy-restore-test
sudo /etc/offsitebuddy/jobs/photos_to_bob/restore-latest.sh /tmp/offsitebuddy-restore-test
```

Open files from the restore target and confirm the data you care about is present.
