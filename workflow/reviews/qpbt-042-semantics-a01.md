# QPBT-042 finite game semantics

## Result

Writer session `i042-orchestrator-a01-semantics` implemented the complete
`F04A-GAME-SEMANTICS` definition layer in
`MIPStarRE/QPBT/Game/Semantics.lean`. The immutable candidate is commit
`16a41327abd1a3fd749c8872c2773f013046d762` over base
`c1d6271394fa9aba6eefb27955618a4540469c2f`.

The candidate adds exactly one file and 312 lines. It defines all 18 frozen
callables, contains no proof placeholder or new assumption, and leaves the
issue worktree clean.

## Immutable identity

| Item | Value |
| --- | --- |
| Base tree | `34e0ef9fbb2579c270ad65e497e5f56449e6760d` |
| Candidate head | `16a41327abd1a3fd749c8872c2773f013046d762` |
| Candidate tree | `b52d1894da91c68edfd6b58b2eaf6a177faa4154` |
| Sole parent | `c1d6271394fa9aba6eefb27955618a4540469c2f` |
| Lean blob | `e881b7beadc9c9f9ff675341dfdf74fb9fb83f59` |
| Lean SHA-256 | `3f87a8c6ea14f326bc046bb77f6e914552acb0e0963ba1382aa31966fe5e807e` |
| Binary patch SHA-256 | `edcaa0c2eb344754b2811774bebc53fca3d33ddf132b2aa959171a98b0e08246` |

The exact source file is
`references/2001.04383v3/sections/dependencies/strategies-distance.tex`, ranges
4-51, 62-81, and 126-190, SHA-256
`a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f`.
The frozen API and contract reports have SHA-256 values
`f37ab823449c85b078330f3912b4ec8eedfc67b8c9ffedb1d1b261434ccc4b27`
and `f98f21f7a9f355ca2f2af4e8ef20a3390f995430d045427b79b1c1a7ed93e1e8`.

## Callable inventory

The exact names are `FiniteGame`, `FiniteGameStrategy`, `strategyValue`,
`StrategyWinsWithProbability`, `FiniteDimensionalGameStrategy`,
`FiniteDimensionalGameStrategy.value`, `gameValue`, `ProjectiveStrategy`,
`SymmetricGame`, `SymmetricStrategy`, `SupportCommutingStrategy`,
`ConsistentStrategy`, `PCCStrategy`, `SPCCStrategy`, `schmidtRank`,
`FiniteDimensionalGameStrategy.schmidtRank`, `entanglementRequirement`, and
`HasValueOnePCCStrategy`, all in namespace `MIPStarRE.QPBT`.

The implementation uses the source's four finite sums, the reviewed one-field
`PureStrategy` wrapper, support-relative commutation, shared-coordinate
consistency, real `sSup`, coefficient-matrix `Matrix.rank`, and `WithTop Nat`
`sInf`. Standalone consistency is the reviewed action-equality predicate;
paper-required projectivity is retained by `PCCStrategy`.

## Statement integrity

| Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| Finite question and answer alphabets, a question PMF, Boolean decision predicate, normalized finite pure tensor strategies with POVMs, and a common local Hilbert space where required. | Explicit `Fintype` and `DecidableEq` carriers, inherited `PureStrategy`, `ProjectiveMeasurementFamily`, `MeasurementConsistentOn`, local tensor actions, and canonical `Fin` dimensions. | Fixed and supremal values; projective, symmetric, support-commuting, consistent, PCC, and SPCC predicates; Schmidt rank; and the least finite rank bound or infinity. | The same formulas and quantifier boundaries, with game association represented by a data-free wrapper and dimension extrema over canonical `Fin` spaces. | faithful boundary |

No source ambiguity or new paper-gap finding arose.

## Validation

All final candidate gates passed before review:

| Gate | Result | Wall time |
| --- | --- | ---: |
| `lake env lean MIPStarRE/QPBT/Game/Semantics.lean` | passed | 5.13 s |
| `lake build MIPStarRE.QPBT.Game.Semantics` | passed; 8,693 jobs, inherited unused-`hpsi` warning only | 24.49 s |
| `lake build` | passed once; 8,992 jobs | 7.37 s |
| pinned-source blueprint check | 54 nodes, 12 chapters, deterministic | 0.12 s |
| exact declaration, debt, forbidden-assumption, executable-content, import, path, and diff scans | passed | not exposed |

Root independently authenticated the base, head, tree, parent, blob, file hash,
binary patch hash, one-path diff, clean worktree, complete source text, and
frozen signature block without rerunning Lean or Lake.

## Cache and attempts

The private seed was a hit for exact-main key
`6b455bc2b3b0b6b35a8a26e43fc072caebc87e13bb67916f396265a57c5ea6cf`:
zero misses, zero builds, zero lock wait, and 73.622629 seconds to copy 124,925
files and three symlinks (10,097,592,794 bytes). No writable build output was
shared.

The snapshot omitted `Approximation.olean` and the worktree initially lacked
the ignored upstream sources. Three failed prerequisite/preflight attempts took
2.17, 1.64, and 13.24 seconds. An approved direct private compilation produced
the missing object in 12.33 seconds. Root then used the authenticated source
materializer once in 3.006716 seconds: upstream commit `507e81220d95266ff3d589d125b2f87c7300a9fb`, archive SHA-256
`656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`,
337 files, 5,970,111 bytes, and inventory SHA-256
`d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.
The five authored QPBT files were preserved exactly.

## Session metrics

The writer elapsed time was 929.200 seconds. It spawned zero subagents. Token
usage is JSON `null` because the collaboration backend does not expose
per-agent token counts. No network, endpoint, GitHub, or credential action was
performed.

## Review

Fresh immutable mathematical/API review is pending for the exact candidate
above. No candidate gate is otherwise outstanding.
