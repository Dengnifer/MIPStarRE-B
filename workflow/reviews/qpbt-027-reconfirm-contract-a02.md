# QPBT-027 append-only reconfirmation contract audit

## Findings

No open findings remain in the final live snapshot.

Resolved during this audit, high severity: malformed JSON-shaped values in the
confirmation evidence path initially escaped as `TypeError` instead of being
aggregated into `ValidationError`. Reproductions included array-valued review
verdicts, finding enums and review IDs, confirmation-reviewer lifecycle and
same-PR provenance fields, PR status, and timing quality. The disposition-aware
update helper also crashed when an open finding's proposed status was an array.
The orchestrator accepted each reproduction and applied the smallest fix:
string/null guards before enum and set membership, plus a guarded open-to-resolved
transition. Current guards are at `scripts/workflow.py:483`,
`scripts/workflow.py:529`, `scripts/workflow.py:540`,
`scripts/workflow.py:600`, `scripts/workflow.py:975`,
`scripts/workflow.py:1067`, `scripts/workflow.py:1070`,
`scripts/workflow.py:1131`, `scripts/workflow.py:1190`, and
`scripts/workflow.py:2498`. Regression coverage is at
`tests/test_workflow.py:949` and `tests/test_workflow.py:1094`. Final replay:
26 malformed/adversarial cases, zero crashes and zero unexpected acceptances.

No smaller unresolved behavior was found. In particular, a public
`workflow.py update pr` probe proved that successful confirmation append is
wired through parsing, `_check_pr_update`, `WorkflowStore`, validation, and
persistence; removal then failed with `WorkflowError` and left persisted
evidence unchanged. Absence of a second store-level regression is therefore
not a finding: the direct helper test exercises the policy core and the public
path has no missing behavior.

## Contract assessment

| Requirement | Evidence and verdict |
| --- | --- |
| Backward compatibility | Missing `confirmation_review_ids` defaults to `[]` at `scripts/workflow.py:595`. The positive fixture includes a current-head resolved finding without the field at `tests/test_workflow.py:284`; `tests/test_workflow.py:921` passes. |
| Current base/head approval | The latest current-base/head review must approve and every resolved finding must bind through its resolution or confirmations to the current pair at `scripts/workflow.py:700`, `scripts/workflow.py:755`, and `scripts/workflow.py:763`. Stale and wrong-head tests are at `tests/test_workflow.py:926` and `tests/test_workflow.py:1005`. Exact. |
| Real formal same-PR independent finished reviewer | Every referenced review is globally checked against an issued, read-only reviewer session that is terminal, PR/base bound, persistently identified, and independent at `scripts/workflow.py:525` through `scripts/workflow.py:539`. Explicit implementer and wrong-PR cases are at `tests/test_workflow.py:1040`. Exact. |
| Duplicate, non-string, unknown, wrong-head, non-approving | Unique string parsing is at `scripts/workflow.py:219`; confirmation lookup and approval are at `scripts/workflow.py:651` and `scripts/workflow.py:660`. Tests are at `tests/test_workflow.py:934` and `tests/test_workflow.py:1005`. All reject. |
| Chronological freshness | Each confirmation must start after the prior review completed and complete strictly later; the prior pointer advances through the list at `scripts/workflow.py:662` through `scripts/workflow.py:679`. The overlap regression is at `tests/test_workflow.py:1020`; an extra two-confirmation probe accepted ordered IDs and rejected their reversal. Exact. |
| Resolved-field immutability and append-only history | Review lists remain prefix append-only. Finding identity/introduction data and resolved dispositions are immutable, while confirmation IDs may only extend their old prefix at `scripts/workflow.py:2462` through `scripts/workflow.py:2500`. Tests at `tests/test_workflow.py:1061` cover append, removal, replacement, resolved-field rewrites, and malformed open transitions. Exact. |
| Malformed values fail as validation errors | Container/item fuzzing of the optional field plus adjacent check, review, finding, PR, session, and update fields now yields only `ValidationError` or intentional `WorkflowError`; no runtime exception remains in the tested surface. Covered at `tests/test_workflow.py:949`. Exact for the requested surface. |

## Validation

- `env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/tmp python3 -B -m unittest discover -s tests -p test_workflow.py -v`: PASS, 67/67 tests.
- `env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/tmp python3 -B scripts/workflow.py validate`: PASS; 27 issues, 16 PRs, 0 planned sessions, 322 issued sessions, 7 stages.
- In-memory malformed matrix: PASS; 26 cases, `unexpected=[]`.
- In-memory formal reviewer matrix: valid reviewer PASS; wrong PR, unfinished, writable, wrong role, unknown session, and implementer-as-reviewer all rejected with `ValidationError`.
- In-memory multi-round chronology: ordered two-confirmation chain PASS; reversed chain rejected with both freshness diagnostics.
- Public update probe in `/tmp`: append persisted `['review-003']`; removal raised `WorkflowError`; persisted list remained unchanged.

No Git, network, GitHub, endpoint, credential, Codex, Lean, Lake, or cache
operation was invoked. Canonical repository files, workflow state, metrics,
and Git were not changed. Report-path incident: the patch helper initially
resolved the report name against the repository root; that transient copy was
immediately moved unchanged to the required `/tmp` path, and the root path was
verified absent.

## Session record

- Logical name: `i027-tester-a02-reconfirm-contract`
- External ID: `/root/i027_orchestrator_a01_finding_reconfirm/i027_tester_a02_reconfirm_contract#logical:i027-tester-a02-reconfirm-contract`
- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-027-finding-reconfirm-a01`
- Supplied branch/base: `issue/qpbt-027-finding-reconfirm-a01` / `506ac7a7b57a2318e0764acfc2558dc62f9e50f0` (not independently queried because Git invocation was prohibited)
- Canonical issued/start: `2026-09-01T04:05:40.946516Z`
- Verification end: `2026-09-01T04:20:46.033546278Z`
- Canonical elapsed: `905.087` seconds
- Tester-observed first clock sample: `2026-09-01T04:05:15Z`; observed sample interval to verification end: `931.034` seconds. This predates the parent-provided canonical ledger start and is recorded separately rather than substituted for it.
- Token usage: `input=null`, `output=null`, `total=null`; availability reason: `not exposed`
- Subagents spawned by this session: `0`
