# LPR-022 changed-head resolution review

## Findings

No blocker, high, medium, or low findings remain at the authenticated head.

## Verdict

`approve`

The exact changed head resolves both findings introduced by
`review-qpbt-034-pr022-a02-immutable`. The backend-aware dispatch rule preserves
the governed Codex CLI null-ID launch lease, and the dispatch publication
transaction restores exact snapshots and re-raises `BaseException` at every
requested publication boundary. The candidate is suitable for formal adoption;
this review does not itself edit canonical PR, issue, protocol, or metrics state.

## Formal finding dispositions

### F-LPR022-001 - resolved, fixed

Verdict: `fixed`.

The admitted materialized prefix derives `confirmation_required_ids` only from
records whose immutable backend is `codex-collaboration`; missing and extraneous
confirmations are compared against that set at `scripts/workflow.py:1831` and
`scripts/workflow.py:1836`. The dry-run envelope uses the same backend predicate
at `scripts/workflow.py:2538`. A generic `external_id` override therefore does
not attest a collaboration launch, while a `codex-cli` candidate needs no
prelaunch confirmation and may remain null-ID while active.

The governed integration at `tests/test_local_agent.py:551` creates a committed
temporary worktree, dispatches a real `codex-cli` row with `external_id: null`,
claims it through `local_agent.run_exec`, invokes the fake runner once, and
imports the runner-returned thread ID into the terminal ledger and registered
artifact. The surrounding launcher claims before execution at
`scripts/local_agent.py:2975`, imports the terminal envelope at
`scripts/local_agent.py:2989`, and rejects a conflicting preexisting identity at
`scripts/local_agent.py:456`.

Independent replay: pass, 1 test, 0.466s test time / 0.84s wall. The 64-test
local-agent suite and 344-test aggregate suite independently pass as well.

### F-LPR022-002 - resolved, fixed

Verdict: `fixed`.

The guarded publication region covers the atomic `sessions.json` replacement,
each `session.issued` append, the `sessions.dispatched` append, and the final
event-log audit at `scripts/workflow.py:1884`. Its handler catches
`BaseException`, restores the captured sessions and event snapshots, and uses a
bare re-raise at `scripts/workflow.py:1926`.

The interrupt matrix at `tests/test_workflow.py:1786` injects
`KeyboardInterrupt` after all five required boundaries: sessions publication,
the first issuance event, the second issuance event, the summary event, and the
successful post-publication audit. Each subcase asserts exact pre-dispatch bytes,
successful validation, equality of preflight plans, and a successful retry at
`tests/test_workflow.py:1880`.

Independent replay: pass, 1 test with five boundary subcases, 0.466s test time /
0.84s wall. The focused 77-test workflow suite and aggregate suite independently
pass.

## Correctness and protocol review

- Collaboration-only confirmation: exact and fail-closed. Confirmation is
  derived after immutable materialization, so an override cannot change backend
  authority (`scripts/workflow.py:1825`, `scripts/workflow.py:1836`).
- Deterministic retry and capacity drift: unconfirmed or queued confirmations
  return before publication; the focused tests compare exact state/event bytes
  and identical repeated plans (`tests/test_workflow.py:1542`,
  `tests/test_workflow.py:1631`).
- Event chronology: the dispatcher computes one timestamp no earlier than the
  validated log tail, uses it for every issuance and summary event, then audits
  the complete lifecycle while still locked (`scripts/workflow.py:1865`,
  `scripts/workflow.py:1899`, `scripts/workflow.py:1925`).
- Nested capacity: every active non-coordinator row is counted independently;
  the root coordinator is excluded and parent/child nesting grants no free slot
  (`scripts/workflow.py:2044`, `tests/test_workflow.py:434`).
- Protocol truth: the spawn-first collaboration boundary, distinct governed CLI
  lease, aggregate capacity, exact rollback, and coordinator-attestation limit
  are stated consistently in `protocols/orchestration.md:29` and recorded as a
  candidate, not an activated revision, in `protocols/CHANGELOG.md:3`.
- Scope: the A03 repair changes the five implementation/protocol/test paths plus
  its evidence report, and materially addresses only the two A02 findings. No
  Lean statement, proof, source claim, endpoint, or credential behavior changes.

## Validation

| Command | Result | Measured time |
| --- | --- | ---: |
| `python3 tests/test_workflow.py WorkflowStoreTests.test_dispatch_rolls_back_keyboard_interrupt_at_every_publication_boundary -v` | pass, 1 test / 5 subcases | 0.466s test; 0.84s wall |
| `python3 tests/test_local_agent.py RuntimeTests.test_dispatch_then_governed_exec_imports_real_codex_cli_thread_id -v` | pass, 1/1 | 0.196s test; 0.69s wall |
| `python3 -m unittest discover -s tests -p 'test_workflow.py' -v` | pass, 77/77 | 1.285s test; 1.37s wall |
| `python3 tests/test_local_agent.py -v` | pass, 64/64 | 4.597s test; 4.71s wall |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | pass, 344/344 | 193.712s test; 194.05s wall |
| `python3 tests/test_check_workflow.py` | pass, 3/3 | 0.002s test; 0.05s wall |
| `python3 -m compileall -q scripts tests` | pass; cache redirected to `/tmp` | 0.36s wall |
| `python3 scripts/workflow.py validate` | pass: 35 issues, 21 PRs, 0 planned sessions, 375 issued sessions, 7 stages | 0.13s wall |
| `git diff --check 17608ac90f1896cc019e8a7a7619ada6a3c05cef..f672839e2d221cba44e70db6ab523eebdd4d0d4a` | pass | 0.01s wall |

The exact worktree remained clean after the checks. No Lean/Lake/cache build was
applicable to this Python/protocol-only change.

## Immutable manifest

- PR: `LPR-022`
- Base commit: `17608ac90f1896cc019e8a7a7619ada6a3c05cef`
- Base tree: `6d7e8918d1ff9bc19fa672923eaf339e56c2c535`
- Head commit: `f672839e2d221cba44e70db6ab523eebdd4d0d4a`
- Head tree: `119e7f038655033878c874b074cbcf9c477cba32`
- Merge base: exact PR base
- Diff: 7 paths, 1007 insertions, 43 deletions; base-scoped diff check clean
- A02 report SHA-256: `2371d3578022674699566184e2a75fa2f4f934a88a04a7f048b8184f4f9c3b6c`

The manifest hash is SHA-256 over these newline-terminated records in exact
displayed order:

```text
manifest-version=1
base-commit=17608ac90f1896cc019e8a7a7619ada6a3c05cef
base-tree=6d7e8918d1ff9bc19fa672923eaf339e56c2c535
head-commit=f672839e2d221cba44e70db6ab523eebdd4d0d4a
head-tree=119e7f038655033878c874b074cbcf9c477cba32
100644 4aa7d5a92cab5468368dd7d1043ef7c1eee084dd 24033 eaff089ae3a0dad1ce2ebeebff64f4de42314cc1ac3a571135f6d056944b131b protocols/CHANGELOG.md
100644 61f53c35ffa69ed61997dc97454e2963c1c4eb65 15124 c31cfde4c0dbece6af1cf24700a99b2702129e668e1e89b9bcae89341d5f1f30 protocols/orchestration.md
100644 7695df623ea4c1dad220411def36e30fa3df3f88 141266 04e0d92a5f52949322a4c5089269cc9f223b0e32f3ca36c3b6b6651ded0b02ab scripts/workflow.py
100644 75a8a33e1928da0dc8635abafb33cc7815f4d0b2 117762 71c249c9e3927e0e491498e4f8d0d5d20888ec2de3b437c5741e9a555dd4541d tests/test_local_agent.py
100644 04dd1a8e6f22ba7608f29652cf74d9d021a968fe 98446 cae992aaae2afe21ff37903e9345ae8b9e939da5699a1d67766ba3c743c65e0e tests/test_workflow.py
100644 c97e4b0c192664479703fd7c0e99fa864bb1b218 8993 81e60885fff4c8f8961105f3ffe8adfb33090032538b07e8208b0f0957e9390d workflow/reviews/qpbt-034-live-admission-a01.md
100644 72b0e1d21f7fdf626850ff946dbd3c392c51874d 7949 fef150cf4d9618817d414c69623d47e6109fbb2eaee7c479ede90c852d2ec837 workflow/reviews/qpbt-034-live-admission-a03.md
```

Manifest SHA-256:
`2f81f811a8043caf7a76b2e84cdc9830b395ac6a5fc600790c3fdd904ad925d5`.

## Residual risk

Collaboration identity remains a root-coordinator attestation because the local
CLI cannot query or authenticate the collaboration backend. A successful
bootstrap spawn followed by local authority drift must still be interrupted and
retired by the coordinator. Exact rollback also assumes the restoration writes
themselves complete; unrecoverable filesystem failure during restoration is
outside an in-process transaction's guarantee. These limits are accurately
disclosed by the candidate and do not leave either A02 finding open.

`workflow/README.md` retains the older dispatcher summary. It does not contradict
the backend-specific rule, but it omits the new operational confirmation
sequence; the canonical orchestration protocol is authoritative and the README
was outside QPBT-034's owned paths.

## Metrics and scope

- Stable session: `i034-reviewer-a04-pr022-resolution`
- External thread: `/root/i034_reviewer_a04_pr022_resolution`
- Topology: root coordinator -> one fresh read-only resolution reviewer; nested
  agents: 0
- Reviewer evidence start: `2026-09-01T13:55:45.387289181Z`
- Evidence cutoff: `2026-09-01T14:02:44.259621516Z`
- Agent-measured elapsed through evidence cutoff: `418.872332335s`
- Timing quality: agent wall-clock samples from the review environment
- Token usage: `{"input":null,"output":null,"total":null,"availability_reason":"Collaboration backend does not expose per-agent token usage"}`
- Findings: 0 new; 2 prior findings formally resolved (`high`: 1, `medium`: 1)
- Repository edits: 0; Git writes: 0; canonical state/event/metrics edits: 0
- Endpoint/network/GitHub/credential operations: 0
- Lean/Lake/cache/build operations: 0
- Agent spawns or nested dispatches: 0
- Adversarial replays: 2; test-suite commands: 5; validation/check commands: 4
- External actions/messages: 0

Only the assigned `/tmp/qpbt-034-pr022-resolution-a04.md` report path was
written. Its SHA-256 is supplied out of band to the root coordinator.
