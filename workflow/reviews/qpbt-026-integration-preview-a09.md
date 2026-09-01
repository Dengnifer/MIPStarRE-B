# QPBT-026 / LPR-016 integration preview A09

## Scope and accounting

- Logical session: `i026-scout-a09-integration-preview`
- Role: read-only integration scout
- Start UTC: `2026-09-01T02:58:27Z`
- End UTC: `2026-09-01T03:02:46Z`
- Measured elapsed: `259` seconds, from the two UTC epoch readings
- Token usage: `null`
- Token availability reason: the collaboration/runtime interface does not expose per-agent token usage; no estimate was made
- Subagents: `0`
- Repository, candidate, branch, ref, index, worktree, and Git-object writes: `0`
- External reports written: exactly this report
- Endpoint contacts: `0`
- GitHub reads/writes: `0`
- Credentials read, inspected, or used: `0`
- Lean commands: `0`
- Lake commands: `0`
- Builds: `0`
- Hot-cache warm/seed/other cache actions: `0`

## Verdict

At the frozen checkpoint, a regular non-fast-forward three-way merge of
`94c0e630b5f2697f678c400da082f108bde89471` into
`e8ba9e4a1f94ac99118e3724d8af507f50235374` has **no predicted conflicts** and
does **not** silently overwrite canonical workflow state or research metrics.
The exact common ancestor is the immutable PR base
`ea584e9e894391773e09ddad2ce4d082497c7913`. The old three-argument, read-only
`git merge-tree BASE MAIN CANDIDATE` completed with exit 0, and the focused scan
found no `changed in both`, `added in both`, removal conflict, conflict marker,
or `CONFLICT` record.

The smallest safe integration is a non-fast-forward merge that retains the
candidate head as the merge commit's second parent. Do not cherry-pick the two
candidate commits and do not copy/restore selected paths. A true merge preserves
the immutable reviewed head and its two-commit, six-path provenance. The two
candidate reports are already present on main with byte-identical blobs, so the
merge will neither duplicate nor rewrite them; its first-parent staged delta is
expected to contain only the four implementation/protocol/test paths.

Integration must not begin at the current live worktree state. The frozen
ledger still says `changes_requested` at `workflow/state/prs.json:3964`, records
the A08 reviewer as `running` at `workflow/state/sessions.json:15515`, leaves its
end time null at `workflow/state/sessions.json:15529`, and explicitly retains
the unexecuted fresh-review gate at `workflow/state/prs.json:4208`. The worktree
also has root-owned, uncommitted changes in `workflow/events.jsonl`,
`workflow/state/sessions.json`, and, by the final status check,
`workflow/state/stages.json`. An approving A08 result must first be imported,
validated, finalized, metered, archived as required, and committed by the root
coordinator; integration must start from a clean post-A08 main.

## Frozen identities

All supplied identities matched:

| Identity | Observed |
| --- | --- |
| canonical main commit | `e8ba9e4a1f94ac99118e3724d8af507f50235374` |
| canonical main tree | `87d267c61ea9aaf379add57a91f219014c2b0248` |
| immutable PR base | `ea584e9e894391773e09ddad2ce4d082497c7913` |
| candidate head | `94c0e630b5f2697f678c400da082f108bde89471` |
| candidate tree | `4188a6d959cb145b945c9618789f96cd98165d02` |
| candidate branch | `issue/qpbt-026-disclosure-a01` -> `94c0e630b5f2697f678c400da082f108bde89471` |
| merge base of main/candidate | `ea584e9e894391773e09ddad2ce4d082497c7913` |

The candidate is exactly two linear commits:

1. `5d6164e949a32c906557a136c7e49558ea13d7ae`, parent `ea584e9e894391773e09ddad2ce4d082497c7913`, tree `7af3fb789c5a4438482599b25e0d42a2088bbba6`
2. `94c0e630b5f2697f678c400da082f108bde89471`, parent `5d6164e949a32c906557a136c7e49558ea13d7ae`, tree `4188a6d959cb145b945c9618789f96cd98165d02`

The canonical main side is exactly two commits after the same base:
`838ac2f90bf70ca3107b9620c3afe19b3b2d118d` then
`e8ba9e4a1f94ac99118e3724d8af507f50235374`.

## Path overlap and merge result

Candidate `base..head` has exactly the six ledger paths recorded at
`workflow/state/prs.json:4191`:

```text
protocols/CHANGELOG.md
protocols/review.md
scripts/local_agent.py
tests/test_local_agent.py
workflow/reviews/qpbt-026-disclosure-preflight-a01.md
workflow/reviews/qpbt-026-disclosure-preflight-a05.md
```

Main `base..checkpoint` changes 14 paths: seven canonical state/metric/event
paths and seven review reports. The intersection with the candidate is only:

```text
workflow/reviews/qpbt-026-disclosure-preflight-a01.md
workflow/reviews/qpbt-026-disclosure-preflight-a05.md
```

Both overlapping additions are identical on main and candidate:

```text
2923e68d180243053e80bc56f48fac9053499d4e  workflow/reviews/qpbt-026-disclosure-preflight-a01.md
0ccf818f3a274a2fd649086a6919cc71a997cb59  workflow/reviews/qpbt-026-disclosure-preflight-a05.md
```

The candidate's seven canonical paths
`research/metrics/{incidents,sessions}.jsonl`, `workflow/events.jsonl`, and
`workflow/state/{issues,prs,sessions,stages}.json` retain exactly their base
blobs. Main changes all seven. Therefore the three-way merge treats them as
main-only edits and retains main's versions. A two-tree command such as
`git diff MAIN..CANDIDATE` misleadingly lists these paths because the endpoint
trees differ; that is not evidence that a merge would revert them.

The four non-report candidate result blobs are:

```text
10fe3df78c746089cbe481be8265d34e2eb91e8b  protocols/CHANGELOG.md
9b190213738a2cce8517b1e833371d7b304c2d61  protocols/review.md
f75c6358bfef67efb03c60691836c78e46573f50  scripts/local_agent.py
8fe81c69921e5da78f9f0d0935deabae14c98a89  tests/test_local_agent.py
```

The merge-tree simulation selects those candidate blobs, retains the main-only
canonical blobs, and omits any report delta because both report blobs are
already identical. Exact predicted conflicts: **none**.

## Ledger hazards

1. **Premature integration is currently blocked.** `workflow/state/prs.json:3964`
   is `changes_requested`; `workflow/state/prs.json:4208` says a fresh independent
   immutable reviewer must approve the exact head; A08 is not terminal at
   `workflow/state/sessions.json:15515`. Merging before the root coordinator
   records an approving A08 review would violate the ledger even though Git can
   merge the trees.

2. **Cherry-picking breaks immutable-head ancestry.** The ledger binds exact head
   `94c0e630...` at `workflow/state/prs.json:3971`, exact tree and two-commit
   ancestry at `workflow/state/prs.json:4082`, and exact six paths at
   `workflow/state/prs.json:4191`. Cherry-picking `5d6164e` then `94c0e63` onto a
   different parent rewrites both commit IDs. The patches are predicted to apply
   cleanly (the first-commit merge simulation was also clean), but the reviewed
   head would not become an ancestor of main. `-x` trailers would be weaker
   provenance and would not satisfy the immutable head binding.

3. **Path copying loses PR provenance and can overwrite future concurrent bytes.**
   Restoring/applying only the four implementation paths would discard both
   candidate report paths from the integration history; restoring all six would
   redundantly rewrite already-canonical evidence. Either approach omits the
   reviewed candidate as a parent and bypasses three-way conflict detection.

4. **First-parent delta and PR delta are intentionally different.** The merge
   commit should have a four-path first-parent delta, while the immutable PR range
   remains six paths. Do not rewrite LPR-016's `changed_paths` to four and do not
   create replacement report files. Record both inventories in integration
   evidence and explain the identical report blobs.

## Recommended integration sequence

The following commands are recommendations only and were not executed by this
scout. Replace `<POST_A08_MAIN_SHA>` and `<MERGE_SHA>` with the full values
captured at those steps.

1. Root coordinator: run `python3 scripts/workflow.py validate --json` before
   canonical state mutation. Import the approving A08 report without changing
   its bytes; finish/metric/archive A08; resolve the four finding dispositions
   against that approving review; set LPR-016 to the repository's approved/ready
   pre-integration status; run `python3 scripts/workflow.py validate --json`
   again; commit only the root-owned state, metrics, event, and review evidence.

2. Require a clean worktree with `git status --porcelain=v2 --branch`, then freeze
   `<POST_A08_MAIN_SHA>` using `git rev-parse HEAD`. Reconfirm candidate identity
   with `git rev-parse 94c0e630b5f2697f678c400da082f108bde89471 94c0e630b5f2697f678c400da082f108bde89471^{tree} issue/qpbt-026-disclosure-a01`.
   Expected values remain candidate head `94c0e630...`, tree `4188a6d...`, and
   branch target `94c0e630...`.

3. Rehearse the actual post-A08 three-way merge read-only with
   `git merge-base <POST_A08_MAIN_SHA> 94c0e630b5f2697f678c400da082f108bde89471`
   and
   `git merge-tree ea584e9e894391773e09ddad2ce4d082497c7913 <POST_A08_MAIN_SHA> 94c0e630b5f2697f678c400da082f108bde89471`.
   Stop if the merge base is no longer `ea584e9e...`, if any candidate-owned
   implementation path changed on post-A08 main, or if merge-tree reports a
   conflict.

4. Start the real merge without committing:
   `git merge --no-ff --no-commit 94c0e630b5f2697f678c400da082f108bde89471`.
   Verify `git rev-parse MERGE_HEAD` is exactly `94c0e630...`.

5. Preserve both inventories. `git diff --name-status ea584e9e894391773e09ddad2ce4d082497c7913..94c0e630b5f2697f678c400da082f108bde89471`
   must show the six paths above. `git diff --cached --name-status` must show only
   `protocols/CHANGELOG.md`, `protocols/review.md`, `scripts/local_agent.py`, and
   `tests/test_local_agent.py`. `git diff --cached --check` must be silent.
   Confirm the two report blobs in both parents with `git ls-tree
   <POST_A08_MAIN_SHA> -- workflow/reviews/qpbt-026-disclosure-preflight-a01.md
   workflow/reviews/qpbt-026-disclosure-preflight-a05.md` and the same command
   against `94c0e630...`; the blob pairs must remain `2923e68...` and
   `0ccf818...`.

6. Run the staged integration gates, serially:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'
python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py
python3 scripts/workflow.py validate --json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py
git diff --cached --check
```

The focused suite must report exactly `58/58`. `scripts/check_workflow.py`
validates workflow state and research ledgers, then runs the aggregate
dependency-free `test_*.py` suite; record its exact test count and duration.
No Lean, Lake, full build, warm, seed, or other hot-cache action is required:
the integration changes workflow Python, protocol text, tests, and already-bound
reports only.

7. With all gates passing, create the merge commit using
   `git commit -m "merge: integrate approved QPBT-026 disclosure preflight"`.
   Capture `<MERGE_SHA>` with `git rev-parse HEAD`.

8. Final merge identity gates:

```text
git rev-parse <MERGE_SHA> <MERGE_SHA>^{tree} <MERGE_SHA>^1 <MERGE_SHA>^2
git merge-base --is-ancestor 94c0e630b5f2697f678c400da082f108bde89471 <MERGE_SHA>
git diff --check <POST_A08_MAIN_SHA>..<MERGE_SHA>
git diff --name-status <POST_A08_MAIN_SHA>..<MERGE_SHA>
git diff --name-status ea584e9e894391773e09ddad2ce4d082497c7913..94c0e630b5f2697f678c400da082f108bde89471
git status --porcelain=v2 --branch
```

`<MERGE_SHA>^1` must equal `<POST_A08_MAIN_SHA>` and `<MERGE_SHA>^2` must equal
`94c0e630...`; the first-parent delta must be four paths, the immutable PR delta
must remain six, candidate ancestry must succeed, and the worktree must be clean.

9. In a separate root-owned closure change, set LPR-016 `integration_sha` to
   `<MERGE_SHA>` and record `merged_at`/merged status, issue/session completion,
   validation results, metrics, and archive data according to the workflow.
   Run `python3 scripts/workflow.py validate --json` before and after that state
   mutation, commit it separately, then confirm
   `git merge-base --is-ancestor <MERGE_SHA> HEAD` and
   `git merge-base --is-ancestor 94c0e630b5f2697f678c400da082f108bde89471 HEAD`.

## Commands actually executed

All commands below were read-only. The two conflict-only `rg` pipelines exited
1 because they found zero conflict tokens; the underlying full merge-tree run
exited 0.

```text
date -u +%Y-%m-%dT%H:%M:%SZ
sed -n '1,260p' AGENTS.md
git rev-parse HEAD HEAD^{tree} ea584e9e894391773e09ddad2ce4d082497c7913 94c0e630b5f2697f678c400da082f108bde89471 94c0e630b5f2697f678c400da082f108bde89471^{tree} issue/qpbt-026-disclosure-a01
git status --short --branch
git merge-base ea584e9e894391773e09ddad2ce4d082497c7913 e8ba9e4a1f94ac99118e3724d8af507f50235374
git merge-base ea584e9e894391773e09ddad2ce4d082497c7913 94c0e630b5f2697f678c400da082f108bde89471
git merge-base e8ba9e4a1f94ac99118e3724d8af507f50235374 94c0e630b5f2697f678c400da082f108bde89471
git diff --name-status ea584e9e894391773e09ddad2ce4d082497c7913..e8ba9e4a1f94ac99118e3724d8af507f50235374
git diff --name-status ea584e9e894391773e09ddad2ce4d082497c7913..94c0e630b5f2697f678c400da082f108bde89471
git log --oneline --decorate --graph --boundary --all --max-count=40
git show --stat --summary --format=fuller 5d6164e
git show --stat --summary --format=fuller 94c0e63
git diff --stat ea584e9e894391773e09ddad2ce4d082497c7913..e8ba9e4a1f94ac99118e3724d8af507f50235374
git diff --stat ea584e9e894391773e09ddad2ce4d082497c7913..94c0e630b5f2697f678c400da082f108bde89471
git ls-tree e8ba9e4a1f94ac99118e3724d8af507f50235374 -- workflow/reviews/qpbt-026-disclosure-preflight-a01.md workflow/reviews/qpbt-026-disclosure-preflight-a05.md
git ls-tree 94c0e630b5f2697f678c400da082f108bde89471 -- workflow/reviews/qpbt-026-disclosure-preflight-a01.md workflow/reviews/qpbt-026-disclosure-preflight-a05.md
git diff --exit-code e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/reviews/qpbt-026-disclosure-preflight-a01.md 94c0e630b5f2697f678c400da082f108bde89471:workflow/reviews/qpbt-026-disclosure-preflight-a01.md
git diff --exit-code e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/reviews/qpbt-026-disclosure-preflight-a05.md 94c0e630b5f2697f678c400da082f108bde89471:workflow/reviews/qpbt-026-disclosure-preflight-a05.md
git show -s --format='%H%n%P%n%T%n%s' 5d6164e949a32c906557a136c7e49558ea13d7ae
git show -s --format='%H%n%P%n%T%n%s' 94c0e630b5f2697f678c400da082f108bde89471
git diff --name-only e8ba9e4a1f94ac99118e3724d8af507f50235374..94c0e630b5f2697f678c400da082f108bde89471
git diff --name-status e8ba9e4a1f94ac99118e3724d8af507f50235374...94c0e630b5f2697f678c400da082f108bde89471
git merge-tree ea584e9e894391773e09ddad2ce4d082497c7913 e8ba9e4a1f94ac99118e3724d8af507f50235374 94c0e630b5f2697f678c400da082f108bde89471
git merge-tree ea584e9e894391773e09ddad2ce4d082497c7913 e8ba9e4a1f94ac99118e3724d8af507f50235374 5d6164e949a32c906557a136c7e49558ea13d7ae
git diff --check ea584e9e894391773e09ddad2ce4d082497c7913..94c0e630b5f2697f678c400da082f108bde89471
git diff --check e8ba9e4a1f94ac99118e3724d8af507f50235374...94c0e630b5f2697f678c400da082f108bde89471
git merge-tree ea584e9e894391773e09ddad2ce4d082497c7913 e8ba9e4a1f94ac99118e3724d8af507f50235374 94c0e630b5f2697f678c400da082f108bde89471 | rg -n '^(changed in both|added in both|removed in remote|removed in local|CONFLICT|<<<<<<<|=======|>>>>>>>)'
git merge-tree ea584e9e894391773e09ddad2ce4d082497c7913 e8ba9e4a1f94ac99118e3724d8af507f50235374 5d6164e949a32c906557a136c7e49558ea13d7ae | rg -n '^(changed in both|added in both|removed in remote|removed in local|CONFLICT|<<<<<<<|=======|>>>>>>>)'
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/state/prs.json | rg -n 'LPR-016|94c0e630|ea584e9e|4188a6d9|qpbt-026-disclosure'
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/state/issues.json | rg -n 'QPBT-026|LPR-016|94c0e630|disclosure'
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/state/sessions.json | rg -n 'i026|94c0e630|disclosure'
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/reviews/qpbt-026-pr016-bind-a02.md
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/reviews/qpbt-026-review-a03-pr016-immutable.md
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/reviews/qpbt-026-review-a04-supplemental.md
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/state/prs.json | sed -n '3958,4210p' | nl -ba -v3958
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/state/issues.json | sed -n '1138,1185p' | nl -ba -v1138
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/state/sessions.json | sed -n '15505,15555p' | nl -ba -v15505
git diff --name-status 5d6164e949a32c906557a136c7e49558ea13d7ae..94c0e630b5f2697f678c400da082f108bde89471
git diff --numstat ea584e9e894391773e09ddad2ce4d082497c7913..94c0e630b5f2697f678c400da082f108bde89471
rg -n "check_workflow\.py|aggregate.*tests|58/58|58 tests|test_local_agent\.py" workflow protocols scripts tests README.md
rg --files scripts tests | sort
git log --oneline --all -- scripts/check_workflow.py tests/test_check_workflow.py tests/test_workflow.py
sed -n '1,240p' scripts/check_workflow.py
sed -n '1,220p' tests/test_check_workflow.py
git ls-tree 94c0e630b5f2697f678c400da082f108bde89471 -- protocols/CHANGELOG.md protocols/review.md scripts/local_agent.py tests/test_local_agent.py workflow/reviews/qpbt-026-disclosure-preflight-a01.md workflow/reviews/qpbt-026-disclosure-preflight-a05.md
git ls-tree e8ba9e4a1f94ac99118e3724d8af507f50235374 -- protocols/CHANGELOG.md protocols/review.md scripts/local_agent.py tests/test_local_agent.py workflow/reviews/qpbt-026-disclosure-preflight-a01.md workflow/reviews/qpbt-026-disclosure-preflight-a05.md
git ls-tree ea584e9e894391773e09ddad2ce4d082497c7913 -- research/metrics/incidents.jsonl research/metrics/sessions.jsonl workflow/events.jsonl workflow/state/issues.json workflow/state/prs.json workflow/state/sessions.json workflow/state/stages.json
git ls-tree 94c0e630b5f2697f678c400da082f108bde89471 -- research/metrics/incidents.jsonl research/metrics/sessions.jsonl workflow/events.jsonl workflow/state/issues.json workflow/state/prs.json workflow/state/sessions.json workflow/state/stages.json
git ls-tree e8ba9e4a1f94ac99118e3724d8af507f50235374 -- research/metrics/incidents.jsonl research/metrics/sessions.jsonl workflow/events.jsonl workflow/state/issues.json workflow/state/prs.json workflow/state/sessions.json workflow/state/stages.json
git show 94c0e630b5f2697f678c400da082f108bde89471:workflow/reviews/qpbt-026-disclosure-preflight-a05.md
git log --oneline ea584e9e894391773e09ddad2ce4d082497c7913..e8ba9e4a1f94ac99118e3724d8af507f50235374 -- workflow/reviews/qpbt-026-disclosure-preflight-a01.md workflow/reviews/qpbt-026-disclosure-preflight-a05.md
git log --oneline --reverse ea584e9e894391773e09ddad2ce4d082497c7913..e8ba9e4a1f94ac99118e3724d8af507f50235374
git show --name-status --format='%H%n%P%n%s' 838ac2f
git show --name-status --format='%H%n%P%n%s' e8ba9e4
git show -s --format='%H%n%P%n%s' c5a0fecc26eb18452219cf0df31ce2a9113e45f1
git show e8ba9e4a1f94ac99118e3724d8af507f50235374:workflow/state/prs.json | rg -n 'c5a0fecc26eb18452219cf0df31ce2a9113e45f1|integration_sha'
git show -s --format='%H%n%P%n%s' 6531521
git show -s --format='%H%n%P%n%s' 6543f21
date -u '+%Y-%m-%dT%H:%M:%SZ %s'
date -u -d '2026-09-01T02:58:27Z' +%s
git rev-parse HEAD HEAD^{tree} issue/qpbt-026-disclosure-a01 issue/qpbt-026-disclosure-a01^{tree}
git status --short --branch
```

## Residual risks

- This preview is exact for canonical checkpoint `e8ba9e4...`. A08 finalization
  necessarily advances main and adds root-owned evidence. Re-run the read-only
  merge-base, overlap, and merge-tree checks against that exact clean post-A08
  main before starting the merge. If post-A08 work changes any of the four
  candidate implementation paths or changes either report blob, this preview's
  clean-result proof no longer applies.
- The current worktree's root-owned uncommitted state was preserved and not
  inspected as candidate content. Its finalization and validation belong only to
  the root coordinator.
- The candidate's own documented functional residual risks (conservative
  path-name screening rather than content scanning, intentionally unsupported
  externally dispatched uncommitted bootstrap targets, and pre-existing
  committed-harness symlink behavior) are review concerns for A08; this scout
  assessed integration mechanics and ledger provenance only.
