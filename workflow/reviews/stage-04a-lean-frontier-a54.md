# Stage-04A Lean frontier (i000-scout-a54-lean-frontier)

## Scope and immutable evidence

- Canonical base and inspected `HEAD`:
  `367ed6904d096e841a3849010395296a52be30c8` (tree
  `8479efe5ce52d9096a02514fa0c6c27b84238593`).
- The canonical worktree already had unrelated modifications to
  `workflow/events.jsonl` and `workflow/state/sessions.json`; they were not
  changed or used as immutable evidence.
- This was read-only except for this required `/tmp` report. No repository,
  workflow-state, metrics, source, cache, or build output was edited. No
  network, Lean, Lake, build, cache warm, or cache seed command was run.
- Elapsed wall time: approximately 30 minutes. Subagents: 0. Exposed token
  usage: `null` (`the collaboration backend does not expose token usage`; not
  estimated).

## Source contract and availability

The canonical root has no `references/2001.04383v3/sections/`, source member,
or `sections/READY`. Therefore a fresh issue worktree must materialize and
verify the source before implementation. A prior ignored worktree contains a
usable evidence copy at
`.workflow-runtime/worktrees/qpbt-002/references/2001.04383v3`: its
`sections/READY` is present; its primary source SHA-256 is
`38b3e662bb85bb902fcd056436fe9ecbe9e68d1990a074d0c0c12b39d5972ea9`, and
the three relevant dependency-fragment hashes exactly match the committed
split manifest:

| Fragment | SHA-256 |
| --- | --- |
| `finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |
| `measurements.tex` | `b3c03f8f4f1cbe979ee12e9db26227c9bb84c483c4743f1de988c4c38d80f946` |
| `strategies-distance.tex` | `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f` |

Exact paper contracts, in source order:

1. **F01:** `finite-fields.tex:62-83` (original 1378-1399) defines trace,
   trace-duality, self-duality, and normality. `:243-248` (original
   1559-1564) restricts admissible fields to `F_(2^k)` for odd `k`.
   `:283-307`, label `lem:efficient_basis` (original 1599-1623), claims a
   deterministic polynomial-time construction of a self-dual normal basis and
   multiplication tables for every odd positive `k`, citing Shoup, Lenstra,
   and Wang. This is constructed data, not a caller hypothesis.
2. **F03:** `measurements.tex:3-19` (original 1856-1872) defines a POVM,
   projectivity, an observable as a unitary matrix, and a binary observable as
   one squaring to identity. `:34-47`, label `def:bracket` (original
   1887-1900), defines family postprocessing by a fiber sum. A corresponding
   binary observable is explicitly `A_0 - A_1` for a two-outcome projective
   measurement at original lines 4808-4812 and 4830-4832; QPBT itself uses
   `F_2`-valued POVMs and the same order at original 5429-5436.
3. **F04:** `strategies-distance.tex:20-32`, label
   `def:tensor-product-strategy` (original 2903-2915), gives a unit vector in a
   finite-dimensional bipartite complex Hilbert space and two POVM families.
   `:213-224`, with label `def:state-distance` at `:214` (original
   3096-3107; label at 3097), is an
   asymptotic family relation with squared norm `O(delta(n))`.
   `:226-265` (original 3109-3148) makes the finite question set, probability
   distribution, state, outcome sum, and averaged squared norm explicit.
   `:267-282` (original 3150-3165) also compares both strategy states and both
   players' measurement families.

Material gaps that must not be normalized away:

- F01's algorithmic theorem does not give a Lean construction.
- The paper only calls `A_0-A_1` an observable in the projective binary case.
  Returning a raw `Op` from an arbitrary binary POVM would lose the paper's
  unitary condition; `Bool` would additionally require a documented
  `Bool ~= ZMod 2` boundary and a fixed sign order.
- F04's paper-level `O(delta)` is a relation between indexed families, while
  the planned Stage-4 API is a concrete real-valued finite error. The
  quantifier/indexing and constant-erasure bridge is not specified by the
  paper or current blueprint.

## Blueprint and issue frontier

`blueprint/metadata/nodes.json:34-49`, `:70-85`, and `:88-103` (generated
mirror `blueprint/src/generated/chapter-02-entries.tex:2-48`) fix:

- F01 module/names: `MIPStarRE.QPBT.Basic.Field`, `FieldData`,
  `fieldDataOfOddExponent`, `fieldTrace`, direct `GaloisField 2 k`, and no
  duplicate caller-supplied field instances.
- F03 module/names: `MIPStarRE.QPBT.Basic.Approximation`,
  `MeasurementFamily`, `ProjectiveMeasurementFamily`,
  `observableOfMeasurement`, using qualified
  `MIPStarRE.Quantum.Measurement` rather than the LDT hierarchy.
- F04 names in the same module: `PureStrategy`, `BipartiteIsometry`,
  `BipartiteIsometry.conjugate`, `stateDependentDistance`, and
  `familyApprox`, with finite Euclidean carriers and explicit adapters.

They do **not** freeze callable signatures/imports. In particular, F03 omits
the exact observable return certificate; F04 omits question/outcome domains,
distribution representation, tensor carrier, and finite-vs-asymptotic error
boundary. QPBT-023 correctly records these as blockers. At the immutable base:

| Issue | Status | Dependencies |
| --- | --- | --- |
| QPBT-003 | blocked | QPBT-002, QPBT-009 |
| QPBT-004 | planned | QPBT-003 |
| QPBT-023 | blocked | QPBT-003 |
| QPBT-013 | planned | QPBT-004, QPBT-023 |

Consequently **cache integration alone does not authorize a Lean writer**.
QPBT-023's contract amendment and immutable review remain a semantic gate even
after a READY cache exists.

## Current Lean and pinned Mathlib APIs

The canonical base tracks no `MIPStarRE/` files. They are intentionally
materialized from the authenticated upstream snapshot. The available ignored
copy in `.workflow-runtime/worktrees/qpbt-004/MIPStarRE` matches the committed
foundation hashes, including `Quantum/Measurement.lean` at
`c84a712e...`, `LDT/Basic/QuantumState.lean` at `0f1c3136...`, and
`LDT/Preliminaries/FiniteFields.lean` at `a5638019...`.

Useful exact declarations after materialization:

- `MIPStarRE.Quantum.Measurement` stores finite PSD effects summing to one
  (`Quantum/Measurement.lean:34-48`). `Measurement.postprocess` implements the
  exact fiber sum and preserves completeness (`:127-145`). This directly
  discharges the paper bracket mechanics.
- `MIPStarRE.Quantum.Op d = Matrix d d Complex`
  (`Quantum/FiniteMatrix/Basic.lean:74-80`).
- The existing LDT `Measurement`, `IdxMeas`, and projective structures are a
  separate hierarchy (`LDT/Basic/SubMeasurementCore.lean:18-76` and
  `SubMeasurementFamilies.lean:17-34`) and must not become the F03 API.
- LDT has a density-matrix `QuantumState` and coordinate-function `PureState`
  (`LDT/Basic/QuantumState.lean:25-32,65-68`), a finite-support real
  `Distribution` plus probability predicate (`LDT/Basic/Distribution.lean:22-37`),
  and raw-operator state-dependent-distance machinery. These are implementation
  references, not definitionally the F04 pure bipartite vector contract.
- `MIPStarRE.Quantum.FiniteHilbert` supplies finite linear-isometry and adjoint
  matrix facts, but no bundled QPBT bipartite conjugation adapter.

The pin is Mathlib commit `81a5d257c8e410db227a6665ed08f64fea08e997`.
It supplies direct `GaloisField 2 k` Field/CharP/Algebra/Finite/
FiniteDimensional instances (`FieldTheory/Finite/GaloisField.lean:65-74`),
`GaloisField.finrank` and `.card` for nonzero exponent (`:80-95,131-135`),
finite-field trace nondegeneracy and the power-sum formula
(`FieldTheory/Finite/Trace.lean:36-56`), a generic normal basis
(`FieldTheory/Galois/NormalBasis.lean:115-129`), and trace-dual bases
(`RingTheory/Trace/Basic.lean:547-604`). A negative search found no
self-dual-normal-basis theorem, characteristic-two odd-degree criterion, or
Wang/Lenstra/Shoup construction. Ordinary `normalBasis` plus `traceDual` does
not prove that one basis has both properties.

## Recommended next Lean issue

**Verdict: no existing Lean issue is ready immediately after cache integration.**
After QPBT-023 completes its full contract freeze and independent review,
split the current two-file QPBT-013 into the following smallest first writer
issue:

> **`feat(QPBT/Basic): add the finite POVM family boundary`**

- Sole owned path: `MIPStarRE/QPBT/Basic/Approximation.lean`.
- Exact import: `MIPStarRE.Quantum.Measurement` (and no `MIPStarRE.LDT`
  measurement import).
- Declarations: `MIPStarRE.QPBT.MeasurementFamily` as a question-indexed
  family of `MIPStarRE.Quantum.Measurement Outcome Coord`, and
  `MIPStarRE.QPBT.ProjectiveMeasurementFamily` as pointwise effect
  idempotence.
- Reuse `MIPStarRE.Quantum.Measurement.postprocess`; do not duplicate its
  fiber-sum implementation unless QPBT-023 deliberately freezes a QPBT-facing
  alias.
- Source anchors: `measurements.tex:3-17,21-47`, especially label
  `def:bracket`, original lines 1856-1870 and 1874-1900.
- Dependencies: completed QPBT-004 cache/materialization gate and completed,
  reviewed QPBT-023. It has no Lean-definition dependency on F01.
- Explicit exclusions: `observableOfMeasurement`, all F04 declarations, and
  all `Basic/Field.lean` declarations. These are not safe additions to the
  same first attempt because their contracts remain unresolved.

Statement-integrity preview:

| Declaration | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| `MeasurementFamily` | POVM family indexed by `x` with finite outcomes | `Question`, finite/decidable `Outcome`, finite/decidable `Coord`; qualified Quantum POVM | family of POVMs | function into the existing complete POVM structure | faithful boundary |
| `ProjectiveMeasurementFamily` | every effect is a projector | same family plus pointwise `M_a*M_a=M_a` | projective family | pointwise idempotence predicate | exact |

The question type need not be finite for the family alias itself; the source
only requires finiteness when distributions/averages are introduced. F04 must
add the appropriate finite question hypotheses rather than overconstrain F03.

**Allowed skeleton debt: none.** The current blueprint permits exactly one
Stage-4A `sorry`, `MIPStarRE.QPBT.pauliSoundness`, and QPBT-013 explicitly
forbids `sorry`, `axiom`, and proof-debt constants. A tracked
`fieldDataOfOddExponent` `sorry` would be source-faithful as a future complete
declaration skeleton, but it is not authorized in Stage 4A without first
changing and reviewing the stage/issue contract. Never replace it with a
caller-supplied basis or arbitrary existence hypothesis.

Follow-on order after this issue:

1. Freeze and implement `observableOfMeasurement` for `ZMod 2` outcomes with
   an explicit projectivity/unitarity certificate and sign order, anchored at
   original 4808-4812, 4830-4832, and 5429-5436.
2. Freeze the F04 finite-distribution and pure-state adapter, document its
   relation to the paper's asymptotic `O(delta)` notation, then implement it
   sequentially in the same owned file.
3. Keep F01 separate in `Basic/Field.lean`. Open a dedicated dependency/proof
   issue for `lem:efficient_basis`; do not make F02/F05 consumers depend on an
   unreviewed basis assumption.

## Validation commands for the recommended issue

Run only in its registered private worktree after the singleton cache is
seeded; the following were not run by this scout:

```text
python3 scripts/reference_source.py verify --reference-root references/2001.04383v3
python3 scripts/materialize_mipstarre.py --repo-root . verify
lake env lean MIPStarRE/QPBT/Basic/Approximation.lean
rg -n '\bsorry\b|\baxiom\b|\bconstant\b|MIPStarRE\.LDT\.(Measurement|IdxMeas|ProjMeas)' MIPStarRE/QPBT/Basic/Approximation.lean
lake build MIPStarRE.QPBT.Basic.Approximation
python3 blueprint/check.py --check --source-root references/2001.04383v3
python3 -m unittest discover -s blueprint/tests -p 'test_*.py'
lake build
```

The final full build is required before review/integration. Record cache hit,
seed result, lock wait, scoped/full build durations, commands, and results.

## Remaining wall-clock ranges with three safe worker lanes

These are planning ranges, not measured completion forecasts. They assume the
root coordinator plus three non-coordinator lanes, at most one writable owner
per issue, one serialized hot-main builder, immediate access to authenticated
archives, and no external-review/network queue. A practical allocation is one
critical-path writer, one fresh source/fidelity reviewer, and one independent
API/cache or disjoint-issue lane. Dependent proofs and same-file F03/F04 work
remain sequential.

| Remaining stage | Three-lane wall-clock range | Critical-path assumption |
| --- | ---: | --- |
| Stage 3 contract completion | 2-5 working days | Reconcile already integrated source/blueprint state; freeze F01/F03/F04 signatures and self-dual gap; one repair/review round. |
| Stage 4A minimal skeleton | 6-16 weeks | QPBT-004/cache closes promptly; the no-sorry F01 self-dual-normal-basis obligation is discharged from a pinned formal source or a tractable construction. |
| Stage 4B full statement skeleton | 4-10 weeks | All 48 blueprint declarations receive reviewed callable statements; tracked proof debt is allowed by this stage but no assumptions hide it. |
| Stage 4C proofs | 18-48 months | Pinned external boundaries are acceptable where declared, paper gaps receive formal repairs, and major LDT/linearity/extraction proofs do not force foundational library redevelopment. |
| Stage 5 final audit | 3-8 weeks | No theorem-statement drift or late source-gap blocker appears; full build and declaration synchronization remain stable. |

The dominant uncertainty is Stage 4C, followed by F01 in Stage 4A. If the
Shoup/Lenstra/Wang algorithmic complexity claim or every cited external
soundness/rigidity theorem must be formalized from first principles, Stage 4A
can exceed 16 weeks and Stage 4C can exceed 48 months. Three lanes improve
scouting, independent review, and disjoint leaf work, but do not divide the
formal proof critical path by three.
