# QPBT-046 proof closeout

## Result

Session `i046-orchestrator-a01-proof-closeout` performed a read-only,
no-byte-change audit of exact head
`54643d8ab4ac7b2e0c6d8efd96222d1417cfa600` in the immutable F04 candidate
worktree. It found no mathematical, source-fidelity, proof, or declaration
issue and concluded that every substantive QPBT-046 acceptance gate is already
evidenced. No new declaration edit or duplicate Lean, Lake, build, or cache run
is needed.

The audit authenticated content commit
`34ac974fed9b9981ff2f73516a8ce7c0f545320d` as an ancestor, Lean blob
`4dba268f1a717753c8d23ccb0c82d6fe67b412e8`, and Lean SHA-256
`c430c02e7168710134e2eeb1a3f70d2720aafa9fd9e3d46835437a9f19bd404d`.
The owned Lean file is byte-identical between the reviewed content commit and
the final candidate head.

## Gate audit

- All four F04 blueprint nodes are `proved`, expose the 50 reviewed public
  names, and record zero allowed or remaining proof holes.
- The finite distance and isometry layer, global Big-O adapters, consistency
  scale, triangle laws, and heterogeneous postprocessing theorem are present.
- Read-only scans found no `sorry`, `admit`, declared `axiom` or `constant`,
  unsafe declaration, `_ofObligations`, or forbidden assumption package.
- Existing immutable evidence records scoped elaboration, affected-target and
  full builds, blueprint and pinned-source synchronization, statement
  integrity, declaration/axiom audits, cache isolation, and fresh approval.
- G17 and G18 retain the two documented paper-boundary clarifications.

## Workflow disposition

The auditor reported that its immutable candidate worktree did not contain
`LPR-029` and still showed the pre-closeout QPBT-046 row. That is expected: the
worktree was frozen at the reviewed candidate head, while canonical state is
written only in the root worktree after review. At disposition time, canonical
root records `LPR-029` as merged at the exact head and QPBT-046 as owned by this
session. The observation is therefore resolved as a worktree-state location
mismatch, not an implementation blocker.

The session performed zero edits, Git writes, compiles, builds, cache actions,
network requests, GitHub operations, or nested launches. Per-session token and
agent elapsed counters were not exposed; canonical lifecycle timing is retained
in `workflow/state/sessions.json`.
