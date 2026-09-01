# QPBT-026 / LPR-016 activation-topology scout A24

## Verdict

`activate only an exact reviewed two-parent object; rebuild and re-review once
if canonical bookkeeping has advanced its first parent`.

There are two valid cases:

1. If canonical `main` still equals the first parent of the exact A23 merge
   commit when its immutable review approves, fast-forward `main` to that exact
   already-reviewed commit. Do not recreate the merge.
2. If canonical bookkeeping has advanced `main` beyond the A23 first parent,
   the A23 commit is a reviewed semantic prototype, not the activatable object.
   Build one new two-parent activation commit from the later actual `main`,
   preserve that parent's entire tree except for the four approved content
   deltas, obtain one fresh exact-object activation audit, and fast-forward to
   that already-reviewed commit before importing the audit outcome.

The second case is expected once resolver/reviewer reports, session outcomes,
metrics, and state are committed. Its sequencing prevents an infinite loop:
the final audit session is registered before the activation parent is frozen;
its report remains outside the canonical tree until the exact approved object
has been activated.

## Authenticated checkpoint and state topology

This scout is detached and porcelain-clean at commit
`710cfafd586172d3658499f3552c2ae5e27fe512`, tree
`1f30c34c056e7eb5bcb693d80176cdcfdbbc5f0b`.

At that checkpoint:

- QPBT-027 is `done` and LPR-017 is `merged` at true merge
  `3686315526fab8704745df6ad69d60e1bd72fa3a`.
- That merge has ordered parents
  `(3a90910de7921e43fd40db44271c528bbca7301d,
  2c6b1f1d0be89d09bad2f60e074cf106be99fd46)` and exactly four
  first-parent deltas: `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/workflow.py`, and `tests/test_workflow.py`.
- QPBT-026 is `in_progress`; LPR-016 is `approved`, with
  `integration_sha: null`. Its unexecuted gate requires the resolved immutable
  true two-parent integration and a fresh combined-tree review before merge.
- The exact LPR-016 candidate is
  `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`, tree
  `88b1b6076aa8890376cf4f8b56c3da2bd372367d`; its declared base and the
  unique merge base with checkpoint `710cfafd...` are both
  `ea584e9e894391773e09ddad2ce4d082497c7913`.

The change from the QPBT-027 integration commit `3686315...` to checkpoint
`710cfaf...` is confined to eleven canonical bookkeeping/evidence paths under
`research/metrics/`, `workflow/events.jsonl`, `workflow/reviews/`, and
`workflow/state/`. None of the four LPR-016 activation paths changed. This is
evidence that the overlay protocol is applicable at this checkpoint; it is not
permission to assume the same about a later parent.

The canonical A22 report, SHA-256
`1738299df52a8a9fdfa12b6423ef5e795b08f0a85d17b1b95067fffcd70f15ae`,
establishes one real changelog conflict, one clean but semantically overlapping
review-protocol merge, two candidate code/test changes, five shared-identical
reports, and the exact semantic-union rule. A23's future commit, tree, protocol
blobs, validation results, and review are intentionally not assumed here.

## Fixed identities

Let:

- `B` be `ea584e9e894391773e09ddad2ce4d082497c7913`;
- `C` be `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`;
- `I` be the eventual exact A23 resolved merge commit;
- `R` be the recorded first parent of `I`;
- `P` be the later actual canonical first parent after all preliminary
  resolver/reviewer bookkeeping and final-auditor issuance are committed; and
- `A` be the final activatable two-parent commit.

The candidate blobs that `A` must use are:

| path | mode | exact blob |
| --- | --- | --- |
| `scripts/local_agent.py` | `100644` | `25a5198e9b3c7e3ace8c6365b7064e8aa55dc506` |
| `tests/test_local_agent.py` | `100644` | `f8b51e87f2e1d7ac5fc40d55b0c415b95cebf824` |

The five reports must have the same blobs in `P`, `C`, `I`, and `A`:

| path | exact blob |
| --- | --- |
| `workflow/reviews/qpbt-026-capability-schema-a19.md` | `80d15f96cc97594236bc6d7d55879b2bead3c0a5` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a01.md` | `2923e68d180243053e80bc56f48fac9053499d4e` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a05.md` | `0ccf818f3a274a2fd649086a6919cc71a997cb59` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a11.md` | `da1e5c1cf6d8fec19a8c21d508c5efbd6f5baabc` |
| `workflow/reviews/qpbt-026-offline-isolation-a17.md` | `ea20399f6dceeea1e7d7ac04e90acd46f45935ce` |

The integrated QPBT-027 implementation must remain the first-parent version in
`P` and `A`:

| path | exact blob at this checkpoint |
| --- | --- |
| `scripts/workflow.py` | `6b5271bc995066641319c4ee0fe880e37d74490e` |
| `tests/test_workflow.py` | `ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe` |

The two protocol blobs are not known until A23 freezes. Extract them from the
reviewed `I` with `git ls-tree`, bind their modes and object IDs in the A23
review, and call them `I_CHANGELOG_BLOB` and `I_REVIEW_BLOB`. Never reconstruct
either blob from prose.

## Preactivation protocol

### 1. Authenticate the reviewed semantic prototype

Require all of the following before using any bytes from `I`:

- `I` is an immutable commit object with exactly two ordered parents `(R, C)`;
- `C` is an ancestor of `I`, and `git merge-base --all R C` returns only `B`;
- the first-parent content delta `R..I` is exactly four modified `100644`
  paths: the two protocol files and the two local-agent files;
- `I` uses the two fixed candidate code/test blobs and the five fixed report
  blobs above;
- the A23 protocol blobs implement A22's exact semantic union and contain no
  conflict markers or rejected hunks;
- the A23 validation logs are bound to the exact `I` commit/tree; and
- a fresh independent reviewer approved the exact `I` commit, tree, ordered
  parents, and disclosed immutable file manifest.

If `refs/heads/main` still equals `R` after that approval and the canonical
worktree is clean, re-run the identity gates immediately and fast-forward to
the exact `I`. That is the only no-rebuild fast path.

### 2. Freeze the last bookkeeping parent

If `main != R`, first canonicalize the completed A23 and preliminary-review
records. Then register the separate final activation-auditor session and commit
that issuance. Finish every other canonical mutation needed before activation.
The resulting clean exact `main` is `P`.

Do not import, finish, or archive the final activation auditor while it is
reviewing. Its eventual report must remain in `/tmp` until activation succeeds.
No other session may advance `main` during this interval.

Before construction, require:

- `R` is an ancestor of `P`;
- the complete `R..P` changed-path list is an explicitly inspected canonical
  bookkeeping/evidence manifest, not an inferred directory pattern;
- `P` and `R` have identical modes and blobs at all four activation paths;
- `P` retains the exact QPBT-027 workflow/test blobs above;
- `git merge-base --all P C` returns only `B`;
- the supported three-argument preview from `(B, P, C)` introduces no overlap
  beyond the two known protocol paths and still has the candidate results for
  the two local-agent paths; and
- all five shared reports have the fixed identical blobs in `P` and `C`.

Any failure means the semantic inputs changed. Stop, resolve again from the new
parent, and obtain a fresh review; do not widen an allowlist after seeing the
diff.

### 3. Construct one exact activation object

Create `A` off-main in the owned integration worktree or through an isolated
temporary index. Start with the complete tree of `P` and replace exactly these
four entries:

| path | source for exact mode/blob |
| --- | --- |
| `protocols/CHANGELOG.md` | reviewed `I` |
| `protocols/review.md` | reviewed `I` |
| `scripts/local_agent.py` | exact `C` |
| `tests/test_local_agent.py` | exact `C` |

Write the tree once, then create one commit with ordered parents `(P, C)` and
retain it under an integration ref while it is reviewed. This is a true merge
object. Do not point `main` at it yet, and do not recreate it after review:
changing metadata changes the commit identity even when the tree is unchanged.

Using a tree overlay is deliberate. It imports only the two reviewed semantic
union blobs and the two exact candidate blobs while preserving every later
canonical byte from `P`. The isolated index must begin from `P^{tree}`; it must
not begin from `I^{tree}`.

## Exact gates on `A`

Before review, and again immediately before activation, require all of these:

1. `git rev-list --parents -n 1 A` is exactly `A P C`, with no third parent.
2. `git rev-parse A^{tree}` equals the frozen reviewed activation tree.
3. `git diff-tree --no-commit-id --name-status -r P A` is exactly four `M`
   records, in path order, for:

   ```text
   protocols/CHANGELOG.md
   protocols/review.md
   scripts/local_agent.py
   tests/test_local_agent.py
   ```

4. The raw diff shows unchanged `100644` modes, protocol result blobs equal to
   the reviewed `I` blobs, and code/test result blobs equal to the fixed `C`
   blobs.
5. Every path outside that four-path manifest is byte-for-byte and mode-for-mode
   identical to `P`; the exact four-entry tree diff proves this globally.
6. `git merge-base --all P C` returns only `B`, and
   `git merge-base --is-ancestor C A` succeeds.
7. The five shared reports have the fixed blobs in `P`, `C`, and `A`.
8. `scripts/workflow.py` and `tests/test_workflow.py` in `A` equal `P` and the
   fixed QPBT-027 blobs above.
9. Both protocol files are free of conflict markers/rejected hunks, and
   `git diff --check P A` passes.
10. The exact-A validation sequence required by A22 passes with newly observed
    counts and durations: workflow validation, focused workflow and local-agent
    tests, aggregate Python tests, compileall, workflow checker, blueprint
    synchronization, identity, and clean-worktree checks. Historical A23 counts
    cannot be relabelled as exact-A results because the tree changed.

The final activation auditor must be fresh, independent, and read-only. It must
review exact `A`, exact ordered parents, the four-entry manifest, the two
reviewed protocol blob identities, the two candidate blob identities, all
first-parent preservation gates, the five reports, candidate ancestry, and the
exact-A validation logs. If an external transport is used, its authorization
must enumerate the exact immutable file manifest actually disclosed; standing
endpoint trust does not authorize credentials or unrelated content.

## Activation without another observer cycle

After the final auditor has frozen an approving report outside the repository:

1. Require canonical `HEAD` and `refs/heads/main` still equal `P`, with an empty
   porcelain status. If not, discard `A` as an activation candidate and repeat
   from the new parent with a fresh audit.
2. Re-run the ten exact identity gates above and verify the frozen audit report
   hash. Do not amend or recreate `A`.
3. Fast-forward `main` to exact `A`, for example with a porcelain
   `git merge --ff-only A` while checked out cleanly at `P`. Because `P` is the
   direct first parent, this updates the branch and worktree without producing
   a new commit.
4. Verify `HEAD == A`, ordered parents `(P, C)`, candidate ancestry, exact tree,
   and the same four-path first-parent delta.
5. Only now import the frozen audit report, finish/archive its session, record
   metrics, set LPR-016 `integration_sha` to exact `A`, transition the PR from
   `approved` to `merged`, and close QPBT-026 through its legal issue states.
   Validate canonical workflow state before and after those updates and commit
   them as descendants of `A`.

The Git activation therefore occurs only after approval, while the canonical
record of that approval occurs immediately after activation. This satisfies the
review-before-activation gate without moving the reviewed first parent. The PR
must remain `approved` with `integration_sha: null`, and QPBT-026 must remain
open, until exact `A` is active.

## Invalid alternatives

- **Wholesale reviewed-tree replacement:** making a new `(P, C)` commit with
  `I^{tree}` discards resolver/reviewer session records, metrics, events, state,
  reports, and any other first-parent bytes added after `R`. Its `P..A` delta
  exceeds four paths and fails preservation.
- **Merging `I` into later `main`:** this makes `I`, not `C`, the direct second
  parent. Candidate ancestry is only indirect, ordered-parent provenance is
  wrong, and the first-parent manifest is no longer the required PR activation.
- **Squash:** a squash has only the current parent and does not authenticate `C`
  as ancestry or preserve the reviewed merge topology.
- **Cherry-pick:** a cherry-pick creates new one-parent commits and neither
  preserves the semantic merge object nor makes `C` the direct second parent.
- **Reversing parents to `(C, P)`:** this turns the feature candidate into the
  mainline, moves canonical state to the second-parent side, and makes the
  first-parent delta include the full later-main history instead of four paths.
- **Resetting or replacing `main`:** this loses canonical history and is both
  destructive and unnecessary; the reviewed true merge can be activated by an
  ordinary fast-forward.

## When another fresh audit is required

A further audit is mandatory when the final activatable commit is not the exact
object previously approved. In particular, it is required if:

- `P != R`, including advancement caused only by canonical bookkeeping;
- `main` moves after `A` is frozen or approved;
- any parent, tree, mode, blob, commit metadata, or four-path manifest changes;
- any of the five report identities, QPBT-027 identities, merge-base result, or
  candidate ancestry checks changes;
- conflict resolution is rerun or either protocol blob is regenerated; or
- validation was executed against a different commit/tree.

No third preactivation review is needed when the final auditor approved exact
`A`, `main` remained exactly `P`, and `A` is fast-forwarded unchanged. A
postactivation identity audit can independently confirm the operation, but it
cannot substitute for the exact-object approval required before activation.

## Metrics and scope

- Stable session: `i026-scout-a24-activation-topology`.
- Topology: one bounded read-only scout; subagents: 0.
- Repository/canonical edits, Git writes, refs, commits, merges, tests, builds,
  Lean, Lake, cache actions, network, endpoint, GitHub, credentials, Codex CLI,
  and external review launches: 0.
- Output: only `/tmp/qpbt-026-activation-topology-a24.md`.
- Token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session token accounting, so no estimate was made.
- End-to-end elapsed time: `null`.
- Elapsed availability reason: no canonical per-agent timer was exposed before
  the first action, so no estimate was made.
