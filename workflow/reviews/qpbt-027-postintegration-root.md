# QPBT-027 / LPR-017 coordinator post-integration evidence

## Outcome

LPR-017 is ready for the canonical approved-to-merged transition. The exact
approved candidate was integrated as a true two-parent merge, the integrated
tree preserves all first-parent evidence, every post-integration activation
gate passed, and fresh read-only reviewer A14 approved the exact merge with no
findings.

Evidence cutoff: 2026-09-01T06:07:41Z.

## Immutable integration identity

- Integration commit: 3686315526fab8704745df6ad69d60e1bd72fa3a.
- Integration tree: 5f076ec1171b80dd0aa9a0e459ef4788897ea2a9.
- Ordered first parent: 3a90910de7921e43fd40db44271c528bbca7301d.
- Ordered second parent / approved candidate:
  2c6b1f1d0be89d09bad2f60e074cf106be99fd46.
- Unique merge base: 506ac7a7b57a2318e0764acfc2558dc62f9e50f0.
- Candidate ancestry, two-parent cardinality, parent order, and clean
  first-parent diff all passed.

The final root-local three-argument merge preview was rerun from the actual
first parent after A13 bookkeeping. It produced four ordinary merged sections,
four result blobs, zero conflict categories, and zero marker lines. The true
merge changes exactly protocols/CHANGELOG.md, protocols/review.md,
scripts/workflow.py, and tests/test_workflow.py relative to its first parent.

Their result blobs are exactly the approved candidate blobs
f5fcf6d0511c889fc35e97ae551f8fcc98c13bfc,
84b5c607426f661ce3defb6b525be99d839f14f9,
6b5271bc995066641319c4ee0fe880e37d74490e, and
ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe. The two shared report blobs are
06e0c36a4b376ec309463b2a3ccd19d8eff054a2 and
815939ceb85a606cb134a6010b8e9a49c6b17df0. Git diff-check passed and the
worktree was clean immediately after the merge identity checks.

## Independent review

Fresh read-only session i027-reviewer-a14-integration-audit reviewed exact
merge 368631552, not a mutable worktree or prose reconstruction. It approved
with no findings, authenticated the parents, four-path manifest, all six
expected blobs, candidate ancestry, and first-parent evidence preservation.

- Report: workflow/reviews/qpbt-027-postintegration-a14.md.
- Report SHA-256:
  9e7ad2b6fa48fa065599a0ce24e496adde1b5fa550be9ad0b85434eb36889534.
- Focused workflow tests: 70/70 in 0.719 seconds.
- Workflow validator and checker with separately owned tests: passed.

## Coordinator validation

| Gate | Result |
| --- | --- |
| Dependency-free aggregate Python suite | 323/323 in 190.970 seconds |
| Python compilation with private /tmp bytecode cache | passed |
| Workflow validator | passed |
| Workflow checker with separately owned tests | passed |
| Blueprint test/check/graph | 26/26; 48 nodes, 12 chapters, acyclic, deterministic |
| Merge parents, ancestry, path and blob inventory, diff hygiene | passed |

The aggregate suite includes the 70 workflow tests; A14 independently reran
that focused file, so no root duplicate focused invocation was needed. One
initial declaration-check command used a nonexistent guessed path; the
coordinator immediately used the repository-documented blueprint make gate,
which passed. No Lean declaration, source pin, build recipe, or cache input
changed, so Lean/Lake compilation and the hot-main cache were not applicable.

## Metrics

- Root aggregate attempts: 1 passed, 0 failed.
- Root compile attempts: 1 passed.
- Root workflow validation/checker attempts before closure: 2 passed.
- Root blueprint attempts: 1 passed; one corrected nonexistent-path probe.
- Post-integration reviewer sessions: 1; nested agents: 0.
- Network, endpoint, GitHub, credential, and external-review transport calls:
  0.
- Lean, Lake, and hot-main-cache actions: 0.
- Root and collaboration token usage: null; neither backend exposes token
  accounting, so no estimate was made.

This evidence authorizes only recording the existing integration SHA and
closing LPR-017/QPBT-027. It does not authorize LPR-016 integration; that later
merge has its own semantic-union and immutable-review gates.
