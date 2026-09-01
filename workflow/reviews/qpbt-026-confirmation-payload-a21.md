# QPBT-026 / LPR-016 confirmation payload scout A21

## Verdict

`PASS`. At exact detached snapshot
`3686315526fab8704745df6ad69d60e1bd72fa3a`, the smallest legal public-CLI
update is one full `findings` replacement. It appends the exact singleton
confirmation list
`["review-qpbt-026-pr016-a20-immutable"]` to F-LPR016-001 through
F-LPR016-007 and changes no field in F-LPR016-008. The isolated copied ledger
accepted the update and then accepted the intended transition sequence
`changes_requested -> ready -> approved`.

No canonical state was mutated. The root coordinator remains the only writer
authorized to apply this payload.

## Immutable identity and authority

- Detached HEAD:
  `3686315526fab8704745df6ad69d60e1bd72fa3a`.
- HEAD tree: `5f076ec1171b80dd0aa9a0e459ef4788897ea2a9`.
- HEAD parents, in order:
  `3a90910de7921e43fd40db44271c528bbca7301d` and
  `2c6b1f1d0be89d09bad2f60e074cf106be99fd46`.
- Worktree: detached and clean before and after inspection.
- LPR-016 immutable base/head:
  `ea584e9e894391773e09ddad2ce4d082497c7913` /
  `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.
- Exact A20 review ID: `review-qpbt-026-pr016-a20-immutable`.
- A20 verdict: `approve`; its immutable base/head exactly match LPR-016.
- A20 report:
  `workflow/reviews/qpbt-026-review-a20-pr016-immutable.md`.
- A20 report SHA-256:
  `7cfeb869a3f150fe68ebe4c153e4a6357f235cb87b0affa357c6c3c7b4bdaae0`.
- A20 resolves F-LPR016-008 and explicitly reconfirms F-LPR016-001 through
  F-LPR016-007 at the exact current head.

## Exact smallest replacement

The integrated public CLI requires `findings` to be replaced as one
disposition-aware list; array-element dotted updates are rejected. The exact
payload is therefore generated from the live LPR-016 list without retyping any
existing evidence:

```sh
payload=$(jq -cj '.pull_requests[] | select(.id=="LPR-016") | .findings | map(if (.id | test("^F-LPR016-00[1-7]$")) then . + {"confirmation_review_ids":["review-qpbt-026-pr016-a20-immutable"]} else . end)' workflow/state/prs.json)
python3 scripts/workflow.py update pr LPR-016 --set "findings=$payload"
```

At the authenticated snapshot, the compact payload is exactly 6,573 bytes and
has SHA-256
`40ca819fd4e58b80bb3dcd85c7d418733d399aec41067c89c397a3f89010bf52`.
The `jq` addition retains every existing key in its existing order and appends
`confirmation_review_ids` as the final key of each of the first seven finding
objects. It preserves finding array order. F-LPR016-008 passes through the
`else` branch byte-for-byte at the JSON data-model level and receives no
confirmation field.

F-LPR016-008 must remain unchanged because A20 is already its
`resolved_by_review_id`; the integrated guard requires a confirmation review
to differ from the resolution review.

The CLI automatically refreshes LPR-016's `updated_at` and appends its normal
workflow event. That bookkeeping effect is outside the `findings` payload; no
other PR field is assigned.

## Isolated proof

I copied all four canonical state documents and `workflow/events.jsonl` to
`/tmp/qpbt-026-confirmation-a21.uVX434`, then invoked only the integrated public
CLI against those copies.

Before mutation, canonical validation passed with 29 issues, 17 PRs, 341
issued sessions, and 7 stages. The single isolated update succeeded. Validation
then passed after the update, after transition to `ready`, and after transition
to `approved`, with the same counts.

Structured before/after assertions all returned `true`:

- finding IDs and array order were preserved;
- for findings 001-007, deleting only the new confirmation field reproduced
  the original object exactly;
- each new list was the exact A20 singleton;
- each new field was appended after all original object keys;
- finding 008 and its key order were unchanged;
- every other LPR-016 value except the automatic `updated_at` timestamp was
  unchanged, and the PR key order was unchanged;
- `issues.json`, `sessions.json`, and `stages.json` remained byte-identical;
  and
- exactly one event was appended for the update, with payload kind `pr`, ID
  `LPR-016`, and field list `["findings"]`.

The two isolated transitions appended their own normal transition events.
There were no failed mutation or validation attempts.

## Legal transitions and integration boundary

Immediately after the payload, LPR-016 remains `changes_requested`. Its legal
next states are `ready` or `closed`; the intended path is `ready`. From `ready`,
the legal states are `changes_requested`, `approved`, or `closed`; the intended
path is `approved`. The isolated proof confirms that A20 plus the seven new
current-head confirmations satisfy the approval validator.

From `approved`, the state machine permits `changes_requested`, `merged`, or
`closed`, but `merged` additionally requires a recorded integration SHA. It is
not yet an honest immediate action. After the already integrated LPR-017,
LPR-016 is expected to conflict in `protocols/CHANGELOG.md` and
`protocols/review.md`. Those files require a semantic union retaining both the
QPBT-027 finding-reconfirmation protocol and the QPBT-026 fail-closed
disclosure/offline-isolation protocol. Because that resolution creates a
combined tree reviewed by neither candidate review, the exact resolved merge
commit requires a fresh independent read-only review before integration and
the `approved -> merged` activation. The immutable candidate SHA must not be
rewritten.

## Metrics

- Evidence cutoff: `2026-09-01T06:00:01.838156817Z`.
- Exposed token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session token accounting; no estimate was made.
- Agent elapsed time: `null`; no trustworthy session-start timestamp was
  exposed before the first action, so no estimate was made.
- Subagents: 0; topology was one bounded read-only state scout.
- Canonical validation attempts: 1 passed. Isolated validation attempts: 3
  passed. Isolated public mutation attempts: 3 passed (one update, two
  transitions).
- Tests, builds, compile attempts, Lean, Lake, and cache actions: 0.
- Repository edits, Git writes, commits, branches, and canonical state/metrics
  writes: 0. Temporary copied-state writes were confined to the isolated
  `/tmp` directory; the only final artifact is this assigned report.
- Endpoint, network, GitHub, credential, Codex CLI, and nested-agent actions: 0.

The report SHA-256 is returned externally after freeze because embedding it in
the report would change the digest.
