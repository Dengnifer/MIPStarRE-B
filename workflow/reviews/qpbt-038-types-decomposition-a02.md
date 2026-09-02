# QPBT-038 Types implementation decomposition (A02)

Session: `i038-scout-a02-types-decomposition`
External identity: `/root/i038_scout_a02_types_decomposition`
Mode: read-only implementation-preparation scout
Canonical checkpoint: `cc9194ad4a38aaf4971db871bdae34f10b447230`

## Result

QPBT-038 remains one sequential owner of
`MIPStarRE/QPBT/Game/Types.lean`, but its reviewed surface is 81 synchronized
names: 14 for F06, 56 for F06A, and 11 for F07. The implementation order is
F06 mathematical conditionally-linear maps, F06A executable samplers, then F07
typed games. The exact import union is:

```lean
import Mathlib.Computability.TuringMachine.Computable
import Mathlib.Data.Nat.Log
import Mathlib.Probability.Distributions.Uniform
import MIPStarRE.QPBT.Basic.Field
```

The rejected `9070aa4d7db267fd890c9b487defa2940e9810a` candidate is negative
evidence only. Its zero maps and pure-zero distributions must not be reused.

## Implementation order

1. F06: define the vector operations, recursive conditionally-linear
   certificate and map, level raising, direct sum, mathematical downsize,
   `CLSampler`, its shared-uniform-seed law, and exact direct-sum/downsize PMF
   theorems.
2. F06A: implement the complete immutable signature block in
   `workflow/reviews/qpbt-054-f06a-repair-a04.md`, whose signature SHA-256 is
   `cfe433e36d0670c344b29ab5107557842e7d4fc8358fba2713b8ff2ee107a3a1`.
   This includes the canonical field codec, dependent query carriers,
   six-tape encoding, genuine `FinTM2` executions, intrinsic exponent program,
   exact runtime maximum, and executable downsize results.
3. F07: implement `TypeGraph`, its edge distribution and point law, typed
   questions and samplers, the three distribution/downsize theorems, and the
   dependent `TypedDecider` acceptance predicate.

Source anchors are `conditionally-linear.tex:35-57,122-178,315-383,394-550,
565-712`, `finite-fields.tex:234-307,350-411`,
`top-level/preliminaries.tex:1-143`, and `types.tex:57-195`.

## Critical risks

1. `ExecutableCLSampler.downsize` must construct an actual composed `FinTM2`,
   exact executions, and a global runtime bound. The pinned Mathlib declaration
   `TM2ComputableInPolyTime.comp` has body `proof_wanted` at
   `Mathlib/Computability/TuringMachine/Computable.lean:276-288`; it is not a
   usable composition theorem. Compiler feasibility is therefore the first
   implementation gate.
2. Direct sum must recursively preserve both arbitrary input maps after level
   equalization, never replace either with zero.
3. Mathematical downsize must conjugate every recursive linear component,
   expand coordinate registers blockwise, and transport scalars to
   `GaloisField 2 1`.
4. Total constructors still need honest `n = 0` and low-level branches even
   though paper-labelled correctness results assume positive indices and
   `1 <= level`.
5. PMF proofs require uniform-law transport through the relevant sum/product
   and coordinate equivalences; F07 should be comparatively small afterward.

## Parallel proof lanes

Under the one writable Types owner, run three non-writing lanes:

- direct-sum certificate and exact product PMF law from
  `conditionally-linear.tex:122-138,315-383`;
- downsize register/scalar/certificate conjugation and uniform pushforward from
  `conditionally-linear.tex:394-550` and `finite-fields.tex:234-307`;
- concrete Turing compiler and step inequality from
  `conditionally-linear.tex:565-712` and `preliminaries.tex:37-143`.

Each lane should validate only a private `/tmp` probe with `lake env lean`.
Dispatch the Turing lane first. Failure to find a concrete compiler is an
implementation blocker, not authority to add an obligation or weaken F06A.

## Accounting

- Observed agent end: `2026-09-02T20:26:52Z`.
- Read-only shell invocations: 72 across 16 batched tool calls.
- Repository/file writes, Lean/Lake/build/cache operations, network/GitHub/
  credential operations, and nested agents: 0.
- Token usage: `null`; the collaboration backend does not expose per-agent
  usage.
- The backend launch preceded canonical registration. Governed timing begins
  at the recorded issued-to-running transition; the session record preserves
  that qualification.
