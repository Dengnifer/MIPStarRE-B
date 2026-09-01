# QPBT-050 fsmonitor admission repair A02

## Finding disposition

Resolved `F-LPR026-001`: every `git_resolved_path` invocation used by
`HotMainCache._eligible_seed_target` now executes with `_trusted_git_environment`,
so ambient `GIT_WORK_TREE`, `GIT_DIR`, and `GIT_CONFIG_*` values cannot alter
worktree identity or enable executable Git configuration.

## Regression coverage

Added `test_seed_admission_ignores_ambient_git_worktree_and_config`, which
warms a cache and successfully seeds a registered issue worktree while hostile
ambient Git identity/configuration variables are present.

Existing fsmonitor-hook, stderr fail-closed, publication-barrier, and hook
regressions remain covered.

## Validation

- `python3 tests/test_hot_main_cache.py` (62/62 passed, 12.564s)
- `python3 -m py_compile scripts/hot_main_cache.py tests/test_hot_main_cache.py`
- `python3 scripts/check_workflow.py --skip-tests` (valid)
- `git diff --check` (clean)

No production warm/seed/publication, Lean/Lake/build/cache/network, endpoint,
credential, or GitHub operations were performed.

## Review request

Request a fresh independent read-only security review against the committed
head, with particular attention to all admission-time `git_resolved_path`
subprocesses and hostile ambient Git environment handling.
