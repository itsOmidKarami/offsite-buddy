# Quota-Full Recovery

Set `enforced: true` only after the storage administrator has enabled a hard
quota outside OffsiteBuddy. This is an administrative assertion; the role
checks the existing path and write probe, not the storage provider's policy.

## Detect the failure

A failed backup followed by its configured failure heartbeat is the normal
signal to investigate. Treat an `ENOSPC` or "no space left" error as capacity
exhaustion. Authentication failures and network failures need credential or
connectivity recovery instead; do not use either capacity path for them.

Before recovery, pause the affected writer and run the generated `restic
check` job. Preserve the failed backup output and confirm which repository is
full.

## Recover capacity

Choose one path for the affected repository:

1. Increase quota or underlying storage capacity using the storage provider's
   administrative interface. Then run `restic check`, run a backup, and make a
   restore proof with the generated restore helper.
2. If the reviewed retention policy allows it, follow the
   [append-only maintenance workflow](append-only-maintenance.md). It pauses
   writers, opens a controlled maintenance window, runs the reviewed prune,
   restores append-only operation, then requires `restic check`, backup, and
   restore proof before timers resume.

There is no direct repository deletion as a recovery path. Do not delete
repository files directly, and do not enable automatic pruning. The existing
append-only maintenance workflow is the only supported retention path.
