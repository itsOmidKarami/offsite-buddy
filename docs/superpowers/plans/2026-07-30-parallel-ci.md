# Parallel CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce required CI wall time by running independent integration scenarios on isolated GitHub-hosted runners while preserving the required `lint` check.

**Architecture:** Keep short static checks in one `checks` job and move independent integration scenarios into a fixed `scenarios` matrix. A final `lint` aggregator runs with `if: always()` and fails unless both upstream jobs succeeded, so branch protection needs no change.

**Tech Stack:** GitHub Actions YAML, Python assert-based regression checks, pre-commit, Molecule, Ansible.

## Global Constraints

- Preserve every existing CI command and its failure behavior.
- Keep default Molecule converge and verify together and ordered.
- Run fixed-name Molecule scenarios concurrently only on separate runners.
- Keep `lint` as the final required check name.
- Disable matrix fail-fast so all scenario results remain visible.
- Do not add path filters, dependencies, reusable workflows, or branch-protection changes.

---

### Task 1: Parallelize independent CI scenarios

**Files:**
- Modify: `tests/test_review_fixes.py:415`
- Modify: `.github/workflows/ci.yml:13`

**Interfaces:**
- Consumes: existing CI commands and branch protection's `lint` check name.
- Produces: `checks`, `scenarios`, and final `lint` jobs in the `CI` workflow.

- [ ] **Step 1: Write the failing workflow-structure regression**

Replace the single REST-rotation workflow assertion with YAML-structure and
command-preservation assertions:

```python
    workflow_text = read(".github/workflows/ci.yml")
    workflow = yaml.safe_load(workflow_text)
    jobs = workflow["jobs"]

    assert set(jobs) == {"checks", "scenarios", "lint"}
    assert jobs["scenarios"]["strategy"]["fail-fast"] is False
    scenarios = jobs["scenarios"]["strategy"]["matrix"]["include"]
    assert {scenario["name"] for scenario in scenarios} == {
        "default",
        "cleanup",
        "systemd",
        "rest-rotation",
        "local-backup-restore",
        "restic-key-rotation",
        "quota-full-recovery",
    }
    default_command = next(
        scenario["command"]
        for scenario in scenarios
        if scenario["name"] == "default"
    )
    assert default_command.index("molecule converge") < default_command.index(
        "molecule verify"
    )

    lint = jobs["lint"]
    assert set(lint["needs"]) == {"checks", "scenarios"}
    assert "always()" in lint["if"]
    lint_step = lint["steps"][0]
    assert lint_step["env"] == {
        "CHECKS_RESULT": "${{ needs.checks.result }}",
        "SCENARIOS_RESULT": "${{ needs.scenarios.result }}",
    }
    assert 'test "$CHECKS_RESULT" = success' in lint_step["run"]
    assert 'test "$SCENARIOS_RESULT" = success' in lint_step["run"]

    for command in (
        "uv run molecule converge --no-report",
        "uv run molecule verify --no-report",
        "uv run molecule test -s cleanup --no-report",
        "uv run molecule test -s systemd --no-report",
        "uv run molecule test -s rest-rotation --no-report",
        "uv run ansible-playbook -i localhost, -c local tests/e2e-local.yml",
        "uv run ansible-playbook -i localhost, -c local tests/restic-key-rotation.yml",
        'sudo -E "$(command -v uv)" run ansible-playbook',
    ):
        assert workflow_text.count(command) == 1, command
```

- [ ] **Step 2: Run the regression and verify RED**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --locked python tests/test_review_fixes.py
```

Expected: FAIL because the workflow still contains only the existing `lint`
job.

- [ ] **Step 3: Implement the three-job workflow**

In `.github/workflows/ci.yml`:

- move title validation, setup, pre-commit, maintenance trap, negative
  validation, sidecar rendering, and collection build into `checks`;
- define `scenarios.strategy.fail-fast: false` with these seven fixed entries:

```yaml
        include:
          - name: default
            command: |
              molecule_schema_filter="$(
                printf '%s%s  Driver docker does not provide a schema.' WARN ING
              )"
              uv run molecule converge --no-report \
                2> >(grep -v -F "$molecule_schema_filter" >&2)
              uv run molecule verify --no-report \
                2> >(grep -v -F "$molecule_schema_filter" >&2)
          - name: cleanup
            command: uv run molecule test -s cleanup --no-report
          - name: systemd
            command: uv run molecule test -s systemd --no-report
          - name: rest-rotation
            command: uv run molecule test -s rest-rotation --no-report
          - name: local-backup-restore
            command: >-
              uv run ansible-playbook -i localhost, -c local tests/e2e-local.yml
          - name: restic-key-rotation
            command: >-
              uv run ansible-playbook -i localhost, -c local
              tests/restic-key-rotation.yml
          - name: quota-full-recovery
            command: >-
              sudo -E "$(command -v uv)" run ansible-playbook
              -i localhost, -c local tests/quota-full.yml
```

- give every scenario runner the existing checkout, Python, uv, and development
  tool installation steps;
- execute the static `matrix.command` as the final scenario step;
- add final job `lint` with `needs: [checks, scenarios]`, `if: ${{ always() }}`,
  and this exact result gate:

```yaml
      - name: Require successful CI jobs
        env:
          CHECKS_RESULT: ${{ needs.checks.result }}
          SCENARIOS_RESULT: ${{ needs.scenarios.result }}
        run: |
          test "$CHECKS_RESULT" = success
          test "$SCENARIOS_RESULT" = success
```

- [ ] **Step 4: Run the focused regression and verify GREEN**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --locked python tests/test_review_fixes.py
```

Expected: `review fix checks passed` and exit 0.

- [ ] **Step 5: Run full local verification**

Run:

```bash
UV_CACHE_DIR=.uv-cache ANSIBLE_LOCAL_TEMP=.ansible/tmp uv run --locked pre-commit run --all-files
git diff --check
```

Expected: every pre-commit hook passes and `git diff --check` exits 0.

- [ ] **Step 6: Commit the implementation**

```bash
git add .github/workflows/ci.yml tests/test_review_fixes.py
git commit -m "ci: run integration scenarios in parallel"
```

- [ ] **Step 7: Verify on hosted CI after publication**

Push the branch and open a pull request only when publication is authorized.
Confirm all seven scenario matrix entries run on separate jobs, final `lint`
passes, and total required-check wall time is materially below the prior
20-minute baseline.
