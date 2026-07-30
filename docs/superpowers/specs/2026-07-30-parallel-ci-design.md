# Parallel CI Design

## Goal

Reduce pull-request CI wall time without dropping coverage or changing the
required `lint` check used by branch protection.

## Design

Split `.github/workflows/ci.yml` into three jobs:

1. `checks` runs title validation, pre-commit, the short standalone checks, and
   the collection build.
2. `scenarios` uses a fixed matrix to run each independent Docker or smoke
   scenario on its own GitHub-hosted runner. The default Molecule converge and
   verify phases remain together because verify depends on converge. Every
   other matrix entry is self-contained.
3. `lint` runs after both jobs with `if: always()` and fails unless both needs
   succeeded. Keeping this job name preserves the existing required check.

Separate runners isolate the fixed Docker container names that made concurrent
local Molecule runs unsafe. No scenario runs concurrently on a shared Docker
daemon.

## Failure behavior

The matrix does not use `fail-fast`, so one failure does not hide results from
the other scenarios. The final `lint` job fails when either `checks` or the
matrix fails, is cancelled, or is skipped.

## Verification

Extend the existing assert-based workflow regression test before changing the
workflow. It must prove that:

- the expected independent scenarios are matrix entries;
- matrix fail-fast is disabled;
- the final job is named `lint`, depends on both upstream jobs, and always
  evaluates their results;
- the default converge and verify commands remain in one matrix entry;
- all existing commands remain represented exactly once.

Run the focused regression, the full pre-commit suite, and a workflow syntax
check locally. Hosted GitHub Actions is the final proof of parallel execution
and reduced wall time.

## Non-goals

- No path-based skipping.
- No branch-protection changes.
- No changes to scenario behavior or coverage.
- No custom composite action or reusable workflow.
