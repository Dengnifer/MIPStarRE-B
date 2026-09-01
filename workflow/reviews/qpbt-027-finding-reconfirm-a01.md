# QPBT-027 append-only finding reconfirmation implementation A01

## Session identity and outcome

- Logical session: `i027-orchestrator-a01-finding-reconfirm`
- Role: sole writable orchestrator for QPBT-027
- Branch: `issue/qpbt-027-finding-reconfirm-a01`
- Worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-027-finding-reconfirm-a01`
- Immutable base / direct parent:
  `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`
- Base tree: `10f8da1ebb8b3fd7ce92dafee19d61fafe2cf8e2`
- Canonical session start: `2026-09-01T04:00:44.363566Z`
- Report freeze: `2026-09-01T04:30:26.270368692Z`
- Elapsed to report freeze: `1781.906803` seconds
- Token usage: `input=null`, `output=null`, `total=null`; availability reason:
  collaboration backend does not expose per-agent token usage
- Result: the contradictory approval/resolution invariant is replaced by a
  backward-compatible append-only reconfirmation contract; all implementation
  and local validation gates pass; fresh immutable PR review remains required.

The containing commit SHA and tree are reported separately because a report
cannot embed the identity of the commit containing its own bytes without a
circular dependency. The final candidate inventory is exactly the five owned
paths listed below.

## Evidence and decision

`AGENTS.md` was read completely before edits. Direct inspection established the
contradiction: `_validate_pr_evidence` required every resolved finding's
`resolved_by_review_id` to bind the current PR head before approval, while
`_require_findings_update` made that field immutable after resolution. A later
head therefore made honest approval impossible.

The independent QPBT-026 A15 critical-path audit confirmed the live LPR-016
instance and prescribed the smallest numbered repair:

```text
workflow/reviews/qpbt-026-stage2-critical-path-a15.md
sha256 266bd04517a5214d5a63c2058b685350268c56707ecafcd96acdccfa5295a17f
```

The selected representation is one optional `confirmation_review_ids` list on
each finding. Missing means an empty historical list, so existing canonical PRs
need no migration. Once resolved, the finding identity, status, disposition,
disposition evidence, and `resolved_by_review_id` remain permanent. A later
fresh review adds evidence instead of rewriting history.

## Implemented contract

### Confirmation validity

Every confirmation ID must be a unique non-empty string naming a review in that
same PR's `reviews` list. It must differ from the original resolution review,
have verdict `approve`, start no earlier than the preceding resolution or
confirmation completed, and complete strictly later. The chronological pointer
advances through the list, so reordering an existing history is invalid.

The same-PR and independence property is enforced through one complete identity
chain: confirmation ID -> review object in the current PR ->
`reviewer_session_id` -> issued session. Existing formal-review validation then
requires that session to be a read-only reviewer, `finished` or `archived`,
bound by `pr_id` to this PR and by `base_revision` to its base, persistently
identified, and distinct from implementers and linked-issue owners. Tests
exercise an implementer/non-reviewer reference and a reviewer session with no
PR binding explicitly.

### Approval and history

`approved` and `merged` still require a latest current-head approving review,
passing current checks, and no open finding. For each resolved finding, either
the immutable original resolution review or one appended confirmation must bind
the exact current PR base/head. Historical confirmations remain evidence but do
not authorize a later head.

This permits the realistic sequence covered by the positive fixture: A01
introduces F001; A02 resolves F001 while requesting changes for newly introduced
F002; A03 resolves F002, reconfirms F001 on the advanced head, and approves.
Removing F001's A03 confirmation makes final approval fail.

### Append-only update rule

PR review lists retain their existing prefix append-only guard. Finding updates
retain positional identity and introduction evidence. Once resolved, every
field except `confirmation_review_ids` remains byte-for-byte immutable; that
list may only extend its old prefix. Removal, replacement, reorder, identity
rewrite, disposition rewrite, evidence rewrite, and resolution-review rewrite
all fail. An absent list and an explicit empty list have the same history.

### Malformed-value safety

The bounded read-only A02 audit found that JSON-shaped arrays in adjacent enum,
review-reference, reviewer-lifecycle, same-PR provenance, and update fields
could raise `TypeError` at Python set membership instead of returning aggregated
validation evidence. Each reproduction was accepted as a high-severity concrete
safety defect in the exact confirmation surface. The smallest string/null guards
were added before those memberships, including the open-to-resolved update
transition. Valid state behavior is unchanged.

A02's final report has no open finding:

```text
workflow/reviews/qpbt-027-reconfirm-contract-a02.md
sha256 148c9e1596e8bab2fdc5071c4c57dc8f1cc337ce81005be12c2b926bacb9d5e2
canonical start 2026-09-01T04:05:40.946516Z
verification end 2026-09-01T04:20:46.033546278Z
canonical elapsed 905.087 seconds
```

The orchestrator read the complete `/tmp` report and independently recomputed
its hash. A02 passed the 67-test workflow module, a 26-case malformed/adversarial
matrix, canonical validation, chronology and reviewer matrices, and a public
`workflow.py update pr` persistence probe. The public append persisted, removal
failed, and the persisted evidence remained unchanged. Its transient report-path
copy was removed; the intended canonical copy is root-owned import work.

## Changed paths

Exactly these five owned paths change:

```text
protocols/CHANGELOG.md
protocols/review.md
scripts/workflow.py
tests/test_workflow.py
workflow/reviews/qpbt-027-finding-reconfirm-a01.md
```

No canonical state, research metric, Lean, blueprint, reference, dependency,
cache, or runtime file was edited.

## Regression matrix

The eight focused tests cover:

1. approval after head advancement with immutable original resolution plus an
   approving current-head confirmation;
2. rejection of that approval when the stale resolution has no confirmation;
3. duplicate, non-string, and unknown confirmation IDs;
4. malformed adjacent check, review, finding, PR, reviewer-session, and update
   values yielding validation errors rather than runtime crashes;
5. wrong-head and non-approving confirmation rejection;
6. a confirmation review that overlaps its predecessor rather than starting
   fresh;
7. non-reviewer/implementer and wrong-PR reviewer rejection; and
8. successful append with immutable resolved fields plus removal, replacement,
   rewrite, and malformed open-transition rejection.

## Validation

| Gate | Result |
| --- | --- |
| Eight focused reconfirmation tests | pass, 8/8 in 0.015 s |
| `python3 tests/test_workflow.py` | pass, 67/67 in 0.488 s |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | pass, 320/320 in 177.124 s |
| `python3 -m compileall -q scripts/workflow.py tests/test_workflow.py` | pass |
| `python3 scripts/workflow.py validate --json` | pass; 27 issues, 16 PRs, 0 planned sessions, 322 issued sessions, 7 stages |
| `python3 scripts/check_workflow.py --skip-tests` | pass |
| `git diff --check` | pass |

The final aggregate intentionally excludes Lean/Lake: this issue changes only
the Python workflow validator, its tests, and review protocol prose.

## Attempts and metrics

- Unit-test commands: 17 before the final post-report aggregate. Fifteen passed;
  one initial selector invocation failed because `tests` is not a Python package,
  and one new seven-test run exposed a second unguarded disposition membership.
  The invocation was corrected to the repository's direct test-file convention,
  and the missing guard was added. The passing aggregate progression was
  318 -> 319 -> 320 as the adversarial matrix expanded.
- The exact post-report aggregate was command 18 and the sixteenth passing test
  command; it repeated the stable 320/320 result.
- Python compilation attempts before report freeze: 5, all passed.
- Workflow validation attempts before report freeze: 4, all passed.
- Workflow checker `--skip-tests` attempts before report freeze: 3, all passed.
- Lean/Lake/project build attempts: 0; cache hit, lock wait, and build duration
  are not applicable.
- Subagents issued: 1. Topology: root coordinator -> this writable orchestrator
  -> `i027-tester-a02-reconfirm-contract`; the tester was read-only and spawned
  zero children.
- A02 findings: one high-severity malformed-value failure class, reported in
  four bounded installments as new fields reached the same unsafe membership
  pattern; all are resolved and replayed clean.
- Protocol revision: `0.1.8 candidate (QPBT-027)`; activation remains gated on
  independent immutable PR review.
- Network requests, endpoints contacted, GitHub reads/writes, credentials
  inspected/used, Codex CLI launches, Lean commands, Lake commands, hot-cache
  warm/seed/status operations, canonical state writes, and research metric
  writes: all 0.

## Residual risk

This change validates evidence recorded in the local workflow; it does not
prove the truth of a review report or authorize external disclosure. It does
not migrate historical records and intentionally treats a missing confirmation
list as empty. Malformed-value hardening is scoped to the confirmation,
formal-review, same-PR session provenance, and disposition-aware update paths
exercised by A02; it is not a claim that every unrelated validator field has
been fuzzed. The candidate still requires a fresh independent immutable review
of its exact base/head before protocol activation or integration.
