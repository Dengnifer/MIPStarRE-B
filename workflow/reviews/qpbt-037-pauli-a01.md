# QPBT-037 Pauli implementation attempt (A01)

## Findings

1. **Blocker: the immutable base does not contain the required foundation.**
   At base `358cd108db045d13f4e0095a2948dd4037be2b54`, the tracked `MIPStarRE/`
   tree contains only `QPBT/Basic/Field.lean` and
   `QPBT/Basic/Approximation.lean`.  The latter imports
   `MIPStarRE.Quantum.Measurement` and `MIPStarRE.Quantum.FiniteHilbert`, but
   those modules are not tracked at this base.  They are only available as
   ignored materialization artifacts in the local hot-main cache.

2. **Blocker: the frozen F05 signatures require a complete POVM.**
   `pauliProjector` has type
   `Quantum.Measurement (GaloisField 2 k) (GaloisField 2 k)`.  A faithful
   implementation must provide PSD rank-one Fourier projectors and prove their
   finite sum is the identity.  The pinned Pauli source is
   `references/2001.04383v3/sections/dependencies/pauli.tex` (lines 1--110;
   root materialization), and the frozen contract is
   `workflow/reviews/qpbt-035-q014-contract-a02.md` (F05 marker).  The tracked
   base supplies neither the Fourier projector lemmas nor an imported module
   exposing them.

   Relevant available primitives were inspected but do not close this gap:
   `Matrix.posSemidef_vecMulVec_self_star` and
   `Matrix.nonneg_iff_posSemidef` prove positivity of an individual rank-one
   projector, while `FiniteField.trace_to_zmod_nondegenerate` proves only
   nondegeneracy of the finite-field trace.  The missing step is the composed
   additive-character orthogonality argument proving the X-basis projector sum
   is `1` (and its Fourier inversion), which must be supplied as a reviewed
   helper or proved inside this lane.

3. **Correctness constraint.**  A provisional diagonal/delta measurement was
   rejected: it does not implement the X eigenbasis and makes the required
   Fourier expansion false.  No candidate was committed and no non-faithful
   declaration is being exported.

## Immutable manifest

The following bytes were the review inputs for this attempt.  The two paths
under `/home/drx/.cache` are ignored, pinned upstream foundation material used
only for read-only API inspection; they are not candidate source.

| Path | SHA-256 |
| --- | --- |
| `AGENTS.md` | `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c` |
| `workflow/state/issues.json` | `e9b13ca4bcef3174a9655590a82ff0a193a409feaa019772e9d0505e22908d46` |
| `workflow/reviews/qpbt-035-q014-contract-a02.md` | `987d17140ae4e1e808ed0504b874c67dc1285f70245cf71363dafe97fc1dd610` |
| `blueprint/metadata/nodes.json` | `705b7a474ac65671ac5f1e2288f671c5f7805b5ce5d3b92d08bade160239b8cd` |
| `blueprint/metadata/gaps.json` | `77c4a093568a48483b5b8dbeb061e8940d91c2a06ebabb670f5c25de95ab8b69` |
| `MIPStarRE/QPBT/Basic/Field.lean` | `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e` |
| `MIPStarRE/QPBT/Basic/Approximation.lean` | `13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a` |
| `references/2001.04383v3/sections/dependencies/pauli.tex` (root materialization) | `aba301b2e225f0ceaeff6a942a75ee6d5db73283ba25e208e2e43452818aef2f` |
| `MIPStarRE/Quantum/FiniteMatrix/Basic.lean` (ignored pinned foundation) | `09f00e0a381ce51f99dd9c583ececaaf8ff0f8c1c40ed2e102d7eda5599f90f3` |
| `MIPStarRE/Quantum/Measurement.lean` (ignored pinned foundation) | `c84a712e34425a46ae17d9f04d789ae7393ae97da3cf7ee3f93fe0e6705b9d0d` |

The contract's F05 signature marker is the exact byte interval between
`BEGIN F05-SIGNATURES` and `END F05-SIGNATURES` in the contract file above;
the blueprint binds that interval to SHA-256
`2046e1a3784f6bf10a1a7c71b279bd41d5c27ed3424e20797cf7c5bba95b4aa7`.

## Reproduction

- `git rev-parse HEAD` = `358cd108db045d13f4e0095a2948dd4037be2b54`.
- `git ls-tree -r --name-only HEAD MIPStarRE` lists only the two QPBT basic
  files above.
- `lake env lean MIPStarRE/QPBT/Basic/Approximation.lean` attempts to fetch
  Mathlib in a fresh worktree because dependencies are not materialized.
- With pinned Mathlib and upstream `.olean` artifacts wired privately from the
  hot-main cache, `lake build MIPStarRE.QPBT.Basic.Field` and
  `lake build MIPStarRE.QPBT.Basic.Approximation` pass (Field emits its
  pre-existing authorized G16 `sorry`).
- A provisional Pauli file type-checked only while its theorem proofs were
  placeholders; its projector constructor failed because
  `Matrix.posSemidef_iff` is not the available API and, more importantly, its
  diagonal effects were not source-faithful.  The file was deleted.

Measured command durations on this attempt: the first fresh Approximation
check reached the network fetch and failed after 60.8s; with private pinned
artifacts, `lake build MIPStarRE.QPBT.Basic.Field` completed in 8.0s and
`lake build MIPStarRE.QPBT.Basic.Approximation` completed in 30.4s.  No full
QPBT build or canonical cache publication was attempted.

## Required unblock

Integrate the pinned upstream foundation materialization/build boundary and a
reviewed Fourier/projector helper contract (or explicitly authorize the
skeleton-stage `sorry` policy for QPBT-037).  After that, rerun this lane from
the same immutable base plus the integrated dependency and implement only
`MIPStarRE/QPBT/Basic/Pauli.lean`.

## Metrics

- Session: `i037-pauli-a01` (orchestrator bootstrap)
- Candidate commit: none
- Changed tracked paths: none
- Token usage: `null` (endpoint does not expose per-session token accounting)
- Nested subagents: 0
- Network/GitHub writes: none
- Cache: private upstream/Mathlib artifacts reused; no canonical warm or seed
  was published from this blocked attempt.
