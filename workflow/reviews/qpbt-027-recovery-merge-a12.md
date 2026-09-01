# QPBT-027 / LPR-017 recovery merge scout A12

## Verdict and scope

**PASS, intermediate recovery-checkpoint only.** Exact candidate
`2c6b1f1d0be89d09bad2f60e074cf106be99fd46` still three-way merges into exact
recovery checkpoint `fc28a5c0649cde455c2da2f5559c79c833f3f814` with zero conflict evidence and
no evidence loss. The checkpoint is detached and clean at tree
`da930649555116e7426f867996f5622cd23376b4`; the candidate tree is
`0c6fdd0f7ce5349b0f543e171871eb0ef292eab6`; the independently recomputed merge
base is the supplied `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`.

This is **not integration authority**. Actual integration must rerun the same
read-only merge preview from the later approved-state commit as the first parent.
The provisional parent vector authenticated here is:

1. first parent: `fc28a5c0649cde455c2da2f5559c79c833f3f814`
2. second parent: `2c6b1f1d0be89d09bad2f60e074cf106be99fd46`

The actual merge must instead have ordered parents
`(LATER_APPROVED_STATE, 2c6b1f1d0be89d09bad2f60e074cf106be99fd46)`.
Any first-parent drift requires a fresh three-argument `git merge-tree` result;
this A12 result must not be reused as authorization.

## Object and ancestry authentication

Commands and exact material results:

```text
$ git rev-parse HEAD^{commit} HEAD^{tree}
fc28a5c0649cde455c2da2f5559c79c833f3f814
da930649555116e7426f867996f5622cd23376b4

$ git rev-parse 2c6b1f1d0be89d09bad2f60e074cf106be99fd46^{tree}
0c6fdd0f7ce5349b0f543e171871eb0ef292eab6

$ git merge-base fc28a5c0649cde455c2da2f5559c79c833f3f814 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
506ac7a7b57a2318e0764acfc2558dc62f9e50f0

$ git cat-file -p fc28a5c0649cde455c2da2f5559c79c833f3f814
tree da930649555116e7426f867996f5622cd23376b4
parent 0b6b6bbee56af367d90e72e74a77b81fef7ea918

$ git cat-file -p 2c6b1f1d0be89d09bad2f60e074cf106be99fd46
tree 0c6fdd0f7ce5349b0f543e171871eb0ef292eab6
parent 44ecdce96e5536407f89266b2be59820be56f01c

$ git rev-list --count 506ac7a7..fc28a5c
8
$ git rev-list --count 506ac7a7..2c6b1f1
2
$ git rev-list --left-right --count fc28a5c...2c6b1f1
8  2
```

Neither tip contains the other. A true merge, rather than a fast-forward or
squash, is therefore required to preserve the ordered second-parent identity.

## Three-way merge result

The only merge operation used was Git-2.34-compatible three-argument syntax:

```text
$ git merge-tree 506ac7a7b57a2318e0764acfc2558dc62f9e50f0 \
    fc28a5c0649cde455c2da2f5559c79c833f3f814 \
    2c6b1f1d0be89d09bad2f60e074cf106be99fd46
exit 0
merged sections: 4
changed in both: 0
added in both: 0
removed in remote: 0
conflict text hits: 0
conflict markers: 0
```

The four ordinary result blobs are exactly the candidate blobs:

| Candidate-only path | merge result Git blob | size | SHA-256 |
|---|---|---:|---|
| `protocols/CHANGELOG.md` | `f5fcf6d0511c889fc35e97ae551f8fcc98c13bfc` | 16,510 | `c667bcbdcb5c139242fe7ce6d936209a7a6d0d45c487ac22ae4d0f938023afd5` |
| `protocols/review.md` | `84b5c607426f661ce3defb6b525be99d839f14f9` | 8,927 | `4638e12e9d82d4a2d2bde3e2074068b468368bedaa21c623432f16ec090634ae` |
| `scripts/workflow.py` | `6b5271bc995066641319c4ee0fe880e37d74490e` | 134,259 | `a23110e0b65843525cc51443ef1c0aa8be1ad21df715c4b3c0b8e20b17e61eca` |
| `tests/test_workflow.py` | `ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe` | 83,117 | `89713c6d0dc2bbed1df1cd90977c7257dc3b67cde91321d6e57923751f96eabd` |

Representative exact merge-tree result lines:

```text
result 100644 f5fcf6d0511c889fc35e97ae551f8fcc98c13bfc protocols/CHANGELOG.md
result 100644 84b5c607426f661ce3defb6b525be99d839f14f9 protocols/review.md
result 100644 6b5271bc995066641319c4ee0fe880e37d74490e scripts/workflow.py
result 100644 ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe tests/test_workflow.py
```

## Path inventory and shared reports

Against merge base `506ac7a7...`:

```text
checkpoint changed paths: 26
candidate changed paths:  6
shared paths:             2
canonical-only paths:    24
candidate-only paths:     4
union paths:             30
```

The two shared add/add reports are authenticated as byte-identical at both tips:

| Shared report | Git blob at both tips | SHA-256 at both tips |
|---|---|---|
| `workflow/reviews/qpbt-027-finding-reconfirm-a01.md` | `06e0c36a4b376ec309463b2a3ccd19d8eff054a2` | `1885c02167279996773fe29d31cf3665d225d02ffd494b02d743fe2437134e73` |
| `workflow/reviews/qpbt-027-stale-append-fix-a05.md` | `815939ceb85a606cb134a6010b8e9a49c6b17df0` | `a442bc60c86ccae962c956ebe024f1b822792a9e9afbb9d81722458e954d5e61` |

They are absent at the merge base, so the apparent overlap is identical content,
not competing evidence. The four candidate-only paths above plus these two
shared reports account for all six candidate paths.

## Recovery evidence retained canonical-only

A08-A10 are absent from the candidate and present only in the checkpoint:

| Canonical-only report | Git blob | SHA-256 |
|---|---|---|
| `workflow/reviews/qpbt-027-review-a08-pr017-immutable.md` | `3997278c7de9832731f44ace379abe89f08ba48f` | `e6f610c8ebde2959e8d987f2baced343a994f94cca4c247a637055c51ca194e0` |
| `workflow/reviews/qpbt-027-pr017-integration-preflight-a09.md` | `201fa288f348749673bb970c37481bbc810a0b5b` | `5662adf704b47a3d5bff209908288868ea85e3a8c7e6838ee37d6b4714d5cec7` |
| `workflow/reviews/qpbt-027-postreview-ledger-a10.md` | `b83b6a0c771a7a8c9f6b16ba0f9df59345f0e9ce` | `0025803b6e92a91960cad61718a80aba050e1ced664dbc0d2c276e198a360560` |

For every ledger below, candidate blob equals merge-base blob while checkpoint
blob is distinct. Thus the candidate has no modification capable of replacing
the checkpoint side, and the merge retains the checkpoint blob unchanged:

| Canonical-only ledger | base = candidate blob | checkpoint/result blob |
|---|---|---|
| `research/metrics/incidents.jsonl` | `01e5c6114d558ba991a64295233fc1c559dd1e7f` | `7479fc14bb54663df04a30053b5d46f786cd77d1` |
| `research/metrics/sessions.jsonl` | `57973c738bc3a1ffc01e2ac494a57b3a179b7bf8` | `97cc7573eafa659d66e6ba3773ce1438ac753328` |
| `research/report.md` | `8aa6e317fadeaba6e0995a1038884adaa35240cc` | `0565717010e078d6aaf9cf62e97022fea7f081a8` |
| `workflow/events.jsonl` | `08bdd18aa96816d645f1623572aea61be8ae1cea` | `54a5f063410abad6c7fcfd0b6b23572f959452dc` |
| `workflow/state/issues.json` | `eeed4e632afdf794fceadcb44807778df4be5fcf` | `8b203a12c105cd601e45a39d0d8b70b10be1a36e` |
| `workflow/state/prs.json` | `21c21c160ea8037a9d51a78c8a62a32c4b706331` | `b51b1cf0407a9715719f1cd570f9181d2b5a47a2` |
| `workflow/state/sessions.json` | `3ee2dc2e2ef78a81b418ff3bc366c6c226a5322e` | `3f9c6ce0c70c800f7a98aca87f3b8f428149a06d` |
| `workflow/state/stages.json` | `4bf8fcd18aaa8f1ebd459d16e0277961bf1acf9d` | `633b588e46632e4dc909b3df00dd0212c53f563e` |

`INC-048` is line 48 of the checkpoint incident ledger. It records the A08
review-session PR-base binding misadmission, its A08/A11 occurrence sessions,
and the mitigation requiring a fresh correctly base-bound review. It is absent
from the candidate-side delta and therefore retained with the canonical incident
blob. The session metrics contain exact A08, A09, and A10 records; the event log
contains their planned/issued/running/update/finish/archive lifecycle; the stage
state lists all three report paths and `INC-048`. These records remain
canonical-only for the same exact base=candidate blob proof above.

The complete canonical-only inventory is 24 paths: the eight ledgers in the
table, A08-A10, eleven other review reports, and two further QPBT-027 reports.
No canonical-only path appears in a merge-tree conflict category.

## Commands and constraints

Material inspection commands included:

```text
git status --short --branch
git cat-file -t <commit>
git cat-file -p <commit>
git rev-parse <commit>^{tree}
git merge-base <checkpoint> <candidate>
git log --reverse --format='%H %T %P %s' <base>..<tip>
git diff --name-status <base> <tip>
git diff --numstat <base> <checkpoint> -- <scoped paths>
git ls-tree -r <tip> -- <scoped paths>
git show <commit>:<path> | sha256sum
git merge-tree <base> <checkpoint> <candidate>
```

The final pre-report status remained detached and clean at the exact checkpoint.
No refs, commits, index entries, or worktree files were changed. No tests,
builds, validation scripts, network, endpoint, GitHub, credential, Codex, Lean,
Lake, cache, or nested-agent actions were performed.

## Action metrics

- Session: `i027-scout-a12-recovery-merge`
- Role/topology: one read-only scout; nested agents `0`
- Inspection shell invocations before report write: `21`
- Report write actions: `1` (this `/tmp` file only)
- Supported three-argument `git merge-tree` invocations: `3`
- Merge conflicts/markers: `0` / `0`
- Repository edits / Git writes / refs created: `0` / `0` / `0`
- Tests / builds / validation commands: `0` / `0` / `0`
- Network / endpoint / GitHub / credentials / Codex launches: all `0`
- Lean / Lake / cache actions: all `0`
- Token usage: `null`
- Token unavailable reason: the collaboration backend does not expose per-agent
  token usage; no estimate was made.
- Exact read-only Git subprocess count: `null`
- Git subprocess count unavailable reason: compound read-only shell loops were
  not process-instrumented; no estimate was made.

## Residual risk and required integration gate

This Git-2.34 merge-tree interface does not emit a synthetic tree ID. The
object-level result is nevertheless complete here because all 24 canonical-only
paths are untouched by the candidate, both overlaps have identical blobs, and
all four ordinary merge results equal the candidate blobs. Residual risk is
limited to later first-parent drift, use of a squash/non-merge operation, manual
resolution, or failure to revalidate the actual integrated tree.

Before integration, freeze the later approved-state commit, recompute its tree
and merge base, rerun three-argument `git merge-tree` with that commit as branch
1, require zero conflict categories/markers, and re-inventory every path and
blob. After the true merge, verify ordered parents exactly
`(LATER_APPROVED_STATE, 2c6b1f1...)`, candidate ancestry, preservation of the
canonical evidence blobs, and equality of the four candidate result blobs.
