# LPR-017 immutable review A04

## Verdict

`request_changes`

## Finding

### F-LPR017-001 (high) - Public updates can permanently append a stale reconfirmation

`scripts/workflow.py:2480` checks only that `confirmation_review_ids` extends its
old prefix, and `_check_pr_update` at `scripts/workflow.py:2510` calls that guard
without checking the newly appended suffix against the PR's current
`base_sha`/`head_sha`. Full static validation intentionally accepts historical
confirmations, so it cannot distinguish a legitimate confirmation that became
historical after a later head advance from one first appended after it was
already stale.

An in-memory reproduction using the candidate's own
`finding_reconfirmation_documents` fixture set a `changes_requested` PR's
current head to `eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee`, removed the existing
confirmation from the old update value, and appended `review-003`, which remains
bound to `dddddddddddddddddddddddddddddddddddddddd`. Both
`_require_findings_update(old, new)` and `validate_documents(state)` accepted
the candidate. No repository bytes were changed by this probe.

This violates acceptance contract item 2: a later review may be appended as a
reconfirmation only when it binds the exact current base/head at append time.
It also weakens item 5 because the invalid entry becomes permanent under the
append-only rule and cannot subsequently be removed. The stale entry does not
authorize `approved` or `merged`, but it falsely records immutable
reconfirmation evidence and can only be corrected by rewriting history.

Smallest reasonable fix: make the PR update guard validate every newly appended
confirmation ID (the suffix beyond the old prefix) against the candidate PR's
exact current base/head and candidate review list before persistence. Preserve
the old prefix without rechecking its head so confirmations that became
historical after a legitimate append remain valid. Cover the public
`workflow.py update pr` path with a rejection test for stale-at-append evidence
and a positive sequence that appends while current, advances the head, and
retains the historical prefix.

## Authentication

- Evidence cutoff: `2026-09-01T12:48:08.355211138+08:00`.
- Detached worktree: `/tmp/qpbt-027-pr017-review-a04`; clean before and after
  review (`git status --short --branch` reported only `## HEAD (no branch)`).
- HEAD: `44ecdce96e5536407f89266b2be59820be56f01c` (exact target).
- HEAD tree: `03e24c81b284f1b9f2e9bafbbc457e8c5f352e9e` (exact target).
- Merge base with `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`:
  exact base; direct range contains exactly one commit.
- Exact no-renames manifest: the supplied five paths and no others.
- `git diff --check`: pass.
- Candidate report SHA-256:
  `1885c02167279996773fe29d31cf3665d225d02ffd494b02d743fe2437134e73`.
- A02 audit SHA-256:
  `148c9e1596e8bab2fdc5071c4c57dc8f1cc337ce81005be12c2b926bacb9d5e2`.
- A03 adoption report SHA-256:
  `72cb9a30151e10f288cfd74315c9bca4fad144470f31e2d9b5a3c06ac5513c75`.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py`: pass, 67/67 in
  0.433 s (external command elapsed 0.52 s).
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p
  'test_*.py'`: pass, 320/320 in 186.295 s (external command elapsed 186.58 s).
- `PYTHONPYCACHEPREFIX=/tmp/qpbt-027-review-a04-pycache python3 -m compileall
  -q scripts/workflow.py tests/test_workflow.py`: pass.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate`: pass; 27
  issues, 16 PRs, 0 planned sessions, 322 issued sessions, 7 stages.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py --skip-tests`:
  pass.
- Adversarial stale-at-append probes: 2; first control accidentally used the
  fixture's current head and passed, corrected distinct-head probe reproduced
  the defect. Unexpected results after correction: 0.

## Review scope and metrics

The complete `AGENTS.md`, exact diff, protocol prose, implementation report,
validator context, review/finding consumers, public mutation path, tests, A02
audit hash, and A03 adoption hash were inspected. Changed paper-labelled Lean
theorems: 0; statement-integrity table is not applicable. Repository edits,
canonical-state writes, metrics writes, Git writes, network calls, endpoint or
credential access, Codex CLI calls, Lean/Lake/build/cache commands, and nested
agent actions: all 0.

Counters: review findings 1 high / 0 medium / 0 low; required test commands 2;
tests passed 387/387; compile attempts 1; workflow validation attempts 1;
workflow checker attempts 1; authentication command groups 2; adversarial
probes 2; subagents 0; topology is root coordinator -> this independent
reviewer only. Session elapsed is `null` because the collaboration interface
does not expose a canonical session start or total elapsed duration. Token usage
is `input=null`, `output=null`, `total=null`; availability reason: per-agent
token usage is not exposed by the collaboration backend.

## Residual risk

Beyond F-LPR017-001, no additional defect was found in the reviewed contract.
The passing suite supports malformed-value fail-closed behavior, reviewer
independence, chronology, immutable resolution fields, current-head approval,
and append-only prefixes. Residual risk remains in unexercised combinations of
multi-field CLI assignments; the repair should evaluate the complete candidate
PR state so assignment order cannot bypass the new suffix check.
