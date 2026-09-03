# QPBT-068 Cache Safety Implementation and Identity Repair Report

Current session: `i068-orchestrator-a06-identity-repair`
Prior implementation session: `i068-orchestrator-a04-cache-transaction`
Role: orchestrator
Repair base commit: `2820c66f2a9f227cfe2a5da6d1448c6e52cb8262`
Owned worktree: `.workflow-runtime/worktrees/qpbt-068-cache-safety-a04`

## Scope

Attempt A04 repaired F068-A02-001 through F068-A02-008 in these five paths.
Attempt A06 preserves those source-input, metric-lock, symlink, provenance,
and rollback controls while repairing the three A05 hostile findings. It does
not edit `protocols/CHANGELOG.md`.
That required protocol-evolution disposition remains a sequential binder
obligation after QPBT-044 releases the file, so this candidate is not
integration-ready until the binder and a fresh immutable review complete.

The repaired implementation rejects every external `.lake` symlink and still
publishes the A04 diagnostic journal before the first replacement rename, but
does not let mutable journal/digest/commit bytes authorize a later process.
Every persistent journal or backup blocks seed/prepare unchanged for manual
disposition. A live operation keeps no-follow descriptors for the registered
worktree root, project root, and worktree parent, detects pathname substitution
and swap/restore generation changes, routes target staging and renames through
the project descriptor, and guards the success metric while its lock is held.
The original `.lake` also remains open across replacement. After commit it is
identity-checked and renamed to retained state; neither normal completion nor
recovery recursively deletes it.

## Validation

| Command | Result | Wall time |
|---|---|---:|
| A06 targeted 8-test identity command | 8/8 passed | 2.32 s |
| `python3 tests/test_hot_main_cache.py` | 107/107 passed | 32.92 s |
| `python3 tests/test_workflow.py` | 77/77 passed | 2.31 s |
| `python3 tests/test_check_workflow.py` | 3/3 passed | 0.08 s |
| `python3 -m unittest discover -s tests` | 405/405 passed outside sandbox | 312.03 s |
| `python3 -m compileall -q scripts tests` | passed | below timer resolution |
| `python3 scripts/workflow.py validate` | valid: 69 issues, 34 PRs, 541 issued sessions, 7 stages | 0.19 s |
| `git diff --check` | passed | below timer resolution |

The first A06 aggregate run completed 405 tests in 201.43 seconds with 403
passing and the two unchanged UNIX-socket cases failing at `listener.bind` with
`EPERM`. The exact command was rerun through the managed escalation path and
passed 405/405. The A04 validation evidence remains part of the immutable
parent. Lean/Lake/full builds, cache warming against the real repository,
network, GitHub, endpoint, credential, canonical state/metric, and
authored-source actions remain zero.

## Findings

| Finding | Disposition |
|---|---|
| F068-A02-001 | Strengthened: `_recover_interrupted_seed` treats every persistent journal/backup as unauthenticated manual-recovery state and never parses it as authority. Canonical self-consistent journal/digest/COMMITTED bytes fail byte-exactly unchanged. |
| F068-A02-002 | Resolved by `_validate_lake_symlink_policy`: every lexical first hop and final target must stay within the private destination; writable and mode-read-only external targets are both rejected. |
| F068-A02-003 | Strengthened in `seed` and `prepare`: persistent-state rejection precedes cache/input admission; the bound target remains live through copy, validation, materialization, registration, metric commit, rollback, and retention. |
| F068-A02-004 | Resolved in `_append_metric` and `_rollback_metric_append_locked`: rollback occurs under one continuous lock. Event-coordinated two-process short-write and fsync regressions preserve writer B exactly. |
| F068-A02-005 | Resolved in the corrected QPBT-067 report: mismatched `READY` returns false; quarantine is explicitly only a proposal. |
| F068-A02-006 | Resolved as an evidence/disposition correction: exact audit start/stop/elapsed and a four-lane interval sweep are recorded, unavailable per-command latency is `null` with a reason, and the QPBT-068 ordering violation is explicit. QPBT-067 remains unapproved. |
| F068-A02-007 | Resolved with symbol-qualified final-candidate anchors for protocol, initialization, readiness, journal, recovery, publication, and tests. |
| F068-A02-008 | Resolved as authenticated provenance with the QPBT-062 commit/tree/blob/size/SHA-256. Because that byte is absent from this candidate tree, approval remains deferred until it is manifest-listed in the next immutable review packet. |
| F068-A05-001 | Resolved fail-closed: no mutable journal record can authorize automatic recovery, rename, chmod, unlink, or deletion. |
| F068-A05-002 | Resolved by `_BoundSeedTarget`, descriptor-relative target operations, parent-generation ABA detection, guarded metric append, and deterministic seed/prepare phase regressions. |
| F068-A05-003 | Resolved by continuously binding the original directory and moving a matching committed backup to `.lake.retained-*`; substitution and ABA never invoke recursive deletion. |

## Integrity and remaining obligation

Repair base commit/tree are
`2820c66f2a9f227cfe2a5da6d1448c6e52cb8262` /
`557a0f1bd5af2803a15c1d90417aa5568879161f`. The frozen head/tree and
five-path hashes are supplied in the A06 terminal result envelope after commit.
No `protocols/CHANGELOG.md` disposition is claimed here. A sequential binder
must update it after QPBT-044 releases the file, validate that changed head,
and obtain a fresh independent immutable review before integration.
