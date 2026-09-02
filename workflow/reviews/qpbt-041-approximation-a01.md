# QPBT-041/046 Approximation Implementation

## Result

The combined F04 implementation content is commit
`34ac974fed9b9981ff2f73516a8ce7c0f545320d` (tree
`444d4533b721c8908bcef195dfe13d4577dd6213`) over base
`4a6683795a71712d6a5c52b7539c2f532fd39f71`. It implements all 50 public
names in the corrected F04 contract, proves every theorem body, and leaves no
`sorry`, `admit`, `axiom`, `constant`, `_ofObligations`, or unsafe declaration.

The implementation is in `MIPStarRE/QPBT/Basic/Approximation.lean`. Its blob
is `4dba268f1a717753c8d23ccb0c82d6fe67b412e8` and its SHA-256 is
`c430c02e7168710134e2eeb1a3f70d2720aafa9fd9e3d46835437a9f19bd404d`.

## Source and contracts

Pinned source hashes:

| Source | SHA-256 |
| --- | --- |
| `sections/top-level/preliminaries.tex` | `045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1` |
| `sections/dependencies/strategies-distance.tex` | `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f` |
| `sections/qpbt/appendix-preliminaries.tex` | `20d608c4a71df57bb8b96bf4006f136a3298521e613d4904092a802eed09c284` |
| `sections/qpbt/qpbt-game-and-soundness.tex` | `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea` |

Reviewed signature block hashes:

| Node | Status | Signature SHA-256 |
| --- | --- | --- |
| `F04-DISTANCE` | proved | `2231ffa4cbce94fb124c51b197d0048363116cfa6d633e96401c20f29d8474e4` |
| `F04-ASYMPTOTIC` | proved | `fe5db22d362700530cc0de13713aed86326a2c029946bc971adbc7a640066075` |
| `F04-CONSISTENCY` | proved | `c013337a66ae81ac4016cbd6b62d18cb82e49631237ce4ce629c0b9160706b06` |
| `F04-DISTANCE-LAWS` | proved | `3caa7d20803ce7fb5ec07a63ae783e4cc03fdad79eeb35bc7091d78d19358b97` |

The corrected contract report has SHA-256
`3dfe7bb3b06400b4a31d94328e159b540d3095b384675a4370ab1cc8ec7fef2`;
the F04 gap note has SHA-256
`beedb84848ff8401178042a9eaf69c4139ad8609ff3ffc956cd733fdaa83735c`.

## Statement integrity

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| `F04-DISTANCE` | Normalized finite bipartite pure strategies, finite POVM/operator families, distributions, and local isometries. | Explicit finite decidable coordinate types, PMFs, norm-one Euclidean states, and rectangular linear isometries. | Finite state-dependent distances and local/tensor isometry actions. | Separate real values and NNReal bounds with certified isometry, local lift, and reindexing operations. | faithful boundary |
| `F04-ASYMPTOTIC` | Positive-integer families, errors in `[0,1]`, and strategy measurement comparisons on either strategy state. | Lean naturals guarded by `0 < n`, global `PaperBigO`, joint-PMF marginals, and an existential shared `StrategyStateChoice`. | Global state/operator/POVM/strategy `O(delta)` relations. | The same global relations; `StrategyFamiliesBigOWithChoice` is the helper and `StrategyFamiliesBigO` existentially chooses the paper branch. | faithful boundary |
| `F04-CONSISTENCY` | Projective exact consistency and arbitrary-POVM asymptotic consistency on a normalized bipartite state. | General local-action equality with projectivity required at paper uses, explicit Alice/Bob carriers, PMFs, and norm-one state premise for the triangle. | Exact consistency, mismatch value, global consistency relation, and Proposition 4.29. | The same data and `epsilon + 2 * sqrt (delta + gamma)` conclusion under explicit normalization. | faithful boundary |
| `F04-DISTANCE-LAWS` | Squared-distance triangle, heterogeneous common postprocessing, and consistency triangle. | Explicit finite types and PMFs; all paper-facing indexed relations use global `PaperBigO`. | The paper's exact laws up to absorbed universal constants. | Factor-two finite triangle, global asymptotic triangle, heterogeneous postprocessing, and exact Proposition 4.29 scale. | exact |

Gap G17 records the corrected heterogeneous postprocessing and normalization
contracts. Gap G18 records the paper's global-versus-eventual Big-O ambiguity;
the explicit top-level global convention controls, with only the valid
`PaperBigO.isBigOAtTop` direction exported.

## Validation

All commands below passed on clean content head `34ac974f`:

| Gate | Result | Wall time | Max RSS |
| --- | --- | ---: | ---: |
| `lake env lean MIPStarRE/QPBT/Basic/Approximation.lean` | passed; one source-required unused-proof-parameter linter warning | 12.25 s | 6,814,352 KB |
| `lake build MIPStarRE.QPBT.Basic.Approximation` | passed; 8,692 jobs replayed | 6.58 s | 936,320 KB |
| `lake build` | passed; 8,992 jobs | 6.74 s | 942,124 KB |
| blueprint unit tests | 32/32 passed | 1.99 s | 22,864 KB |
| pinned-source blueprint check | 54 nodes, 12 chapters, deterministic | 0.12 s | 20,760 KB |
| `python3 scripts/workflow.py validate` | 53 issues, 28 PRs, 433 sessions, 7 stages | 0.17 s | 31,080 KB |
| declaration/axiom audit | passed; only `propext`, `Classical.choice`, and `Quot.sound` | 4.63 s | 6,715,416 KB |
| strategy signature audit | helper has explicit choice; paper relation has no choice argument | passed | not recorded |
| base-to-head `git diff --check` and proof-debt/import scans | passed | not recorded | not recorded |

The normalized-state proof argument in `POVMConsistencyBigOTriangleLaw` is
needed by its theorem proof but does not occur in the reduced proposition, so
Lean emits one harmless unused-variable linter warning. Removing that public
argument would make the paper-labelled theorem false.

The PDF visual checker reports five overlaps in unchanged F06 content. The
same words and dimensions fail on exact base `4a668379`; the candidate only
shifts that block from page 14 to page 15. This is a baseline checker defect,
not an F04 regression.

## Cache and attempts

The exact-main recipe-v7 cache key was
`303d4b07cd0c9ccc9b83d83f69da6e35794fa2a3bdcc5ee18eceb3e6dc0f2624`
for main `4a668379`. Seeding the private issue worktree recorded one hit, zero
misses, zero lock wait, and zero builds. Because reflinks were unavailable, it
copied 124,925 files (10,097,592,794 bytes) in 80.62 seconds. No writable build
directory was shared.

One initial command handoff lost its polling handle at the 30-second tool
yield and did not publish a replacement. A dry-run reauthenticated the same
target and key; the explicitly polled retry completed successfully. Exactly
one agent ran Lean commands. The post-seed validation sequence comprised two
scoped elaborations, two affected-target builds, and two full builds because
the blueprint repair created a new exact content head; the second target and
full builds replayed the private cache.

## Review dispositions

Three independent reviews of previous head `04a8d5e8` agreed on the missing
existential strategy relation. The changed head renames the helper to
`StrategyFamiliesBigOWithChoice` and gives the paper relation the canonical
`StrategyFamiliesBigO` name. The integration review's other findings are also
fixed: all four F04 nodes are `proved`, and the nonexistent abbreviated
implementation SHA in the correction report is replaced by the exact commit.

The API review found no other blocking layering or simplification issue. Its
only cleanup suggestion is to relocate a generic measurement-completeness
lemma currently duplicated privately because the reusable copy sits in a
higher LDT layer. That non-critical refactor is deferred to a numbered issue
and is not part of this integration repair.
