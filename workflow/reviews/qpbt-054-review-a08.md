# QPBT-054 / LPR-031 immutable gap-linkage review (A08)

Session: `i054-reviewer-a08-gap-linkage`
External identity: `/root/i054_reviewer_a08_gap_linkage`
Verdict: `request_changes`

## Finding

1. **Medium, blocking: one manifest Git blob identity is malformed.** The
   immutable manifest records the `blueprint/metadata/gaps.json` blob as the
   39-character value `ed9f21e679dcaebf088236c829f7c27ea432bb5` at line 68.
   The actual candidate blob is the 40-character value
   `ed9f21e6797dcaebf088236c829f7c27ea432bb5`. Its independent SHA-256 is
   correct, but exact authentication of every manifest entry fails.

Required change: refreeze a corrected manifest and perform a fresh explicit
immutable authentication. The candidate itself does not need to change.

## Substantive disposition

`F-LPR031-A06-001` is substantively resolved. G19 accurately records that the
paper permits arbitrary pointwise admissible `q(n)`, while one downsized
machine must determine widths involving `log q(n)` without being given an
algorithm for the odd exponent or charging that computation in `TIME_S(n)`.

At `blueprint/metadata/gaps.json:185`, G19 has the correct source, problem,
disposition, public effect, affected node `F06A-EXECUTABLE-CL`, and issue
`QPBT-054`. The reciprocal node link is at
`blueprint/metadata/nodes.json:426`. The regression at
`blueprint/tests/test_check.py:589` checks issue binding and semantic text and
then breaks each reciprocal direction independently. Generated consumers carry
the same data.

No false source claim or public obligation was added. The marker-delimited
F06A signature remains
`cfe433e36d0670c344b29ab5107557842e7d4fc8358fba2713b8ff2ee107a3a1`,
and its source Git blob is unchanged between repaired head `3a248eac` and final
candidate `f425986`. The final commit is report-only and nonsemantic.

## Authentication

- Manifest SHA-256: `49e1ef32b687b9095b6326d5019986e8ca7eb750d5dbb6d7444576e69b4c8904`.
- Canonical checkpoint/tree: `cc9194ad` / `0ba66c89`.
- Base/head/tree: `639c8837` / `f4259860` / `9a37c6ff`.
- Sole parent: `1c5f12b0`; full linear ancestry authenticated.
- Full-base, repaired-head, and report-followup patch SHA-256 values: PASS.
- Exact ten-path base diff and seven-path repaired-head diff: PASS.
- Candidate worktree: clean.
- Manifest entries: 18 passed completely; `gaps.json` passed content SHA-256
  but failed its malformed blob identity.

## Residual risk and accounting

Tests, Lean, Lake, builds, generation, and workflow validation were excluded by
the review constraints. Executable downsize and its runtime proof remain future
Lean work.

- Observed end: `2026-09-02T20:29:32.169904630Z`.
- Read-only shell invocations: 24.
- Writes, network, GitHub, credential access, and nested agents: 0.
- Token usage: `null`; the collaboration backend does not expose per-session
  usage.
