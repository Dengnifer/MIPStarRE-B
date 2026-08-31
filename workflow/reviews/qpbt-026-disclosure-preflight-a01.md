# QPBT-026 disclosure preflight A01

- Issue: `QPBT-026`
- Session: `i026-orchestrator-a01-disclosure-preflight`
- Base: `ea584e9e894391773e09ddad2ce4d082497c7913`
- Implementation head before report finalization: `aa8b1600c4274d966a68b017a52a17d62c3b1055`
- Implementation tree before report finalization: `db442268bb90d9f3eb44f3fdb6e54182303dbe1d`
- Branch: `issue/qpbt-026-disclosure-a01`
- Endpoint/network: not contacted; no credentials read or copied
- Token usage: unavailable (local test/runtime tools expose no model token data)

## Immutable metadata binding

The implementation checkpoint above is intentionally the commit/tree at which
the code and tests were last validated before this report's final wording was
added. Because this report is itself one of the five committed paths, embedding
the hash of the commit containing those final bytes would be self-referential:
any hash update would change the report bytes again. The final candidate
identity is therefore bound externally by the PR ledger and coordinator
handoff, while the checkpoint fields preserve the validated implementation
identity. A reviewer must run `git rev-parse HEAD` and `git rev-parse
HEAD^{tree}` on the submitted branch, compare them with that handoff, and treat
any changed head as a fresh review target.

## Source anchors and intent

The implementation follows `research/metrics/incidents.jsonl#INC-045`, which
records three endpoint-review paths stopping because the exact private evidence
scope was not explicitly authorized. `workflow/reviews/qpbt-010-endpoint-review-a06.md`
and `...-a08.md` document the rejected launch boundary, while
`workflow/reviews/qpbt-010-endpoint-retry-a08.md` records that endpoint/model
authorization alone is insufficient. `protocols/review.md` requires endpoint,
model, wire protocol, evidence scope, explicit authorization, credential
exclusion, and fail-closed rejection.

## Change and integrity

`scripts/local_agent.py` adds a version-1 JSON authorization schema with exact
keys for `authorized`, endpoint origin, model, wire API, immutable base/head/tree,
private file paths, and credential/unrelated-content exclusions. For committed
targets it resolves a clean source HEAD, ancestry, head tree, and exact changed
paths. Missing or mismatched authorization is checked before task/context
loading, persistence probing, harness preparation, or issued-session claim.
Credential-looking paths, duplicate/path-traversal paths, uncommitted external
targets, and unknown/missing authorization fields fail closed. Authorization is
never placed in prompts, result envelopes, or logs. The target envelope now also
records the resolved target tree identity.

Statement/protocol integrity: this is workflow behavior, not a paper-labelled
Lean theorem. The protocol change is exact (`protocol change`): it narrows
external dispatch to an explicitly authorized immutable scope and adds no public
mathematical assumptions. Existing local-only reviews remain unchanged when no
custom transport profile is supplied.

## Validation

- `python3 -m unittest discover -s tests -p 'test_local_agent.py'`: passed, 51 tests.
- `python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py`: passed.
- `python3 scripts/workflow.py validate`: passed (`valid=true`, 27 issues, 15 PRs,
  308 issued sessions, 7 stages).
- `git diff --check`: passed.
- No Lake/Lean/full build, hot-main cache, endpoint, GitHub, or credential command
  was run, per task bounds.

Focused regressions cover missing authorization before evidence/persistence,
endpoint/model/wire/revision/tree/path drift, credential path rejection, and one
exact committed scope success. The baseline transport fixtures were updated to
provide the newly required explicit scope.

## Findings and residual risk

No implementation blocker was found in the scoped offline checks. A fresh
independent immutable reviewer is still required; this report is implementation
evidence, not approval. The preflight intentionally rejects external review of
uncommitted targets because no immutable base/head/tree binding exists.

## Timing and tree hygiene

Focused unittest runtime: approximately 4.0 seconds; compileall and workflow
validation each completed in under one second. Candidate worktree was clean
before edits, contains only the owned paths listed in the task, and has no
untracked files after the report is added. Candidate commit is created only
after the final checks pass.

The candidate changes exactly five paths (`protocols/CHANGELOG.md`,
`protocols/review.md`, `scripts/local_agent.py`, `tests/test_local_agent.py`,
and this report), with 434 insertions and 22 deletions. The sanitized
authorization binding is included in review target evidence; no raw
authorization file or secret value is recorded.
