# Local-Agent Cutover Transaction Repair A03

## Identity

- Canonical issue: GitHub #31
- Pull request: GitHub #29 repair follow-up
- Stable orchestrator session: `i031-orchestrator-a03-local-agent-binding`
- Orchestrator external ID: `/root/i031_orchestrator_a03_local_agent_binding`
- Reviewed base SHA: `9711e638013fa10de31196e2d21bd81abdd75e28`
- Implementation commit: `1312256c4a7e3649839952a048dc2d6f66999f28`
- Implementation tree: `e4461dbc5704574fb32a1b8637f1f76fec9ccbe6`

## Baseline Failure

The three post-cutover local-agent paths named in the dispatch packet failed
before any state transition. `claim_issued_session` and the governed
`run_exec` path, including a migrated pull-request claim, reached
`WorkflowStore.append_event` without `_event_binding` and raised:

```text
WorkflowError: GitHub-canonical event append requires its bound event transaction
```

The focused reproduction command ran 3 tests and produced 3 errors in 0.398s.
The prior 126-test workflow-only scope did not exercise `local_agent`'s
`_session_transaction` consumers, so it could not detect this cross-module
regression. The local-agent suite had to be included in the aggregate gate.

## Repair

`_session_transaction` now detects the active cutover while holding the store
lock, opens exactly one `WorkflowStore._open_cutover_event_log()` binding, and
uses that binding for initial and final event validation, append, and rollback.
The exact state/event/artifact snapshots are captured before publication;
rollback delegates the event restoration to the bound descriptor and restores
the artifact independently. A `finally` closes the descriptor pair on
success, idempotent no-op, validation error, publication error, and rollback
error. The pre-cutover path retains pathname-based event snapshots and
creation behavior.

Added local-agent regressions cover:

- successful cutover claim and terminal import, including an identical retry
  with byte-exact state/event/artifact preservation;
- a canonical event-leaf symlink swap at the append boundary, proving state
  and the displaced original inode are restored while the alternate target is
  unchanged; and
- canonical event-leaf removal at import append, proving state and event bytes
  are restored and the newly written terminal artifact is removed.

## Validation

- Initial reproduction: the three named tests, `3` errors, `0.398s`.
- Focused repaired regressions: `3/3` passed in `0.302s`.
- `python3 tests/test_local_agent.py`: `80/80` passed, elapsed `7.70s`.
- `python3 tests/test_workflow.py`: `126/126` passed, elapsed `3.10s`.
  The expected argparse usage line is emitted by an existing invalid-argument
  regression and does not indicate a failed test.
- `python3 scripts/check_workflow.py --root . --skip-tests`: passed, elapsed
  `0.20s` (`workflow state: valid`).
- `PYTHONPYCACHEPREFIX=/tmp/i031-a03-pycache2 python3 -m compileall -q
  scripts/local_agent.py tests/test_local_agent.py`: passed, elapsed `0.27s`.
- `git diff --check`: passed.

Changed-file SHA-256 values at the implementation commit:

- `scripts/local_agent.py`: `9075c1a710aede48ca48d0f8c67b9f0ed8bf159f4a80eaa4bb57a5800de04521`
- `tests/test_local_agent.py`: `659e6edfc96464572898830eb9917ebd61c7f90c41d5ec66e26634541e570512`

## Residual Risk

- The bound descriptor implementation is intentionally Linux-specific (`/proc/self/fd`,
  `dir_fd`, `O_NOFOLLOW`) and follows the workflow store's existing Linux
  directory-lock contract.
- As with the surrounding workflow store, a power loss between the state-file
  rename and event append is not a single-filesystem atomic commit; the
  in-process guarded failure path is byte-exact and covered by the tests.
- This repair does not attempt to reconstruct a directory replaced by an
  external process; the binding fails closed when its directory identity
  changes.

## Scope And Availability

Only the following leased paths changed: `scripts/local_agent.py`,
`tests/test_local_agent.py`, and this report. No GitHub mutation, push,
canonical state/metrics edit, Lean file edit, credential access, or subagent
dispatch occurred. Token usage was not exposed by the local runner; it is
recorded as unavailable rather than estimated.
