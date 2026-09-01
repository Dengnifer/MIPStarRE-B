# QPBT-050 / LPR-026 immutable security review A03

## Verdict

**Approve.** The A02 repair closes `F-LPR026-001`: every Git subprocess used
by cache identity/admission diagnostics, including both `git_resolved_path`
calls in `_eligible_seed_target`, now receives `_trusted_git_environment()`.
Hostile ambient Git identity/configuration variables therefore cannot redirect
worktree identity or enable an executable fsmonitor/hook configuration. The
existing fail-closed diagnostics and publication barriers remain intact.

No new findings.

## Authentication

- Base commit: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`
- Candidate head: `c70267e3d65aeb3c47b4680ab53693c5b9ead6fa`
- Candidate tree: `1c1be2d9c9e7c790842fab47077055f929826c06`
- Sole parent: `5e67781ac40cb3f0bfda141e6b631479db994ba7`
- Parent-to-head ancestry: verified
- Changed paths (parent-to-head, no renames):
  `scripts/hot_main_cache.py`, `tests/test_hot_main_cache.py`,
  `workflow/reviews/qpbt-050-fsmonitor-repair-a02.md`
- Changed-path manifest SHA-256 (`git diff --no-renames --name-only`):
  `a3358d0d5ce28b5569eaaff61872f9f231c47d693c0df31996ef732e2b8319da`
- Repair report SHA-256:
  `db01b6ce1ecf155dd478270b9ea0c574371e7bdd22e60b52e4b589a9ac96da47`
- Worktree: clean, detached at the exact candidate head after review
- `git diff --check` (base..head and parent..head): passed

The checked-out `workflow/state/prs.json` snapshot does not contain a direct
`LPR-026` object; this review used the immutable packet hashes above and the
committed A02 repair report for candidate binding.

## Security review

`_trusted_git_environment()` removes inherited `GIT_*`, pager, and SSH askpass
variables, disables system/global config, and injects the fixed fsmonitor-off,
hooks-off, pager-off, credential-helper-off, and ext protocol restrictions.
Every direct Git diagnostic subprocess in `hot_main_cache.py` was inspected:
`_git_command_bytes`, `git_blob`, `git_commit`, `git_source_changes`,
`git_worktrees`, `git_resolved_path`, and `_parse_isolated_git_config` all pass
that environment. `_eligible_seed_target` invokes `git_worktrees` once and
`git_resolved_path` three times; all four calls are therefore isolated.

The seed regression was independently exercised with hostile
`GIT_WORK_TREE`, `GIT_DIR`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`,
`GIT_CONFIG_COUNT`, and `GIT_CONFIG_PARAMETERS` values; target admission still
resolved the registered worktree and succeeded. The direct helper probe
resolved `--show-toplevel` to the candidate worktree and `--git-common-dir` to
the repository `.git` under the same hostile environment, with hostile Git
variables absent from the effective environment.

The existing fsmonitor-hook regression confirms the configured hook does not
execute. Exit-zero Git stderr remains rejected by `git_source_changes`, and the
full-warm warning regression confirms diagnostic failure leaves no snapshot or
`READY` marker. Snapshot publication still occurs only after source, identity,
cleanliness, and artifact checks complete.

## Validation

| Check | Result |
| --- | --- |
| `python3 tests/test_hot_main_cache.py` | 62/62 passed in 12.630 s |
| `python3 -m compileall -q scripts tests` | passed |
| `python3 scripts/check_workflow.py --skip-tests` | workflow state valid |
| `git diff --check` | passed for base..head and parent..head |

No production warm/seed/publication, Lean/Lake/build/cache warm, network,
endpoint, GitHub, credential, or nested-agent operations were performed.

## Metrics

- Reviewer session: `/root/i050-reviewer-a03-fsmonitor-repair`
- Subagents: 0 (nested depth 0)
- Findings: 0 new; `F-LPR026-001` confirmed resolved by the changed head
- Compile attempts: 1 compileall; no Lean/Lake attempts
- Cache actions: 0; cache lock acquisitions: 0
- Token usage: `null` (collaboration backend does not expose per-agent token usage)
