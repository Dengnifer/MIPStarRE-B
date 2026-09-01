# QPBT-027 / LPR-017 no-byte-change formal adoption A03

## Verdict

PASS. `i027-integrator-a03-pr017-bind` formally adopts the exact QPBT-027
candidate at LPR-017 head `44ecdce96e5536407f89266b2be59820be56f01c`
without changing candidate, repository, canonical-state, metric, or Git bytes.
No requested identity, report hash, ledger linkage, registered check, local
validation, or root reproduction mismatch was found.

The adoption is necessary. The original orchestrator session
`i027-orchestrator-a01-finding-reconfirm` started at
`2026-09-01T04:00:44.363566Z`, before LPR-017 was created at
`2026-09-01T04:35:17.175430Z`, and its issued record therefore has
`pr_id: null`. `pr_id` is an immutable dispatch and issued-session authority
field in `scripts/workflow.py` (`DISPATCH_IMMUTABLE_FIELDS` and
`_check_session_update`), so the original issued row cannot honestly be rebound
afterward. This A03 session was issued at `2026-09-01T04:36:29.055169Z`, started
at `2026-09-01T04:36:29.355776Z`, and is immutably bound to `pr_id: LPR-017`
and base revision equal to the exact candidate head.

## Authenticated identity

- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-027-finding-reconfirm-a01`
- Branch: `issue/qpbt-027-finding-reconfirm-a01`
- Base: `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`
- Head: `44ecdce96e5536407f89266b2be59820be56f01c`
- Head tree: `03e24c81b284f1b9f2e9bafbbc457e8c5f352e9e`
- Direct parent: base, exact
- Merge base: base, exact
- Commit count in `base..head`: 1
- Candidate worktree: clean before and immediately before report freeze
- `git diff --check base..head`: passed

The exact no-renames path inventory is:

```text
M protocols/CHANGELOG.md
M protocols/review.md
M scripts/workflow.py
M tests/test_workflow.py
A workflow/reviews/qpbt-027-finding-reconfirm-a01.md
```

Report digests:

- Candidate report SHA-256:
  `1885c02167279996773fe29d31cf3665d225d02ffd494b02d743fe2437134e73`
- Canonical A02 report SHA-256, independently matched for both
  `/tmp/qpbt-027-reconfirm-contract-a02.md` and
  `workflow/reviews/qpbt-027-reconfirm-contract-a02.md`:
  `148c9e1596e8bab2fdc5071c4c57dc8f1cc337ce81005be12c2b926bacb9d5e2`

## Canonical linkage and checks

Canonical QPBT-027 is in `review`, owned by the original A01 orchestrator, and
LPR-017 addresses QPBT-027 with the exact authenticated base, head, branch, and
five changed paths. The A01 orchestrator record carries the candidate digest,
head tree, direct-parent and one-commit evidence, candidate validation results,
and the exact A02 child digest. The A02 tester record remains `pr_id: null` and
records no open findings after its adversarial audit. The A03 record is the
post-LPR formal binding and contains `pr_id: LPR-017`.

LPR-017 contains exactly seven registered checks. Every check is `passed`,
binds base `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`, binds head
`44ecdce96e5536407f89266b2be59820be56f01c`, and points to the authenticated
candidate report:

1. `check-qpbt-027-focused-44ecdce`
2. `check-qpbt-027-workflow-44ecdce`
3. `check-qpbt-027-aggregate-44ecdce`
4. `check-qpbt-027-compile-44ecdce`
5. `check-qpbt-027-validate-44ecdce`
6. `check-qpbt-027-checker-44ecdce`
7. `check-qpbt-027-identity-44ecdce`

## Validation and reproduction

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate`: PASS;
  valid with 27 issues, 16 PRs, 0 planned sessions, 322 issued sessions, and 7
  stages.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py --skip-tests`:
  PASS (`workflow state: valid`).
- Exact diff, path, tree, direct-parent, merge-base, one-commit, branch,
  report-hash, and clean-worktree predicates: PASS.
- Canonical LPR/check and A01/A03 session-link predicates: PASS.
- Root exact-head reproduction, supplied before freeze:
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'`
  passed 320/320 in 190.629 seconds at
  `44ecdce96e5536407f89266b2be59820be56f01c`. Root also reported compileall,
  workflow validation, checker `--skip-tests`, and exact diff/path/tree/
  ancestry/direct-parent/clean identity passed. This session did not rerun the
  long aggregate.

## Timing and counters

- Canonical session start: `2026-09-01T04:36:29.355776Z`
- Initial local clock sample: `2026-09-01T04:37:06Z`
- Final candidate identity cutoff: `2026-09-01T04:38:57.206974188Z`
- Canonical ledger cutoff: `2026-09-01T04:38:57.487033184Z`
- Report freeze: `2026-09-01T04:39:05.294026613Z`
- Elapsed canonical start to report freeze: `155.938251` seconds
- Token usage: `input=null`, `output=null`, `total=null`; availability reason:
  collaboration backend does not expose per-agent token usage.
- Candidate/repository edits: 0; canonical state edits: 0; metric edits: 0;
  Git writes: 0; commits: 0; branches created/changed: 0.
- Unit/aggregate test executions by this session: 0; compile attempts: 0;
  Lean attempts: 0; Lake attempts: 0; builds: 0; cache actions: 0.
- Network: 0; endpoint: 0; GitHub: 0; credential access: 0; Codex launches: 0.
- Nested agents: 0.
- Sole physical write: `/tmp/qpbt-027-pr017-bind-a03.md`.

Residual gate: LPR-017 still requires the separately assigned fresh independent
immutable reviewer of this exact base/head before integration. This adoption
does not itself approve, merge, or mutate the PR.
