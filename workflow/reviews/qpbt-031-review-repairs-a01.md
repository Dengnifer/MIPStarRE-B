# GitHub PR-029 Review Repairs A01

## Identity

- Canonical issue: GitHub #31
- Pull request: GitHub #29
- Stable orchestrator session: `i031-orchestrator-a01-review-repairs`
- Collaboration task: `/root/i031_orchestrator_a01_review_repairs`
- Reviewed base SHA: `4a6683795a71712d6a5c52b7539c2f532fd39f71`
- Reviewed head SHA: `1356fc25110770adcd10f5056767f3803630e76f`
- Source review: `/home/drx/MIPStarRE-auto/.workflow-runtime/runs/i031-reviewer-a01-pr29-immutable/review.json`
- Reviewer identity: `i031-reviewer-a01-pr29-immutable`
- Reviewer external ID: `/root/i031_reviewer_a01_pr29_immutable`
- Reviewer verdict before repair: `request_changes`

## Finding Dispositions

### R1-F1: Canonical sessions could use a noncanonical event log

Resolved. `WorkflowStore` now captures and validates the exact adjacent
`workflow/events.jsonl` real path after cutover, rejects lexical aliases,
symlink components, alternate files, and missing canonical logs, and applies
the same guard to planning and dispatch. Regressions prove alternate and
aliased paths leave canonical sessions, canonical events, and alternate bytes
unchanged.

### R1-F2: Removing both authority files could reopen legacy mutation

Resolved. In addition to durable positive GitHub issue/PR numbers in
`sessions.json` and sticky marker observation for long-lived stores, the
repository now carries the exact read-only indicator
`workflow/github-cutover-indicator.json` (SHA-256
`7dda9f6bb7a244ec953d39e1a6f13d172b3a719fd95836f94dd347dbe9b6e7a1`). Its
strict schema is `{schema_version:1, kind:"github-cutover-irreversible",
repository:{owner:"Dengnifer", name:"MIPStarRE-B", database_id:1352436168,
node_id:"R_kgDOUJyJyA"}, base_ref:"main", cutover_main_sha:<40 lowercase hex}`.
The indicator is regular, non-symlink, duplicate-key rejected, and cross-checked
against both authority metadata files when present. A fresh-store regression
deleting `workflow/github.json` and `workflow/github-cutover.json` proves issue,
PR, session, and event mutations fail closed with exact state/event bytes
preserved; the fixture contains zero positive GitHub issue/PR session IDs, so
the indicator is the sole surviving cutover evidence. Malformed, extra-field,
and symlinked indicators also fail closed.

Residual limitation: if an operator additionally removes the committed
indicator and every durable session evidence row, a new store has no remaining
repository-level fact from which to infer historical cutover. This is the only
remaining inference boundary.

### R1-F3: Integration preflight CLI could not bind review-comment authority

Resolved. `github_workflow.py preflight` now accepts
`--integration-review-expectations-file JSON_FILE`, requiring a strict schema
with exact comment database/node IDs, body digest, reviewer session and
external identities, verdict, and nonempty exclusion identity arrays. Entries
must map one-to-one to unique `--pull-request-expectation` values; malformed,
duplicate, missing, mismatched, overlapping, or ambiguous data fails before
any live read. Existing GET-only review-comment validation performs the final
binding.

## Validation

- `python3 tests/test_workflow.py`: `124/124` passed (the expected argparse
  usage line is emitted by an invalid-argument regression).
- `python3 tests/test_github_workflow.py`: `35/35` passed.
- The first `455`-test aggregate run exposed one compatibility error in the
  local-agent GitHub-only governed-exec fixture. Adding exactly
  `self.activate_cutover()` supplies exact authority while leaving issue `#28`
  unbound by the fixture manifest.
- The corrected local-agent case passed `1/1`; `python3
  tests/test_local_agent.py` passed `77/77`.
- `python3 scripts/check_workflow.py --root .`: final aggregate `455/455`
  passed in `280.787s`, exit status `0`.
- `PYTHONPYCACHEPREFIX=/tmp/i031-combined-pycache python3 -m compileall -q scripts/workflow.py scripts/github_workflow.py tests/test_workflow.py tests/test_github_workflow.py`: passed.
- `git diff --check`: passed.

Changed implementation files were owned by the two fixer sessions:

- `scripts/workflow.py`: SHA-256
  `1f2f6b6dcebd68dae4a64f92d52f7d5fcb27405af0f1d96a38776c29775a05f7`
- `tests/test_workflow.py`: SHA-256
  `9820c84e0f87104d132152eeea896698b15dd4658277b8480e7852da37d3d7ac`
- `scripts/github_workflow.py`: SHA-256
  `5a2edc3ed8e84fb4f86f56c50c0b6c5b2a60475a2632dd45c0ae8e1fd3bf99e6`
- `tests/test_github_workflow.py`: SHA-256
  `d54a7906864792c5574879c9a8f92b8f83888b8d34658794433f4e49b20eeb34`
- `tests/test_local_agent.py`: SHA-256
  `b4ef2936afb8c15e7498f479673906c04d78833b4bcd8c6c0ce616b65584831a`
- `workflow/github-cutover-indicator.json`: SHA-256
  `7dda9f6bb7a244ec953d39e1a6f13d172b3a719fd95836f94dd347dbe9b6e7a1`

No Lean/Lake build, network, GitHub mutation, credentials, canonical state,
metrics, or commit operation was performed. Both fixer sessions spawned zero
subagents. Fixer timing and token usage were unavailable where not exposed;
the adapter fixer reported 462 seconds elapsed and token usage `null`.
