# QPBT-068 Cache Safety Implementation Report

Session: `i068-orchestrator-a04-cache-transaction`
Role: orchestrator
Base commit: `97e61b3487c762f1447576219dbd6cd85c162efa`
Owned worktree: `.workflow-runtime/worktrees/qpbt-068-cache-safety-a04`

## Scope

This preliminary candidate repairs F068-A02-001 through F068-A02-008 in the
five paths owned by attempt A04. It does not edit `protocols/CHANGELOG.md`.
That required protocol-evolution disposition remains a sequential binder
obligation after QPBT-044 releases the file, so this candidate is not
integration-ready until the binder and a fresh immutable review complete.

The implementation rejects every external `.lake` symlink; publishes a
canonical, digest-bound seed journal before the first replacement rename;
binds the random transaction ID, exact target/lock, backup/staging/retained
basenames, original and replacement identities/inventories, cache identity, and
manifest digest; and recovers only journal-owned state. Recovery runs under the
target lock before target-input, environment, or shared-cache admission. An
uncommitted replacement is retained separately before the old tree is restored;
a durable success metric authenticates the commit if termination precedes the
`COMMITTED` marker. Metric write/fsync rollback holds the original lock and
descriptor continuously.

## Validation

| Command | Result | Wall time |
|---|---|---:|
| Targeted 12-test hostile regression command | 12/12 passed | 3.725 s |
| `python3 tests/test_hot_main_cache.py` | 99/99 passed | 25.19 s |
| `python3 tests/test_workflow.py` | 77/77 passed | 1.16 s |
| `python3 tests/test_check_workflow.py` | 3/3 passed | 0.06 s |
| `python3 -m unittest discover -s tests` | 397/397 passed outside sandbox | 207.58 s |
| `python3 -m compileall -q scripts tests` | passed | 0.04 s |
| `python3 scripts/workflow.py validate` | valid: 69 issues, 34 PRs, 541 issued sessions, 7 stages | 0.19 s |
| `git diff --check` | passed | below timer resolution |

The first in-sandbox aggregate run completed 397 tests in 218.129 seconds with
395 passing and two unchanged UNIX-socket cases failing at `listener.bind`
with `EPERM`. The exact aggregate command was rerun through the managed
escalation path and passed 397/397. Lean/Lake/full builds, cache warming against
the real repository, network, GitHub, endpoint, credential, canonical
state/metric, and authored-source actions were all zero.

## Findings

| Finding | Disposition |
|---|---|
| F068-A02-001 | Resolved in `HotMainCache._write_seed_journal`, `_load_seed_journal`, and `_recover_interrupted_seed`: filename globs only detect ambiguity; unowned/tampered/extra/wrong-identity state fails unchanged; `replace=false` is rechecked after recovery. |
| F068-A02-002 | Resolved by `_validate_lake_symlink_policy`: every lexical first hop and final target must stay within the private destination; writable and mode-read-only external targets are both rejected. |
| F068-A02-003 | Resolved in `seed` and `prepare`: registered-target authentication and journal recovery precede cache/input admission. Regressions invalidate `READY` and inject preflight failure after a real first-rename SIGKILL. |
| F068-A02-004 | Resolved in `_append_metric` and `_rollback_metric_append_locked`: rollback occurs under one continuous lock. Event-coordinated two-process short-write and fsync regressions preserve writer B exactly. |
| F068-A02-005 | Resolved in the corrected QPBT-067 report: mismatched `READY` returns false; quarantine is explicitly only a proposal. |
| F068-A02-006 | Resolved as an evidence/disposition correction: exact audit start/stop/elapsed and a four-lane interval sweep are recorded, unavailable per-command latency is `null` with a reason, and the QPBT-068 ordering violation is explicit. QPBT-067 remains unapproved. |
| F068-A02-007 | Resolved with symbol-qualified final-candidate anchors for protocol, initialization, readiness, journal, recovery, publication, and tests. |
| F068-A02-008 | Resolved as authenticated provenance with the QPBT-062 commit/tree/blob/size/SHA-256. Because that byte is absent from this candidate tree, approval remains deferred until it is manifest-listed in the next immutable review packet. |

## Integrity and remaining obligation

Base commit/tree are
`97e61b3487c762f1447576219dbd6cd85c162efa` /
`c3c35472e7ce33f0f664d7606ed8c798015ae2c6`. The frozen head/tree and
five-path hashes are supplied in the terminal result envelope after commit.
No `protocols/CHANGELOG.md` disposition is claimed here. A sequential binder
must update it after QPBT-044 releases the file, validate that changed head,
and obtain a fresh independent immutable review before integration.
