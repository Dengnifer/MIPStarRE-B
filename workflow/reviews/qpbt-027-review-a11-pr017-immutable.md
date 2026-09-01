# QPBT-027 / LPR-017 immutable review A11

## Findings

None.

## Verdict

`approve`.

The exact immutable candidate fixes the high-severity stale-append defect without
weakening the append-only finding ledger. No blocker, high, medium, or low
finding remains in the reviewed range.

## F-LPR017-001 disposition

`F-LPR017-001` is resolved.

The public `update pr` path now constructs a deep-copied complete candidate from
all assignments before invoking the PR guard (`scripts/workflow.py:2941-2945`).
The guard compares append-only lists and immutable finding identity against the
old record, then authenticates only each newly appended confirmation suffix
against the candidate's exact `base_sha` and `head_sha`
(`scripts/workflow.py:2503-2580`). Each new ID must be a unique string naming a
candidate review, differ from the resolution review, approve, have well-formed
strictly advancing chronology, and match the candidate base/head.

The complete document validator remains the second gate before persistence
(`scripts/workflow.py:514-679`, `scripts/workflow.py:1739-1755`). It supplies the
reviewer's terminal read-only role, same-PR and base binding, persistent identity,
and independence checks. Approval additionally requires current checks, a latest
current approving review, resolved findings, and a current resolution or
confirmation for every finding (`scripts/workflow.py:747-790`). Thus the update
guard and static validator have separate, non-conflicting jobs: the former proves
append-time currency for new suffixes; the latter validates the complete stored
history and current approval claim.

Existing confirmation prefixes are intentionally not rebound when a head later
advances. Their order and values remain immutable, static chronology remains
enforced, and a stale historical prefix cannot authorize `approved` or `merged`.
Newly appended findings are covered because their old confirmation prefix is
empty, so every supplied confirmation ID is authenticated. Existing findings
are covered by slicing after the exact old prefix. Removal, reorder, resolution
rewrite, duplicate IDs, missing reviews, wrong base/head, non-approve verdicts,
malformed timestamps, overlapping/out-of-order reviews, non-reviewer or
implementer sessions, wrong-PR reviewers, and open-finding confirmations all
fail either the update guard or the complete validator.

All six public assignment orders for `findings`, `reviews`, and `head_sha` were
independently probed in both directions. Six valid current-head orders persisted
the suffix and event; six stale-head orders failed with byte-identical PR and
event files. The committed public-path regression independently covers all six
stale orders for a newly appended finding and byte-for-byte rollback
(`tests/test_workflow.py:1711`). The historical-prefix regression confirms that
a legitimately current append survives a later head advance
(`tests/test_workflow.py:1741`).

No relevant public bypass was found for mutation of an existing PR. `update pr`
is the sole public evidence-field update path; nested evidence assignments are
rejected, lifecycle transition changes status only, and `add pr` creates a new
uniquely identified record rather than modifying an existing one. Every accepted
mutation undergoes complete cross-file validation before the PR replacement and
event append.

## Immutable identity

- Review worktree: `/tmp/qpbt-027-pr017-review-a11`.
- State: detached HEAD; final porcelain status empty.
- Immutable base: `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`.
- Base tree: `10f8da1ebb8b3fd7ce92dafee19d61fafe2cf8e2`.
- A05 parent / A01 head: `44ecdce96e5536407f89266b2be59820be56f01c`.
- A05 parent tree: `03e24c81b284f1b9f2e9bafbbc457e8c5f352e9e`.
- Candidate HEAD: `2c6b1f1d0be89d09bad2f60e074cf106be99fd46`.
- Candidate tree: `0c6fdd0f7ce5349b0f543e171871eb0ef292eab6`.
- Direct ancestry: candidate parent is exactly A05 parent; A05 parent is directly
  based on the immutable PR base; merge-base is exactly the immutable PR base.
- Full manifest digest (newline-delimited `git diff --name-only`):
  `814a1285e97c6e0d533fb0efb0ddb2ce3f198d26789973cb67aa06ebeaab244d`.
- Direct A05 manifest digest: `624e6c531937c17fa42bd0a4472a166dc6e96d3869c3b0f23762816a05c57815`.

The full base-to-head manifest is exactly six paths:

```text
protocols/CHANGELOG.md
protocols/review.md
scripts/workflow.py
tests/test_workflow.py
workflow/reviews/qpbt-027-finding-reconfirm-a01.md
workflow/reviews/qpbt-027-stale-append-fix-a05.md
```

The direct A05 delta is exactly `scripts/workflow.py`,
`tests/test_workflow.py`, and
`workflow/reviews/qpbt-027-stale-append-fix-a05.md`.

Report-source hashes independently recomputed:

- A01 report SHA-256:
  `1885c02167279996773fe29d31cf3665d225d02ffd494b02d743fe2437134e73`.
- A05 report SHA-256:
  `a442bc60c86ccae962c956ebe024f1b822792a9e9afbb9d81722458e954d5e61`.
- This A11 report's SHA-256 is necessarily recorded externally after the file is
  closed; it cannot self-embed its own digest.

## Validation

| Gate | Result | Timing |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py` | pass, 70/70 | unittest 0.651 s; wall 0.74 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'` | pass, 323/323 | unittest 183.881 s; wall 184.17 s |
| `PYTHONPYCACHEPREFIX=/tmp/qpbt-027-a11-pycache python3 -m compileall -q scripts/workflow.py tests/test_workflow.py` | pass | wall 0.21 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate` | pass: 27 issues, 16 PRs, 0 planned sessions, 322 issued sessions, 7 stages | wall 0.12 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py --skip-tests` | pass | wall 0.13 s |
| `git diff --check BASE..HEAD` | pass | wall 0.00 s |
| Public six-order positive/stale probe | pass, 6 accepted and 6 rejected with rollback | 0.156 s |
| Direct/static adversarial probe | pass, 1 guard positive, 10 guard rejections, 4 static cases | 0.003 s |

The extra adversarial cases covered existing and newly appended findings,
missing/duplicate/non-string IDs, resolution-ID reuse, wrong base/head,
non-approve verdict, malformed and out-of-order chronology, wrong reviewer role,
wrong reviewer PR, historical-prefix preservation, and refusal of approval from
only stale confirmation evidence.

## Residual risk

Static validation cannot reconstruct whether an already stored historical prefix
was current at the time it entered state; append-time provenance is established
prospectively by the public `update pr` guard. Out-of-band state edits or imports
therefore remain outside that temporal guarantee, although they must still pass
the full-history and current-approval rules. This is the intended boundary
between suffix authorization and static validation, not a bypass in the reviewed
public update path.

The rejection rollback checked here is pre-write atomicity: guard or complete
validation failure leaves both PR and event bytes unchanged. The pre-existing
store sequence is not a claim of crash-atomicity across an operating-system I/O
failure after the JSON replacement but before event append. No Lean, blueprint,
paper statement, build recipe, or cache behavior changed, so mathematical-source
fidelity and Lean build risk are not applicable to this PR.

## Actions and metrics

- New findings: 0. Reconfirmed resolved findings: 1 high (`F-LPR017-001`).
- Repository edits, canonical state writes, canonical metric writes, Git-state
  writes, issue creation, and PR mutation: 0.
- Report files written: 1, this `/tmp` report only.
- Required test commands: 2, both passed. Required compilation commands: 1,
  passed. Required workflow validation/check commands: 2, both passed.
- Additional adversarial probe commands: 2, both passed; 27 total bounded cases.
- Identity/diff/status check groups: 4 final groups, all passed.
- Subagents: 0. Topology: root coordinator -> this independent reviewer.
- Network requests, endpoints, GitHub operations, credentials, Codex CLI, Lean,
  Lake, build, and hot-cache actions: 0 each.
- Session elapsed: `null`; availability reason: the collaboration backend does
  not expose a canonical per-agent session duration.
- Token usage: input `null`, output `null`, total `null`; availability reason:
  per-agent token usage is not exposed by the collaboration backend.
- Incidents: 0. Protocol revisions made by this review: 0.
