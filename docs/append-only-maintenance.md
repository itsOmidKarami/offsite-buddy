# Append-Only Maintenance

v0.1 keeps rest-server append-only by default.

OffsiteBuddy does not enforce retention automatically while rest-server stays
append-only. Choose the retention target during manual maintenance.

Do not schedule automatic destructive prune. Use an admin maintenance window:

1. Confirm the retention intent.
2. Stop the friend stack.
3. Start a temporary non-append-only maintenance endpoint or run restic against the repository from a controlled admin environment.
4. Run `restic forget --prune`.
5. Start the append-only friend stack again.
6. Run `restic check`.
