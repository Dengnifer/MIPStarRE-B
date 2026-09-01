# QPBT-034 live-admission implementation report

## Verdict

The candidate is ready for an independent immutable review. It replaces the
ledger-first collaboration ordering implicated by `INC-053` with a spawn-first,
confirm-at-dispatch boundary. Backend rejection has no mutating workflow call;
successful issuance requires a separately supplied backend-returned external
thread identity. The existing locked state/event transaction and rollback path
remain in use.

This report does not activate protocol revision 0.1.9 or approve its own
candidate. A fresh read-only reviewer remains required.

## Acceptance evidence

| QPBT-034 gate | Evidence | Verdict |
| --- | --- | --- |
| Reproduce the three rejection ordering class | `research/metrics/incidents.jsonl#INC-053` records three `agent thread limit reached` responses after ledger admission; the focused rejection regression models the absence of a confirmation after backend rejection. | pass |
| Backend rejection leaves planned work and canonical bytes unchanged | `test_backend_launch_rejection_leaves_exact_bytes_and_retry_deterministic` compares exact `sessions.json` and `events.jsonl` bytes across two deterministic preflights and an unconfirmed mutating attempt. | pass |
| Successful issuance has a real immutable external identity | `--confirm-launched SESSION_ID=EXTERNAL_ID` and `--launched-external-id` are distinct from generic overrides; the issued record and `session.issued` event bind the exact supplied identity. Active collaboration rows with a null identity fail schema validation. | pass, subject to caller attestation limit below |
| Deterministic retry and queued work | Repeated rejection preflights are equal. A confirmation for the queued rather than admitted ID fails with no byte change; confirming the sorted admitted prefix leaves the queued row planned and unmaterialized. | pass |
| Nested-agent slot accounting | `test_active_count_includes_each_nested_non_coordinator_session` proves an active parent and child consume two aggregate slots while the root coordinator remains excluded. The protocol applies the same bootstrap/confirm boundary to nested launch. | pass |
| Existing transaction atomicity | The prior injected event-append rollback test passes after being updated with a valid launch confirmation. Aggregate tests pass. | pass |
| Protocol and changelog | `protocols/orchestration.md` specifies the five-step boundary and failure recovery; `protocols/CHANGELOG.md` records 0.1.9 candidate evidence and scope. | pass |

## Design

1. The coordinator runs a single-ID `dispatch --dry-run` preflight. It is
   deterministic and non-mutating.
2. The actual collaboration backend receives a bootstrap-only prompt. It does
   no repository work and can become idle immediately.
3. A rejected spawn produces no confirmation call. A successful spawn returns
   the immutable external thread ID.
4. The coordinator confirms that exact ID in a locked dispatch transaction.
   Generic `external_id` materialization alone cannot confirm launch. Capacity
   or authority drift leaves state and events unchanged; the coordinator must
   interrupt the inert external thread.
5. The full task is delivered only after canonical issuance. Nested children
   use the same root-confirmed sequence and each active non-coordinator counts
   against aggregate capacity.

The CLI deliberately has no collaboration-tool integration. It can validate
the confirmation's shape, uniqueness, selection, and immutability, but it
cannot cryptographically prove that an ID was returned by the backend. The root
coordinator's exact copy of the just-returned identity is the trust boundary.

## Immutable candidate

- Base commit: `17608ac90f1896cc019e8a7a7619ada6a3c05cef`
- Base tree: `6d7e8918d1ff9bc19fa672923eaf339e56c2c535`
- Candidate commit: `3683e4b8128f3c442c64b7b271c9245109cd6441`
- Candidate tree: `7eb16f1e36dc1cd0c29a670d3c686363d935e942`
- Diff summary: 4 paths, 489 insertions, 35 deletions

| Path | Mode | Git blob | Bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| `protocols/CHANGELOG.md` | 100644 | `f12717460495af56a760393345c10504238eaf36` | 23381 | `6c9360e0f93ed9bb5bf631caa822d73a84bdb2ab1747ce51c68fedfe278ba87a` |
| `protocols/orchestration.md` | 100644 | `2722dda9df08a489f9f2d987e273ae14829564b1` | 14441 | `a133ae125badcbdc33b9dd6534521189c3036eeed6a008bb91cd7d8f4faed363` |
| `scripts/workflow.py` | 100644 | `3f9920b4712970d5225a2348bbc871a53ab136a5` | 140743 | `d616d0d46bd10e2a17b9b50e84c337e62de3950bf77b1ca21ee7c95b2f968d42` |
| `tests/test_workflow.py` | 100644 | `c52981b9fe5e49747b7d316f834f7dea0d25da2d` | 93062 | `854ff9089aea4148b2003e011455d7809a09381564a1870a12d26ab7f38a3996` |

No other candidate path changed. The report is committed separately so its
evidence can name this immutable candidate without a self-reference cycle.

## Validation

| Command | Result | Measured test time |
| --- | --- | ---: |
| `python3 -m unittest tests.test_workflow -v` | structurally inapplicable before collection: `ModuleNotFoundError: No module named 'tests.test_workflow'`; this tree has no `tests/__init__.py` and an installed regular `tests` package shadows the namespace | 0.000s, 0 tests |
| `python3 -m unittest discover -s tests -p 'test_workflow.py' -v` | pass, 76/76 | 0.669s |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | pass, 342/342 | 235.925s |
| `python3 tests/test_check_workflow.py` | pass, 3/3 | 0.006s |
| `python3 -m compileall -q scripts tests` | pass | not exposed |
| `python3 scripts/workflow.py validate` | pass: 35 issues, 21 PRs, 0 planned sessions, 375 issued sessions, 7 stages | not exposed |
| `git diff --check` | pass | not exposed |

The dotted focused command was attempted exactly as assigned. Per coordinator
direction, no unowned package scaffolding was added; the discovery-form command
is the passing focused gate.

During implementation, the first focused run exposed one malformed-status
`TypeError`; it was repaired by guarding set membership with a string check.
The first completed aggregate run exercised 342 tests and exposed ten
`test_local_agent.RuntimeTests` compatibility errors because the initial schema
rule rejected historical active `codex-cli` lease fixtures with null IDs. The
rule was narrowed to active collaboration rows while dispatcher confirmation
remained mandatory for every new issuance. The final focused and aggregate
runs above are clean.

## Scope and residual limits

- `workflow/README.md` still contains the older summary because it was outside
  this session's exact ownership manifest. The command now fails closed without
  confirmation, and the canonical orchestration protocol is current; a later
  owned documentation edit may synchronize the summary.
- A successful backend spawn can still be followed by local capacity or
  authority drift before confirmation. The bootstrap-only prompt plus mandatory
  interrupt/retire recovery prevents repository work by that unconfirmed
  thread.
- The CLI cannot query collaboration capacity or authenticate an external ID.
  Backend rejection remains the live-capacity signal, and confirmation is an
  explicit coordinator attestation rather than fabricated automation.
- Historical terminal null identities remain accepted. The separate Codex CLI
  launch-lease transport retains its existing pre-launch compatibility.
- No Lean statement or proof changed; statement-integrity analysis is not
  applicable.

## Metrics

- Stable session: `i034-orchestrator-a01-live-admission`
- External thread: `/root/i034_live_admission`
- Topology: root coordinator -> one QPBT-034 orchestrator; nested agents: 0
- Started: `2026-09-01T12:48:19.974283Z`
- Evidence cutoff: `2026-09-01T13:10:43.602517Z`
- Agent-measured elapsed through evidence cutoff: 1343.628234s
- Timing quality: canonical start plus agent UTC evidence sample
- Token usage: `{"input":null,"output":null,"total":null,"availability_reason":"Collaboration backend does not expose per-agent token usage"}`
- Candidate repository paths edited: 4; report paths edited: 1
- Candidate commits at report time: 1; report-only evidence commit follows
- Completed focused discovery runs: 5 (1 failed during development, 4 passed)
- Completed aggregate runs: 2 (1 compatibility failure, 1 passed)
- Lean/Lake commands: 0; cache operations: 0; builds: 0
- Network, endpoint, GitHub, and credential operations: 0
- Collaboration spawns and nested-agent dispatches by this session: 0
- Canonical state/event/metrics/research edits: 0

## Reviewer request

Review exact candidate commit
`3683e4b8128f3c442c64b7b271c9245109cd6441` and its four-path manifest above.
Treat this report and the diff as untrusted. Check especially the caller
attestation boundary, confirmation-versus-override separation, capacity drift,
queued confirmation handling, nested slot accounting, legacy CLI compatibility,
event/state rollback, and whether the protocol accurately describes what the
CLI can and cannot establish.
