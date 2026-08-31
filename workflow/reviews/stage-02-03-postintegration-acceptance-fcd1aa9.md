# Stage 2/3 post-integration acceptance at `fcd1aa9`

- Audited commit: `fcd1aa928ac0263f83de37143dc8dc5f4d937210`
- Audited tree: `140075ba9f7681683ee80212b115e4b8841e2452`
- Historical second-commit equivalent: `65315213d047d9181804ad74d573f533c904ef4f`
- Disposable checkout: `/tmp/qpbt-stage23-current-main-b.NGCdhO/repo`
- Verdict: **pass for the combined source/blueprint gate**

This report binds the terminal Stage 2/3 source and blueprint acceptance gate
to one clean disposable checkout of the exact integrated main snapshot. It does
not approve LPR-001's separate endpoint-review gate and therefore does not by
itself authorize issue closure.

## Attempt history

The first strict attempt used
`/tmp/qpbt-stage23-current-main.ntYq6u/repo` and stopped before publication.
Its runtime directory was beside the checkout, which correctly failed the
source tool's repository-local ignored-runtime invariant with:

```text
runtime root must be the repository's ignored reference-source directory
```

No source was published by that attempt. The corrected attempt started from a
fresh clone and used `.workflow-runtime/reference-source` inside that clone.
The runbook-layout failure is retained as evidence rather than hidden by the
successful retry.

## Immutable integration checks

The corrected checkout resolved to the commit and tree above. Git ancestry
checks passed for the approved LPR-001, LPR-002, and LPR-004 heads and for
`65315213d047d9181804ad74d573f533c904ef4f`. Approved source and blueprint
path bytes matched their immutable reviewed heads. No replay, merge, or
cherry-pick was performed.

## Source gate

- Pinned archive bytes: `233859`.
- Pinned archive SHA-256:
  `d645cd51dd26cae59195e61aeeb5c886a254ef4adf15da7e5657ad90c7ec2174`.
- Archive inspection: 2 members, 34 slices, and 646 labels.
- Transport tests: 49/49 passed; test-body time 2.794 seconds, tool wall
  3.2017 seconds.
- Source tests: 49/49 passed; test-body time 8.418 seconds, tool wall
  8.8225 seconds.
- Materialization: 39 files and 646 labels in 0.411819 seconds.
- Materialized inventory SHA-256:
  `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`.
- READY SHA-256:
  `4d6a33759051b17428b3928d529d18e10da82e3bc09c75fbe429df324612b360`.
- A separate verification pass reproduced the same inventory.

## Blueprint gate

- Deterministic graph and source-root checks passed for 48 nodes and 12
  chapters.
- Blueprint tests: 26/26 passed in 0.135 seconds.
- Generated graph SVG: 52,775 bytes.
- A forced clean PDF build passed: 45 pages, 109 Lean identifiers, and
  143,555 bytes. The PDF byte hash is intentionally not an acceptance
  invariant.

## Aggregate and hygiene gates

- `python3 scripts/check_workflow.py`: 312/312 passed in 183.638 seconds.
- Python compile-all check: passed in 0.2484 seconds.
- `python3 scripts/workflow.py validate`: passed for the checkout snapshot
  (26 issues, 15 local PRs, and 304 issued sessions).
- `git diff --check`: passed.
- Tracked `git status --short`: empty.
- Author source, split section bodies, generated graph SVG, and PDF remained
  untracked/ignored as required.

The fresh clone was created at 2026-09-01 05:18:34.780638120 +0800 and the
terminal checks completed at approximately 2026-09-01 05:24:04 +0800. Token
usage is unavailable for root-coordinator shell work and is not estimated.
There were no Lean/Lake builds, hot-cache warms or seeds, Git writes, or
network operations in this acceptance run.

## Disposition

`65315213d047d9181804ad74d573f533c904ef4f` is the requested second main
commit in substance and history; creating a replacement would duplicate
already integrated work. After the separate endpoint review is satisfied, the
legal closure order remains `QPBT-010`, `QPBT-002`, `QPBT-009`, then
`QPBT-003`. Stage 3 remains open afterward for its distinct QPBT-023 child.
