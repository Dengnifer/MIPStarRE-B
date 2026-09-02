# Next Lean Lane Readiness A01

## Identity

- Canonical tracking issue: `Dengnifer/MIPStarRE-B#5`
- Stable local session: `i005-scout-a01-lean-readiness`
- Exact collaboration task path: `/root/i005_scout_a01_lean_readiness`
- Separate immutable external identity: unavailable; the collaboration runtime
  exposed no additional thread identifier
- Exact main: `4a6683795a71712d6a5c52b7539c2f532fd39f71`
- Completed: `2026-09-02T03:34:25Z`
- Start and elapsed time: unavailable
- Token usage: JSON `null`; per-agent usage was not exposed
- Subagents: 0

## Recommendation

Dispatch GitHub issue #17, migrated marker `QPBT-041`, as the next Lean lane.
Its archived dependencies QPBT-032 and QPBT-045 are complete at integration
SHAs `aa1f579d56b4476220d2d6ef4c69c3c06ae779e2` and
`b9cef4736f5b404ac63ab4b27133544f797f2960`, both ancestors of exact main.

The single writable path is
`MIPStarRE/QPBT/Basic/Approximation.lean`, current blob
`b3eb1b1eee2860b83b71659add650b9ff3e8ed4c`, SHA-256
`13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a`.
It contains the five integrated F03 declarations and 0/47 frozen F04
declarations. The required surface is 40 definitions or structures and seven
named theorems, frozen under blueprint nodes `F04-DISTANCE`,
`F04-ASYMPTOTIC`, `F04-CONSISTENCY`, and `F04-DISTANCE-LAWS`.

The source anchors are `strategies-distance.tex` lines 20-32, 138-150,
213-282, and 377-395; `appendix-preliminaries.tex` lines 49-53; and
`qpbt-game-and-soundness.tex` lines 533-545. Their SHA-256 values are,
respectively, `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f`,
`20d608c4a71df57bb8b96bf4006f136a3298521e613d4904092a802eed09c284`,
and `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea`.

Before issue worktree seeding, one elected builder must warm the recipe-v7
cache for exact main. Useful parallel sublanes after dispatch are read-only
Mathlib/isometry scouting, source/signature integrity review, and asymptotic or
consistency proof scouting. Only the issue writer may edit `Approximation.lean`.

Issue #16 remains blocked on a reviewed Fourier/rank-one-projector helper.
Issue #15 requires a larger certificate/PMF repair after its rejected A01.
The QPBT-041/QPBT-046 tracked-sorry split must be reconciled explicitly with
the older blueprint `allowed_minimal_sorries: []` metadata before approval.

The scout performed no compilation, build, edits, network access, or GitHub
writes.
