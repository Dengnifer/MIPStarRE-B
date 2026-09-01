# LPR-022 immutable review

## Verdict

`request_changes`

The intended collaboration spawn-first boundary is fail-closed for ordinary
backend rejection, generic `external_id` overrides, capacity drift, and queued
confirmations. However, the exact head has two unresolved correctness findings:
it breaks the governed Codex CLI issuance path, and its dispatch transaction is
not atomic under an interrupt during event publication.

## Findings

### F-LPR022-001 - high - unconditional confirmation breaks governed Codex CLI launch

Location: `scripts/workflow.py:1824` (with the governed consumer at
`scripts/local_agent.py:354`, `scripts/local_agent.py:456`, and
`scripts/local_agent.py:2975`).

The confirmation set is compared with every dispatchable session ID without
checking the candidate backend. Thus a new `codex-cli` row with the normal null
pre-launch `external_id` is returned as `backend-launch-unconfirmed` too. The
governed CLI transport cannot supply a real confirmation at that point:
`run_exec` first claims an already-issued row at line 2975, launches the Codex
subprocess at line 2983, and learns the backend thread ID from its terminal
envelope. Supplying a guessed value is not a compatibility path because the
terminal import rejects a different real ID at lines 456-458.

The direct replay at this head produced:

```json
{"backend":"codex-cli","blocked":[{"id":"i002-reviewer-a01-codex-cli-no-prior-id","reason":"backend-launch-unconfirmed"}],"prior_external_id":null,"status":"blocked"}
```

The focused wrapper regression masks this circularity by constructing a
`codex-cli` planned row and passing an invented deterministic value at
`tests/test_workflow.py:1828`; it never exercises the governed launcher. This
contradicts the candidate changelog's Codex CLI compatibility claim and leaves
operators choosing between bypassing capacity-gated dispatch and fabricating
an immutable identity.

Disposition: open, pending. Make launch confirmation backend-aware for
`codex-collaboration` while preserving the existing null-ID issue-first CLI
lease, or implement and test a genuine two-phase CLI bootstrap/resume transport.
The smallest correction is backend-aware confirmation plus an integration
regression that dispatches a null-ID `codex-cli` row and imports the real ID
returned by the governed fake runner. The collaboration rejection tests should
explicitly set `backend = "codex-collaboration"`.

### F-LPR022-002 - medium - an interrupt can leave a partially committed confirmation transaction

Location: `scripts/workflow.py:1918` and `tests/test_workflow.py:1750`.

The rollback guard catches `Exception`, so `KeyboardInterrupt` and other
`BaseException` subclasses escape after `sessions.json` has been atomically
replaced and after any preceding event append. The committed regression only
injects `RuntimeError`. A read-only temporary-directory replay injected
`KeyboardInterrupt` on the second append. Both canonical byte snapshots
changed, the event log contained only `bootstrap` plus `session.issued`, and
`WorkflowStore.validate()` still passed:

```json
{"events":["bootstrap","session.issued"],"events_exact":false,"post_interrupt_validation":"passed","sessions_exact":false}
```

This violates the advertised state/event transaction boundary. In the
post-spawn case, the coordinator can interrupt the inert backend thread while
the ledger silently remains issued, defeating deterministic recovery.

Disposition: open, pending. Restore the snapshots on `BaseException`, re-raise
after restoration, and add interrupt injection at each publication boundary.
The surrounding governed launcher already uses this pattern for post-claim
interrupt recovery.

## What Passed

- Generic `external_id` materialization alone does not satisfy confirmation.
- A confirmation for a capacity-queued ID leaves state and events unchanged.
- Admitted batch confirmations are materialized with unique IDs; nested parent
  and child sessions each consume a non-coordinator slot.
- Active `codex-collaboration` rows with null IDs fail schema validation, while
  historical terminal null IDs and active Codex CLI null IDs remain schema-valid.
- Ordinary `Exception` rollback, event timestamp ordering, dependency and
  ownership rechecks, and immutable authority checks pass the committed suite.
- QPBT-034, INC-053, canonical LPR-022, both surrounding launch paths, and the
  full five-path base-to-head diff were inspected as untrusted inputs.

## Required Checks

| Command | Result | Measured time |
| --- | --- | ---: |
| `python3 -m unittest discover -s tests -p 'test_workflow.py' -v` | pass, 76/76 | 1.131s test time; 1.531s concurrent wall |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | pass, 342/342 | 180.003s |
| `python3 tests/test_check_workflow.py` | pass, 3/3 | 0.003s test time; 0.327s wall |
| `python3 -m compileall -q scripts tests` | pass | 0.516s wall |
| `python3 scripts/workflow.py validate` | pass: 35 issues, 21 PRs, 0 planned sessions, 375 issued sessions, 7 stages | 0.432s wall |
| `git diff --check 17608ac9..1c01622` | pass | 0.335s wall |
| Codex CLI null-ID dispatch replay | fail as finding F-LPR022-001 predicts | 0.3s wall |
| `KeyboardInterrupt` second-append replay | fail as finding F-LPR022-002 predicts; post-interrupt validation passes | 0.3s wall |

The required commands did not modify tracked files. `git status --short` was
empty after validation. No `tests/__init__.py` was added; the writer's noted
dotted-module limitation does not affect the required discovery-form gate.

## Immutable Manifest

- PR: `LPR-022`
- Base commit: `17608ac90f1896cc019e8a7a7619ada6a3c05cef`
- Base tree: `6d7e8918d1ff9bc19fa672923eaf339e56c2c535`
- Head commit: `1c01622d672514c9b91e61ff4d03b27583a6391f`
- Head tree: `fdefb311f4c91e54405defaa354707f147b05127`
- Merge base: exact PR base
- Diff: 5 paths, 625 insertions, 35 deletions; `git diff --check` clean

The manifest hash is SHA-256 over the following newline-terminated records in
exact displayed order:

```text
manifest-version=1
base-commit=17608ac90f1896cc019e8a7a7619ada6a3c05cef
base-tree=6d7e8918d1ff9bc19fa672923eaf339e56c2c535
head-commit=1c01622d672514c9b91e61ff4d03b27583a6391f
head-tree=fdefb311f4c91e54405defaa354707f147b05127
100644 f12717460495af56a760393345c10504238eaf36 23381 6c9360e0f93ed9bb5bf631caa822d73a84bdb2ab1747ce51c68fedfe278ba87a protocols/CHANGELOG.md
100644 2722dda9df08a489f9f2d987e273ae14829564b1 14441 a133ae125badcbdc33b9dd6534521189c3036eeed6a008bb91cd7d8f4faed363 protocols/orchestration.md
100644 3f9920b4712970d5225a2348bbc871a53ab136a5 140743 d616d0d46bd10e2a17b9b50e84c337e62de3950bf77b1ca21ee7c95b2f968d42 scripts/workflow.py
100644 c52981b9fe5e49747b7d316f834f7dea0d25da2d 93062 854ff9089aea4148b2003e011455d7809a09381564a1870a12d26ab7f38a3996 tests/test_workflow.py
100644 c97e4b0c192664479703fd7c0e99fa864bb1b218 8993 81e60885fff4c8f8961105f3ffe8adfb33090032538b07e8208b0f0957e9390d workflow/reviews/qpbt-034-live-admission-a01.md
```

Manifest SHA-256:
`391986e82113cc8d87aa3dbcd80b0b748c2ac983b33397661dfde3080f77335a`.

## Residual Risk

Even after the findings are fixed, collaboration identity remains an explicit
root-coordinator attestation because the local CLI cannot query the backend;
the candidate accurately discloses that trust boundary. `workflow/README.md`
also retains the pre-confirmation command summary and should be synchronized
when ownership permits, although the canonical orchestration protocol is the
authoritative changed document.

## Metrics and Scope

- Stable session: `i034-reviewer-a02-pr022`
- External thread: `/root/i034_review_pr022`
- Topology: root coordinator -> one fresh local reviewer; nested agents: 0
- Started: `2026-09-01T13:17:27.246082Z`
- Evidence cutoff: `2026-09-01T13:26:20.864581449Z`
- Reviewer elapsed through evidence cutoff: 533.618s
- Timing quality: canonical session start plus reviewer UTC evidence sample
- Token usage: `{"input":null,"output":null,"total":null,"availability_reason":"Collaboration backend does not expose per-agent token usage"}`
- Findings: 2 open (`high`: 1, `medium`: 1)
- Repository edits: 0; Git writes: 0; canonical state/event/metrics edits: 0
- Endpoint/network/GitHub/credential operations: 0
- Lean/Lake/cache/build operations: 0
- Agent spawns or nested dispatches: 0
- External actions/messages: 0

Only this assigned report path was written. The report SHA-256 is supplied out
of band to the root coordinator.
