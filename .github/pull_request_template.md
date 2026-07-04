## Summary

Release impact:

- [ ] PR title uses a conventional prefix:
      `fix:`/`feat:`/`perf:` for release-worthy changes, or
      `docs:`/`test:`/`ci:`/`chore:`/`refactor:` otherwise

## Validation

- [ ] `uv run --locked pre-commit run --all-files`
- [ ] `uv run molecule converge`
- [ ] `uv run molecule verify`
- [ ] `uv run ansible-playbook -i localhost, -c local tests/validation-negative.yml`
- [ ] `uv run ansible-playbook -i localhost, -c local tests/client-sidecar-render.yml`
- [ ] `uv run ansible-playbook -i localhost, -c local tests/e2e-local.yml`
- [ ] `uv run ansible-galaxy collection build --force`
