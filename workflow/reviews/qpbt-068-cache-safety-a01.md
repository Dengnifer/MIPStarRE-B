# QPBT-068 Cache Safety Transaction Repair Report

Current session: `i068-orchestrator-a10-transaction-repair`
Prior repair head/tree: `f03c94e074f2ebfd7e99e05394c4116126455895` /
`1aa8ff42dbf89f78e09d46d3efdf0195e2dd38a6`
Owned worktree: `.workflow-runtime/worktrees/qpbt-068-cache-safety-a04`

## Scope and authenticated inputs

A10 repairs every A08/A09 transaction finding in the five QPBT-068 owned
paths while preserving the A04 authenticated-input, source-evidence, authored
QPBT, private-copy, and deep-inventory controls and the A06 metric-lock and
rollback controls. It does not edit `protocols/CHANGELOG.md`; that remains a
sequential binder obligation before integration.

The two required review artifacts authenticated before implementation:

- A08: `/tmp/i068-reviewer-a08-security.md`, SHA-256
  `e2824460afc2657d6695d10c53a2944b2622f85df129114d68822a10ff7cdbf4`.
- A09: `/tmp/i068-reviewer-a09-regression.md`, SHA-256
  `65dff9813338a2da76bf2e7ef199d8fc7588bf74037e5ef489347456d2e85963`.

The A07 repair audit (SHA-256
`c9791defd746b5432296cff7458c388652c2ec3bb27bdf532fc893de8af5f04c`)
and both required A10 scouts were also authenticated and inspected. The
atomic-rename scout report is
`/tmp/i068-scout-a10-atomic-rename.md`, SHA-256
`c101c3807b24d6177d5df23265db8e78a42a559aaa1dd97f48942205e6426e17`;
the continuous-authority report is
`/tmp/i068-scout-a10-continuous-authority.md`, SHA-256
`1fe6e7aa89386dd1134abc55199da6bccdb6f76d1b1f8d059eeac7afd366357a`.

## Transaction contract

Seed and prepare now require Linux `renameat2`, inotify, descriptor-relative
operations, a conservatively approved local filesystem, and a successful
same-device disposable semantic probe before input/cache admission or target
mutation. Non-replacement publication is one `RENAME_NOREPLACE`; replacement
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

Every fixed seed journal, backup, or active staging object on a later invocation
causes refusal before cache/input admission. The dead seed-journal recovery
parser was removed. Prepare likewise rejects a materializer transaction or
cleanup tombstone before archive/cache admission and immediately before
invocation. The bound adapter never delegates to the legacy persisted recovery
routine, refuses a module missing any required private fail-closed operation,
and provides no lexical target fallback.

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

## Validation

| Command | Result | Wall time |
|---|---|---:|
| Final hostile 22-test selector | 22/22 passed | 10.097 s |
| `python3 tests/test_hot_main_cache.py` | 120/120 passed | 42.740 s |
| `python3 tests/test_workflow.py` | 77/77 passed | 1.023 s |
| `python3 tests/test_check_workflow.py` | 3/3 passed | 0.003 s |
| `python3 -m unittest discover -s tests` | 418 run; 416 passed, two unchanged AF_UNIX fixtures blocked by sandbox `EPERM` | 226.958 s |
| `python3 scripts/check_workflow.py` | workflow valid; 418 run, same 416 passed and two sandbox AF_UNIX errors | 256.335 s |
| Outside-sandbox focused AF_UNIX command | 2/2 passed | 90.773 s |
| `python3 -m compileall -q scripts tests` | passed | below timer resolution |
| `python3 scripts/workflow.py validate` | valid: 69 issues, 34 PRs, 541 issued sessions, 7 stages | below timer resolution |
| `git diff --check` and five-path scope check | passed | below timer resolution |

The aggregate was run exactly once after the cache/workflow implementation was
stable. Its only errors were the two unchanged socket fixtures at
`listener.bind`; the exact two tests then passed in the focused managed
outside-sandbox run. The registered checker encountered the same environmental
pair after validating workflow state; it introduced no distinct failure.
Commit/tree/patch/report identities are recorded in the terminal A10 report
after the canonical report is frozen.

No Lean/Lake/full build, real cache warm/seed/prepare, network, GitHub,
credential, endpoint, canonical workflow-state, or research-metric action ran.

## Capacity and remaining gates

A coordinator read-only check on 2026-09-04 observed 97% filesystem utilization
with 164 GB free. Archived QPBT-040 and active QPBT-069 each hold a separate
approximately 9.8 GB `.lake` after reflink was unsupported. A10 created no
cache copy and deletes neither tree. QPBT-069 remains an active lease. After
independent review, a separately authorized reclamation pass may dry-run the
archived QPBT-040 tree, but only after proving terminal session state, no Git
registration, no live lock/reference/lease, and an authenticated source cache;
quarantine plus the configured grace interval and a repeated final check must
precede deletion.

This candidate still requires a fresh immutable security/regression review,
the existing QPBT-062 evidence inclusion gate, and the sequential
`protocols/CHANGELOG.md` binder. It is not integration-ready until those gates
are recorded against the frozen A10 commit.
