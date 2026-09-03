# QPBT-074 Game-layer source contract

This contract lowers the finite, repetition-one classical low-degree game core
out of the later analysis adapter and repairs the missing dependency from the
Magic Square construction to the finite-game semantics it uses. It is pinned
to arXiv:2001.04383v3.

## Authenticated sources

- `dependencies/classical-ldt.tex`, SHA-256
  `2314b141dbe31a12718244fabbf15a96f630351b7e22ded0fd21edf294039638`,
  split lines `88-258,306-377`, original lines `4250-4420,4468-4539`.
- `top-level/preliminaries.tex`, SHA-256
  `045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1`,
  split lines `306-383`, original lines `1203-1280`.
- `dependencies/finite-fields.tex`, SHA-256
  `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd`,
  split lines `250-263`, original lines `1566-1579`.
- QPBT-015 canonical-line scout A41, SHA-256
  `a9d2db7f33f89f40faf397e94dadcb1c62b9d30fb4b4451683d93df25b43ed5e`;
  the material contract anchor is exactly lines `161-596`, covering both paper
  gaps, the declaration surface, all required laws, the integrity tables, and
  the implementation acceptance gates.
- QPBT-015 Magic Square API scout, SHA-256
  `95644ca5d97382780f1b0e17fb4412a54dc6cca3f00c0ebb2d0a5912204c1cdb`.
- Issue-DAG review A46, SHA-256
  `81c549622be1459c7fd41a743021a6ea8459e72988146ff8ce2dc888e42f15c0`.

## Dependency repair

`F08-MAGIC-GAME` directly depends on `F04A-GAME-SEMANTICS`: its game,
strategy, SPCC, and value declarations use that node's API. The new
`F09A-LDT-GAME-CORE` is a Game-layer definition required directly by both the
later `F09-LDT-GAME` Analysis adapter and `G02-GAME`. This keeps the verifier
from importing a downstream Analysis module.

## Frozen Lean contract

The future proof-complete issue owns only
`MIPStarRE/QPBT/Game/ClassicalLDT.lean`, directly imports
`MIPStarRE.QPBT.Basic.Polynomial` and `MIPStarRE.QPBT.Game.Types`, and permits no
`sorry`. Private helpers may vary; these public declaration signatures may not.

<!-- BEGIN F09A-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

abbrev ClassicalLDTSeed (k m : Nat) :=
  FieldPoint k m × (GaloisField 2 k × FieldPoint k m)

noncomputable def classicalLDTSeedEquiv (k m : Nat) :
    ClassicalLDTSeed k m ≃ₗ[GaloisField 2 k] FieldVector k (2 * m + 1)

def standardDirection {k m : Nat} (i : Fin m) : FieldPoint k m

def truncateDirection {k m : Nat} (i : Fin m) :
    FieldPoint k m →ₗ[GaloisField 2 k] FieldPoint k m

noncomputable def firstNonzeroCoordinate {k m : Nat}
    (v : FieldPoint k m) : Option (Fin m)

noncomputable def fieldElementIndex {k : Nat} (D : FieldData k) :
    GaloisField 2 k ≃ Fin (2 ^ k)

noncomputable def chi {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) : GaloisField 2 k → Fin m

noncomputable def canonicalLineProjection {k m : Nat}
    (v : FieldPoint k m) :
    FieldPoint k m →ₗ[GaloisField 2 k] FieldPoint k m

structure AffineLine (k m : Nat) where
  base : FieldPoint k m
  direction : FieldPoint k m
  deriving DecidableEq

def AffineLine.pointAt {k m : Nat} (line : AffineLine k m)
    (t : GaloisField 2 k) : FieldPoint k m

noncomputable def AffineLine.parameter? {k m : Nat}
    (line : AffineLine k m) (point : FieldPoint k m) :
    Option (GaloisField 2 k)

structure AxisLineQuestion (k m : Nat) where
  base : FieldPoint k m
  selector : GaloisField 2 k
  deriving DecidableEq

structure DiagonalLineQuestion (k m : Nat) where
  base : FieldPoint k m
  selector : GaloisField 2 k
  direction : FieldPoint k m
  deriving DecidableEq

noncomputable def AxisLineQuestion.line {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) (question : AxisLineQuestion k m) : AffineLine k m

noncomputable def DiagonalLineQuestion.line {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) (question : DiagonalLineQuestion k m) : AffineLine k m

noncomputable def pointCLMap (k m : Nat) :
    ConditionallyLinearMap k (2 * m + 1) 1

noncomputable def axisLineCLMap {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) : ConditionallyLinearMap k (2 * m + 1) 2

noncomputable def diagonalLineCLMap {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) : ConditionallyLinearMap k (2 * m + 1) 3

noncomputable def axisLinePointDistribution {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) : PMF (AxisLineQuestion k m × FieldPoint k m)

noncomputable def diagonalLinePointDistribution {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) : PMF (DiagonalLineQuestion k m × FieldPoint k m)

abbrev BoundedUnivariatePolynomial (k degree : Nat) :=
  Fin (degree + 1) → GaloisField 2 k

def BoundedUnivariatePolynomial.eval {k degree : Nat}
    (f : BoundedUnivariatePolynomial k degree)
    (t : GaloisField 2 k) : GaloisField 2 k

inductive IndividualLDTQuestion (k m : Nat)
  | point (u : FieldPoint k m)
  | axisLine (question : AxisLineQuestion k m)
  | diagonalLine (question : DiagonalLineQuestion k m)
  deriving DecidableEq

def IndividualLDTAnswer (k m d : Nat) : IndividualLDTQuestion k m → Type

noncomputable def simultaneousIndividualLDTOne {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k)
    (qA qB : IndividualLDTQuestion k m)
    (aA : IndividualLDTAnswer k m d qA)
    (aB : IndividualLDTAnswer k m d qB) : Bool

-- Required source-law names (their exact mathematical content is listed below):
-- fieldElementIndex_apply, chi_val, chi_fiber_card, chi_map_uniform,
-- truncateDirection_apply_of_lt, truncateDirection_apply_of_le,
-- truncateDirection_idempotent, canonicalLineProjection_zero,
-- canonicalLineProjection_apply_of_ne_zero,
-- canonicalLineProjection_direction_of_ne_zero,
-- canonicalLineProjection_idempotent,
-- canonicalLineProjection_sub_mem_span, canonicalLineProjection_add_smul,
-- AffineLine.parameter?_sound, AffineLine.parameter?_isSome_iff,
-- AffineLine.parameter?_unique_of_ne_zero,
-- AffineLine.parameter?_zero_direction, pointCLMap_apply,
-- axisLineCLMap_apply, diagonalLineCLMap_apply,
-- axisLinePointDistribution_eq_map, diagonalLinePointDistribution_eq_map,
-- axisLinePointDistribution_incident,
-- diagonalLinePointDistribution_incident, axisLine_selector_uniform,
-- diagonalLine_prefix_agrees, BoundedUnivariatePolynomial.eval_zero,
-- BoundedUnivariatePolynomial.eval_congr,
-- simultaneousIndividualLDTOne_point_point,
-- simultaneousIndividualLDTOne_axisLine_axisLine,
-- simultaneousIndividualLDTOne_diagonalLine_diagonalLine,
-- simultaneousIndividualLDTOne_axisLine_point,
-- simultaneousIndividualLDTOne_point_axisLine,
-- simultaneousIndividualLDTOne_diagonalLine_point,
-- simultaneousIndividualLDTOne_point_diagonalLine,
-- simultaneousIndividualLDTOne_nonincident,
-- simultaneousIndividualLDTOne_unlisted,
-- simultaneousIndividualLDTOne_zero_direction

end MIPStarRE.QPBT
```
<!-- END F09A-SIGNATURES -->

The implementation must additionally prove the twelve law families frozen by
the authenticated QPBT-015 scout: little-endian index and `chi` bijection/fiber
laws; truncation formulas and idempotence; exact nonzero RREF projection and
the G22 zero branch; parameter soundness, completeness, uniqueness, and zero
branch; exact CL tuple formulas and distribution pushforwards; polynomial
evaluation laws; and every same-type, oriented line/point, nonincident,
unlisted, and zero-direction decider reduction.

## Statement integrity

| Surface | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
|---|---|---|---|---|---|
| Field index and `chi` | `q` is a field size, `m` divides `q`, and elements have a fixed binary representation. | `D : FieldData k`, `hm : m ∣ 2^k`, with positivity of `m` derived; coordinate zero is least significant. | The unique one-based block selector is uniform. | The zero-based quotient selector has fibers of size `2^k/m`. | Faithful boundary (G23). |
| Canonical line | The projector is indexed by kernel basis `{v}`, while sampled directions include zero. | The concrete field and vector dimension only. | A canonical representative is constant on, and belongs to, its affine line. | The least-pivot RREF formula for nonzero `v`; identity and distinguished parameter zero for `v=0`. | Exact off zero; documented G22 repair at zero. |
| Truncation | `i=chi(s)` is one-based and `pi_(i-1)` zeros the first `i-1` coordinates. | Zero-based `i : Fin m`. | Retain coordinates `i,...,m`. | Zero `j.val < i.val`, retain all later coordinates. | Exact. |
| CL maps | The three paper registers, canonical lines, `chi`, and truncation. | A fixed `FieldVector` equivalence, `FieldData`, and divisibility. | Exact level-1/2/3 maps and line-point distributions. | The same maps, levels, and exact PMF pushforwards, subject only to G22/G23. | Faithful boundary. |
| Bounded answers and decider | `(q,m,d,ldc)` with `ldc=1`, valid coefficient encodings, and line/point questions. | Typed scalar/coefficient-vector answers; G02 rejects malformed outer encodings. | Same-type consistency, both orientations of line/point evaluation, accept otherwise. | The exhaustive dependent Bool case split, including checked incidence and the G22 parameter. | Faithful boundary. |

## Paper gaps

G22 totalizes only the source's undefined zero-direction branch. It neither
conditions away a positive-probability sample nor adds a nonzero-direction
premise. G23 fixes a transparent little-endian coordinate boundary and never
uses an opaque `Fintype.equivFin` choice. Both gaps are inherited by F09 and
G02; neither is presented as a repaired theorem of the paper.

## A46 finding dispositions

- `F046-A46-001`: resolved by authenticating A41 lines `161-596` and freezing
  the exact 63-name declaration/law list, two direct imports, Game-layer owned
  path, source ranges, and zero-debt requirement in machine-checked metadata.
- `F046-A46-002`: the typed F09A decider checks same-type equality, both
  line/point orientations, incidence rejection, accept-default, and the G22
  zero branch. It has no malformed typed value. G02 separately rejects a failed
  outer codec decode before calling F09A.
- `F046-A46-003`: A41 and the F09A contract supersede A43 for
  `AxisLineQuestion`, `DiagonalLineQuestion`, `BoundedUnivariatePolynomial`,
  and its evaluator. The later G02 verifier imports and reuses those definitions
  and owns only its QPBT-specific tags, payloads, codecs, support, and checks.

G02 remains `not-started`, which records implementation progress, but its
fidelity is `faithful-boundary` because it inherits G22 and G23. F09A itself is
`paper-gap` because it owns the explicit source repair.

## Validation record

Pending issue-head validation and independent review.
