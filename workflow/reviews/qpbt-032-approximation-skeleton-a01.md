# QPBT-032 Approximation Skeleton Attempt A01

## Scope and provenance

- Issue: `QPBT-032`, session: `i032-orchestrator-a01-approximation-skeleton`.
- Owned implementation path: `MIPStarRE/QPBT/Basic/Approximation.lean`.
- Base HEAD: `259c73a368ef7403b4e36e190c9bf940497b300f`.
- Base tree: `b3a404a012f9f120f1fa5fa692e51b92d000d615`.
- Source contract: `blueprint/metadata/nodes.json#F03-MEASUREMENT`.
- Frozen callable contract: `workflow/reviews/qpbt-023-leaf-contract-a04.md#F03-SIGNATURES` (SHA-256 `8de7983b66b2cce523b45bb3b14a788ac34b0315be91644610cf455b5306b065`).
- Paper source: `references/2001.04383v3/sections/dependencies/measurements.tex`, `def:bracket`, generated lines 3-47 and original lines 1856-1900. The source was verified from the primary worktree because this detached issue worktree does not contain the ignored section material.
- Authenticated MIPStarRE source: commit `507e81220d95266ff3d589d125b2f87c7300a9fb`, archive SHA-256 `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.

## Implemented boundary

The file declares exactly the F03 measurement-family boundary:

1. `MIPStarRE.QPBT.MeasurementFamily`, a question-indexed family of qualified `MIPStarRE.Quantum.Measurement` values.
2. `MIPStarRE.QPBT.ProjectiveMeasurementFamily`, pointwise effect idempotence.
3. `MIPStarRE.QPBT.MeasurementFamily.postprocess`, delegating to `MIPStarRE.Quantum.Measurement.postprocess`.
4. `MIPStarRE.QPBT.MeasurementFamily.postprocess_effect`, the exact qualified fiber sum.
5. `MIPStarRE.QPBT.MeasurementFamily.postprocess_effect_eq_zero_of_not_mem_range`, the empty-fiber consequence.

F04, observables, and all other declarations are intentionally excluded. There are no `sorry`, `axiom`, `constant`, public obligations, or imports from `MIPStarRE.LDT` measurement APIs.

## Statement-integrity table

| Declaration | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
|---|---|---|---|---|---|
| `MeasurementFamily` | Finite-outcome POVM family indexed by questions | Arbitrary `Question`; `[Fintype] [DecidableEq]` `Outcome` and `Coord`; qualified finite POVM | Family of POVMs | Function into the existing complete POVM structure | faithful boundary |
| `ProjectiveMeasurementFamily` | Every effect is a projector | Same family and pointwise `M.effect a * M.effect a = M.effect a` | Projective family | Exact pointwise idempotence predicate | exact |
| `postprocess` / `postprocess_effect` | Arbitrary outcome map; fiber sum | Finite/decidable source and target outcomes; qualified `Measurement.postprocess` | Relabeled POVM and `sum_{a:f(a)=b} M_a` | Same fiber sum, definitionally delegated | exact |
| `postprocess_effect_eq_zero_of_not_mem_range` | `b` outside image has zero effect | `b ∉ Set.range f` | Empty fiber evaluates to zero | Empty filtered `Finset` sum is zero | exact |

## Cache and timing

- Main cache key: `d71a99abea8f7ebf5bda5194dfef088b06f526230caf5ccbca34d62d5b4267b9`.
- Cache action: `seed`; cache hit; no main compilation by this issue.
- Seed target: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-032-approx-a01/.lake`.
- Seed elapsed: `67.092063` seconds; 124,925 files, 10,097,592,794 bytes copied; no writable build tree was shared.
- MIPStarRE materialization elapsed: `2.810645` seconds.
- Exposed token usage: `null` (local agent endpoint does not expose token counters in the workflow record).

## Validation

| Check | Result |
|---|---|
| `lake env lean MIPStarRE/QPBT/Basic/Approximation.lean` | pass |
| proof-debt and forbidden-import scan on owned file | pass; no matches |
| `lake build MIPStarRE.QPBT.Basic.Approximation` | pass (`8659/8659`, 3.5s) |
| `lake build` | pass (`8992` jobs, 6.02s; private seeded cache) |
| pinned reference verification | pass (`39` files, `646` labels) |
| MIPStarRE materialization verification | pass (`337` files, inventory `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`) |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass (`51` nodes, `12` chapters) |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | pass (`28` tests) |
| `git diff --check` | pass |

The implementation file SHA-256 is `13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a`. The worktree remains based on the requested detached HEAD; the implementation and this report are uncommitted candidate content for coordinator review and integration.

## Findings

No correctness or contract-fidelity findings. The only execution incident was an initial seed invocation from the linked worktree that the cache CLI classified as the primary worktree; rerunning with explicit `--repo-root /home/drx/MIPStarRE-auto` succeeded. No protocol change is proposed from this single occurrence.
