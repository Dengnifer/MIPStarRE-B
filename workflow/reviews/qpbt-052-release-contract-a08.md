# LPR-025 immutable review A02 retry

## Verdict

`request_changes`. Integration is blocked by the findings below. The review
used the exact formal base `4a6683795a71712d6a5c52b7539c2f532fd39f71` and
head `9d3b81b4c431d4b8e095d8dc94a8363c2ff07d84` (PR #26, issue/qpbt-052-
release-contract-a07). The branch merge base is
`b0d5c83f7aa215a3c37372a962cb82019ceefa2d`.

## Findings

### F-LPR025-A08-001 (blocker): durable `running` status bypasses release

At `scripts/workflow.py:1571-1578`, `release_required` is gated by
`bool(running or terminal or archived)`, i.e. by lifecycle events observed in
the log rather than the durable session status. A schema-valid marked
`codex-collaboration` row with `status: "running"`, a non-empty immutable
`external_id`, valid running timing, and only this event:

```text
session.issued({release_contract: "post-confirmation-v1", external_id: "thread-good"})
```

is accepted by both `validate_documents` and `validate_event_log`; no
`session.released` event is required. The same construction accepts `finished`
and `failed` rows when their terminal lifecycle event is absent. This is a
direct bypass of the documented contract (“Running now requires one
identity-bound `session.released` event”) and of the previously reported
F-LPR025-002 durable-running case. A crash after the sessions snapshot is
published but before its transition/release event is appended can leave this
accepted state as well. Derive the requirement from the marked durable status
and/or reject status/event mismatches, while retaining markerless legacy
compatibility; add regressions for running and terminal rows with missing
lifecycle events (and `session.started`/legacy ID variants if retained).

### F-LPR025-A08-002 (blocker): mutation rollback restores the changed target

`WorkflowStore.mutate` replaces `documents[filename]` with `changed_document`
before persistence (`scripts/workflow.py:1848-1859`). On an append or
post-validation failure, the rollback at `scripts/workflow.py:1862-1871`
restores sessions/events but writes `documents[filename]`, which is still the
*mutated* value, for every target other than `sessions.json`. Reproduction on
the exact head: mutate an `issues.json` title, inject an `append_event`
`RuntimeError`, and observe that the call raises while the title remains
`MUTATED` and the original file bytes differ. This leaves an unlogged ledger
mutation after a transient writer failure and contradicts the claimed exact
transaction boundary. Snapshot and restore the original target bytes (or an
exact original document) and add failure tests for every mutable state file,
including post-validation rejection.

### F-LPR025-A08-003 (blocker): public `WorkflowStore.mutate` defaults to an
unvalidated lifecycle path

The new `validate_events` argument defaults to `False` at
`scripts/workflow.py:1832-1847`, and post-append event validation is likewise
conditional at `scripts/workflow.py:1858-1861`. A caller can invoke this
public API on `sessions.json`, call `_transition_record` to move a marked
collaboration row from `issued` to `running`, and return successfully without
any release event; only a later `store.validate()` reports the invalid history.
The CLI opts in and the local-agent transaction validates after writing, but
the API promised by QPBT-052 (“CLI/API transition through one lock-held
pre/post event-log validation and rollback boundary”) remains bypassable.
Make issued-session lifecycle mutations unconditionally use the shared
validation/rollback path (or narrow the generic API so it cannot mutate session
status), and add a direct API regression with byte-preservation assertions.

## Authentication

- Repository: `Dengnifer/MIPStarRE-B`, PR #26, base ref `main`.
- Base: `4a6683795a71712d6a5c52b7539c2f532fd39f71`.
- Head: `9d3b81b4c431d4b8e095d8dc94a8363c2ff07d84`.
- Head tree: `3bb25c9933326774ec07d23cb97071e0c61aec5c`.
- Base tree: `0e2c01f4b63cd8292beb4399c7135c4d0d12ee65`.
- Merge base: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`.
- Sorted changed-path manifest SHA-256:
  `a7287a2f92263ef5d40635effc2702046157e3baf1666b4855a0d9e31f3ec9ac`.
- Changed paths are exactly: `protocols/CHANGELOG.md`,
  `protocols/orchestration.md`, `scripts/workflow.py`,
  `tests/test_local_agent.py`, `tests/test_workflow.py`,
  `workflow/reviews/qpbt-049-release-repair-a02.md`, and
  `workflow/reviews/qpbt-049-task-release-a01.md`.
- `AGENTS.md` was read from the authenticated candidate; no candidate or
  canonical files were modified.

## Validation

- `python3 tests/test_workflow.py`: 87/87 passed (1.17 s wall).
- `python3 tests/test_local_agent.py`: 65/65 passed (5.17 s wall).
- `python3 -m compileall -q scripts tests`: passed (0.03 s).
- `python3 scripts/workflow.py --root . validate`: valid; 52 issues, 24 PRs,
  407 issued sessions, 7 stages (0.16 s).
- `python3 scripts/check_workflow.py --root . --skip-tests`: valid (0.15 s).
- `git diff --check` for merge-base to head: passed.
- Aggregate `python3 -m unittest discover -s tests -p 'test_*.py'`: 369 tests;
  two errors were environment-only `PermissionError: [Errno 1] Operation not
  permitted` while tests created Unix sockets under the managed sandbox. No
  failure was attributable to the PR code.
- No Lean/Lake build, hot-cache action, tracked edit, workflow-state/metrics
  write, credential access, or GitHub write was performed. One read-only
  `gh pr view` authenticated the canonical PR metadata.

## Review identity and metrics

- Stable local name: `i025-reviewer-a02-pr26-retry`.
- Canonical task path/external identity: `/root/i025_reviewer_a02_pr26_retry`.
- Nested subagents: 0; topology: root coordinator -> this fresh reviewer.
- Token usage: `input=null`, `output=null`, `total=null`; the collaboration
  runtime exposes no per-agent token counters.
- Session elapsed: unavailable from the runtime; command wall times above are
  measured independently. No retries after the initial immutable checkout;
  the prior attempt's transient endpoint failure was not reused.

## Cutover overlap

The GitHub-canonical cutover candidate also changes `scripts/workflow.py` and
`tests/test_workflow.py` substantially (the current cutover diff is 434 and
340 lines respectively). Even though Git's three-way merge against the formal
base is textually clean, release-contract logic must be reapplied and
re-reviewed after cutover integration; do not cherry-pick this head blindly
over the canonical adapter changes.
