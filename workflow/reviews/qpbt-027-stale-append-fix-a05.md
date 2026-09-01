# QPBT-027 stale confirmation append fix A05

## Scope and result

This session fixes only `F-LPR017-001`. The public PR update path now assembles
all assignments into one candidate record before checking append-only evidence.
Every confirmation ID newly introduced in an existing or newly appended
finding is authorized against that complete candidate: it must be a unique
string naming a candidate review on the exact candidate base/head, the review
must approve, differ from the resolution review, and occur strictly after the
preceding resolution or confirmation. The complete atomic document validator
continues to enforce reviewer lifecycle, read-only reviewer role, same-PR/base
binding, independence, and all other semantic constraints.

The prior confirmation prefix is not rebound to a later candidate head. A
confirmation appended while current can therefore remain as immutable
historical evidence after a legitimate head advance. Existing resolution and
disposition evidence remains immutable.

## Provenance and authentication

- Stable session: `i027-fixer-a05-stale-append-guard`.
- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-027-finding-reconfirm-a01`.
- Branch: `issue/qpbt-027-finding-reconfirm-a01`.
- Required parent: `44ecdce96e5536407f89266b2be59820be56f01c`.
- Required parent tree: `03e24c81b284f1b9f2e9bafbbc457e8c5f352e9e`.
- Immutable review: `workflow/reviews/qpbt-027-review-a04-pr017-immutable.md`.
- Immutable review SHA-256: `2fd2a123a2ed32b34d674509f4faf78fe398ee44add61270db570bd46a30d58e`.
- Independent A06 contract report: `/tmp/qpbt-027-stale-append-contract-a06.md`.
- A06 report SHA-256: `302cb14303a2cf1c574724df2968d4d88e5b9c7459c972f85656f76dff7a7e73`.

## Test coverage

The direct guard matrix covers current evidence, missing and duplicate IDs,
wrong base/head, non-approve verdict, malformed chronology, out-of-order
reviews, and a newly appended finding with stale confirmation evidence.
Existing full-document tests cover malformed/non-string IDs, reviewer role and
independence, wrong PR/base, finished lifecycle, and immutable dispositions.

The public CLI tests cover all six permutations of simultaneous
`findings`/`reviews`/`head_sha` assignments, stale-at-append rejection, exact PR
and event-log byte preservation after rejection, append while current, later
head advance, and retention of the now-historical prefix.

Final validation commands and results:

- `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py`: pass, 70/70.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'`: pass, 323/323.
- `PYTHONPYCACHEPREFIX=/tmp/qpbt-027-a05-pycache python3 -m compileall -q scripts/workflow.py tests/test_workflow.py`: pass.
- `python3 scripts/workflow.py validate`: pass, 27 issues, 16 PRs, 0 planned sessions, 322 issued sessions, 7 stages.
- `python3 scripts/check_workflow.py --skip-tests`: pass.
- `git diff --check`: pass.

## Metrics and safety

- Session elapsed: `null`; availability reason: the collaboration backend does
  not expose a canonical per-agent session elapsed duration.
- Token usage: input `null`, output `null`, total `null`; availability reason:
  per-agent token usage is not exposed by the collaboration backend.
- Subagents: 0; topology: root coordinator -> this fixer only.
- Focused workflow-suite attempts: 5 (4 pass, 1 intermediate test-fixture
  failure before adding `itertools` and correcting append-only review setup).
- Full discovered-suite attempts: 2, both pass.
- Compile attempts: 3 (one `py_compile` smoke check and two required
  `compileall` runs), all pass.
- Workflow validation attempts: 2, both pass.
- Workflow checker attempts: 2, both pass.
- Review findings addressed: 1 high (`F-LPR017-001`).
- Coordinator diff-review findings addressed: 1 newly appended-finding bypass.
- Network, endpoint, GitHub, credential, Codex CLI, Lean, Lake, build, and cache
  actions: 0 each.
- Canonical state writes, canonical metrics writes, protocol edits, and
  out-of-scope file edits: 0 each.
- Incidents: 0. Protocol revisions: 0.

## Identity and residual risk

Owned paths are exactly `scripts/workflow.py`, `tests/test_workflow.py`, and
this report. The containing commit SHA and tree and this report's SHA-256 are
recorded externally because a file cannot self-embed the identity of its
containing commit or its own digest.

No paper-labelled Lean theorem changed, so a statement-integrity table is not
applicable. Residual risk is limited to future mutation paths that bypass the
public atomic `update pr` command; static validation intentionally cannot infer
whether historical confirmation evidence was current when originally appended.
