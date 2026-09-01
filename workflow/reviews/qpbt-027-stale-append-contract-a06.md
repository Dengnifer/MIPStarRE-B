# QPBT-027 stale-append update contract A06

## Verdict

F-LPR017-001 is reproduced at exact candidate HEAD. The smallest complete
repair is an update-time old/candidate comparison performed once after all
assignments have been applied. Static historical validation must remain
distinct and must not re-authorize old confirmation prefixes against the PR's
later head.

No additional finding was identified.

## Derived contract

The public `update pr` transaction should have this shape:

```python
old_pr = record
candidate_pr = copy.deepcopy(old_pr)
for keys, value in assignments:
    _set_nested(candidate_pr, keys, value)
_check_pr_update(old_pr, candidate_pr)
replace_record(candidate_pr)
# StateStore.mutate then runs validate_documents on the complete state before
# writing prs.json or appending record.updated.
```

`_check_pr_update` should accept old and complete candidate records, not raw
assignments. It must enforce existing checks/reviews/implementer append-only
rules, integration immutability, finding identity/resolution immutability, and
the exact confirmation prefix. For every existing finding, define:

```python
old_ids = old_finding.get("confirmation_review_ids", [])
new_ids = candidate_finding.get("confirmation_review_ids", [])
suffix = new_ids[len(old_ids):]
```

Only `suffix` receives append-time authority checking. Each suffix ID must be a
string; the complete candidate list must contain no duplicate; the ID must name
a review in the complete candidate PR; and that review must:

- have `base_sha == candidate_pr["base_sha"]` and
  `head_sha == candidate_pr["head_sha"]` exactly;
- have verdict `approve`;
- begin no earlier than the completion of the finding's
  `resolved_by_review_id` review (using the repository's existing strict/fresh
  chronology rule);
- be backed, under complete-document validation, by a finished, read-only
  reviewer session bound to the same PR and PR base; and
- be independent of every implementer/orchestrator identity according to the
  existing reviewer-independence rules.

Missing/malformed review fields, malformed timestamps, unknown review IDs, or
malformed reviewer/session values fail closed as `WorkflowError` or aggregated
`ValidationError`, never an uncaught type error. Same-PR membership means both
that the review occurs in `candidate_pr.reviews` and its reviewer session is
bound to this PR; finding an identically named review elsewhere is insufficient.

The old prefix must be compared byte-for-byte/list-item-for-list-item but must
not be checked against the candidate head. It was authorized when appended and
is immutable historical evidence. Rechecking it would force forbidden evidence
rewrites after every legitimate head advance.

Assignment order is semantically irrelevant. In particular, permutations of
`reviews=...`, `findings=...`, and `head_sha=...` must all evaluate the same
final candidate and return the same result. Multiple assignments to one field
are governed by the final assembled value, with the old persisted record as the
sole prefix baseline; no intermediate assignment creates evidence.

## Static versus update-time authority

`validate_documents` answers whether a persisted historical state is
well-formed and whether its current status claim has current evidence. It may
therefore accept a `changes_requested` PR whose immutable confirmation prefix
was current when appended and became historical after a later head advance.

The update guard answers a different question: whether evidence newly entering
the immutable suffix is authoritative at this transaction's candidate
base/head. Static validation cannot reconstruct append time, so it cannot
replace this guard.

## Required regression matrix

Recommended public-CLI tests should snapshot `prs.json` bytes and event-log
bytes before each rejected command and assert both remain exactly unchanged.

| Case | Complete candidate | Expected |
|---|---|---|
| exact-current append | review is present, approving, exact candidate base/head, fresh and independent | accept |
| positive lifecycle | exact-current append; later separate head advance | append persists; advance demotes ready/approved as existing policy requires; historical prefix remains unchanged; validation accepts without evidence rewrite |
| stale head | suffix review binds old head | reject atomically |
| wrong base | suffix review binds different base | reject atomically |
| missing review | suffix ID absent from candidate reviews | reject atomically |
| non-approve | suffix review requests changes or has malformed verdict | reject atomically |
| malformed ID/list | non-string ID, non-list field, or malformed finding | reject cleanly and atomically |
| duplicate | duplicate within suffix or suffix duplicates prefix | reject atomically |
| chronology | confirmation starts before resolved-by review completes, overlaps it, or timestamp is malformed | reject atomically |
| wrong role/lifecycle | session writable, non-reviewer, unfinished, or malformed | reject atomically |
| wrong PR/base | reviewer session belongs to another/no PR or is based on another base | reject atomically |
| non-independent | reviewer is implementer/orchestrator or aliases an implementation identity | reject atomically |
| assignment permutations | all six orders of reviews/findings/head updates | identical result for identical final candidate |
| intermediate-only evidence | first assignment adds a valid suffix, later assignment removes/replaces it before validation | final candidate governs; no intermediate persistence |
| old-prefix tamper | remove, replace, reorder, or mutate old IDs | reject atomically |
| historical-prefix recheck trap | retain old exact prefix while advancing head | accept head update; do not demand new confirmation merely to preserve history |

Concrete test API recommendation: add a public CLI helper that writes fixture
state to a temporary store, captures `prs.json` and events bytes, invokes one
multi-`--set` update, and on expected failure asserts byte identity plus absence
of `record.updated`. Separately unit-test `_check_pr_update(old, candidate)` for
suffix extraction and exact current binding. Keep session/independence cases at
the public store layer because they require the complete documents.

## Adversarial evidence

Six behavioral in-memory probes plus one authentication probe were run against
the pinned candidate without repository writes:

1. exact-current fixture: accepted;
2. same fixture after head advance plus `changes_requested`: accepted, proving
   the required historical-prefix behavior;
3. stale-at-append suffix passed `_require_findings_update` and then static
   validation: accepted, reproducing F-LPR017-001;
4. duplicate confirmation IDs: rejected;
5. non-string confirmation ID: rejected;
6. missing confirmation review: rejected; and
7. exact review/report hash and Git identity/cleanliness authentication: passed.

The present mutation sequence calls `_check_pr_update(record, assignments)` at
`scripts/workflow.py:2863`, before applying assignments at line 2866. The guard
at lines 2503-2517 iterates raw assignments, and `_require_findings_update` at
lines 2462-2500 enforces only the confirmation prefix. `StateStore.mutate` at
lines 1739-1755 deep-copies state, runs full validation, then writes and appends
the event; a guard or validation rejection therefore occurs before persistence.

## Authentication and metrics

- Evidence cutoff: `2026-09-01T12:53:56.345159801+08:00`.
- Detached worktree: `/tmp/qpbt-027-pr017-review-a04`; clean before and after
  (`git status --short --branch` reported only `## HEAD (no branch)`).
- HEAD: `44ecdce96e5536407f89266b2be59820be56f01c`.
- HEAD tree: `03e24c81b284f1b9f2e9bafbbc457e8c5f352e9e`.
- Frozen A04 report SHA-256:
  `2fd2a123a2ed32b34d674509f4faf78fe398ee44add61270db570bd46a30d58e`.
- Findings: 0 additional (0 high / 0 medium / 0 low); inherited reproduced
  finding: 1 high.
- Probes: 7 total; unexpected outcomes: 0 relative to the pre-fix diagnosis.
- Recommended matrix: 16 cases, including 6 assignment-order permutations.
- Repository edits, canonical/metrics writes, Git writes, network/endpoint/
  GitHub/credential/Codex CLI actions, Lean/Lake/build/cache actions: 0 each.
- Nested agents: 0; topology: root coordinator -> this independent tester.
- Read-only shell commands: 15 across 8 execution groups; test-suite runs: 0;
  compile attempts: 0; workflow validation attempts: 0.
- Session elapsed: `null`; reason: the collaboration interface exposes neither
  a canonical per-agent start timestamp nor total elapsed duration.
- Tokens: `input=null`, `output=null`, `total=null`; availability reason:
  per-agent token usage is not exposed by the collaboration backend.

## Residual risk

This is a contract/design audit of the unfixed head, not validation of repaired
code. The largest residual risk is implementing suffix checking in an
assignment loop or reusing full static current-head checks on the old prefix.
The fixer must demonstrate complete-candidate order independence and rejected
transaction byte/event atomicity on the actual repair.
