# QPBT-052 Release Contract A04 Review

Verdict: `request_changes`

## Findings

### A04-001 (P1): terminal lifecycle can precede the required release

`scripts/workflow.py:1540-1543` requires a marked collaboration session to
have some release event when a `running` or terminal event exists, but only
checks release chronology against `running`. It never checks the first
terminal event against release (nor release against archive). Consequently an
event log in the order `session.issued`, `session.finished`,
`session.archived`, `session.released` validates for an archived,
`post-confirmation-v1` collaboration session. A direct `validate_event_log`
probe reproduced this with exit result `PASS`.

This permits a release attestation to be recorded after the worker has already
finished or been archived, contrary to the stated contract that release is the
post-confirmation gate before terminal progression and the repair report's
claimed strict lifecycle chronology. Reject release when it is after terminal
or archive, and add a regression covering equal-timestamp and ordinary-time
orders.

### A04-002 (P1): issuance identity is not validated against the session

`scripts/workflow.py:1523-1527` validates the release payload's
`external_id`, but there is no corresponding check that the marked
`session.issued` payload's `external_id` equals the issued session's immutable
`external_id`. A direct probe with issuance `external_id="thread-wrong"`,
session/release identity `"thread-expected"`, and a valid release/running
sequence also returned `PASS`.

Dispatch emits the expected value at `scripts/workflow.py:1947-1957`, but
`validate_event_log` is the integrity boundary and must reject tampered or
malformed identity-bound issuance events. Add issuance-payload identity and
backend/contract consistency checks (with legacy markerless histories retained)
and a focused regression.

## Authentication

- Candidate commit: `40d3e565426f74a0e3c60798ec7e2b5f7e35cfbf`
- Candidate tree: `29c30cc8e5482a463f583ccad8eebe120a7a1f11`
- Candidate parent: `687803efcfd2e092960435606e6eb1ff45cdcdf6`
- Formal PR base: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`
- Candidate tree and parent match the release packet. Parent-to-candidate
  changed paths are exactly `scripts/workflow.py`,
  `tests/test_workflow.py`, and `tests/test_local_agent.py`.
- Supplied path SHA-256 values match:
  - `scripts/workflow.py`: `ffd1a7446e8054a22e77dc894690572c9bce6a3f3ec400f91ecdd0b1a7d011e5`
  - `tests/test_workflow.py`: `1c771b48859c3e57eb2954bb02e8406ad6cb2cb4d0322df96b5e0c317fa40c51`
  - `tests/test_local_agent.py`: `1740b745ae8d1244fb8529ddf130ba5eece23e34509d59718eb6e6b9250465b0`
- Repair report `/home/drx/MIPStarRE-auto/workflow/reviews/qpbt-052-release-contract-repair-a03.md`
  SHA-256: `591730f6940c2eb8d27caf88d1c8dd188138fcc18b5beac84157268c4f1544af`.
- `AGENTS.md` SHA-256: `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c`.

## Validation

All commands were run read-only in `/tmp/qpbt-052-review-a04`:

| Command | Result | Timing |
| --- | --- | ---: |
| `python3 tests/test_workflow.py` | 82 tests passed | 1.539 s |
| `python3 tests/test_local_agent.py` | 65 tests passed | 5.051 s |
| `python3 -m compileall scripts/workflow.py scripts/local_agent.py tests/test_workflow.py tests/test_local_agent.py` | passed | <1 s |
| `python3 scripts/check_workflow.py --skip-tests` | `workflow state: valid` | <1 s |
| `python3 scripts/workflow.py --root /tmp/qpbt-052-review-a04 validate` | valid; 52 issues, 24 PRs, 407 issued sessions, 7 stages | <1 s |
| `git diff --check` | passed | <1 s |

Additional read-only probes reproduced A04-001 and A04-002 as described above.
No network, GitHub, Lean/Lake build, cache write, workflow-state mutation, or
subagent was used.

## Residual risk

The focused suites cover release presence, duplicate/pre-issuance chronology,
release identity, backend scope, CLI rollback, and legacy compatibility, but do
not cover release-after-terminal/archive or issuance identity mismatch. The
candidate tests therefore do not detect either finding.
