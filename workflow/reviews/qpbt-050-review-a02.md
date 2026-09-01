# QPBT-050 / LPR-026 immutable security review

## Findings

### HIGH F-LPR026-001: seed admission leaves `git rev-parse` outside the trusted environment

- **Path:** `scripts/hot_main_cache.py:1047` (consumed by `_eligible_seed_target` at `scripts/hot_main_cache.py:2736-2740`).
- **Disposition:** `request_changes`.
- **Evidence:** The candidate hardens `git_blob`, `git_commit`, `git_source_changes`, and `git_worktrees`, but `git_resolved_path` still calls `subprocess.run(..., env=...)` with no `env` argument. Seed admission uses this helper for `--show-toplevel` and `--git-common-dir` after the trusted worktree enumeration. Ambient variables such as `GIT_WORK_TREE` remain effective: `GIT_WORK_TREE=/tmp git -C /home/drx/MIPStarRE-auto rev-parse --show-toplevel` returns `/tmp`. Therefore a caller-controlled Git environment can alter the final worktree identity/attachment diagnostic (at minimum causing fail-open/DoS behavior, and violating the issue acceptance gate that every Git diagnostic used by cache admission runs under `_trusted_git_environment`). Pass `_trusted_git_environment()` to this helper (and add a focused regression covering the admission path).

## Verdict

**Request changes.** The new fsmonitor hardening is correct for the four changed diagnostics and the focused regressions preserve fail-closed warning handling and publication gating, but the remaining untrusted cache-admission diagnostic must be fixed before approval.

## Gates and authentication

- Candidate base: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`.
- Candidate head: `5e67781ac40cb3f0bfda141e6b631479db994ba7`.
- Candidate tree: `cb2a6e85311ea3ff681e8e5d378c8b075c283641`.
- Sole parent: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d` (ancestor check passed).
- Three-path manifest SHA: `85693d6b11e7714aaf04ffef551693989bddf094e8394cfd552f80ce25e9ccfb`.
- Candidate report SHA (A01): `51955d5f069865d45bc1eb50b0aa4a52aec0b54e186623d623830187446f8f68`.
- Candidate source and test syntax compilation: passed.
- Candidate targeted in-memory tests: 3/3 passed (`test_git_source_changes_does_not_execute_fsmonitor_hook`, exit-zero diagnostics, and no-READY warm failure).
- Main-worktree baseline hot-cache suite: 60/60 passed. The immutable candidate adds one test (61 expected); no production warm/build/cache publication was run.
- `python3 scripts/check_workflow.py --skip-tests`: passed (state was concurrently updated after an earlier transient count mismatch).
- `python3 scripts/workflow.py validate`: passed.
- Immutable `git diff --check`: passed.
- Source preservation/publication review: staging failures retain evidence and remove staging; snapshot rename and `READY` creation occur only after all source, Git, and artifact checks. No regression found there.
- Integration gate: **blocked pending HIGH finding disposition; no integration or production cache publication authorized.**

## Session metadata

- Reviewer external identity: `/root/i050-reviewer-a02-fsmonitor`.
- Review started after explicit coordinator release; elapsed wall time: approximately 430 seconds.
- Token usage: `null` (collaboration backend does not expose per-agent token usage).
- Subagent topology: 0 subagents issued; nested depth 0.
- Compile attempts: 2 candidate syntax checks plus the focused test execution; no Lean/Lake/build attempts.
- Cache behavior: no hot-cache warm/seed/publication; no cache lock acquired.
- Network, endpoint, GitHub, credentials: not accessed.
