# QPBT-049 / LPR-025 Immutable Review A03

Verdict: `request_changes`

Candidate authentication:

- Base: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`
- Head: `687803efcfd2e092960435606e6eb1ff45cdcdf6`
- Head tree: `86da3fa54c1fa4ccdfdda7c31d2e348f64d23b22`
- Head parent: `d202aca7c352d5480bff3726539a3354d5176b52`
- Changed-path manifest SHA (packet): `eeb1e91987e812a849ed330aca52e4176f8289526e81cb3418b294aaa2dace19`
- Repair report SHA: `4ee1544e166b69cb048d5e8dfe27674af0413a1530c50125fc5a8cb0e4b8e407`
- Observed exact seven changed paths: `protocols/CHANGELOG.md`,
  `protocols/orchestration.md`, `scripts/workflow.py`,
  `tests/test_local_agent.py`, `tests/test_workflow.py`,
  `workflow/reviews/qpbt-049-release-repair-a02.md`, and
  `workflow/reviews/qpbt-049-task-release-a01.md`.
- Worktree was detached/clean at the authenticated head. No repository files
  were modified by this review.

## Findings

### F-LPR025-A03-001 (blocker): new validator rejects valid legacy history

`scripts/workflow.py:1525-1526` requires a `session.released` event for every
active or terminal `codex-collaboration` row with an external ID. The existing
canonical `workflow/events.jsonl` contains valid historical collaboration
sessions (for example `i001-auditor-a01-mipstarre-workflow`, issued at event
line 3 and finished/archive events at lines 6-7) with no release event. Running
the governed checker on the candidate (`python3 scripts/workflow.py --root .
validate`) exits 2 with 382 `collaboration session requires
post-confirmation release` errors. This violates the packet's requirement to
preserve valid legacy history and blocks validation of the canonical state.
The implementation needs an explicit compatibility boundary (for example,
recognizing pre-feature issuance records) while enforcing release for newly
confirmed collaboration launches.

### F-LPR025-A03-002 (high): direct CLI transition bypasses event-log validation

The release guard in `scripts/workflow.py:3184-3197` scans raw lines for any
matching release, then calls `WorkflowStore.mutate` at lines 3205-3209.
`WorkflowStore.mutate` validates documents but neither validates the existing
event log before mutation nor validates it after appending. A fixture with a
`session.released` line before `session.issued` is accepted by the direct
`transition issued-session ID running` CLI, which changes the row and appends
`record.transitioned`; a subsequent `store.validate()` rejects the resulting
state with `release event precedes session issuance`. Thus the governed CLI/API
path can create invalid lifecycle history and bypass the intended chronology
gate. The transition must use the same lock-held, pre/post event validation (and
rollback boundary) as the local-agent claim path.

### F-LPR025-A03-003 (high): equal timestamps permit release-before-issuance

`validate_event_log` stores line numbers but compares release and issuance only
by timestamp at `scripts/workflow.py:1518-1519`, and compares running/release only
by timestamp at lines 1527-1528. A release line placed before issuance with the
same ISO timestamp is accepted, including a running session with that history.
The release contract says release must be post-confirmation and the packet
explicitly calls out pre-issuance/reverse cases; semantic ordering must use the
event sequence (line number) as a tie-breaker, not permit equal-time inversion.

## Checks

- `python3 tests/test_local_agent.py`: passed, 65 tests, 4.196s test time.
- `python3 tests/test_workflow.py`: passed, 78 tests, 0.999s test time (the
  suite emits an expected argparse usage diagnostic while exercising rejection).
- `python3 -m compileall -q scripts tests`: passed.
- `git diff --check`: passed.
- `python3 scripts/workflow.py --root . validate`: failed, exit 2, 382 legacy
  collaboration-release errors.
- Lean/Lake/build/cache/network/GitHub/credential actions: 0.
- Compile attempts: 0 (Python compileall is not a Lean compile).
- Child agents: 0.
- Token usage: `null`; availability reason: runtime does not expose per-agent
  token counters.

The A02 repair report's claimed identity, wrong-scope, duplicate, and
wrong-external-ID checks were reproduced for isolated fixtures; the findings
above are additional compatibility and transaction/ordering defects on the
authenticated head.
