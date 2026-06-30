# UGOS Shared Folder Quotas

For v0.1, use UGOS to create a shared folder with a quota for each friend.

Then configure that path as `existing_path`:

```yaml
quota:
  backend: existing_path
  path: /mnt/ugos-shares/alice-offsite-backup
  size: 2T
  enforced: true
  enforcement_note: "UGOS shared folder quota set to 2 TB."
```

OffsiteBuddy verifies the path exists and is writable. It cannot prove the UGOS UI quota is active, so `enforced: true` is an explicit admin assertion.
