# QPBT-027 / LPR-017 integration preflight A09

## Verdict

**PASS: exact current main and exact candidate are cleanly compatible as a true
merge.** The unique merge base is the reviewed base
`506ac7a7b57a2318e0764acfc2558dc62f9e50f0`. Git 2.34.1's supported
three-argument `git merge-tree` reports four ordinary `merged` blocks, zero
conflict blocks, and zero conflict markers. The only paths changed on both sides
from the merge base are two add/add review-evidence files; both tips contain the
same mode and blob IDs, and independent SHA-256 hashes of the blob bytes match.

The safe integration is a true `--no-ff` merge made while current main is
exactly `0b6b6bbee56af367d90e72e74a77b81fef7ea918`. It must not be implemented by
resetting to, replacing the tree with, or fast-forwarding to the candidate: the
candidate does not descend from current main, and a tree replacement would omit
canonical state, metrics, report, event, and review evidence.

## Fixed inputs and workspace

- Scout worktree: `/tmp/qpbt-027-integration-scout-a09`
- Worktree state: detached and clean (`## HEAD (no branch)`; no short-status
  entries)
- Current main commit: `0b6b6bbee56af367d90e72e74a77b81fef7ea918`
- Current main tree: `d88d1b673b9c6e668dd989ddadd4096d9f2299cb`
- Candidate commit: `2c6b1f1d0be89d09bad2f60e074cf106be99fd46`
- Candidate tree: `0c6fdd0f7ce5349b0f543e171871eb0ef292eab6`
- Reviewed base: `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`
- Candidate direct parent: `44ecdce96e5536407f89266b2be59820be56f01c`
- Git: `git version 2.34.1`
- Repository `AGENTS.md`: read fully before inspection.

Initial identity command and exact result:

```text
$ pwd && git status --short --branch && git rev-parse HEAD HEAD^{tree}
/tmp/qpbt-027-integration-scout-a09
## HEAD (no branch)
0b6b6bbee56af367d90e72e74a77b81fef7ea918
d88d1b673b9c6e668dd989ddadd4096d9f2299cb
```

Candidate identity command and relevant exact result:

```text
$ git rev-parse 2c6b1f1d0be89d09bad2f60e074cf106be99fd46^ 2c6b1f1d0be89d09bad2f60e074cf106be99fd46^{tree} 506ac7a7b57a2318e0764acfc2558dc62f9e50f0^{tree} 44ecdce96e5536407f89266b2be59820be56f01c^{tree}
44ecdce96e5536407f89266b2be59820be56f01c
0c6fdd0f7ce5349b0f543e171871eb0ef292eab6
10f8da1ebb8b3fd7ce92dafee19d61fafe2cf8e2
03e24c81b284f1b9f2e9bafbbc457e8c5f352e9e
```

## Ancestry

Commands and exact results:

```text
$ git merge-base 0b6b6bbee56af367d90e72e74a77b81fef7ea918 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
506ac7a7b57a2318e0764acfc2558dc62f9e50f0

$ git merge-base --all 0b6b6bbee56af367d90e72e74a77b81fef7ea918 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
506ac7a7b57a2318e0764acfc2558dc62f9e50f0

$ git merge-base --is-ancestor 506ac7a7b57a2318e0764acfc2558dc62f9e50f0 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
[exit 0]

$ git merge-base --is-ancestor 44ecdce96e5536407f89266b2be59820be56f01c 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
[exit 0]

$ git rev-list --parents 506ac7a7b57a2318e0764acfc2558dc62f9e50f0..2c6b1f1d0be89d09bad2f60e074cf106be99fd46
2c6b1f1d0be89d09bad2f60e074cf106be99fd46 44ecdce96e5536407f89266b2be59820be56f01c
44ecdce96e5536407f89266b2be59820be56f01c 506ac7a7b57a2318e0764acfc2558dc62f9e50f0
```

Thus the candidate is exactly a two-commit line from the reviewed base, its
direct parent is the supplied A05 parent, and neither tip contains the other.
A true merge created from current main must have this ordered parent vector:

```text
first parent:  0b6b6bbee56af367d90e72e74a77b81fef7ea918
second parent: 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
```

## Changed-path inventory

The inventory is relative to the unique reviewed merge base
`506ac7a7b57a2318e0764acfc2558dc62f9e50f0`. There are 27 combined paths: 21
canonical-only, 4 candidate-only, and 2 shared byte-identical add/add paths.

Canonical-only (21; all retained unchanged by the true merge):

```text
M research/metrics/incidents.jsonl
M research/metrics/sessions.jsonl
M research/report.md
M workflow/events.jsonl
A workflow/reviews/qpbt-018-021-closure-evidence-a18.md
A workflow/reviews/qpbt-026-capability-schema-a19.md
A workflow/reviews/qpbt-026-disclosure-preflight-a11.md
A workflow/reviews/qpbt-026-offline-isolation-a17.md
A workflow/reviews/qpbt-026-review-a14-pr016-immutable.md
A workflow/reviews/qpbt-026-review-a18-pr016-immutable.md
A workflow/reviews/qpbt-026-review-a20-pr016-immutable.md
A workflow/reviews/qpbt-026-stage2-critical-path-a15.md
A workflow/reviews/qpbt-027-pr017-bind-a03.md
A workflow/reviews/qpbt-027-reconfirm-contract-a02.md
A workflow/reviews/qpbt-027-review-a04-pr017-immutable.md
A workflow/reviews/qpbt-027-stale-append-contract-a06.md
A workflow/reviews/qpbt-stage2-integration-order-a07.md
M workflow/state/issues.json
M workflow/state/prs.json
M workflow/state/sessions.json
M workflow/state/stages.json
```

Candidate-only (4; merged onto current main):

```text
M protocols/CHANGELOG.md
M protocols/review.md
M scripts/workflow.py
M tests/test_workflow.py
```

Shared (2; add/add relative to the base, but byte-identical on both tips):

```text
A workflow/reviews/qpbt-027-finding-reconfirm-a01.md
A workflow/reviews/qpbt-027-stale-append-fix-a05.md
```

Source commands:

```text
$ git diff --name-status 506ac7a7b57a2318e0764acfc2558dc62f9e50f0..0b6b6bbee56af367d90e72e74a77b81fef7ea918
[23 paths: the 21 canonical-only paths plus the 2 shared paths listed above]

$ git diff --stat 506ac7a7b57a2318e0764acfc2558dc62f9e50f0..0b6b6bbee56af367d90e72e74a77b81fef7ea918
23 files changed, 4519 insertions(+), 49 deletions(-)

$ git diff --name-status 506ac7a7b57a2318e0764acfc2558dc62f9e50f0..2c6b1f1d0be89d09bad2f60e074cf106be99fd46
[6 paths: the 4 candidate-only paths plus the 2 shared paths listed above]

$ git diff --stat 506ac7a7b57a2318e0764acfc2558dc62f9e50f0..2c6b1f1d0be89d09bad2f60e074cf106be99fd46
6 files changed, 976 insertions(+), 58 deletions(-)
```

The direct A05-parent-to-candidate delta was also checked:

```text
$ git diff --name-status 44ecdce96e5536407f89266b2be59820be56f01c..2c6b1f1d0be89d09bad2f60e074cf106be99fd46
M scripts/workflow.py
M tests/test_workflow.py
A workflow/reviews/qpbt-027-stale-append-fix-a05.md
```

## Shared add/add identity proof

Exact tree-object queries against current main followed by the candidate:

```text
$ git ls-tree 0b6b6bbee56af367d90e72e74a77b81fef7ea918 workflow/reviews/qpbt-027-finding-reconfirm-a01.md workflow/reviews/qpbt-027-stale-append-fix-a05.md
100644 blob 06e0c36a4b376ec309463b2a3ccd19d8eff054a2 workflow/reviews/qpbt-027-finding-reconfirm-a01.md
100644 blob 815939ceb85a606cb134a6010b8e9a49c6b17df0 workflow/reviews/qpbt-027-stale-append-fix-a05.md

$ git ls-tree 2c6b1f1d0be89d09bad2f60e074cf106be99fd46 workflow/reviews/qpbt-027-finding-reconfirm-a01.md workflow/reviews/qpbt-027-stale-append-fix-a05.md
100644 blob 06e0c36a4b376ec309463b2a3ccd19d8eff054a2 workflow/reviews/qpbt-027-finding-reconfirm-a01.md
100644 blob 815939ceb85a606cb134a6010b8e9a49c6b17df0 workflow/reviews/qpbt-027-stale-append-fix-a05.md
```

Independent SHA-256 over the exact Git blob bytes:

```text
$ git cat-file blob 06e0c36a4b376ec309463b2a3ccd19d8eff054a2 | sha256sum
1885c02167279996773fe29d31cf3665d225d02ffd494b02d743fe2437134e73  -

$ git cat-file blob 815939ceb85a606cb134a6010b8e9a49c6b17df0 | sha256sum
a442bc60c86ccae962c956ebe024f1b822792a9e9afbb9d81722458e954d5e61  -
```

Because each path has mode `100644` and exactly the same blob object on both
tips, the apparent add/add overlap is identical content, not a conflict.

## Exact merge-tree result

Git 2.34.1 supports the explicit-base form in this checkout. The initially
probed newer interface was rejected and made no changes:

```text
$ git merge-tree --write-tree --messages 0b6b6bbee56af367d90e72e74a77b81fef7ea918 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
usage: git merge-tree <base-tree> <branch1> <branch2>
[exit 129]
```

The supported exact true-merge query was:

```text
$ git merge-tree 506ac7a7b57a2318e0764acfc2558dc62f9e50f0 0b6b6bbee56af367d90e72e74a77b81fef7ea918 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
[exit 0; four ordinary merged blocks, no conflict block]
```

The exact merged block identities are:

```text
merged
  result 100644 f5fcf6d0511c889fc35e97ae551f8fcc98c13bfc protocols/CHANGELOG.md
  our    100644 224a0ef6a92be7f15d4fc5a4884d0e62ee2b9812 protocols/CHANGELOG.md
merged
  result 100644 84b5c607426f661ce3defb6b525be99d839f14f9 protocols/review.md
  our    100644 98e6590233e8a295e0cd87a72a9acf5e5c0092b5 protocols/review.md
merged
  result 100644 6b5271bc995066641319c4ee0fe880e37d74490e scripts/workflow.py
  our    100644 e2586f93d73eee0e7a402f03f026f1b6c6978040 scripts/workflow.py
merged
  result 100644 ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe tests/test_workflow.py
  our    100644 f4262b6bcc046fec29dda961ac0c5e60171cdffe tests/test_workflow.py
```

Conflict inventory probes and exact results:

```text
$ git merge-tree 506ac7a7b57a2318e0764acfc2558dc62f9e50f0 0b6b6bbee56af367d90e72e74a77b81fef7ea918 2c6b1f1d0be89d09bad2f60e074cf106be99fd46 | grep -E '^(merged|changed in both|added in both|removed in local|removed in remote|CONFLICT)'
merged
merged
merged
merged
[exit 0]

$ git merge-tree 506ac7a7b57a2318e0764acfc2558dc62f9e50f0 0b6b6bbee56af367d90e72e74a77b81fef7ea918 2c6b1f1d0be89d09bad2f60e074cf106be99fd46 | grep -E '<<<<<<<|=======|>>>>>>>'
[no output; grep exit 1]
```

Conflict inventory: **zero paths**.

## Evidence preservation assessment

No report, state, metrics, event, or review evidence is overwritten or omitted
by the true merge:

- All four `workflow/state/*.json` changes are canonical-only and survive
  unchanged.
- Both `research/metrics/*.jsonl` changes, `research/report.md`, and
  `workflow/events.jsonl` are canonical-only and survive unchanged.
- Thirteen canonical-only review reports survive unchanged.
- The two review reports present on both branches coalesce by identical blob ID
  and byte hash; neither has competing content.
- Candidate protocol, validator, and test changes are on paths untouched by
  current main since the common base.

`git diff --name-status current-main candidate` misleadingly displays the 13
canonical-only review files as deletions because they do not exist in the
candidate tip. That is a two-tip comparison, not a three-way merge result. The
explicit-base `merge-tree` result proves those main-side additions are retained.

Residual evidence risk is procedural only: replacing main's tree with the
candidate, rebasing/cherry-picking without a fresh review decision, or merging
from the wrong first parent could omit or mis-bind canonical evidence. The exact
true-merge sequence below avoids that risk.

## Smallest safe integration sequence

Run in the canonical main worktree, not this scout worktree:

```bash
git status --short --branch
git rev-parse HEAD HEAD^{tree}
git merge --no-ff --no-edit 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
```

Gate the merge command on an empty status and exact pre-merge output:

```text
HEAD       0b6b6bbee56af367d90e72e74a77b81fef7ea918
HEAD^{tree} d88d1b673b9c6e668dd989ddadd4096d9f2299cb
```

Do not use a squash merge: it would not produce the required second-parent
identity. Do not use a candidate-tree checkout/reset.

## Post-merge identity and validation checks

Immediately after the merge:

```bash
git rev-parse HEAD^1 HEAD^2
git status --short --branch
git diff --name-status HEAD^1..HEAD
git ls-tree HEAD workflow/reviews/qpbt-027-finding-reconfirm-a01.md workflow/reviews/qpbt-027-stale-append-fix-a05.md
python3 scripts/workflow.py validate
python3 -m unittest tests.test_workflow
git diff --check HEAD^1..HEAD
```

Required identity results:

```text
HEAD^1 = 0b6b6bbee56af367d90e72e74a77b81fef7ea918
HEAD^2 = 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
```

`git diff --name-status HEAD^1..HEAD` must list exactly the four candidate-only
modified paths (`protocols/CHANGELOG.md`, `protocols/review.md`,
`scripts/workflow.py`, `tests/test_workflow.py`). The two shared evidence paths
must retain blob IDs `06e0c36...` and `815939ce...`. The worktree must be clean,
workflow validation and the workflow unit suite must pass, and `git diff
--check` must report no whitespace errors. These validation commands are
recommended post-merge gates; this read-only scout did not execute tests,
builds, Lean, Lake, or cache commands.

The merge commit SHA and tree SHA cannot be specified before creation because
the commit identity includes integration metadata and this Git version's
read-only `merge-tree` interface does not emit a synthetic tree ID. Parent and
path/blob checks above provide the deterministic identity gates available in
this preflight.

## Metrics and action counts

- Session: `i027-scout-a09-pr017-integration`
- Role: fresh read-only integration scout
- Topology: one agent; nested/subagents: 0
- Measurement interval: `2026-09-01T05:19:29Z` to
  `2026-09-01T05:21:05Z` (96 seconds, from first explicit timestamp through
  completion of merge analysis; report write/hash time excluded)
- Shell execution actions through analysis completion: 23
- Read-only Git process invocations through analysis completion: 29
- Rejected syntax probes: 1 (Git-version compatibility only; exit 129)
- Merge-tree true-merge analyses: 4 supported invocations (one full result,
  three filtered/relevant-result replays)
- Conflicts: 0
- Shared add/add paths checked by blob ID and SHA-256: 2
- Tests/builds/Lean/Lake/cache actions: 0
- Network/endpoint/GitHub/credential/Codex actions: 0
- Refs/commits/index/worktree mutations: 0
- Canonical repository files written: 0
- Report files written: 1 (this `/tmp` artifact only)
- Token usage: `null`
- Token availability reason: the execution environment does not expose a
  per-session token counter; no estimate was made.
- Residual risk: integration-time first-parent drift or use of a non-merge tree
  replacement; mitigated by exact pre/post SHA and path/blob gates above.

Final scout worktree check before report creation:

```text
$ git status --short --branch
## HEAD (no branch)
```
