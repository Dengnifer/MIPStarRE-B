# LPR-012 / QPBT-021 integration scout a10

Verdict: **approved and admissible for unchanged-head integration after the
coordinator first commits/cleans the current canonical-state checkpoint.** Do
not cherry-pick or rebase the candidate. Merge the immutable head as the second
parent. A three-way merge has one known textual conflict in
`protocols/CHANGELOG.md`; the other four overlapping paths auto-merge. No merge,
build, warm, seed, network access, or canonical edit was performed by this
scout.

## Observed identities and lifecycle

- Canonical checkpoint: commit
  `367ed6904d096e841a3849010395296a52be30c8`, tree
  `8479efe5ce52d9096a02514fa0c6c27b84238593`. Base `7669f70...` is an
  ancestor, 32 commits behind this checkpoint.
- Candidate clone `/tmp/qpbt-021-repair-a05` was detached and clean at head
  `6303aab63eeed144fe176969ca7c87f5a852b967`, tree
  `def685a69b3aee904b6ef6c2d711d63c75211efe`; its parent is `c37431ec...`,
  whose parent is the registered base
  `7669f70be786a53ba1a0a92c1d347f5fe7544681`, tree
  `48f451bc82f2037abe09e9d97130fdb4d0cbdd53`. Exact-base diff hygiene passed.
  The range is exactly the five paths registered at
  `workflow/state/prs.json:3463-3469`, 2162 insertions and 14 deletions.
- QPBT-021 remains `review`; its only dependency QPBT-001 is `done`, and the
  four acceptance gates are recorded at `workflow/state/issues.json:671-693`.
- LPR-012 is now `approved` at `workflow/state/prs.json:3279-3293`. The
  coordinator repaired the initially incomplete implementer set, then made the
  legal `draft -> ready -> approved` transitions at
  `2026-08-31T13:13:13Z` and `2026-08-31T13:13:27Z`. Current validation passes.
- The exact writable-session set bound to LPR-012 is now equal to the PR list:
  `i021-orchestrator-a04-pr012-bind`, canceled/no-work
  `i021-orchestrator-a05-changelog-count`, and
  `i021-orchestrator-a06-changelog-count`. The canceled attempt is still
  `read_only: false` and PR-bound at `workflow/state/sessions.json:12487-12533`,
  so it must remain listed. The validator enforces exact set equality at
  `scripts/workflow.py:425-450`.
- The current-head checks are all passed at
  `workflow/state/prs.json:3356-3413`; the fresh independent read-only reviewer
  approved this exact base/head/tree at `workflow/state/prs.json:3431-3439` and
  `workflow/state/sessions.json:12702-12757`. The sole earlier blocker is
  resolved on the changed head at `workflow/state/prs.json:3442-3455`.

## Main overlap and risk

All five candidate paths also changed between base `7669f70...` and current
main. However, none changed from main `7526e586...` to `367ed690...`, and a
direct tree comparison `367ed690..6303aab` is exactly the intended five-path
QPBT-021 delta: 1849 insertions and 10 deletions. The three-way `git merge-tree`
found one conflict only: both sides inserted changelog entries at the top.
Candidate `protocols/CHANGELOG.md` is byte-for-byte current main plus the
27-line QPBT-021 0.1.7 block, so taking the candidate version of that one file
preserves QPBT-022 and resolves the conflict exactly. The other four paths
auto-merge, but their combined runtime behavior still requires the post-merge
gates.

The current worktree is not integration-clean: coordinator-owned changes exist
in `workflow/events.jsonl`, `workflow/state/prs.json`, and
`workflow/state/sessions.json`. They contain the approval and three running
scout records. Finish/import/archive the scouts, run validation, and commit that
checkpoint before merging. Do not stash or discard it. If any of the five
candidate paths changes after `367ed690`, rerun the overlap and merge-tree
preflight; this conflict analysis is then stale.

## Guarded unchanged-head merge

Run from a clean `main` after the canonical checkpoint is committed. Capture
the new clean parent rather than assuming it is still `367ed690`.

```bash
python3 scripts/workflow.py validate
test -z "$(git status --porcelain)"
qpbt021_main_before=$(git rev-parse HEAD)
git merge-base --is-ancestor 367ed6904d096e841a3849010395296a52be30c8 "$qpbt021_main_before"

git fetch --no-tags /tmp/qpbt-021-repair-a05 \
  6303aab63eeed144fe176969ca7c87f5a852b967:refs/heads/issue/qpbt-021-local-mathlib-a05
test "$(git rev-parse refs/heads/issue/qpbt-021-local-mathlib-a05)" = \
  6303aab63eeed144fe176969ca7c87f5a852b967
test "$(git rev-parse refs/heads/issue/qpbt-021-local-mathlib-a05^{tree})" = \
  def685a69b3aee904b6ef6c2d711d63c75211efe
test "$(git rev-parse refs/heads/issue/qpbt-021-local-mathlib-a05^^)" = \
  7669f70be786a53ba1a0a92c1d347f5fe7544681

git merge --no-ff --no-commit refs/heads/issue/qpbt-021-local-mathlib-a05
```

The merge command is expected to stop with only
`protocols/CHANGELOG.md` unmerged. Confirm that exact condition, then resolve
with the reviewed candidate blob; this changes only the merge result, not the
approved head.

```bash
git diff --name-only --diff-filter=U
git restore --source=6303aab63eeed144fe176969ca7c87f5a852b967 \
  --staged --worktree protocols/CHANGELOG.md
test -z "$(git diff --name-only --diff-filter=U)"
git diff --quiet 6303aab63eeed144fe176969ca7c87f5a852b967 -- protocols/CHANGELOG.md
git diff --cached --check
git diff --cached --name-status "$qpbt021_main_before"
git commit -m "merge: integrate approved QPBT-021 local mathlib cache"

qpbt021_integration_sha=$(git rev-parse HEAD)
test "$(git rev-parse HEAD^1)" = "$qpbt021_main_before"
test "$(git rev-parse HEAD^2)" = 6303aab63eeed144fe176969ca7c87f5a852b967
git merge-base --is-ancestor 6303aab63eeed144fe176969ca7c87f5a852b967 HEAD
```

## Post-merge gates and closure

Do not mark the PR merged until all commands pass on the merge commit. Record
command, exit status, duration, cache hit/lock wait/build duration, and logs.

```bash
python3 -m unittest discover -s tests -p 'test_hot_main_cache.py' -v
python3 -m unittest discover -s tests -v
python3 scripts/check_workflow.py
python3 -m compileall -q scripts tests
python3 scripts/workflow.py validate
git diff --check "$qpbt021_main_before..$qpbt021_integration_sha"

env MATHLIB_ARCHIVE=/tmp/mathlib-81a5d257-shallow-repo.tar.gz \
  python3 scripts/hot_main_cache.py warm
python3 scripts/hot_main_cache.py status
```

The local archive was observed at 51,938,317 bytes with SHA-256
`c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`, matching
the reviewed pin. `warm` is the singleton full-main build required after
integration; do not run another builder concurrently.

After successful gates, make the coordinator-owned ledger transition and
validate before and after it:

```bash
python3 scripts/workflow.py validate
python3 scripts/workflow.py update pr LPR-012 \
  --set "integration_sha=\"$qpbt021_integration_sha\""
python3 scripts/workflow.py transition pr LPR-012 merged
python3 scripts/workflow.py transition issue QPBT-021 done
python3 scripts/workflow.py validate
git diff --check
```

Then record/import integration metrics and commit the state/event/review changes
as the post-merge workflow commit. Verify LPR-012 is `merged`, its
`integration_sha` equals the two-parent merge commit, QPBT-021 is `done`, and
the worktree is clean.

## Scout metrics

- Elapsed: approximately 10 minutes.
- Subagents: 0.
- Token usage: `null`; the collaboration backend did not expose per-agent token
  usage, so it was not estimated.
