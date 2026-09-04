# QPBT-074 Game-layer source contract

This contract lowers the finite, repetition-one classical low-degree game core
out of the later analysis adapter and repairs the missing dependency from the
Magic Square construction to the finite-game semantics it uses. It is pinned
to arXiv:2001.04383v3.

## Authenticated sources

- `dependencies/classical-ldt.tex`, SHA-256
  `2314b141dbe31a12718244fabbf15a96f630351b7e22ded0fd21edf294039638`,
  split lines `88-258,262-273,306-377`, original lines
  `4250-4420,4424-4435,4468-4539`. The middle range is the named
  `def:line-point-dist` definition.
- `qpbt/qpbt-game-and-soundness.tex`, SHA-256
  `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea`,
  split lines `235-238,248-254,271-289`, original lines
  `5281-5284,5294-5300,5317-5335`.
  These ranges specialize the low-degree subroutine to `(q,m,d,1)`, freeze the
  scalar and polynomial answer formats, and give the two QPBT subroutine calls.
- `top-level/preliminaries.tex`, SHA-256
  `045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1`,
  split lines `306-383`, original lines `1203-1280`.
- `dependencies/finite-fields.tex`, SHA-256
  `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd`,
  split lines `250-263`, original lines `1566-1579`.

<!-- BEGIN F09A-SOURCE-MANIFEST -->
```json
[
  {
    "path": "references/2001.04383v3/sections/dependencies/classical-ldt.tex",
    "sha256": "2314b141dbe31a12718244fabbf15a96f630351b7e22ded0fd21edf294039638",
    "anchors": [
      {"path": "references/2001.04383v3/sections/dependencies/classical-ldt.tex", "label": "def:line", "generated_lines": [88, 258], "original_lines": [4250, 4420]},
      {"path": "references/2001.04383v3/sections/dependencies/classical-ldt.tex", "label": "def:line-point-dist", "generated_lines": [262, 273], "original_lines": [4424, 4435]},
      {"path": "references/2001.04383v3/sections/dependencies/classical-ldt.tex", "label": "fig:ld-decider", "generated_lines": [306, 377], "original_lines": [4468, 4539]}
    ]
  },
  {
    "path": "references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex",
    "sha256": "30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea",
    "anchors": [
      {"path": "references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex", "label": "", "generated_lines": [235, 238], "original_lines": [5281, 5284]},
      {"path": "references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex", "label": "", "generated_lines": [248, 254], "original_lines": [5294, 5300]},
      {"path": "references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex", "label": "", "generated_lines": [271, 289], "original_lines": [5317, 5335]}
    ]
  },
  {
    "path": "references/2001.04383v3/sections/top-level/preliminaries.tex",
    "sha256": "045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1",
    "anchors": [
      {"path": "references/2001.04383v3/sections/top-level/preliminaries.tex", "label": "def:canonical-complement", "generated_lines": [306, 383], "original_lines": [1203, 1280]}
    ]
  },
  {
    "path": "references/2001.04383v3/sections/dependencies/finite-fields.tex",
    "sha256": "379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd",
    "anchors": [
      {"path": "references/2001.04383v3/sections/dependencies/finite-fields.tex", "label": "", "generated_lines": [250, 263], "original_lines": [1566, 1579]}
    ]
  }
]
```
<!-- END F09A-SOURCE-MANIFEST -->

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

noncomputable local instance classicalLDTGaloisFieldFintype (k : Nat) :
    Fintype (GaloisField 2 k) :=
  Fintype.ofFinite (GaloisField 2 k)

noncomputable local instance classicalLDTGaloisFieldDecidableEq (k : Nat) :
    DecidableEq (GaloisField 2 k) :=
  Classical.decEq (GaloisField 2 k)

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
  deriving DecidableEq, Fintype

structure DiagonalLineQuestion (k m : Nat) where
  base : FieldPoint k m
  selector : GaloisField 2 k
  direction : FieldPoint k m
  deriving DecidableEq, Fintype

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
  deriving DecidableEq, Fintype

def IndividualLDTAnswer (k m d : Nat) : IndividualLDTQuestion k m → Type
  | .point _ => GaloisField 2 k
  | .axisLine _ => BoundedUnivariatePolynomial k d
  | .diagonalLine _ => BoundedUnivariatePolynomial k (m * d)

noncomputable def simultaneousIndividualLDTOne {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k)
    (qA qB : IndividualLDTQuestion k m)
    (aA : IndividualLDTAnswer k m d qA)
    (aB : IndividualLDTAnswer k m d qB) : Bool

theorem fieldElementIndex_apply {k : Nat} (D : FieldData k)
    (s : GaloisField 2 k) :
    (fieldElementIndex D s).val =
      ∑ i : Fin k, (D.coordinates s i).val * 2 ^ i.val

theorem fieldElementIndex_testBit {k : Nat} (D : FieldData k)
    (s : GaloisField 2 k) (i : Fin k) :
    Nat.testBit (fieldElementIndex D s).val i.val =
      decide (D.coordinates s i = 1)

theorem chi_val {k m : Nat} (D : FieldData k) (hm : m ∣ 2 ^ k)
    (s : GaloisField 2 k) :
    (chi D hm s).val = (fieldElementIndex D s).val / ((2 ^ k) / m)

theorem chi_fiber_card {k m : Nat} (D : FieldData k) (hm : m ∣ 2 ^ k)
    (i : Fin m) :
    Fintype.card {s : GaloisField 2 k // chi D hm s = i} = (2 ^ k) / m

theorem chi_map_uniform {k m : Nat} (D : FieldData k) (hm : m ∣ 2 ^ k)
    (i : Fin m) :
    ((PMF.uniformOfFintype (GaloisField 2 k)).map (chi D hm)) i =
      (m : ENNReal)⁻¹

theorem truncateDirection_apply_of_lt {k m : Nat} (i j : Fin m)
    (v : FieldPoint k m) (hji : j.val < i.val) :
    truncateDirection i v j = 0

theorem truncateDirection_apply_of_le {k m : Nat} (i j : Fin m)
    (v : FieldPoint k m) (hij : i.val ≤ j.val) :
    truncateDirection i v j = v j

theorem truncateDirection_idempotent {k m : Nat} (i : Fin m)
    (v : FieldPoint k m) :
    truncateDirection i (truncateDirection i v) = truncateDirection i v

theorem canonicalLineProjection_zero {k m : Nat} :
    canonicalLineProjection (0 : FieldPoint k m) = LinearMap.id

theorem canonicalLineProjection_apply_of_ne_zero {k m : Nat}
    (v u : FieldPoint k m) (p : Fin m) (hv : v ≠ 0)
    (hp : firstNonzeroCoordinate v = some p) :
    canonicalLineProjection v u = u - (u p / v p) • v

theorem canonicalLineProjection_direction_of_ne_zero {k m : Nat}
    (v : FieldPoint k m) (hv : v ≠ 0) :
    canonicalLineProjection v v = 0

theorem canonicalLineProjection_idempotent {k m : Nat}
    (v u : FieldPoint k m) :
    canonicalLineProjection v (canonicalLineProjection v u) =
      canonicalLineProjection v u

theorem canonicalLineProjection_sub_mem_span {k m : Nat}
    (v u : FieldPoint k m) :
    u - canonicalLineProjection v u ∈
      Submodule.span (GaloisField 2 k) ({v} : Set (FieldPoint k m))

theorem canonicalLineProjection_add_smul {k m : Nat}
    (v u : FieldPoint k m) (t : GaloisField 2 k) :
    canonicalLineProjection v (u + t • v) = canonicalLineProjection v u

theorem AffineLine.parameter?_sound {k m : Nat} (line : AffineLine k m)
    (point : FieldPoint k m) (t : GaloisField 2 k)
    (ht : line.parameter? point = some t) :
    line.pointAt t = point

theorem AffineLine.parameter?_isSome_iff {k m : Nat} (line : AffineLine k m)
    (point : FieldPoint k m) :
    (line.parameter? point).isSome = true ↔
      ∃ t : GaloisField 2 k, line.pointAt t = point

theorem AffineLine.parameter?_unique_of_ne_zero {k m : Nat}
    (line : AffineLine k m) (point : FieldPoint k m)
    (t s : GaloisField 2 k) (hline : line.direction ≠ 0)
    (ht : line.parameter? point = some t) (hs : line.pointAt s = point) :
    s = t

theorem AffineLine.parameter?_zero_direction {k m : Nat}
    (line : AffineLine k m) (point : FieldPoint k m)
    (hline : line.direction = 0) :
    line.parameter? point = if point = line.base then some 0 else none

theorem pointCLMap_apply {k m : Nat} (u : FieldPoint k m)
    (s : GaloisField 2 k) (v : FieldPoint k m) :
    pointCLMap k m (classicalLDTSeedEquiv k m (u, (s, v))) =
      classicalLDTSeedEquiv k m (u, (0, 0))

theorem axisLineCLMap_apply {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) (u : FieldPoint k m) (s : GaloisField 2 k)
    (v : FieldPoint k m) :
    axisLineCLMap D hm (classicalLDTSeedEquiv k m (u, (s, v))) =
      classicalLDTSeedEquiv k m
        (canonicalLineProjection (standardDirection (chi D hm s)) u, (s, 0))

theorem diagonalLineCLMap_apply {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) (u : FieldPoint k m) (s : GaloisField 2 k)
    (v : FieldPoint k m) :
    diagonalLineCLMap D hm (classicalLDTSeedEquiv k m (u, (s, v))) =
      let v' := truncateDirection (chi D hm s) v
      classicalLDTSeedEquiv k m (canonicalLineProjection v' u, (s, v'))

theorem axisLinePointDistribution_eq_map {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) :
    axisLinePointDistribution D hm =
      (PMF.uniformOfFintype (ClassicalLDTSeed k m)).map fun seed =>
        ({ base := canonicalLineProjection
              (standardDirection (chi D hm seed.2.1)) seed.1
           selector := seed.2.1 } : AxisLineQuestion k m,
         seed.1)

theorem diagonalLinePointDistribution_eq_map {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) :
    diagonalLinePointDistribution D hm =
      (PMF.uniformOfFintype (ClassicalLDTSeed k m)).map fun seed =>
        ({ base := canonicalLineProjection
              (truncateDirection (chi D hm seed.2.1) seed.2.2) seed.1
           selector := seed.2.1
           direction := truncateDirection (chi D hm seed.2.1) seed.2.2 } :
          DiagonalLineQuestion k m,
         seed.1)

theorem axisLinePointDistribution_incident {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) (pair : AxisLineQuestion k m × FieldPoint k m)
    (hpair : axisLinePointDistribution D hm pair ≠ 0) :
    ∃ t : GaloisField 2 k, (pair.1.line D hm).pointAt t = pair.2

theorem diagonalLinePointDistribution_incident {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) (pair : DiagonalLineQuestion k m × FieldPoint k m)
    (hpair : diagonalLinePointDistribution D hm pair ≠ 0) :
    ∃ t : GaloisField 2 k, (pair.1.line D hm).pointAt t = pair.2

theorem axisLine_selector_uniform {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) (i : Fin m) :
    ((axisLinePointDistribution D hm).map fun pair =>
      chi D hm pair.1.selector) i = (m : ENNReal)⁻¹

theorem diagonalLine_prefix_agrees {k m : Nat} (D : FieldData k)
    (hm : m ∣ 2 ^ k) (pair : DiagonalLineQuestion k m × FieldPoint k m)
    (hpair : diagonalLinePointDistribution D hm pair ≠ 0)
    (j : Fin m) (hj : j.val < (chi D hm pair.1.selector).val)
    (t : GaloisField 2 k) :
    ((pair.1.line D hm).pointAt t) j = pair.2 j

theorem BoundedUnivariatePolynomial.eval_zero {k degree : Nat}
    (f : BoundedUnivariatePolynomial k degree) :
    f.eval 0 = f ⟨0, Nat.succ_pos degree⟩

theorem BoundedUnivariatePolynomial.eval_congr {k degree : Nat}
    (f g : BoundedUnivariatePolynomial k degree) (t : GaloisField 2 k)
    (hfg : ∀ i, f i = g i) :
    f.eval t = g.eval t

theorem simultaneousIndividualLDTOne_point_point {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) (uA uB : FieldPoint k m)
    (aA aB : GaloisField 2 k) :
    simultaneousIndividualLDTOne D hm (.point uA) (.point uB) aA aB =
      decide (aA = aB)

theorem simultaneousIndividualLDTOne_axisLine_axisLine {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) (qA qB : AxisLineQuestion k m)
    (aA aB : BoundedUnivariatePolynomial k d) :
    simultaneousIndividualLDTOne D hm (.axisLine qA) (.axisLine qB) aA aB =
      decide (aA = aB)

theorem simultaneousIndividualLDTOne_diagonalLine_diagonalLine {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) (qA qB : DiagonalLineQuestion k m)
    (aA aB : BoundedUnivariatePolynomial k (m * d)) :
    simultaneousIndividualLDTOne D hm (.diagonalLine qA) (.diagonalLine qB) aA aB =
      decide (aA = aB)

theorem simultaneousIndividualLDTOne_axisLine_point {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) (q : AxisLineQuestion k m)
    (u : FieldPoint k m) (f : BoundedUnivariatePolynomial k d)
    (a : GaloisField 2 k) :
    simultaneousIndividualLDTOne D hm (.axisLine q) (.point u) f a =
      match (q.line D hm).parameter? u with
      | some t => decide (f.eval t = a)
      | none => false

theorem simultaneousIndividualLDTOne_point_axisLine {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) (u : FieldPoint k m)
    (q : AxisLineQuestion k m) (a : GaloisField 2 k)
    (f : BoundedUnivariatePolynomial k d) :
    simultaneousIndividualLDTOne D hm (.point u) (.axisLine q) a f =
      match (q.line D hm).parameter? u with
      | some t => decide (f.eval t = a)
      | none => false

theorem simultaneousIndividualLDTOne_diagonalLine_point {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) (q : DiagonalLineQuestion k m)
    (u : FieldPoint k m) (f : BoundedUnivariatePolynomial k (m * d))
    (a : GaloisField 2 k) :
    simultaneousIndividualLDTOne D hm (.diagonalLine q) (.point u) f a =
      match (q.line D hm).parameter? u with
      | some t => decide (f.eval t = a)
      | none => false

theorem simultaneousIndividualLDTOne_point_diagonalLine {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) (u : FieldPoint k m)
    (q : DiagonalLineQuestion k m) (a : GaloisField 2 k)
    (f : BoundedUnivariatePolynomial k (m * d)) :
    simultaneousIndividualLDTOne D hm (.point u) (.diagonalLine q) a f =
      match (q.line D hm).parameter? u with
      | some t => decide (f.eval t = a)
      | none => false

theorem simultaneousIndividualLDTOne_nonincident {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) :
    (∀ (q : AxisLineQuestion k m) (u : FieldPoint k m)
        (f : BoundedUnivariatePolynomial k d) (a : GaloisField 2 k),
      (q.line D hm).parameter? u = none →
        simultaneousIndividualLDTOne D hm (.axisLine q) (.point u) f a = false) ∧
    (∀ (u : FieldPoint k m) (q : AxisLineQuestion k m)
        (a : GaloisField 2 k) (f : BoundedUnivariatePolynomial k d),
      (q.line D hm).parameter? u = none →
        simultaneousIndividualLDTOne D hm (.point u) (.axisLine q) a f = false) ∧
    (∀ (q : DiagonalLineQuestion k m) (u : FieldPoint k m)
        (f : BoundedUnivariatePolynomial k (m * d)) (a : GaloisField 2 k),
      (q.line D hm).parameter? u = none →
        simultaneousIndividualLDTOne D hm
          (.diagonalLine q) (.point u) f a = false) ∧
    (∀ (u : FieldPoint k m) (q : DiagonalLineQuestion k m)
        (a : GaloisField 2 k) (f : BoundedUnivariatePolynomial k (m * d)),
      (q.line D hm).parameter? u = none →
        simultaneousIndividualLDTOne D hm
          (.point u) (.diagonalLine q) a f = false)

theorem simultaneousIndividualLDTOne_unlisted {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) :
    (∀ (qAxis : AxisLineQuestion k m) (qDiagonal : DiagonalLineQuestion k m)
        (fAxis : BoundedUnivariatePolynomial k d)
        (fDiagonal : BoundedUnivariatePolynomial k (m * d)),
      simultaneousIndividualLDTOne D hm
        (.axisLine qAxis) (.diagonalLine qDiagonal) fAxis fDiagonal = true) ∧
    (∀ (qDiagonal : DiagonalLineQuestion k m) (qAxis : AxisLineQuestion k m)
        (fDiagonal : BoundedUnivariatePolynomial k (m * d))
        (fAxis : BoundedUnivariatePolynomial k d),
      simultaneousIndividualLDTOne D hm
        (.diagonalLine qDiagonal) (.axisLine qAxis) fDiagonal fAxis = true)

theorem simultaneousIndividualLDTOne_zero_direction {k m d : Nat}
    (D : FieldData k) (hm : m ∣ 2 ^ k) (q : DiagonalLineQuestion k m)
    (u : FieldPoint k m) (f : BoundedUnivariatePolynomial k (m * d))
    (a : GaloisField 2 k) (hq : (q.line D hm).direction = 0) :
    (simultaneousIndividualLDTOne D hm
        (.diagonalLine q) (.point u) f a =
      if u = (q.line D hm).base then decide (f.eval 0 = a) else false) ∧
    (simultaneousIndividualLDTOne D hm
        (.point u) (.diagonalLine q) a f =
      if u = (q.line D hm).base then decide (f.eval 0 = a) else false)

end MIPStarRE.QPBT
```
<!-- END F09A-SIGNATURES -->

The declarations above are the complete callable form of the twelve law
families frozen by the authenticated QPBT-015 scout. In particular,
`fieldElementIndex_testBit` fixes the ordered-codec coherence promised by G23,
the dependent answer definition fixes the three repetition-one answer fibers,
and every decider branch has an exact reduction theorem. The
`BoundedUnivariatePolynomial.eval_zero` name deliberately states evaluation at
argument zero equals coefficient zero, which is the fact used by G22's
distinguished parameter; evaluation of the zero coefficient vector at an
arbitrary argument remains a private implementation lemma.

## Combined-import compatibility gate

The proof-complete F09A implementation and the later G02 implementation must
each run fresh import-only probes in both orders below. The manifest covers the
complete direct module surface of the future Verifier, including Pauli and
ClassicalLDT. This catches duplicate generated declaration names before the
modules are combined; it does not authorize an orphan instance in Verifier.

<!-- BEGIN F09A-COMBINED-IMPORT-PROBE -->
```json
{
  "pauli_first": [
    "MIPStarRE.QPBT.Basic.Pauli",
    "MIPStarRE.QPBT.Basic.Polynomial",
    "MIPStarRE.QPBT.Game.Types",
    "MIPStarRE.QPBT.Game.Parameters",
    "MIPStarRE.QPBT.Game.MagicSquare.Defs",
    "MIPStarRE.QPBT.Game.ClassicalLDT"
  ],
  "classical_ldt_first": [
    "MIPStarRE.QPBT.Game.ClassicalLDT",
    "MIPStarRE.QPBT.Game.MagicSquare.Defs",
    "MIPStarRE.QPBT.Game.Parameters",
    "MIPStarRE.QPBT.Game.Types",
    "MIPStarRE.QPBT.Basic.Polynomial",
    "MIPStarRE.QPBT.Basic.Pauli"
  ]
}
```
<!-- END F09A-COMBINED-IMPORT-PROBE -->

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
  the exact 64-name declaration/law list, two direct imports, Game-layer owned
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
