# QPBT-018 current EXDEV fallback outcome (a10)

## Verdict

PASS. The already-reviewed QPBT-018 EXDEV recovery was manually transplanted
into the current QPBT-021-aware hot-cache implementation without cherry-picking
the stale branch or changing any local-Mathlib acquisition, authentication,
environment, identity, or publication gate.

Commit: `fix(cache): retry detached clone across devices`

## Immutable Git identity

- Base: `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`
- Base tree: `1cd467af136866b4aee74b7da421402ff4d38d35`
- Head: `c0de0900a01724c2a515311424dcbe5e7526ebd4`
- Head parent: `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`
- Head tree: `8b3d2caee539921fe4bcbcc456f0fc00ae2bbe17`
- Branch: `issue/qpbt-018-current-a10`
- Final worktree status: clean

## Exact diff identity and scope

Only the two owned files changed:

```text
32  8  scripts/hot_main_cache.py
167 0  tests/test_hot_main_cache.py
```

Overall: 2 files changed, 199 insertions, 8 deletions.

Committed blob identities:

```text
48e020d7392f2e1974f5983d6737171e034417d2  scripts/hot_main_cache.py
39dca3d47f3e8c79dd7ac1c07f4f69ae723aed06  tests/test_hot_main_cache.py
```

Production behavior changed only in `HotMainCache._detached_clone`:

1. Keep the initial exact `git clone --local --no-checkout` attempt.
2. Record the pre-attempt log byte offset and inspect only diagnostics appended
   by the failed local clone.
3. Recognize explicit case-insensitive `cross-device` or `EXDEV` evidence.
4. Remove only the fixed failed `staging/checkout` path, unlinking a symlink or
   file and recursively removing a real directory; cleanup errors are not
   suppressed.
5. Append a fallback marker and retry exactly once with `--no-local`, Git's
   object-copy mode.
6. Preserve the exact `git -C <checkout> checkout --detach <main_commit>` step.
7. Preserve all current QPBT-021 detached-input checks, Mathlib source handling,
   post-build HEAD/input/source verification, and READY/publication gates.

Four focused regressions prove full argv order, partial-checkout cleanup,
stale-log non-triggering, one bounded fallback, retained diagnostics, and no
snapshot or READY publication after an invalid fallback checkout.

## Source evidence and scout disposition

The historical approved implementation is `1273f1dc9fed33b6a5eafd5e25e6081c8b32ceb7`;
the additional no-publication regression is
`e21c9cda11803f7564a500c005fd55882530538d`. The current failure envelope is:

`/home/drx/MIPStarRE-auto/.workflow-runtime/cache/failures/a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0-20260831T220839-2`

It binds the failure to the immutable base and records Git failing to hardlink
an object with `Invalid cross-device link` before Mathlib source preparation.

One nested read-only scout was used:

- Logical ID: `i018-scout-a11-fallback-diff`
- Runtime name: `/root/i018_orchestrator_a10_current_exdev/i018_scout_a11_fallback_diff`
- Expected external ledger identity:
  `/root/i018_orchestrator_a10_current_exdev/i018_scout_a11_fallback_diff#logical:i018-scout-a11-fallback-diff`
- Model/reasoning: `gpt-5.6-sol`, high
- Result: PASS; recommended the method-local manual transplant and strengthened
  regressions, and independently warned against cherry-picking the pre-QPBT-021
  commits.
- Authored scout report: `/tmp/qpbt-018-fallback-diff-a11.md`
- Canonical destination: intentionally not selected or written by this session;
  the root coordinator owns any import into canonical report/state/metrics paths.
- Scout operations: read-only; no tests, builds, warm, seed, Lean, Lake, cache,
  network, or repository edits.

All scout points were accepted and covered by the committed candidate. The only
residual noted risk is the approved diagnostic matcher being textually broad
within the newly appended bytes; a false positive can cause at most one harmless
object-copy attempt, and cannot bypass checkout or publication verification.

## Validation

Final-state required checks:

- `python3 -m unittest discover -s tests -p 'test_hot_main_cache.py' -v`:
  PASS, 46 tests in 10.575 s (wall 10.68 s).
- `python3 -m unittest discover -s tests -v`:
  PASS, 303 tests in 72.173 s (wall 72.31 s).
- `python3 scripts/check_workflow.py`:
  PASS, its 303-test phase in 75.270 s (wall 75.44 s); workflow state valid.
- `python3 -m compileall -q scripts tests`: PASS, wall 0.03 s.
- `python3 scripts/workflow.py validate`: PASS, wall 0.10 s; 24 issues,
  12 pull requests, 0 planned sessions, 269 issued sessions, 7 stages.
- `git diff --check c5a0fecc26eb18452219cf0df31ce2a9113e45f1..HEAD`:
  PASS, no output.

Earlier pre-strengthening checks also passed: focused 46 tests in 10.886 s,
full 303 tests in 75.375 s, and a captured `check_workflow.py` rerun with 303
tests in 74.644 s. One initial parallel `check_workflow.py` PTY result handle was
not retained, so its terminal status was unavailable; the exact command was
rerun to captured success before and after the final assertion edits.

## Operational metrics

- Session elapsed: approximately 14 minutes; labeled approximate because the
  collaboration runtime does not expose an authoritative session timer.
- Subagent count: 1.
- Topology: root coordinator -> this writable orchestrator -> one read-only scout.
- Production compile/build attempts: 0.
- Cache behavior: not applicable; no production cache command was run, so there
  were no cache hits, lock waits, or cache build durations to record.
- Token usage: `null`; per-session token usage is not exposed to this agent.
- Warm/no-warm statement: no `hot_main_cache.py warm` or `seed` CLI, shared-cache
  mutation, Lean, Lake, or network operation was run. Required unit tests used
  isolated temporary repositories and mocked/fake build callbacks to exercise
  the Python warm/seed logic without touching the production cache.
- Git sandbox incident: the first commit attempt stopped before staging because
  the linked-worktree Git metadata was read-only; the narrow approved retry
  created the required local commit. No content changed between validation and
  commit.
