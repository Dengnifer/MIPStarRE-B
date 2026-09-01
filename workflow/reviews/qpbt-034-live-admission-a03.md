# QPBT-034 A03 finding repair report

## Verdict

The changed candidate resolves exactly `F-LPR022-001` and `F-LPR022-002` and
is ready for a fresh immutable resolution review. It does not approve itself or
activate protocol revision 0.1.9.

The repair makes prelaunch confirmation specific to `codex-collaboration`,
preserves governed `codex-cli` issue-first launch with a null external ID, and
restores exact dispatch snapshots for every `BaseException` publication
failure before re-raising it. No change to `scripts/local_agent.py` was needed.

## Finding dispositions

### F-LPR022-001 - fixed, pending independent confirmation

The dispatcher now materializes the admitted prefix, derives the confirmation
set only from candidates whose immutable backend is `codex-collaboration`, and
rejects missing or extraneous confirmations against that set. The plan's
`launch_confirmation_required` result and summary event use the same backend
rule. All collaboration rejection, generic-ID, queue, batch, and rollback
fixtures now identify their backend explicitly.

Governed CLI compatibility is exercised end to end by
`test_dispatch_then_governed_exec_imports_real_codex_cli_thread_id`. It creates
a real temporary Git worktree, dispatches a capacity-gated `codex-cli` row with
`external_id: null` and no launch confirmation, invokes the governed
`local_agent.run_exec` path with `FakeRunner`, and validates claim, runner
execution, terminal artifact import, and the actual returned thread ID in the
canonical terminal row. No prelaunch identity is fabricated.

Disposition evidence: `scripts/workflow.py`, `tests/test_workflow.py`,
`tests/test_local_agent.py`, and the 64/64 governed-agent plus 344/344 aggregate
results below.

### F-LPR022-002 - fixed, pending independent confirmation

The dispatch transaction now catches `BaseException`, invokes the existing
exact sessions/event snapshot restoration, and re-raises. The interrupt matrix
uses a two-session collaboration batch and injects `KeyboardInterrupt` after:

1. atomic publication of `sessions.json`;
2. publication of the first `session.issued` event;
3. publication of the second `session.issued` event;
4. publication of the `sessions.dispatched` summary; and
5. the successful post-publication audit, identified explicitly by the event
   log tail rather than a call ordinal.

Every subcase proves exact pre-dispatch sessions/event bytes, successful
canonical validation, equality of the preflight plan before and after the
interrupt, and a successful deterministic retry.

Disposition evidence: `scripts/workflow.py`,
`test_dispatch_rolls_back_keyboard_interrupt_at_every_publication_boundary`,
and the focused and aggregate results below.

## Immutable repair candidate

- Reviewed repair base: `1c01622d672514c9b91e61ff4d03b27583a6391f`
- Reviewed repair base tree: `fdefb311f4c91e54405defaa354707f147b05127`
- Repair candidate: `7811f53c00bf168416650cf19e7e51002e6e7cb7`
- Repair candidate tree: `a106f51c33a5f9b5813a50fd3d214ef124be6e27`
- A02 review SHA-256: `2371d3578022674699566184e2a75fa2f4f934a88a04a7f048b8184f4f9c3b6c`
- Repair diff: 5 paths, 284 insertions, 51 deletions

| Path | Mode | Git blob | Bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| `protocols/CHANGELOG.md` | 100644 | `4aa7d5a92cab5468368dd7d1043ef7c1eee084dd` | 24033 | `eaff089ae3a0dad1ce2ebeebff64f4de42314cc1ac3a571135f6d056944b131b` |
| `protocols/orchestration.md` | 100644 | `61f53c35ffa69ed61997dc97454e2963c1c4eb65` | 15124 | `c31cfde4c0dbece6af1cf24700a99b2702129e668e1e89b9bcae89341d5f1f30` |
| `scripts/workflow.py` | 100644 | `7695df623ea4c1dad220411def36e30fa3df3f88` | 141266 | `04e0d92a5f52949322a4c5089269cc9f223b0e32f3ca36c3b6b6651ded0b02ab` |
| `tests/test_local_agent.py` | 100644 | `75a8a33e1928da0dc8635abafb33cc7815f4d0b2` | 117762 | `71c249c9e3927e0e491498e4f8d0d5d20888ec2de3b437c5741e9a555dd4541d` |
| `tests/test_workflow.py` | 100644 | `04dd1a8e6f22ba7608f29652cf74d9d021a968fe` | 98446 | `cae992aaae2afe21ff37903e9345ae8b9e939da5699a1d67766ba3c743c65e0e` |

No other repair-candidate path changed. This report is committed separately so
it can bind the immutable candidate without a self-reference cycle.

## Validation

| Command | Result | Test time |
| --- | --- | ---: |
| `python3 tests/test_workflow.py WorkflowStoreTests.test_dispatch_rolls_back_keyboard_interrupt_at_every_publication_boundary -v` | pass, 1 test with 5 publication-boundary subcases | 0.668s |
| `python3 tests/test_local_agent.py RuntimeTests.test_dispatch_then_governed_exec_imports_real_codex_cli_thread_id -v` | pass, 1/1 | 0.229s |
| `python3 -m unittest discover -s tests -p 'test_workflow.py' -v` | pass, 77/77 | 1.169s |
| `python3 tests/test_local_agent.py -v` | pass, 64/64 | 3.943s |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | pass, 344/344 | 175.619s |
| `python3 tests/test_check_workflow.py` | pass, 3/3 | 0.002s |
| `python3 -m compileall -q scripts tests` | pass | not exposed |
| `python3 scripts/workflow.py validate` | pass: 35 issues, 21 PRs, 0 planned sessions, 375 issued sessions, 7 stages | not exposed |
| `git diff --check` | pass | not exposed |

One initial focused invocation used the repository-inapplicable dotted module
form and failed before collection because `tests` is not a local package. It was
immediately corrected to direct script invocation; no package scaffolding or
scope expansion was introduced. All substantive focused runs passed.

## Protocol accuracy and limits

- The collaboration CLI still cannot query backend capacity or authenticate a
  returned external ID. The root coordinator's exact copy remains the disclosed
  attestation boundary.
- A spawned collaboration bootstrap can encounter local authority drift before
  confirmation. It remains inert and must be interrupted when the confirmation
  transaction fails.
- Governed CLI launch is intentionally different: dispatch is issue-first with
  a null ID, the lease validates authority before execution, and terminal import
  records the real runner ID once.
- Catching `BaseException` preserves transaction bytes across interrupts; if
  restoration itself encounters an unrecoverable filesystem failure, that
  failure remains outside what an in-process transaction can guarantee.
- `workflow/README.md` remains deferred and unowned as directed. The canonical
  orchestration protocol and changelog now describe the backend-aware rule.
- No Lean statement or proof changed; statement integrity is not applicable.

## Metrics and scope

- Stable session: `i034-orchestrator-a03-live-admission-fixes`
- External continuation: `/root/i034_live_admission#continuation:a03`
- Topology: root coordinator -> one A03 repair orchestrator; nested agents: 0
- Started: `2026-09-01T13:31:09.566627Z`
- Candidate evidence cutoff: `2026-09-01T13:42:52.376230Z`
- Agent-measured elapsed through candidate cutoff: 702.809603s
- Timing quality: canonical start plus agent UTC evidence sample
- Token usage: `{"input":null,"output":null,"total":null,"availability_reason":"Collaboration backend does not expose per-agent token usage"}`
- Candidate paths edited: 5; report paths edited: 1
- Repair commits at report time: 1; report-only evidence commit follows
- Substantive focused runs: 4, all passed; invocation-form corrections: 1
- Aggregate runs: 1, passed; aggregate retries: 0
- Lean/Lake commands: 0; cache operations: 0; builds: 0
- Network, endpoint, GitHub, and credential operations: 0
- Collaboration spawns and nested-agent dispatches by this session: 0
- Canonical state/event/metrics/research edits: 0

## Resolution-review request

Review exact repair candidate
`7811f53c00bf168416650cf19e7e51002e6e7cb7` against base
`1c01622d672514c9b91e61ff4d03b27583a6391f` using the five-path manifest
above. Treat this report and the diff as untrusted. Re-run both adversarial
replays and verify that no behavior beyond `F-LPR022-001` and `F-LPR022-002`
was changed materially.
