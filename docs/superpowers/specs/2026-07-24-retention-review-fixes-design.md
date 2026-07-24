# Retention Review Fixes Design

## Goal

Keep append-only maintenance fail-closed when Docker state changes outside the
helper, while preserving the existing manual prune workflow.

## Design

Before the server role writes or removes maintenance files, inspect Docker for
each configured friend's exact maintenance Compose project identity. Refuse
convergence if any matching containers or networks exist. This prevents mode
transitions and ordinary convergence from changing recovery files during an
active or foreign maintenance project.

Immediately before the helper stops the ordinary append-only project, repeat
the exact Docker identity check. Refuse to start when that identity already
exists, closing the gap between Ansible convergence and operator invocation.
Neither guard automatically removes Docker resources.

Maintenance containers use no automatic restart policy. During helper cleanup,
ignore termination signals until the maintenance project is down and the
ordinary append-only project is restored. Preserve the existing error ordering
and recovery files when either operation fails.

The runbook requires pausing every backup and check job that targets the
repository, including jobs on other hosts, before policy preview or prune.

## Verification

Extend the existing helper harness to prove that an exact-identity collision is
refused and that a signal delivered during cleanup cannot interrupt ordinary
project restoration. Reuse the existing maintenance identity-shadow Molecule
fixture without a managed marker so it exercises the Docker-state guard rather
than the marker guard. Keep focused static assertions for restart policy,
preflight ordering, and runbook wording, then run the repository's existing
validation suite.
