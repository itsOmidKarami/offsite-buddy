## Summary

Release impact:

- [ ] PR title uses `fix:`, `feat:`, `feat!:`, `docs:`, `chore:`, or another
      conventional commit prefix

## Validation

- [ ] `uv run --locked pre-commit run --all-files`
- [ ] `uv run molecule converge`
- [ ] `uv run molecule verify`
- [ ] `uv run ansible-playbook -i localhost, -c local tests/validation-negative.yml`
- [ ] `uv run ansible-playbook -i localhost, -c local tests/client-sidecar-render.yml`
- [ ] `uv run ansible-playbook -i localhost, -c local tests/e2e-local.yml`
- [ ] `uv run ansible-galaxy collection build --force`
