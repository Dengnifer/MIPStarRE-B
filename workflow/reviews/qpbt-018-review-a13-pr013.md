# LPR-013 / QPBT-018 Immutable Review A13

## Findings

None. No finding IDs or dispositions are required.

## Formal Verdict

**approve**

The exact immutable candidate implements the requested bounded EXDEV recovery,
preserves the QPBT-021 authenticated-Mathlib and publication contract, and
passes every prescribed gate. This review is independent of the implementer,
orchestrator, and prior scout.

## Immutable Identity and Scope

- Review worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-018-current-a10`
- Base: `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`
- Head: `c0de0900a01724c2a515311424dcbe5e7526ebd4`
- Sole head parent: `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`
- Head tree: `8b3d2caee539921fe4bcbcc456f0fc00ae2bbe17`
- Production blob: `48e020d7392f2e1974f5983d6737171e034417d2`
- Test blob: `39dca3d47f3e8c79dd7ac1c07f4f69ae723aed06`
- Changed paths: exactly `scripts/hot_main_cache.py` and
  `tests/test_hot_main_cache.py`
- Diff size: 199 insertions and 8 deletions; production 32/8, tests 167/0
- Final candidate worktree status: clean

The base is the two-parent `merge: integrate approved QPBT-021 local mathlib
cache` commit, with QPBT-021 candidate `6303aab63eeed144fe176969ca7c87f5a852b967`
as its second parent. The LPR-013 production delta is confined to
`HotMainCache._detached_clone`.

## Correctness and Preservation Review

At `scripts/hot_main_cache.py:1891`, the candidate retains the initial exact
`git clone --local --no-checkout` command. It records the pre-attempt log byte
offset and examines only bytes appended by that attempt (`:1894-1906`). Only
new `cross-device` or `EXDEV` text enables recovery. Recovery deletes only the
fixed `staging/checkout` entry, using unlink for a symlink/file and `rmtree` for
a real directory; cleanup errors remain fatal (`:1907-1911`). It appends an
auditable marker and performs exactly one `--no-local` object-copy retry
(`:1912-1917`). A successful clone must still execute
`checkout --detach self.identity.main_commit`, and any retry or checkout failure
raises `CacheError` (`:1919-1924`).

The four added regressions at `tests/test_hot_main_cache.py:355`, `:401`,
`:428`, and `:467` cover exact argv order, partial-checkout cleanup, newly
appended evidence only, the one-retry bound, retained diagnostics, exact commit
checkout, and no snapshot or `READY` publication after checkout failure.

QPBT-021 is preserved. The authenticated Mathlib requirement and preparation
remain at `scripts/hot_main_cache.py:1598`, `:1681`, and `:1749`; the elected
singleton lock remains at `:2033`; immediate detached-input verification remains
at `:2097`; post-build exact HEAD, inputs, and clean-source verification remain
at `:2154-2161`; Mathlib is reverified at `:2165-2166`. Manifest creation,
manifest-bound `READY`, and atomic snapshot publication still occur only after
those gates at `:2204-2214`. Failure handling at `:2229-2265` retains the log and
failure identity, removes staging, and never publishes the failed transaction.
No cache identity, recipe, source-authentication, locking, or consumer behavior
was weakened.

The broad textual diagnostic predicate is a small residual risk: an unrelated
new clone diagnostic containing `exdev` or `cross-device` could cause one extra
object-copy attempt. It cannot bypass the exact checkout, input, source,
artifact, READY, or publication gates, so this is not a blocking finding.

## LPR-013 Evidence and Independence

Current canonical state records LPR-013 as `ready`, addressing QPBT-018, with
the exact base/head pair above, exactly the two changed paths, six passed
SHA-bound checks, no reviews yet, and no findings. Its implementer is
`i018-integrator-a12-pr013-bind`; implementation provenance is
`i018-orchestrator-a10-current-exdev` plus nested read-only scout
`i018-scout-a11-fallback-diff`.

This reviewer is `i018-reviewer-a13-pr013-immutable`, a read-only sibling
session with no owned paths. It is not the implementer, orchestrator, or scout,
and performed no candidate or canonical edits. Canonical workflow validation
also passed while this independent review session was registered: 24 issues,
13 pull requests, 0 planned sessions, 276 issued sessions, and 7 stages.

The canonical and temporary copies of the implementer and scout reports match
their recorded SHA-256 digests. LPR-007 remains closed as superseded historical
evidence with its immutable old base/head and three reviews intact.

## Prescribed Gates

All commands ran serially from the candidate worktree.

1. `python3 -m unittest discover -s tests -p 'test_hot_main_cache.py' -v`
   passed 46/46 tests in 10.651 seconds; wall 10.75 seconds.
2. `python3 -m unittest discover -s tests -v` passed 303/303 tests in
   72.255 seconds; wall 72.39 seconds.
3. `python3 scripts/check_workflow.py` passed, including 303/303 tests in
   72.020 seconds and workflow-state validation; wall 72.19 seconds.
4. `python3 -m compileall -q scripts tests` passed; wall 0.03 seconds.
5. `python3 scripts/workflow.py validate` passed; wall 0.10 seconds, reporting
   24 issues, 12 pull requests, 0 planned sessions, 269 issued sessions, and 7
   stages in the immutable candidate snapshot.
6. `git diff --check c5a0fecc26eb18452219cf0df31ce2a9113e45f1..c0de0900a01724c2a515311424dcbe5e7526ebd4`
   passed with no output; wall 0.00 seconds.

An auxiliary read-only validation of the live canonical state also passed in
0.10 seconds with the counts recorded above. The candidate remained clean after
all validation.

## Remaining Gate and Accounting

LPR-013 is approved for faithful integration. QPBT-018 is not yet complete:
after integration, exactly one elected authenticated singleton warm must use the
approved local foundation, Lake-package, and Mathlib inputs, publish the
integrated-key snapshot exactly once, and produce a verified `READY`/status-ready
result. This review deliberately did not run that operational gate.

- Review interval: 543.826 seconds from canonical session start through report
  drafting (`2026-08-31T14:50:51.440037Z` to
  `2026-08-31T14:59:55.266354Z`).
- Subagents: 0.
- Token usage: `null`; the collaboration backend does not expose per-agent
  token usage.
- Prescribed gate invocations: 6, all passed.
- Test-suite invocations: 3; 652 test cases executed including repeated
  aggregate coverage (46 + 303 + 303), all passed.
- Python compile checks: 1. Candidate workflow validations: 1. Auxiliary live
  canonical validations: 1. SHA-bound diff checks: 1.
- Repository content edits, staging operations, commits, and ref changes: 0.
- Cache status/warm/seed operations: 0/0/0.
- Lean invocations, Lake invocations, and production builds: 0/0/0.
- Network and GitHub operations: 0/0.
