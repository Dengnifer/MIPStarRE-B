# QPBT-050 fsmonitor hardening A01

## Scope

Harden every Git diagnostic used during cache admission against ambient and
repository executable configuration. `git_blob`, `git_commit`,
`git_source_changes`, and `git_worktrees` now pass `_trusted_git_environment`,
which disables hooks/fsmonitor and strips inherited `GIT_CONFIG_*` inputs while
retaining the existing fail-closed diagnostics contract.

## Regression coverage

- `git_source_changes` with a repository `core.fsmonitor` hook does not execute
  the hook.
- Existing exit-zero stderr handling remains fail-closed.
- Existing full-warm warning regression confirms no snapshot or `READY` marker
  is published after Git diagnostics failure.

## Validation

- `python3 tests/test_hot_main_cache.py` (61/61 passed)
- `python3 -m py_compile scripts/hot_main_cache.py tests/test_hot_main_cache.py`
- `python3 scripts/check_workflow.py --skip-tests` (valid)
- `git diff --check` (clean)

No production warm, cache publication, Lean/Lake, network, endpoint, or
credential operations were performed.
