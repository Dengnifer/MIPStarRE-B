# QPBT-027 post-review ledger scout A10

## Verdict

`blocked-as-requested; one fresh correctly bound review is required`.

An approving A08 report cannot be entered as a formal LPR-017 review.  At the
authoritative checkpoint `0b6b6bbee56af367d90e72e74a77b81fef7ea918`, the
issued session `i027-reviewer-a08-pr017-immutable` has immutable
`base_revision = 2c6b1f1d0be89d09bad2f60e074cf106be99fd46`, while LPR-017 has
`base_sha = 506ac7a7b57a2318e0764acfc2558dc62f9e50f0`.  The candidate validator
requires a formal reviewer session's `base_revision` to equal the PR
`base_sha` (`scripts/workflow.py:523-535`), and the public session updater makes
`base_revision` immutable (`scripts/workflow.py:2595-2628`).  Appending A08 to
`reviews` therefore fails complete-document validation.  Neither changing A08
nor changing LPR-017's immutable base is a valid repair.

The smallest honest route is to freeze and archive A08 as nonbinding review
evidence, record the dispatch-binding incident, and issue a new fresh reviewer
session with `base_revision = 506ac7a...` while its detached worktree remains at
the exact candidate head `2c6b1f1...`.  Only that new terminal approving review
may resolve F-LPR017-001 and unlock the remainder of the requested sequence.

## Authority and authenticated evidence

- Read-only source of canonical state: commit
  `0b6b6bbee56af367d90e72e74a77b81fef7ea918`, tree
  `d88d1b673b9c6e668dd989ddadd4096d9f2299cb`.  All state facts below came from
  `git show CHECKPOINT:workflow/state/{issues,prs,sessions,stages}.json`, not the
  older files in the candidate worktree.
- Candidate: commit `2c6b1f1d0be89d09bad2f60e074cf106be99fd46`, tree
  `0c6fdd0f7ce5349b0f543e171871eb0ef292eab6`; detached scout worktree was clean.
  It is a direct child of A04 head `44ecdce96e5536407f89266b2be59820be56f01c`.
- LPR-017 is `changes_requested`, exact base/head `506ac7a.../2c6b1f1...`, with
  exact-current passed checks.  F-LPR017-001 is open/pending and was introduced
  by A04 at historical head `44ecdce...`.
- A08 has now returned `approve`, no new findings, and explicitly resolves
  F-LPR017-001.  Its frozen `/tmp/qpbt-027-review-a08-pr017-immutable.md`
  SHA-256 is
  `e6f610c8ebde2959e8d987f2baced343a994f94cca4c247a637055c51ca194e0`.
  The report correctly authenticates PR base/head `506ac7a.../2c6b1f1...`; the
  blocker is solely the contradictory immutable A08 session field in canonical
  `sessions.json`, not a defect in the report's reviewed range.
- A04 report `workflow/reviews/qpbt-027-review-a04-pr017-immutable.md` has
  SHA-256 `2fd2a123a2ed32b34d674509f4faf78fe398ee44add61270db570bd46a30d58e`.
  It requires suffix-only exact-current authorization.  A05 report
  `workflow/reviews/qpbt-027-stale-append-fix-a05.md` has SHA-256
  `a442bc60c86ccae962c956ebe024f1b822792a9e9afbb9d81722458e954d5e61`
  and records 70/70 workflow and 323/323 aggregate passes.
- LPR-016 remains `changes_requested` at exact immutable candidate head
  `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.  A20 is already a formal,
  terminal, exact-current `approve` review with report SHA-256
  `7cfeb869a3f150fe68ebe4c153e4a6357f235cb87b0affa357c6c3c7b4bdaae0`.
  F-LPR016-001..007 are resolved on historical heads; F-LPR016-008 is resolved
  by A20 on the current head.
- Classic read-only merge-tree from exact checkpoint and candidate is clean.
  The result blobs for `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/workflow.py`, and `tests/test_workflow.py` exactly equal candidate
  blobs `f5fcf6d0...`, `84b5c607...`, `6b5271bc...`, and `ac747a95...`.
  Both candidate report add/add blobs also equal checkpoint blobs.

## Required recovery ledger

Run `python3 scripts/workflow.py validate` immediately before and after every
state mutation.  Do not run `scripts/check_workflow.py` in the short interval
after a session becomes terminal and before its metric is appended: the
aggregate checker requires exactly one metric for every terminal session
(`scripts/check_workflow.py:72-80,142-144`).

### 1. Freeze and retire nonbinding A08

1. Copy the returned `/tmp/qpbt-027-review-a08-pr017-immutable.md` bytes to
   `workflow/reviews/qpbt-027-review-a08-pr017-immutable.md`; hash source and
   canonical copy and require byte equality.  Do not normalize an immutable
   report silently.
2. In one `update issued-session` mutation, populate only the still-null A08
   outcome fields: `timing_quality`, `agent_measured_elapsed_seconds`,
   `source_report_sha256`, `canonical_report_sha256`, `outcome_path`, `outcome`,
   `checks`, and `notes`.  The outcome/notes must say that the report approved
   the code but is nonbinding because the immutable reviewer base is wrong.
3. Transition A08 `running -> finished`.  This emits the sole terminal
   lifecycle event and supplies `ended_at`/`elapsed_seconds`.
4. Append exactly one `research/metrics/sessions.jsonl` record using the final
   session elapsed value, `stage_id=STAGE-02`, `issue_id=QPBT-027`,
   `pr_id=LPR-017`, `token_usage=null`, and reason
   `Collaboration backend does not expose per-agent token usage`.
5. Transition A08 `finished -> archived`; this emits the sole archive event.
6. Append a new incident record (allocate the next ID from then-current
   authority, do not assume `INC-048`) with class such as
   `formal-reviewer-base-revision-misbound`, occurrence session A08, and the
   immutable retry mitigation.  Later append that incident ID and the A08 report
   path to STAGE-02 in the same full-list stage update used after retry dispatch.

Safe CLI shape for step 2:

```text
python3 scripts/workflow.py update issued-session i027-reviewer-a08-pr017-immutable \
  --set 'timing_quality="runtime-measured"' \
  --set 'agent_measured_elapsed_seconds=null' \
  --set 'source_report_sha256="<A08_SHA256>"' \
  --set 'canonical_report_sha256="<A08_SHA256>"' \
  --set 'outcome_path="workflow/reviews/qpbt-027-review-a08-pr017-immutable.md"' \
  --set 'outcome="approve-nonbinding-invalid-base-revision"' \
  --set 'checks=<REPORT_DERIVED_OBJECT>' \
  --set 'notes="<NONBINDING_EXPLANATION>"'
python3 scripts/workflow.py transition issued-session i027-reviewer-a08-pr017-immutable finished
# append the metric here
python3 scripts/workflow.py transition issued-session i027-reviewer-a08-pr017-immutable archived
```

Do **not** append an A08 review object to LPR-017 and do not resolve
F-LPR017-001 with A08.

### 2. Issue the fresh retry

Allocate the next unused stable attempt at execution time (A11 is plausible,
but must not be assumed).  Add one full planned reviewer record and dispatch it
under the explicit STAGE-02 capacity.  Its critical authority fields are:

```json
{
  "id": "i027-reviewer-aNN-pr017-immutable-retry",
  "name": "i027-reviewer-aNN-pr017-immutable-retry",
  "role": "reviewer",
  "issue_id": "QPBT-027",
  "pr_id": "LPR-017",
  "parent_session_id": "i027-orchestrator-a01-finding-reconfirm",
  "attempt": "<NN as integer>",
  "read_only": true,
  "base_revision": "506ac7a7b57a2318e0764acfc2558dc62f9e50f0",
  "worktree": "/tmp/qpbt-027-pr017-review-aNN",
  "owned_paths": [],
  "result_envelope_path": "workflow/reviews/qpbt-027-review-aNN-pr017-immutable.md"
}
```

The `base_revision_reason` and validation prompt must independently bind the
detached worktree HEAD/tree to `2c6b1f1.../0c6fdd0f...`, the exact PR range
`506ac7a.....2c6b1f1...`, all six paths, A04 finding, A05 repair, and prescribed
checks.  Use a new external identity; A08 cannot be resumed or relabeled as the
fresh reviewer.

After dispatch, transition `issued -> running`, then replace the complete
STAGE-02 `subagents_issued`, `outputs`, and `incident_ids` lists in one stage
update.  `subagents_issued` must equal the actual non-coordinator issued-session
count after the new session is materialized; incrementing before dispatch or
forgetting the increment makes the aggregate checker fail
(`scripts/check_workflow.py:130-140`).

### 3. Close retry and approve LPR-017

If and only if the fresh retry returns `approve` at the exact current base/head:

1. Freeze/import and hash its report; populate session outcome fields;
   transition `running -> finished`; append its unique metric; transition
   `finished -> archived`.
2. In one atomic LPR-017 update, append the review and resolve F-LPR017-001.
   Splitting resolution before review is invalid; combining them is smallest.
3. Transition LPR-017 `changes_requested -> ready -> approved`.  Two transitions
   are mandatory; the state machine has no direct changes-requested-to-approved
   edge.
4. Commit this report/session/metric/PR state as a state-only checkpoint before
   integration.  Never add these bytes to or amend candidate `2c6b1f1...`.

Review append shape (replace the whole append-only list, preserving its prefix):

```json
{
  "id": "review-qpbt-027-pr017-aNN-immutable",
  "reviewer_session_id": "i027-reviewer-aNN-pr017-immutable-retry",
  "verdict": "approve",
  "base_sha": "506ac7a7b57a2318e0764acfc2558dc62f9e50f0",
  "head_sha": "2c6b1f1d0be89d09bad2f60e074cf106be99fd46",
  "started_at": "<REPORT_START_AT_OR_AFTER_CURRENT_CHECKS>",
  "completed_at": "<REPORT_CUTOFF_NOT_AFTER_SESSION_END>",
  "result_path": "workflow/reviews/qpbt-027-review-aNN-pr017-immutable.md",
  "finding_ids": [],
  "formal_pr_review": true,
  "report_sha256": "<RETRY_SHA256>",
  "resolved_finding_ids": ["F-LPR017-001"]
}
```

F-LPR017-001 keeps all identity/introduction fields and changes only to:

```json
{
  "status": "resolved",
  "disposition": "fixed",
  "disposition_evidence": "Fresh retry A-NN verified the A05 complete-candidate suffix authorization at exact current head 2c6b1f1.",
  "resolved_by_review_id": "review-qpbt-027-pr017-aNN-immutable"
}
```

The review's `finding_ids` must be empty because it introduces no finding
(`scripts/workflow.py:681-693`).  `fixed` is valid because the resolving review
is later and its head differs from the introducing A04 head.

## True merge and activation

From the exact state-only approval checkpoint, re-run the read-only merge
preview, then create a true no-fast-forward merge whose ordered parents are
`(PREMERGE_MAIN, 2c6b1f1...)`.  Verify candidate ancestry, two parents, and that
the four changed code/protocol blobs and two candidate report blobs equal the
authenticated candidate blobs.  No rebase, squash, cherry-pick, amendment, or
candidate-branch state commit is allowed.

The current preview is mechanically clean and preserves candidate blobs, so a
second integration review is not required by the current ledger solely because
of the true merge.  A fresh read-only integration review becomes mandatory if
the actual merge reports a conflict, requires any manual resolution, or yields
noncandidate bytes on the six-path candidate surface.

Run the exact post-merge gates before activation: workflow validation; 70/70
workflow tests; dependency-free aggregate tests; compileall for `scripts` and
`tests`; full workflow checker; blueprint `test check graph`; diff hygiene,
clean status, ordered-parent/ancestry checks, and report/blob hashes.  No Lean,
Lake, or hot-cache action is justified because neither candidate changes Lean,
pins, or the build recipe.

Freeze a post-integration evidence report.  Then, in order:

1. Update approved LPR-017 once with `integration_sha=<TRUE_MERGE_SHA>` and a
   `post_integration_evidence` object containing report path/hash, merge SHA,
   ordered parents, candidate ancestry/blob equality, and gate results.
2. Transition LPR-017 `approved -> merged` (this sets `merged_at`).
3. Transition QPBT-027 `review -> done`.
4. Append the retry and integration report paths to STAGE-02 outputs in one
   full-list update, validate/check, and commit this activation checkpoint.

The integration SHA must be recorded before the merged transition
(`scripts/workflow.py:792-800`), and a merged PR cannot later be updated.

## Activate A20 confirmation evidence for LPR-016

Only after the activation checkpoint contains the new workflow code, replace
LPR-016's full `findings` list once.  Preserve every byte of each resolved
finding except append
`review-qpbt-026-pr016-a20-immutable` to `confirmation_review_ids` for exactly
F-LPR016-001 through F-LPR016-007.  Do not append it to F-LPR016-008: A20 is
already that finding's `resolved_by_review_id`, and a confirmation must differ
from the resolution review (`scripts/workflow.py:2539-2540`).  Do not change
the review list, dispositions, evidence, resolving review IDs, base/head, or
candidate SHA.

The candidate update guard checks only the newly appended suffix against the
complete current PR (`scripts/workflow.py:2503-2563`), while resolved finding
fields other than the confirmation list are immutable
(`scripts/workflow.py:2488-2496`).  A20 is later than all seven resolution
reviews, approves exact base/head `ea584e9.../5bf6e08...`, and is already a
terminal independent same-PR review, so the one update validates.

Then transition LPR-016 `changes_requested -> ready -> approved`.  No fresh
LPR-016 candidate review is required: the head did not change and A20 is the
latest exact-current approving review.  Approval now satisfies the current
review, all-resolved, and per-finding exact-current binding gates
(`scripts/workflow.py:747-790`) while preserving
`head_sha = 5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.

Stop at `approved` for the requested scope.  A later true merge of LPR-016 is a
separate boundary: after LPR-017, the two protocol files are expected to need a
semantic union, so that combined integration tree requires a fresh independent
read-only review before LPR-016 merge activation.  That review must not rewrite
the exact LPR-016 candidate SHA.

## Atomicity, events, and counts

- One `workflow.py update` mutates one JSON document and emits one
  `record.updated` event.  The retry review plus F-LPR017-001 resolution can and
  should be atomic in one PR update; the seven A20 confirmations likewise form
  one PR update.
- Status edges cannot be combined with field updates.  Each transition emits
  one `record.transitioned` event.  Dispatch is one state mutation but emits
  `session.issued` and `sessions.dispatched`.
- Report imports, metric JSONL appends, incident JSONL appends, Git commits, and
  the true merge are outside the workflow store transaction.  Freeze/hash a
  report before referencing it; append the metric after terminal timing exists;
  commit approved state before merging.
- With the two stage-list updates consolidated as above, the minimum recovery
  from returned A08 through honest LPR-016 approval is 20 workflow state
  mutations and 21 automatically generated workflow events, plus 3 immutable
  report imports (A08, retry, post-integration), 2 session metric lines, 1
  incident line, 1 true merge, and 5 ordered canonical commits/checkpoints.
  This excludes read-only validations and the reviewer's own commands.  A
  dedicated integration session or a conflict review adds its own governed
  lifecycle, metric, report, state mutations, and events.

## Residual risks and metrics

- The retry attempt number and incident ID must be allocated from current
  authority at execution; concurrent later state may make A11/INC-048 stale.
- Re-run merge preview from the actual premerge first parent.  The present
  clean preview does not authorize ignoring a future conflict.
- Every append-only list assignment must contain the exact old prefix.  Nested
  `reviews.*` or `findings.*` assignments are rejected; replace each full list.
- Event timestamps must not move before the append-only log tail.  Use the
  workflow CLI for lifecycle events rather than hand-writing equivalents.
- Scout repository writes: 0; Git writes: 0; canonical state/metric writes: 0;
  network/endpoint/GitHub/credential/Codex/Lean/Lake/cache actions: 0; nested
  agents: 0.  Sole write: this assigned `/tmp` report.
- Scout elapsed seconds: `null`; availability reason: the collaboration
  interface exposed no canonical session start/end pair, so elapsed was not
  estimated.  Token usage: input/output/total `null`; availability reason:
  collaboration does not expose per-agent token accounting.
