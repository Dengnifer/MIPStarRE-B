# QPBT-057 source-fidelity review (A06)

Session: `i057-reviewer-a06-source-fidelity`
Issue: `QPBT-057`
Declared review base: `6b43c72ab382fa53ee7cfd259a56ec2fbe41b623`
Candidate: `a9abedb3d08d1b020d310075fc2865ae21397eb8`
Candidate tree: `f736b0ccd81f3f4e34b1cdfc1a35a25e112e5cd8`
Candidate patch SHA-256: `611f09855c6e35da2c1c3cb44dae8c8a1a8325d050504cce2b850de430693721`

## Findings

1. **High, blocking: the candidate is not based on the immutable review base.**
   The candidate's own report identifies `20745fe45450276db3c2130d2631d863e8346ba3`
   as its base (`workflow/reviews/qpbt-057-f06a-a01.md:3-6`), and
   `git merge-base 6b43c72ab382fa53ee7cfd259a56ec2fbe41b623 a9abedb3d08d1b020d310075fc2865ae21397eb8`
   is `20745fe45450276db3c2130d2631d863e8346ba3`, not the declared base.
   Consequently, the full diff against the declared base contains unrelated
   deletions and rewrites, including `workflow/events.jsonl`, canonical issue
   and session state, and prior review reports (the diff is 8,143 deletions).
   This violates the exact immutable-manifest requirement and makes it
   impossible to attribute the candidate changes to QPBT-057 or preserve the
   intervening project history. Rebase or reconstruct the implementation on
   `6b43c72...`, regenerate the candidate head/tree/patch and report hashes,
   then request a fresh review.

## Source-fidelity inspection (blocked by finding 1)

After isolating `MIPStarRE/QPBT/Game/Types.lean` relative to the candidate's
actual parent, the declarations inspected at `:1083-1161`, `:1212-1268`,
`:1288-1618` follow the pinned `preliminaries.tex:96-143` and
`conditionally-linear.tex:553-712` contracts: the six-tape body is the stated
dual-rail encoding with `00` terminators, query modes use canonical blank
unused tapes, and the two tracked holes are exactly
`downsizeCompiler_exists` and `downsize_time`. The dimension, associated-map,
and PMF statements retain the frozen signatures. This inspection cannot
constitute approval while the candidate is stale and deletes unrelated
canonical files.

## Verdict

**REQUEST CHANGES.** No tests, builds, Lean elaboration, cache operations,
network access, GitHub operations, or repository writes were performed.

## Accounting

- Token usage: `null` (not exposed by the collaboration backend).
- Child agents: none.
- Repository writes: zero.
- Review artifact: this file only.
