# QPBT-049 Candidate Report

- Parent/base: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`
- Scope: post-confirmation collaboration release lease in `scripts/workflow.py`, focused regressions in `tests/test_workflow.py`, and protocol documentation.
- Amendment: `validate_event_log` recognizes `session.released` and rejects duplicate or pre-issuance chronology; tests cover both failures.
- Validation: `python3 tests/test_workflow.py` (78 tests passed); `python3 -m compileall -q scripts tests`; `git diff --check`.
- Checker/workflow validation: not run in this worktree because canonical workflow state is root-owned.
- Build: Lean/Lake build not run; no network, endpoint, GitHub, or credentials access.
- Commit: report is supplied for the coordinator's follow-up candidate commit.
- Token metrics: unavailable (`null`; runtime does not expose token counters).
