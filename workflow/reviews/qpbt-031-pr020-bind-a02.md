# QPBT-031 / LPR-020 immutable binding (A02)

## Identity and ancestry

- Session: `i031-integrator-a02-pr020-bind`.
- Issue: `QPBT-031`; local PR: `LPR-020`.
- Base commit/tree: `259c73a368ef7403b4e36e190c9bf940497b300f` / `b3a404a012f9f120f1fa5fa692e51b92d000d615`.
- Candidate head/tree: `f5ed1cb3e10831b0230f7c28eeef4d94d0335b88` / `b3b368d5fb7cf2bb91c26890b3857cab7882e8b5`.
- `git merge-base --is-ancestor BASE HEAD`: exit 0.
- `git symbolic-ref -q HEAD`: exit 1, confirming detached HEAD.
- Candidate worktree status before this report-only write: clean (`git status --short --branch` returned only `## HEAD (no branch)`).

## Local PR identity

The canonical `workflow/state/prs.json` entry for `LPR-020` was read without
modification. It is a draft for `QPBT-031`, names base `main`, records the exact
base and candidate head above, names head `issue/qpbt-031-field-a01`, and lists
exactly the same two changed paths below. Its implementer list was empty when
this post-PR adoption session authenticated it.

## Combined immutable manifest

`git diff --name-status BASE..HEAD` returned exactly:

```text
A\tMIPStarRE/QPBT/Basic/Field.lean
A\tworkflow/reviews/qpbt-031-field-skeleton-a01.md
```

Candidate path identities:

- `MIPStarRE/QPBT/Basic/Field.lean`: Git blob `6844e84a08f473dc29620c80392538935348995d`; SHA-256 `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e`.
- `workflow/reviews/qpbt-031-field-skeleton-a01.md`: Git blob `7430dfae6aa53a13cc2d0dd2df803a20d8610f98`; SHA-256 `584346e9f6709f1e6350ace98ba37730ba3a7654b2fedc52283cc31531526d32`.

No candidate byte was modified by this adoption session.

## Timing, topology, and action accounting

- Canonical session start: `2026-09-01T12:12:53.236177Z`.
- Local inspection interval: epoch `1788264896.788427128` through
  `1788264974.681130074`, or `77.892703` seconds through the pre-write evidence
  cut. Coordinator lifecycle elapsed time remains authoritative for archival.
- Topology: root coordinator -> this integrator; nested agents: 0.
- Repository content writes: 1 owned report; candidate content writes: 0;
  Git refs/index writes: 0.
- Lean/Lake/build/cache actions: 0.
- Endpoint/network/GitHub/credential actions: 0.
- Retries/incidents/new issues: 0.
- Token usage: `null` (the collaboration backend does not expose per-agent
  token usage; no estimate was made).

## Post-write hygiene

After the report write, `git status --short --branch` returned exactly:

```text
## HEAD (no branch)
?? workflow/reviews/qpbt-031-pr020-bind-a02.md
```

Thus the tracked candidate worktree remained clean and the only untracked path
was this owned report. Re-reading `HEAD`, `HEAD^{tree}`, the two-path base/head
manifest, and both candidate SHA-256 digests reproduced the identities above.
`git diff --check BASE..HEAD` exited 0.

Disposition: immutable binding accepted for coordinator-side LPR-020
transition and integration. This report is formal implementer adoption of the
exact candidate; it is not independent reviewer approval.
