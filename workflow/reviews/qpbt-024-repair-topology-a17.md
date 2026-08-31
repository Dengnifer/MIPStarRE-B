# QPBT-024 sidecar repair lifecycle topology (a17)

## Verdict

Create **QPBT-025 as a child implementation issue of QPBT-024**. Do not reuse
QPBT-024 for the writer.

QPBT-024 already has its one recorded orchestrator,
`i024-orchestrator-a01-source-projection`, and its one issue worktree,
`/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-024-postbuild-a01`.
Both writable sessions on that worktree are archived, its exact candidate is
physically integrated at `9c9b49548fabdd6b01916787d7dc17a4bca36513`, and its
immutable LPR-014 evidence is approved. The failed acceptance warm discovered
a new, bounded hypothesis after that lifecycle. Reusing QPBT-024 would either
issue a second orchestrator or leave substantial implementation without an
active issue orchestrator. A child gives the new hypothesis exactly one owner,
one worktree, one branch, one PR, and one post-integration warm.

The child relationship is organizational, not a dependency edge. QPBT-025
must not depend on unfinished QPBT-024, and QPBT-024 cannot add unfinished
QPBT-025 as a dependency while remaining `review`: `workflow.py` rejects
`review` issues with unfinished dependencies. Keep QPBT-024 in `review` and
make completion of its child an explicit close predicate.

## Frozen issue and stage topology

| Issue | Parent | Dependencies | Initial/active status | Owner | Stage |
|---|---|---|---|---|---|
| QPBT-025 | QPBT-024 | `["QPBT-001"]` | create `ready`; then `in_progress`; then `review` | null at creation; `i025-orchestrator-a01-sidecar-removal` after dispatch | STAGE-04A |
| QPBT-024 | QPBT-000 | `["QPBT-001"]` unchanged | remain `review` | `i024-orchestrator-a01-source-projection` unchanged | STAGE-04A |
| QPBT-004 | QPBT-000 | `["QPBT-003", "QPBT-024"]` unchanged | remain `planned` | null unchanged | STAGE-04A |

QPBT-025 should be `kind: "workflow"`,
`execution_category: "implementation"`, with acceptance gates freezing A14's
four-file explicit-flag, recipe-version-5 repair, A16's omission-sensitive
matrix, exact-head Python/workflow/diff gates, fresh immutable review, guarded
integration, and exactly one successful new-key authenticated warm with READY
and deep-inventory verification. Its source references should include the 9b6
failure report and A11-A16, with A14 as the adjudication that supersedes A11's
retention recommendation.

Do not add QPBT-025 directly to QPBT-004's dependencies. QPBT-024 remains the
single cache-acceptance dependency and cannot close before QPBT-025 closes.

## Sequence-counter hazard

The live documents contain QPBT-000 through QPBT-024 and LPR-001 through
LPR-014, but record stale counters:

```text
workflow/state/issues.json next_sequence = 23
workflow/state/prs.json    next_sequence = 6
```

`scripts/workflow.py:756-758` checks only that a counter is a positive integer.
It does not require it to exceed the largest allocated suffix. The generic
`add` path at `scripts/workflow.py:2730-2745` appends an explicit record and
does not advance either counter. Duplicate-ID validation may reject an obvious
collision, but the counter itself can remain silently stale.

Therefore never allocate from the current counters. Compute maxima from the
record IDs. When the checkpoint adds QPBT-025, set
`issues.json.next_sequence` to **26**. Before LPR-015 exists, reconcile
`prs.json.next_sequence` to **15**; when LPR-015 is added, advance it to
**16**. These header changes are root-only canonical writes and need the
prescribed before/after workflow validation; the CLI has no counter-update
operation, so root must also inspect the resulting event/state consistency.

## Checkpoint, worktree, and ownership order

1. Finish or fail A14-A17 explicitly, import one metric row per issued session,
   archive them, and inspect their reports. Preserve the 9b6 failure envelope
   and its prior warm metric unchanged.
2. Run the pre-change workflow validation. Reconcile LPR-014/QPBT-024 failure
   evidence without changing their lifecycle statuses, add QPBT-025 as `ready`
   with null owner, add it to STAGE-04A, correct the sequence counters, and
   import the accepted A11-A16 reports/session accounting.
3. Run post-change workflow validation and commit this root-only evidence/state
   checkpoint on main. Call its exact resulting SHA **C0**. C0 must be a
   descendant of base/current main
   `9c9b49548fabdd6b01916787d7dc17a4bca36513`. Do not create the writable child
   worktree before C0 is immutable.
4. Create branch `issue/qpbt-025-sidecar-a01` and the sole QPBT-025 worktree
   `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-025-sidecar-a01`
   at exact C0. Do not reuse the QPBT-024 worktree or writable `.lake/build`.
5. Add draft LPR-015 with `base: "main"`,
   `head: "issue/qpbt-025-sidecar-a01"`, `base_sha: C0`, null `head_sha`,
   `issue_ids: ["QPBT-025"]`, empty checks/reviews/findings/implementers, and
   null integration metadata. Advance the PR counter to 16.
6. Plan and dispatch `i025-orchestrator-a01-sidecar-removal`, bound to LPR-015,
   base C0, and the new worktree. It is the only QPBT-025 orchestrator and sole
   writer. Its exact owned paths are:

```text
scripts/materialize_lake_packages.py
scripts/hot_main_cache.py
tests/test_lake_package_materialization.py
tests/test_hot_main_cache.py
```

   After it is issued, set QPBT-025's owner to that session, transition the
   issue `ready -> in_progress`, then start the session. Before finishing the
   orchestrator, transition the issue `in_progress -> review`; otherwise the
   validator sees an in-progress implementation issue with no active
   orchestrator. Finish, import metrics, inspect the diff/result, then archive.
7. Freeze exact candidate head **H**, attach only C0/H checks, list exactly the
   writable PR-bound orchestrator in `implementer_session_ids`, and transition
   LPR-015 `draft -> ready`. A fresh read-only
   `i025-reviewer-a02-lpr015-immutable`, bound to LPR-015 with base C0, reviews
   only after every current check completes. Approval permits `ready ->
   approved`.

Canonical state/metrics/reports remain root-owned throughout. The new writer
must not edit pins, protocol files, workflow state, metrics, runtime cache, or
the old QPBT-024 branch/worktree.

## PR and integration disposition

LPR-014 remains exactly:

```text
status          approved
base_sha        38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe
head_sha        9c9b49548fabdd6b01916787d7dc17a4bca36513
integration_sha null
merged_at       null
```

Its code is physically on main, but its post-integration gate failed. Do not
change its head, checks, reviews, findings, or old failure evidence. LPR-015 is
new evidence for C0/H and must not absorb or rewrite LPR-014 evidence.

After LPR-015 approval, root authenticates main still at C0 and performs one
guarded fast-forward to exact H. LPR-015 remains approved with null integration
metadata until the warm gate terminates. The only authorized warm is one
authenticated `hot_main_cache.py warm` for exact main H and its newly derived
recipe-v5 key. The old `9c9b495.../9b6ccb7...` attempt remains a failed count
of one and must never be retried.

On success, preserve the observed warm/status/READY/manifest/deep-inventory
facts in append-only post-integration evidence, not as a late PR check: adding
a check after approval can violate the validator's check/review chronology.
Then reconcile in physical order:

1. Set LPR-014 `integration_sha` to exact `9c9b495...` and transition it to
   `merged`.
2. Set LPR-015 `integration_sha` to exact H and transition it to `merged`.
3. Attach the same successful warm evidence to QPBT-025 and transition it
   `review -> done`.
4. Attach child/warm completion evidence to QPBT-024 and transition it
   `review -> done`.
5. Update QPBT-004's blocker text/evidence to say only QPBT-003 remains; leave
   QPBT-004 `planned`.

`integration_sha` is set once and is immutable. For LPR-014 it is the old
physical integration commit, not H and not the later state-reconciliation
commit. For LPR-015 it is H. `merged_at` is assigned only by the approved-to-
merged transitions.

On warm failure, set neither integration SHA, merge neither PR, and close
neither issue. Retain LPR-014 and LPR-015 as approved/null, QPBT-025 and
QPBT-024 as review, and QPBT-004 as planned. Do not retry the same H/key. A
further changed hypothesis requires a new child/owner/worktree and LPR-016;
do not advance the already physically integrated LPR-015 head.

## Close predicates

- **QPBT-025:** LPR-015 has immutable approval, H is physically integrated,
  the single new-key warm succeeds, status is a hit, READY equals the manifest
  digest, deep inventory matches, no failure envelope exists for the new key,
  and its orchestrator/reviewer sessions and metrics are terminally imported.
- **QPBT-024:** QPBT-025 is done; LPR-014 and LPR-015 are merged with their
  exact integration SHAs; the same successful warm discharges QPBT-024's final
  acceptance gate; INC-044 is reconciled without deleting either historical
  failure occurrence.
- **QPBT-004:** QPBT-024 and QPBT-003 are both done and QPBT-004's own pin,
  provenance, empty-project build, and local cache gates are reconciled. The
  sidecar warm may discharge the cache portion, but it cannot close QPBT-004
  while QPBT-003 is unfinished.

## Evidence hashes

```text
9c9b49548fabdd6b01916787d7dc17a4bca36513  audited base/current HEAD
c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c  AGENTS.md
5cff15811f193d6f33ea9a8a9b66d8d6e5a7d9cd37653091fa25bdad35bbd69d  workflow/state/issues.json
55c6dcefa2a3446c81098c6df0aad90b08f2f9a003733572525e05f70e0c878f  workflow/state/prs.json
a491cacdcfc5b9023b508cc3fb0975d891858a7c050e07c51bb7bc7e35f4f22f  workflow/state/sessions.json
7853885fd932929cf4a2fb13d78da85d96d301551abd388b4b86bc66ed8c3a34  workflow/state/stages.json
103ac6fe6db4bc72b52ba94122c9408a427e6c5a60d0c3f0d144fe091e17065c  scripts/workflow.py
5b2e0067c507b8a8ef610f700198b60be803ef24681b4df5ff3005db6bd4c4b6  workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md
72388d58782faa23ce28ed6abbcc2a12b9923446e82834c2b8ab5cdd9eca38d0  workflow/reviews/qpbt-024-sidecar-security-a12.md
e590a72922a24abf6f0fd5346cac540a96da49f678b6065e2d435d3f8affac5f  workflow/reviews/qpbt-024-protocol-evolution-a13.md
bd0d1a613db912bd45e64c4db435135fba547c73c35db496a540603b6f187407  /tmp/qpbt-024-sidecar-synthesis-a14.md
368d94af2c526241b66e238148b8d0d180efe6b17f2fa64b724d4d6e9c0bd5dd  workflow/reviews/qpbt-024-sidecar-tests-a16.md
```

## Session accounting

- Logical session: `i024-scout-a17-repair-topology`.
- Base and observed HEAD:
  `9c9b49548fabdd6b01916787d7dc17a4bca36513`.
- Start: `2026-09-01T01:56:42.681604+08:00`.
- End: `2026-09-01T02:03:45.734965462+08:00`.
- Elapsed: `423.053361462` seconds.
- Token usage: JSON `null`.
- Token availability reason: the collaboration backend does not expose
  per-session token usage; no estimate was made.
- Topology: root coordinator -> one read-only scout; subagents `0`; depth `1`.
- Repository/state/Git/runtime edits, validation commands, tests, builds, warm,
  seed, Lean/Lake, and network actions: `0`.
- Authored output: `/tmp/qpbt-024-repair-topology-a17.md` only.

The report SHA-256 is supplied out of band because embedding it would change
the digest.
