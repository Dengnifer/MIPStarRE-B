# QPBT-032 / LPR-021 immutable binding (A02)

## Identity and ancestry

- Session: `i032-integrator-a02-pr021-bind`.
- Issue: `QPBT-032`; local PR: `LPR-021`.
- Base commit/tree: `259c73a368ef7403b4e36e190c9bf940497b300f` / `b3a404a012f9f120f1fa5fa692e51b92d000d615`.
- Candidate head/tree: `00b74473b04a72b57c7c7b9ebdfd9ad7ef17a99f` / `d47252b71d1cfa5df331c77f03f9b890c29ca770`.
- `git rev-list --parents -n 1 HEAD` returned the candidate followed by the exact base as its sole parent.
- `git merge-base --is-ancestor BASE HEAD`: exit 0.
- `git symbolic-ref -q HEAD`: exit 1, confirming detached HEAD.
- Candidate worktree status before this report-only write: clean (`git status --short --branch` returned only `## HEAD (no branch)`).

## Local PR identity

The canonical `workflow/state/prs.json` entry for `LPR-021` was read without
modification. It is a draft for `QPBT-032`, names base `main`, records the exact
base and candidate head above, names head
`issue/qpbt-032-approximation-a01`, and lists exactly the same two changed
paths below. Its five candidate-bound checks are passed, its independent A01
review approves this exact head with zero findings, and its implementer list
was empty when this post-PR adoption session authenticated it.

## Combined immutable manifest

`git diff --name-status BASE..HEAD` returned exactly:

```text
A\tMIPStarRE/QPBT/Basic/Approximation.lean
A\tworkflow/reviews/qpbt-032-approximation-skeleton-a01.md
```

Candidate path identities:

- `MIPStarRE/QPBT/Basic/Approximation.lean`: mode `100644`, 3317 bytes, Git blob `b3eb1b1eee2860b83b71659add650b9ff3e8ed4c`, SHA-256 `13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a`.
- `workflow/reviews/qpbt-032-approximation-skeleton-a01.md`: mode `100644`, 4827 bytes, Git blob `a1b56a0024f8bb89d8f18db5c50985cccd6eb136`, SHA-256 `b69eb36ebfa77f2839ff7a5c4c84a6fed011aae2eb30140a4fcd64ea64575320`.

The writer report SHA-256 is therefore exactly the value required by the
session envelope. No candidate byte was modified by this adoption session.

## Timing, topology, and action accounting

- Canonical session start: `2026-09-01T12:16:31.639706Z`.
- Local inspection interval: epoch `1788265105.234643962` through
  `1788265175.884995222`, or `70.650351` seconds through the pre-write evidence
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
?? workflow/reviews/qpbt-032-pr021-bind-a02.md
```

Thus the tracked candidate worktree remained clean and the only untracked path
was this owned report. Re-reading `HEAD`, `HEAD^{tree}`, the exact two-path
base/head manifest, and both candidate SHA-256 digests reproduced the identities
above. `git diff --check BASE..HEAD` exited 0, and a path-limited `git diff` over
the two candidate files was empty.

Disposition: immutable binding accepted for coordinator-side LPR-021
transition and integration. This report is formal implementer adoption of the
exact candidate; it is not independent reviewer approval.
