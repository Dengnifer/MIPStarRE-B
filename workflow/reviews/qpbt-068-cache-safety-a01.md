# QPBT-068 Cache Safety Transaction Repair Report

Current session: `i068-orchestrator-a13-materializer-transaction`
Prior repair head/tree: `650097d3fc65ecb93683dcbd5fbc3071240cf1e8` /
`9e74df6a4b96beddc547507f3e16020b96075556`
Owned worktree: `.workflow-runtime/worktrees/qpbt-068-cache-safety-a04`

## Scope and authenticated inputs

A13 resolves the A11 live-materializer blocker and A12 dry-run ordering finding
while preserving every A10 cache transaction guarantee. The repair extends the
owned scope to the authenticated materializer and its focused tests. It does
not edit `protocols/CHANGELOG.md`; that remains a sequential binder obligation
before integration.

The two required A13 review artifacts authenticated before implementation:

- A11: `/tmp/i068-reviewer-a11-transaction.md`, SHA-256
  `a8566ce28fd663578a91baa9700dd6695c9924c90f25871381a57a8baa2605b5`.
- A12: `/tmp/i068-reviewer-a12-regression.md`, SHA-256
  `870b45e7b45f11ef5d0c7b96f19a7ea5006194692b09b31eb4d92b2aeb010f5d`.

The immutable A11 review manifest authenticated as SHA-256
`dfc0ccd3674d55ecd927ab74d39bfa996286e04cd4404f41e66437453fefbc70`.
Two bounded read-only A13 scouts independently analyzed materializer authority
and dry-run admission ordering before implementation.

## Transaction contract

Seed and prepare now require Linux `renameat2`, inotify, descriptor-relative
operations, a conservatively approved local filesystem, and a successful
same-device semantic probe before input/cache admission or target mutation.
The uniquely named probe tree is retained instead of recursively deleted.
Non-replacement publication is one `RENAME_NOREPLACE`; replacement
is one `RENAME_EXCHANGE`, so a crash cannot expose an absent destination and a
concurrent destination is never replaced. There is no ordinary-rename
fallback.

The target monitor binds every ancestor root-to-leaf, installs each parent
watch before opening its child, holds all descriptors, and remains poisoned by
any protected rename, substitution, invalidation, malformed/unknown event, or
ABA. Live Git registration and the initially captured worktree `HEAD` are
rechecked before publication, around metric commit and finalization, and before
return. Rollback, old-tree retention, journal retention, failed-tree retention,
and empty-staging finalization use continuously held object descriptors plus
atomic exchange/no-replace. Seed/prepare never recursively delete transaction
objects and no longer unlink or `rmdir` live journal/staging names; successful
finalization moves them to unique retained evidence names. A last-instant
substitution can therefore only be preserved or moved intact before failure.

The authenticated foundation materializer now applies the same contract to
`MIPStarRE/`: existing output is replaced by one descriptor-bound
`RENAME_EXCHANGE`, absent output is published by `RENAME_NOREPLACE`, and
rollback reverses the exchange or retains the failed new tree. Stage,
destination, and transaction names have exact event accounting and held
descriptors. Completion moves the active transaction no-replace to unique
evidence. There is no recursive deletion or ordinary-rename publication,
rollback, or cleanup path; ambiguous objects remain preserved.

Every fixed seed journal, backup, or active staging object on a later invocation
causes refusal before cache/input admission. The dead seed-journal recovery
parser was removed. Prepare likewise rejects a materializer transaction or
cleanup tombstone before archive/cache admission and immediately before
invocation. The bound adapter never delegates to the legacy persisted recovery
routine, refuses a module missing any required private fail-closed operation,
and provides no lexical target fallback.

Dry-run seed and prepare now bind without checking cache-key inputs, prove the
atomic capability set, then rebind with input checks and prove capabilities
again. The capability gate therefore precedes identity, archive, and cache
admission on dry and live paths.

## Finding dispositions

| Finding | A10 disposition |
|---|---|
| F068-A08-001 | Resolved: materializer recovery state is refused before admission and again before invocation; adapted `_recover` never parses or delegates persisted recovery. |
| F068-A08-002 / A09 atomic-publication blocker | Resolved: capability-gated `RENAME_NOREPLACE` and `RENAME_EXCHANGE`, with no ordinary fallback and crash/collision regressions for seed and prepare. |
| F068-A08-003 / A09 live-cleanup blocker | Resolved conservatively: rollback and retention are descriptor-bound object-preserving atomic moves; journal and staging finalization retain instead of deleting. Substitution/collision/ABA preserves every candidate. |
| F068-A08-004 / A09 Git blocker | Resolved: `_assert_seed_target_registered` performs a fresh eligibility/Git query and compares project, worktree, parent, and initial `HEAD` bindings at every live barrier. |
| F068-A08-005 | Resolved: the QPBT-067 report uses final A10 symbol/line anchors and labels them pre-commit until the terminal identity envelope. |
| A09 ancestor-ABA blocker | Resolved: root-to-leaf held-descriptor inotify construction observes setup-time and live ancestor changes; poison is permanent. |
| A09 materializer-fallback blocker | Resolved: incomplete materializers fail before seed allocation/publication for both replace modes; no lexical fallback is reachable. |
| A09 regression-evidence high | Resolved: the hostile matrix is symmetric where applicable, metadata snapshots include root/entries, type, link text, mode, size, device, inode, link count, digest, and payload, and exact metric bytes remain separately checked. |
| F068-A11-001 | Resolved: live foundation publication, rollback, and transaction retention use held descriptors, exact permanent name monitors, and atomic exchange/no-replace only; cleanup is preserve-only. |
| F068-A12-001 | Resolved: dry-run gates capabilities before identity, archive, cache-status, or cache-key admission; the regression covers seed/prepare and dry/live combinations. |

## Validation

| Command | Result | Wall time |
|---|---|---:|
| `python3 tests/test_mipstarre_materialization.py` | 19/19 passed | 1.070 s |
| `python3 tests/test_hot_main_cache.py` | 122/122 passed | 46.058 s |
| `python3 tests/test_workflow.py` | 77/77 passed | 1.082 s |
| `python3 tests/test_check_workflow.py` | 3/3 passed | 0.006 s |
| `python3 scripts/check_workflow.py --skip-tests` | workflow state valid | below timer resolution |
| `python3 -m compileall -q scripts tests` | passed | below timer resolution |
| `python3 scripts/workflow.py validate` | valid: 69 issues, 34 PRs, 541 issued sessions, 7 stages | below timer resolution |
| `git diff --check` and seven-path scope check | passed | below timer resolution |

No aggregate suite was needed: both complete owned suites and the complete
workflow/checker unit suites passed. Commit/tree/patch/report identities are
recorded in the terminal A13 report after this canonical report is frozen.
The final bounded security scout authenticated the two script hashes and the
combined script diff, then reported no remaining blocker or high finding in
F068-A11-001 scope. Retained evidence growth and dependence on the admitted
Linux rename/inotify semantics remain explicit non-blocking risks.

No Lean/Lake/full build, real cache warm/seed/prepare, network, GitHub,
credential, endpoint, canonical workflow-state, or research-metric action ran.

## Capacity and remaining gates

A coordinator read-only check on 2026-09-04 observed 97% filesystem utilization
with 164 GB free. Archived QPBT-040 and active QPBT-069 each hold a separate
approximately 9.8 GB `.lake` after reflink was unsupported. A13 created no
cache copy and deletes neither tree. QPBT-069 remains an active lease. After
independent review, a separately authorized reclamation pass may dry-run the
archived QPBT-040 tree, but only after proving terminal session state, no Git
registration, no live lock/reference/lease, and an authenticated source cache;
quarantine plus the configured grace interval and a repeated final check must
precede deletion.

This candidate still requires a fresh immutable security/regression review,
the existing QPBT-062 evidence inclusion gate, and the sequential
`protocols/CHANGELOG.md` binder. It is not integration-ready until those gates
are recorded against the frozen A13 commit.
