import Mathlib.Analysis.Asymptotics.Defs
import Mathlib.Analysis.SpecialFunctions.Pow.Asymptotics
import Mathlib.Probability.ProbabilityMassFunction.Constructions
import MIPStarRE.LDT.Preliminaries.ComparisonCore
import MIPStarRE.LDT.Preliminaries.Triangles.SimEq
import MIPStarRE.Quantum.Measurement
import MIPStarRE.Quantum.FiniteHilbert

/-!
# Finite measurement families

This module records the finite POVM-family boundary used by the QPBT
formalization.  The family index is intentionally unrestricted; finiteness is
required only by the outcome and coordinate types of each measurement.

The postprocessing declarations are the QPBT-facing names for the qualified
`MIPStarRE.Quantum.Measurement` API.  In particular, the fiber sum is not
duplicated here.
-/

open scoped BigOperators MatrixOrder Matrix ComplexOrder

namespace MIPStarRE.QPBT

universe uQuestion uOutcome uOutcome' uCoord

/-- A question-indexed family of finite POVMs on a coordinate space. -/
abbrev MeasurementFamily
    (Question : Type uQuestion) (Outcome : Type uOutcome)
    (Coord : Type uCoord)
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord] :=
  Question → MIPStarRE.Quantum.Measurement Outcome Coord

/-- Every effect in the family is idempotent. -/
def ProjectiveMeasurementFamily
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (M : MeasurementFamily Question Outcome Coord) : Prop :=
  ∀ x a, (M x).effect a * (M x).effect a = (M x).effect a

namespace MeasurementFamily

/-- Relabel each measurement outcome by summing along the fibers of `f`. -/
noncomputable def postprocess
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'} {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Coord] [DecidableEq Coord]
    (M : MeasurementFamily Question Outcome Coord)
    (f : Outcome → Outcome') : MeasurementFamily Question Outcome' Coord :=
  fun x => MIPStarRE.Quantum.Measurement.postprocess (M x) f

@[simp] theorem postprocess_effect
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'} {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Coord] [DecidableEq Coord]
    (M : MeasurementFamily Question Outcome Coord)
    (f : Outcome → Outcome') (x : Question) (b : Outcome') :
    (postprocess M f x).effect b =
      ∑ a ∈ Finset.univ.filter (fun a => f a = b), (M x).effect a := by
  rfl

theorem postprocess_effect_eq_zero_of_not_mem_range
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'} {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Coord] [DecidableEq Coord]
    (M : MeasurementFamily Question Outcome Coord)
    (f : Outcome → Outcome') (x : Question) (b : Outcome')
    (hb : b ∉ Set.range f) :
    (postprocess M f x).effect b = 0 := by
  rw [postprocess_effect]
  have hfilter : Finset.univ.filter (fun a => f a = b) = ∅ := by
    apply Finset.not_nonempty_iff_eq_empty.mp
    intro hnonempty
    rcases hnonempty with ⟨a, ha⟩
    exact hb ⟨a, (Finset.mem_filter.mp ha).2⟩
  rw [hfilter, Finset.sum_empty]

end MeasurementFamily

end MIPStarRE.QPBT

/-!
# Strategy and state-dependent approximation

The declarations below formalize the finite expressions, indexed asymptotic
relations, consistency relation, and distance laws used in the paper's
Definitions 3.2, 4.7, and 4.8, Facts 4.26 and 4.28, and Proposition 4.29. Finite values and
exact `NNReal` bounds remain separate from the paper-facing `atTop` Big-O
relations.

Blueprint nodes: `F04-DISTANCE`, `F04-ASYMPTOTIC`, `F04-CONSISTENCY`, and
`F04-DISTANCE-LAWS`.
-/

namespace MIPStarRE.QPBT

universe uQuestion uOutcome uOutcome' uCoord
universe uQuestionA uQuestionB uOutcomeA uOutcomeB uAlice uBob
universe uSource uTarget uAuxAlice uAuxBob
universe uAliceJunk uAliceIdeal uBobJunk uBobIdeal

private noncomputable def pmfDistribution
    {Question : Type uQuestion} [Fintype Question]
    (mu : PMF Question) : MIPStarRE.LDT.Distribution Question := by
  classical
  exact {
    support := Finset.univ
    weight := fun x => (mu x).toReal
    nonnegative := fun x => ENNReal.toReal_nonneg
    outsideSupport := fun x hx => (hx (Finset.mem_univ x)).elim
  }

private theorem pmfDistribution_isProbability
    {Question : Type uQuestion} [Fintype Question]
    (mu : PMF Question) :
    (pmfDistribution mu).IsProbability := by
  classical
  unfold MIPStarRE.LDT.Distribution.IsProbability
    MIPStarRE.LDT.Distribution.totalWeight pmfDistribution
  change (∑ x : Question, (mu x).toReal) = 1
  calc
    (∑ x : Question, (mu x).toReal) =
        (∑ x : Question, mu x).toReal := by
      rw [ENNReal.toReal_sum]
      exact fun x _ => mu.apply_ne_top x
    _ = (∑' x : Question, mu x).toReal := by rw [tsum_fintype]
    _ = 1 := by rw [mu.tsum_coe]; norm_num

private noncomputable def measurementToLDT
    {Outcome : Type uOutcome} {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (M : MIPStarRE.Quantum.Measurement Outcome Coord) :
    MIPStarRE.LDT.Measurement Outcome Coord where
  outcome := M.effect
  total := 1
  outcome_pos := M.pos
  sum_eq_total := M.sum_eq_one
  total_le_one := le_rfl
  total_eq_one := rfl

private noncomputable def measurementFamilyToLDT
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (M : MeasurementFamily Question Outcome Coord) :
    MIPStarRE.LDT.IdxMeas Question Outcome Coord :=
  fun x => measurementToLDT (M x)

private theorem measurementToLDT_postprocess
    {Outcome : Type uOutcome} {Outcome' : Type uOutcome'}
    {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Coord] [DecidableEq Coord]
    (M : MIPStarRE.Quantum.Measurement Outcome Coord)
    (f : Outcome → Outcome') :
    (measurementToLDT (M.postprocess f)).toSubMeas =
      MIPStarRE.LDT.postprocess (measurementToLDT M).toSubMeas f := by
  apply MIPStarRE.LDT.SubMeas.ext
  · intro b
    change (M.postprocess f).effect b =
      (MIPStarRE.LDT.postprocess (measurementToLDT M).toSubMeas f).outcome b
    rw [MIPStarRE.Quantum.Measurement.postprocess_effect,
      MIPStarRE.LDT.SubMeas.postprocess_outcome]
    change (∑ a with f a = b, M.effect a) =
      ∑ a with f a = b, M.effect a
    rfl
  · rfl

private noncomputable def vectorQuantumState
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex Coord) :
    MIPStarRE.LDT.QuantumState Coord where
  density := MIPStarRE.LDT.pureDensity psi
  density_psd := by
    refine Matrix.nonneg_iff_posSemidef.mpr ?_
    exact (Matrix.posSemidef_vecMulVec_self_star psi).smul
      (by positivity : 0 ≤ (Fintype.card Coord : Complex))

private theorem vectorQuantumState_ev_eq_inner
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex Coord)
    (X : MIPStarRE.Quantum.Op Coord) :
    MIPStarRE.LDT.ev (vectorQuantumState psi) X =
      Complex.re (inner Complex psi (Matrix.toEuclideanLin X psi)) := by
  classical
  rcases isEmpty_or_nonempty Coord with hCoord | hCoord
  · letI := hCoord
    have hpsi : psi = 0 := Subsingleton.elim _ _
    subst psi
    simp [MIPStarRE.LDT.ev, vectorQuantumState, MIPStarRE.LDT.pureDensity,
      MIPStarRE.Quantum.normalizedTrace]
  · letI := hCoord
    have hcard : (Fintype.card Coord : Complex) ≠ 0 :=
      Nat.cast_ne_zero.mpr Fintype.card_ne_zero
    have htrace :
        MIPStarRE.Quantum.normalizedTrace
            ((vectorQuantumState psi).density * X) =
          star psi ⬝ᵥ (X *ᵥ psi) := by
      calc
        MIPStarRE.Quantum.normalizedTrace
            ((vectorQuantumState psi).density * X) =
            MIPStarRE.Quantum.normalizedTrace
              (X * (vectorQuantumState psi).density) := by
          rw [MIPStarRE.Quantum.normalizedTrace_mul_comm]
        _ = MIPStarRE.Quantum.normalizedTrace
            ((Fintype.card Coord : Complex) •
              (X * Matrix.vecMulVec psi (star psi))) := by
          simp [vectorQuantumState, MIPStarRE.LDT.pureDensity]
        _ = (Fintype.card Coord : Complex) *
            MIPStarRE.Quantum.normalizedTrace
              (X * Matrix.vecMulVec psi (star psi)) := by
          rw [MIPStarRE.Quantum.normalizedTrace_smul]
        _ = (Fintype.card Coord : Complex) *
            ((X * Matrix.vecMulVec psi (star psi)).trace /
              (Fintype.card Coord : Complex)) := by
          simp [MIPStarRE.Quantum.normalizedTrace]
        _ = (Fintype.card Coord : Complex) *
            ((Matrix.vecMulVec (X *ᵥ psi) (star psi)).trace /
              (Fintype.card Coord : Complex)) := by
          rw [Matrix.mul_vecMulVec]
        _ = (Fintype.card Coord : Complex) *
            (((X *ᵥ psi) ⬝ᵥ star psi) /
              (Fintype.card Coord : Complex)) := by
          rw [Matrix.trace_vecMulVec]
        _ = (X *ᵥ psi) ⬝ᵥ star psi := by
          field_simp [hcard]
        _ = star psi ⬝ᵥ (X *ᵥ psi) := by
          rw [dotProduct_comm]
    unfold MIPStarRE.LDT.ev
    rw [htrace]
    congr 1
    simp [EuclideanSpace.inner_eq_star_dotProduct,
      Matrix.ofLp_toLpLin, dotProduct_comm]

private theorem euclideanSpace_nonempty_of_norm_eq_one
    {Coord : Type uCoord} [Fintype Coord]
    (psi : EuclideanSpace Complex Coord) (hpsi : ‖psi‖ = 1) :
    Nonempty Coord := by
  classical
  by_contra hCoord
  rw [not_nonempty_iff] at hCoord
  letI : IsEmpty Coord := hCoord
  have hzero : psi = 0 := Subsingleton.elim _ _
  rw [hzero, norm_zero] at hpsi
  exact zero_ne_one hpsi

private theorem vectorQuantumState_isNormalized
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord] [Nonempty Coord]
    (psi : EuclideanSpace Complex Coord) (hpsi : ‖psi‖ = 1) :
    (vectorQuantumState psi).IsNormalized := by
  let psiPure : MIPStarRE.LDT.PureState Coord :=
    { vector := psi
      unit := by
        rw [dotProduct_comm]
        rw [← EuclideanSpace.inner_eq_star_dotProduct]
        exact inner_self_eq_one_of_norm_eq_one hpsi }
  change MIPStarRE.Quantum.normalizedTrace
      (MIPStarRE.LDT.pureDensity psi) = 1
  simpa [psiPure, MIPStarRE.LDT.PureState.density] using
    MIPStarRE.LDT.PureState.normalizedTrace_density psiPure

/-! ## Finite strategies, isometries, and distance values -/

/-- A finite-dimensional bipartite pure strategy with a normalized state.

Paper source: Definition `def:tensor-product-strategy`.
-/
structure PureStrategy
    (QuestionA : Type uQuestionA) (QuestionB : Type uQuestionB)
    (OutcomeA : Type uOutcomeA) (OutcomeB : Type uOutcomeB)
    (Alice : Type uAlice) (Bob : Type uBob)
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob] where
  state : EuclideanSpace Complex (Alice × Bob)
  normalized : ‖state‖ = 1
  alice : MeasurementFamily QuestionA OutcomeA Alice
  bob : MeasurementFamily QuestionB OutcomeB Bob

/-- The rectangular matrix of a finite-dimensional linear isometry. -/
noncomputable def isometryMatrix
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source] [Fintype Target]
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target) : Matrix Target Source Complex :=
  Matrix.toEuclideanLin.symm V.toLinearMap

/-- The adjoint of the rectangular matrix of a linear isometry. -/
noncomputable def isometryAdjointMatrix
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source] [Fintype Target]
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target) : Matrix Source Target Complex :=
  (isometryMatrix V)ᴴ

/-- Rectangular isometry conjugation, with formula `V * A * Vᴴ`. -/
noncomputable def conjugateByIsometry
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source] [Fintype Target]
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target)
    (A : MIPStarRE.Quantum.Op Source) : MIPStarRE.Quantum.Op Target :=
  isometryMatrix V * A * isometryAdjointMatrix V

/-- The matrix of an isometry satisfies `Vᴴ * V = 1`. -/
theorem isometryMatrix_adjoint_mul_self
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source] [Fintype Target]
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target) :
    (isometryMatrix V)ᴴ * isometryMatrix V = 1 := by
  apply Matrix.toEuclideanLin.injective
  calc
    Matrix.toEuclideanLin ((isometryMatrix V)ᴴ * isometryMatrix V) =
        (Matrix.toEuclideanLin (isometryMatrix V)).adjoint.comp
          (Matrix.toEuclideanLin (isometryMatrix V)) := by
      exact Matrix.toEuclideanLin_conjTranspose_mul_self _
    _ = V.toLinearMap.adjoint.comp V.toLinearMap := by
      rw [isometryMatrix, Matrix.toEuclideanLin.apply_symm_apply]
    _ = 1 := by
      exact V.adjoint_comp_self'
    _ = Matrix.toEuclideanLin (1 : Matrix Source Source Complex) := by
      rw [Matrix.toEuclideanLin, Matrix.toLpLin_one]
      rfl

/-- Lift an Alice-side operator to the bipartite coordinate space. -/
def aliceLocal
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (A : MIPStarRE.Quantum.Op Alice) :
    MIPStarRE.Quantum.Op (Alice × Bob) :=
  Matrix.kronecker A 1

/-- Lift a Bob-side operator to the bipartite coordinate space. -/
def bobLocal
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (B : MIPStarRE.Quantum.Op Bob) :
    MIPStarRE.Quantum.Op (Alice × Bob) :=
  Matrix.kronecker 1 B

/-- A pair of independently typed local isometries. -/
structure BipartiteIsometry
    (Alice : Type uAlice) (Bob : Type uBob)
    (AuxAlice : Type uAuxAlice) (AuxBob : Type uAuxBob)
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob] where
  alice : EuclideanSpace Complex Alice →ₗᵢ[Complex]
    EuclideanSpace Complex AuxAlice
  bob : EuclideanSpace Complex Bob →ₗᵢ[Complex]
    EuclideanSpace Complex AuxBob

/-- Conjugate an Alice-side operator by the Alice isometry only. -/
noncomputable def BipartiteIsometry.conjugateAlice
    {Alice : Type uAlice} {Bob : Type uBob}
    {AuxAlice : Type uAuxAlice} {AuxBob : Type uAuxBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob]
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob)
    (A : MIPStarRE.Quantum.Op Alice) : MIPStarRE.Quantum.Op AuxAlice :=
  conjugateByIsometry V.alice A

/-- Conjugate a Bob-side operator by the Bob isometry only. -/
noncomputable def BipartiteIsometry.conjugateBob
    {Alice : Type uAlice} {Bob : Type uBob}
    {AuxAlice : Type uAuxAlice} {AuxBob : Type uAuxBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob]
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob)
    (B : MIPStarRE.Quantum.Op Bob) : MIPStarRE.Quantum.Op AuxBob :=
  conjugateByIsometry V.bob B

/-- The Kronecker matrix of the two local isometries. -/
noncomputable def BipartiteIsometry.tensorMatrix
    {Alice : Type uAlice} {Bob : Type uBob}
    {AuxAlice : Type uAuxAlice} {AuxBob : Type uAuxBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob]
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob) :
    Matrix (AuxAlice × AuxBob) (Alice × Bob) Complex :=
  Matrix.kronecker (isometryMatrix V.alice) (isometryMatrix V.bob)

/-- The Kronecker matrix of local isometries also satisfies `Vᴴ * V = 1`. -/
theorem BipartiteIsometry.tensorMatrix_adjoint_mul_self
    {Alice : Type uAlice} {Bob : Type uBob}
    {AuxAlice : Type uAuxAlice} {AuxBob : Type uAuxBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob]
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob) :
    V.tensorMatrixᴴ * V.tensorMatrix = 1 := by
  simp only [BipartiteIsometry.tensorMatrix, Matrix.kronecker]
  rw [Matrix.conjTranspose_kronecker]
  rw [← Matrix.mul_kronecker_mul, isometryMatrix_adjoint_mul_self,
    isometryMatrix_adjoint_mul_self, Matrix.one_kronecker_one]

/-- The certified tensor product of the two local isometries. -/
noncomputable def BipartiteIsometry.tensorIsometry
    {Alice : Type uAlice} {Bob : Type uBob}
    {AuxAlice : Type uAuxAlice} {AuxBob : Type uAuxBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob]
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob) :
    EuclideanSpace Complex (Alice × Bob) →ₗᵢ[Complex]
      EuclideanSpace Complex (AuxAlice × AuxBob) := by
  let L := Matrix.toEuclideanLin V.tensorMatrix
  apply L.isometryOfInner
  intro x y
  rw [← L.adjoint_inner_right x (L y), ← LinearMap.comp_apply]
  have hAdj : L.adjoint.comp L = 1 := by
    rw [← Matrix.toEuclideanLin_conjTranspose_mul_self]
    rw [V.tensorMatrix_adjoint_mul_self]
    rw [Matrix.toEuclideanLin, Matrix.toLpLin_one]
    rfl
  rw [hAdj]
  rfl

/-- Apply the certified tensor isometry to a bipartite state. -/
noncomputable def BipartiteIsometry.mapState
    {Alice : Type uAlice} {Bob : Type uBob}
    {AuxAlice : Type uAuxAlice} {AuxBob : Type uAuxBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob]
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob)
    (psi : EuclideanSpace Complex (Alice × Bob)) :
    EuclideanSpace Complex (AuxAlice × AuxBob) :=
  V.tensorIsometry psi

/-- Regroup the local junk/ideal products into junk and ideal bipartite factors. -/
def localProductToJunkIdeal
    (AliceJunk : Type uAliceJunk) (AliceIdeal : Type uAliceIdeal)
    (BobJunk : Type uBobJunk) (BobIdeal : Type uBobIdeal) :
    ((AliceJunk × AliceIdeal) × (BobJunk × BobIdeal)) ≃
      ((AliceJunk × BobJunk) × (AliceIdeal × BobIdeal)) where
  toFun x := ((x.1.1, x.2.1), (x.1.2, x.2.2))
  invFun x := ((x.1.1, x.2.1), (x.1.2, x.2.2))
  left_inv x := by
    rcases x with ⟨⟨a, i⟩, b, j⟩
    rfl
  right_inv x := by
    rcases x with ⟨⟨a, b⟩, i, j⟩
    rfl

/-- Reindex Euclidean coordinates along an equivalence. -/
noncomputable def reindexState
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [Fintype Target] (e : Source ≃ Target) :
    EuclideanSpace Complex Source ≃ₗᵢ[Complex]
      EuclideanSpace Complex Target :=
  LinearIsometryEquiv.piLpCongrLeft 2 Complex Complex e

/-- Reindex square operators along an equivalence. -/
def reindexOperator
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source]
    [Fintype Target] [DecidableEq Target] (e : Source ≃ Target) :
    MIPStarRE.Quantum.Op Source ≃ₐ[Complex]
      MIPStarRE.Quantum.Op Target :=
  Matrix.reindexAlgEquiv Complex Complex e

/-- Apply a square operator to a Euclidean state. -/
noncomputable def operatorAction
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (A : MIPStarRE.Quantum.Op Coord)
    (psi : EuclideanSpace Complex Coord) :
    EuclideanSpace Complex Coord :=
  Matrix.toEuclideanLin A psi

/-- The finite squared state-dependent distance between two operators. -/
noncomputable def stateDependentDistance
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex Coord)
    (A B : MIPStarRE.Quantum.Op Coord) : Real :=
  ‖operatorAction (A - B) psi‖ ^ 2

/-- State-dependent distance is nonnegative. -/
theorem stateDependentDistance_nonneg
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex Coord)
    (A B : MIPStarRE.Quantum.Op Coord) :
    0 ≤ stateDependentDistance psi A B := by
  exact sq_nonneg _

/-- The PMF-averaged state-dependent distance between raw operator families. -/
noncomputable def operatorFamilyDistanceValue
    {Question : Type uQuestion} {Coord : Type uCoord}
    [Fintype Question] [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : Question → MIPStarRE.Quantum.Op Coord) : Real :=
  ∑ x, (mu x).toReal * stateDependentDistance psi (A x) (B x)

/-- The PMF- and outcome-averaged distance between two POVM families. -/
noncomputable def measurementFamilyDistanceValue
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : MeasurementFamily Question Outcome Coord) : Real :=
  ∑ x, (mu x).toReal *
    ∑ a, stateDependentDistance psi ((A x).effect a) ((B x).effect a)

private theorem measurementFamilyDistanceValue_nonneg
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : MeasurementFamily Question Outcome Coord) :
    0 ≤ measurementFamilyDistanceValue mu psi A B := by
  unfold measurementFamilyDistanceValue
  apply Finset.sum_nonneg
  intro x _
  apply mul_nonneg NNReal.zero_le_coe
  exact Finset.sum_nonneg fun a _ =>
    stateDependentDistance_nonneg psi ((A x).effect a) ((B x).effect a)

private theorem measurementFamilyDistanceValue_triangle_bound
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B C : MeasurementFamily Question Outcome Coord) :
    measurementFamilyDistanceValue mu psi A C ≤
      2 * (measurementFamilyDistanceValue mu psi A B +
        measurementFamilyDistanceValue mu psi B C) := by
  have hpoint (x : Question) (a : Outcome) :
      stateDependentDistance psi ((A x).effect a) ((C x).effect a) ≤
        2 * (stateDependentDistance psi ((A x).effect a) ((B x).effect a) +
          stateDependentDistance psi ((B x).effect a) ((C x).effect a)) := by
    have hsplit :
        operatorAction ((A x).effect a - (C x).effect a) psi =
          operatorAction ((A x).effect a - (B x).effect a) psi +
            operatorAction ((B x).effect a - (C x).effect a) psi := by
      rw [show (A x).effect a - (C x).effect a =
        ((A x).effect a - (B x).effect a) +
          ((B x).effect a - (C x).effect a) by abel]
      simp [operatorAction]
    unfold stateDependentDistance
    rw [hsplit]
    calc
      ‖operatorAction ((A x).effect a - (B x).effect a) psi +
          operatorAction ((B x).effect a - (C x).effect a) psi‖ ^ 2 ≤
          (‖operatorAction ((A x).effect a - (B x).effect a) psi‖ +
            ‖operatorAction ((B x).effect a - (C x).effect a) psi‖) ^ 2 := by
        gcongr
        exact norm_add_le _ _
      _ ≤ 2 * (‖operatorAction ((A x).effect a - (B x).effect a) psi‖ ^ 2 +
          ‖operatorAction ((B x).effect a - (C x).effect a) psi‖ ^ 2) :=
        add_sq_le
  calc
    measurementFamilyDistanceValue mu psi A C ≤
        ∑ x, (mu x).toReal * ∑ a,
          2 * (stateDependentDistance psi ((A x).effect a) ((B x).effect a) +
            stateDependentDistance psi ((B x).effect a) ((C x).effect a)) := by
      unfold measurementFamilyDistanceValue
      apply Finset.sum_le_sum
      intro x _
      apply mul_le_mul_of_nonneg_left
      · exact Finset.sum_le_sum fun a _ => hpoint x a
      · exact NNReal.zero_le_coe
    _ = 2 * (measurementFamilyDistanceValue mu psi A B +
        measurementFamilyDistanceValue mu psi B C) := by
      unfold measurementFamilyDistanceValue
      simp only [mul_add, Finset.sum_add_distrib, Finset.mul_sum]
      ring_nf

/-- The PMF- and outcome-averaged distance between raw two-index operator families. -/
noncomputable def operatorOutcomeFamilyDistanceValue
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question] [Fintype Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : Question → Outcome → MIPStarRE.Quantum.Op Coord) : Real :=
  ∑ x, (mu x).toReal *
    ∑ a, stateDependentDistance psi (A x a) (B x a)

/-- An exact finite bound on raw operator-family distance. -/
def OperatorFamilyDistanceBoundedBy
    {Question : Type uQuestion} {Coord : Type uCoord}
    [Fintype Question] [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : Question → MIPStarRE.Quantum.Op Coord)
    (delta : NNReal) : Prop :=
  operatorFamilyDistanceValue mu psi A B ≤ (delta : Real)

/-- An exact finite bound on POVM-family distance. -/
def MeasurementFamilyDistanceBoundedBy
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : MeasurementFamily Question Outcome Coord)
    (delta : NNReal) : Prop :=
  measurementFamilyDistanceValue mu psi A B ≤ (delta : Real)

/-! ## Indexed asymptotic relations -/

/-- A natural-number-indexed error profile taking values in `[0, 1]`. -/
abbrev ErrorProfile := Nat → Set.Icc (0 : Real) 1

/-- Real-valued Big-O at `Filter.atTop`. -/
def IsBigOAtTop (value scale : Nat → Real) : Prop :=
  Asymptotics.IsBigO Filter.atTop value scale

/-- Indexed squared state distance is Big-O of the error profile. -/
def StateFamiliesBigO
    {Coord : Type uCoord} [Fintype Coord]
    (psi phi : Nat → EuclideanSpace Complex Coord)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop (fun n => ‖psi n - phi n‖ ^ 2)
    (fun n => (delta n : Real))

/-- Indexed raw operator-family distance is Big-O of the error profile. -/
def OperatorFamiliesBigO
    {Question : Type uQuestion} {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex Coord)
    (A B : Nat → Question → MIPStarRE.Quantum.Op Coord)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop
    (fun n => operatorFamilyDistanceValue (mu n) (psi n) (A n) (B n))
    (fun n => (delta n : Real))

/-- Indexed POVM-family distance is Big-O of the error profile. -/
def MeasurementFamiliesBigO
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex Coord)
    (A B : Nat → MeasurementFamily Question Outcome Coord)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop
    (fun n => measurementFamilyDistanceValue (mu n) (psi n) (A n) (B n))
    (fun n => (delta n : Real))

/-- Alice's marginal of a joint question PMF. -/
noncomputable def aliceQuestionMarginal
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    (mu : PMF (QuestionA × QuestionB)) : PMF QuestionA :=
  mu.map Prod.fst

/-- Bob's marginal of a joint question PMF. -/
noncomputable def bobQuestionMarginal
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    (mu : PMF (QuestionA × QuestionB)) : PMF QuestionB :=
  mu.map Prod.snd

/-- Select which strategy state witnesses the paper's either-state clause. -/
inductive StrategyStateChoice
  | first
  | second

/-- The state selected for comparing two finite strategies. -/
def strategyComparisonState
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (choice : StrategyStateChoice)
    (S T : PureStrategy QuestionA QuestionB OutcomeA OutcomeB Alice Bob) :
    EuclideanSpace Complex (Alice × Bob) :=
  match choice with
  | .first => S.state
  | .second => T.state

/-- Indexed strategy distance, using the joint question PMF's marginals and an
explicit choice of comparison state. -/
def StrategyFamiliesBigO
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat → PMF (QuestionA × QuestionB))
    (S T : Nat →
      PureStrategy QuestionA QuestionB OutcomeA OutcomeB Alice Bob)
    (choice : StrategyStateChoice)
    (delta : ErrorProfile) : Prop :=
  StateFamiliesBigO (fun n => (S n).state) (fun n => (T n).state) delta ∧
  IsBigOAtTop (fun n =>
    operatorOutcomeFamilyDistanceValue (aliceQuestionMarginal (mu n))
      (strategyComparisonState choice (S n) (T n))
      (fun x a => aliceLocal (Alice := Alice) (Bob := Bob)
        (((S n).alice x).effect a))
      (fun x a => aliceLocal (Alice := Alice) (Bob := Bob)
        (((T n).alice x).effect a)))
    (fun n => (delta n : Real)) ∧
  IsBigOAtTop (fun n =>
    operatorOutcomeFamilyDistanceValue (bobQuestionMarginal (mu n))
      (strategyComparisonState choice (S n) (T n))
      (fun y b => bobLocal (Alice := Alice) (Bob := Bob)
        (((S n).bob y).effect b))
      (fun y b => bobLocal (Alice := Alice) (Bob := Bob)
        (((T n).bob y).effect b)))
    (fun n => (delta n : Real))

/-! ## Exact and asymptotic consistency -/

/-- Equality of the two local actions of one POVM on a bipartite state.

Paper source: Definition `def:consistent-measurement`.
Paper-labelled uses must separately require the measurement to be projective.
-/
def MeasurementConsistentOn
    {Outcome : Type uOutcome} {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex (Coord × Coord))
    (M : MIPStarRE.Quantum.Measurement Outcome Coord) : Prop :=
  ∀ a,
    operatorAction (aliceLocal (Bob := Coord) (M.effect a)) psi =
      operatorAction (bobLocal (Alice := Coord) (M.effect a)) psi

/-- The finite PMF-weighted off-diagonal POVM consistency value.

Paper source: Definition `def:consistency`.
-/
noncomputable def povmConsistencyValue
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MeasurementFamily Question Outcome Alice)
    (B : MeasurementFamily Question Outcome Bob) : Real :=
  ∑ x, (mu x).toReal *
    ∑ a, ∑ b ∈ (Finset.univ.erase a),
      Complex.re (inner Complex psi
        (operatorAction
          (aliceLocal (Bob := Bob) ((A x).effect a) *
            bobLocal (Alice := Alice) ((B x).effect b)) psi))

private theorem consistencyInner_eq_ev
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (psi : EuclideanSpace Complex (Alice × Bob))
    (X : MIPStarRE.Quantum.Op Alice)
    (Y : MIPStarRE.Quantum.Op Bob) :
    Complex.re (inner Complex psi
      (operatorAction
        (aliceLocal (Bob := Bob) X * bobLocal (Alice := Alice) Y) psi)) =
      MIPStarRE.LDT.ev (vectorQuantumState psi)
        (MIPStarRE.LDT.opTensor X Y) := by
  rw [vectorQuantumState_ev_eq_inner]
  rw [← MIPStarRE.LDT.leftTensor_mul_rightTensor_eq_opTensor]
  rfl

private theorem qBipartiteConsDefect_measurements_eq_sub
    {Outcome : Type uOutcome} {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (psi : MIPStarRE.LDT.QuantumState (Alice × Bob))
    (A : MIPStarRE.LDT.Measurement Outcome Alice)
    (B : MIPStarRE.LDT.Measurement Outcome Bob) :
    MIPStarRE.LDT.qBipartiteConsDefect psi A.toSubMeas B.toSubMeas =
      MIPStarRE.LDT.ev psi (1 : MIPStarRE.Quantum.Op (Alice × Bob)) -
        MIPStarRE.LDT.qBipartiteMatchMass psi A.toSubMeas B.toSubMeas := by
  have hmatch_le :
      MIPStarRE.LDT.qBipartiteMatchMass psi A.toSubMeas B.toSubMeas ≤
        MIPStarRE.LDT.ev psi (1 : MIPStarRE.Quantum.Op (Alice × Bob)) := by
    calc
      MIPStarRE.LDT.qBipartiteMatchMass psi A.toSubMeas B.toSubMeas =
          ∑ a : Outcome, MIPStarRE.LDT.ev psi
            (MIPStarRE.LDT.opTensor (A.outcome a) (B.outcome a)) := by
              rfl
      _ ≤ ∑ a : Outcome, MIPStarRE.LDT.ev psi
          (MIPStarRE.LDT.leftTensor (ι₂ := Bob) (A.outcome a)) := by
            refine Finset.sum_le_sum ?_
            intro a _
            exact MIPStarRE.LDT.ev_mono psi _ _ <|
              MIPStarRE.LDT.opTensor_le_leftTensor (ι₂ := Bob)
                (A.outcome_pos a) (MIPStarRE.LDT.Measurement.outcome_le_one B a)
      _ = MIPStarRE.LDT.ev psi
          (MIPStarRE.LDT.leftTensor (ι₂ := Bob) A.total) := by
            rw [← MIPStarRE.LDT.ev_sum psi
              (fun a : Outcome => MIPStarRE.LDT.leftTensor (ι₂ := Bob) (A.outcome a))]
            rw [MIPStarRE.LDT.leftTensor_finset_sum (ι₂ := Bob)
              Finset.univ A.outcome, A.sum_eq_total]
      _ = MIPStarRE.LDT.ev psi (1 : MIPStarRE.Quantum.Op (Alice × Bob)) := by
            simp [A.total_eq_one, MIPStarRE.LDT.leftTensor]
  unfold MIPStarRE.LDT.qBipartiteConsDefect
  rw [show MIPStarRE.LDT.ev psi
      (MIPStarRE.LDT.opTensor A.toSubMeas.total B.toSubMeas.total) =
        MIPStarRE.LDT.ev psi (1 : MIPStarRE.Quantum.Op (Alice × Bob)) by
    simp [A.total_eq_one, B.total_eq_one, MIPStarRE.LDT.opTensor]]
  rw [max_eq_right (sub_nonneg.mpr hmatch_le)]

private theorem consistencyOffDiagonal_eq_qBipartiteConsDefect
    {Outcome : Type uOutcome} {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MIPStarRE.Quantum.Measurement Outcome Alice)
    (B : MIPStarRE.Quantum.Measurement Outcome Bob) :
    (∑ a, ∑ b ∈ (Finset.univ.erase a),
      Complex.re (inner Complex psi
        (operatorAction
          (aliceLocal (Bob := Bob) (A.effect a) *
            bobLocal (Alice := Alice) (B.effect b)) psi))) =
      MIPStarRE.LDT.qBipartiteConsDefect (vectorQuantumState psi)
        (measurementToLDT A).toSubMeas (measurementToLDT B).toSubMeas := by
  classical
  rw [qBipartiteConsDefect_measurements_eq_sub]
  unfold MIPStarRE.LDT.qBipartiteMatchMass
  simp_rw [consistencyInner_eq_ev]
  simp_rw [Finset.sum_erase_eq_sub (Finset.mem_univ _)]
  rw [Finset.sum_sub_distrib]
  congr 1
  calc
    (∑ a, ∑ b, MIPStarRE.LDT.ev (vectorQuantumState psi)
        (MIPStarRE.LDT.opTensor (A.effect a) (B.effect b))) =
        ∑ a, MIPStarRE.LDT.ev (vectorQuantumState psi)
          (∑ b, MIPStarRE.LDT.opTensor (A.effect a) (B.effect b)) := by
      apply Finset.sum_congr rfl
      intro a _
      rw [MIPStarRE.LDT.ev_sum]
    _ = MIPStarRE.LDT.ev (vectorQuantumState psi)
        (∑ a, ∑ b, MIPStarRE.LDT.opTensor (A.effect a) (B.effect b)) := by
      rw [MIPStarRE.LDT.ev_sum]
    _ = MIPStarRE.LDT.ev (vectorQuantumState psi)
        (MIPStarRE.LDT.opTensor (∑ a, A.effect a) (∑ b, B.effect b)) := by
      congr 1
      symm
      rw [MIPStarRE.LDT.opTensor_sum_left_univ]
      apply Finset.sum_congr rfl
      intro a _
      rw [MIPStarRE.LDT.opTensor_sum_right_univ]
    _ = MIPStarRE.LDT.ev (vectorQuantumState psi) 1 := by
      rw [A.sum_eq_one, B.sum_eq_one]
      simp [MIPStarRE.LDT.opTensor]

private theorem povmConsistencyValue_eq_bipartiteConsError
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MeasurementFamily Question Outcome Alice)
    (B : MeasurementFamily Question Outcome Bob) :
    povmConsistencyValue mu psi A B =
      MIPStarRE.LDT.bipartiteConsError (vectorQuantumState psi)
        (pmfDistribution mu)
        (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT A))
        (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT B)) := by
  classical
  unfold povmConsistencyValue MIPStarRE.LDT.bipartiteConsError
    MIPStarRE.LDT.avgOver
  change (∑ x, (mu x).toReal *
      ∑ a, ∑ b ∈ Finset.univ.erase a, Complex.re (inner Complex psi
        (operatorAction
          (aliceLocal (Bob := Bob) ((A x).effect a) *
            bobLocal (Alice := Alice) ((B x).effect b)) psi))) =
    ∑ x, (mu x).toReal *
      MIPStarRE.LDT.qBipartiteConsDefect (vectorQuantumState psi)
        (measurementToLDT (A x)).toSubMeas
        (measurementToLDT (B x)).toSubMeas
  apply Finset.sum_congr rfl
  intro x _
  rw [consistencyOffDiagonal_eq_qBipartiteConsDefect]

private theorem povmConsistencyValue_nonneg
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MeasurementFamily Question Outcome Alice)
    (B : MeasurementFamily Question Outcome Bob) :
    0 ≤ povmConsistencyValue mu psi A B := by
  rw [povmConsistencyValue_eq_bipartiteConsError]
  exact MIPStarRE.LDT.bipartiteConsError_nonneg _ _ _ _

private theorem povmConsistencyValue_triangle_bound
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (hpsi : ‖psi‖ = 1)
    (A C : MeasurementFamily Question Outcome Alice)
    (B D : MeasurementFamily Question Outcome Bob) :
    povmConsistencyValue mu psi A D ≤
      povmConsistencyValue mu psi A B +
        2 * Real.sqrt
          (povmConsistencyValue mu psi C B +
            povmConsistencyValue mu psi C D) := by
  letI : Nonempty (Alice × Bob) :=
    euclideanSpace_nonempty_of_norm_eq_one psi hpsi
  have hAB : MIPStarRE.LDT.ConsRel (vectorQuantumState psi) (pmfDistribution mu)
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT A))
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT B))
      (povmConsistencyValue mu psi A B) := by
    constructor
    rw [← povmConsistencyValue_eq_bipartiteConsError]
  have hCB : MIPStarRE.LDT.ConsRel (vectorQuantumState psi) (pmfDistribution mu)
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT C))
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT B))
      (povmConsistencyValue mu psi C B) := by
    constructor
    rw [← povmConsistencyValue_eq_bipartiteConsError]
  have hCD : MIPStarRE.LDT.ConsRel (vectorQuantumState psi) (pmfDistribution mu)
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT C))
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT D))
      (povmConsistencyValue mu psi C D) := by
    constructor
    rw [← povmConsistencyValue_eq_bipartiteConsError]
  have htriangle :=
    MIPStarRE.LDT.Preliminaries.simeqTriangleInequality_heterogeneous
      (vectorQuantumState psi) (pmfDistribution mu)
      (vectorQuantumState_isNormalized psi hpsi)
      (pmfDistribution_isProbability mu).weight_sum_le_one
      (measurementFamilyToLDT A) (measurementFamilyToLDT C)
      (measurementFamilyToLDT B) (measurementFamilyToLDT D)
      (povmConsistencyValue mu psi A B)
      (povmConsistencyValue mu psi C B)
      (povmConsistencyValue mu psi C D)
      hAB hCB hCD
  simpa only [← povmConsistencyValue_eq_bipartiteConsError] using
    htriangle.offDiagonalBound

private theorem povmConsistencyValue_postprocess_le
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MeasurementFamily Question Outcome Alice)
    (B : MeasurementFamily Question Outcome Bob)
    (f : Outcome → Outcome') :
    povmConsistencyValue mu psi
        (MeasurementFamily.postprocess A f)
        (MeasurementFamily.postprocess B f) ≤
      povmConsistencyValue mu psi A B := by
  have hAB : MIPStarRE.LDT.ConsRel (vectorQuantumState psi) (pmfDistribution mu)
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT A))
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas (measurementFamilyToLDT B))
      (povmConsistencyValue mu psi A B) := by
    constructor
    rw [← povmConsistencyValue_eq_bipartiteConsError]
  have hprocessed :=
    MIPStarRE.LDT.Preliminaries.simeqDataProcessing_heterogeneous
      (vectorQuantumState psi) (pmfDistribution mu)
      (measurementFamilyToLDT A) (measurementFamilyToLDT B)
      (povmConsistencyValue mu psi A B) f hAB
  rw [povmConsistencyValue_eq_bipartiteConsError]
  change MIPStarRE.LDT.bipartiteConsError (vectorQuantumState psi)
      (pmfDistribution mu)
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas
        (measurementFamilyToLDT (MeasurementFamily.postprocess A f)))
      (MIPStarRE.LDT.IdxMeas.toIdxSubMeas
        (measurementFamilyToLDT (MeasurementFamily.postprocess B f))) ≤
    povmConsistencyValue mu psi A B
  rw [show MIPStarRE.LDT.IdxMeas.toIdxSubMeas
        (measurementFamilyToLDT (MeasurementFamily.postprocess A f)) =
      fun q => MIPStarRE.LDT.postprocess
        ((measurementFamilyToLDT A q).toSubMeas) f by
    funext q
    exact measurementToLDT_postprocess (A q) f]
  rw [show MIPStarRE.LDT.IdxMeas.toIdxSubMeas
        (measurementFamilyToLDT (MeasurementFamily.postprocess B f)) =
      fun q => MIPStarRE.LDT.postprocess
        ((measurementFamilyToLDT B q).toSubMeas) f by
    funext q
    exact measurementToLDT_postprocess (B q) f]
  exact hprocessed.offDiagonalBound

/-- An exact finite bound on POVM consistency mismatch. -/
def POVMConsistencyBoundedBy
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MeasurementFamily Question Outcome Alice)
    (B : MeasurementFamily Question Outcome Bob)
    (delta : NNReal) : Prop :=
  povmConsistencyValue mu psi A B ≤ (delta : Real)

/-- Indexed POVM consistency is Big-O of the error profile. -/
def POVMConsistencyBigO
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex (Alice × Bob))
    (A : Nat → MeasurementFamily Question Outcome Alice)
    (B : Nat → MeasurementFamily Question Outcome Bob)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop
    (fun n => povmConsistencyValue (mu n) (psi n) (A n) (B n))
    (fun n => (delta n : Real))

/-- Proposition 4.29's three-premise consistency triangle contract. -/
def POVMConsistencyBigOTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex (Alice × Bob))
    (hpsi : ∀ n, ‖psi n‖ = 1)
    (A C : Nat → MeasurementFamily Question Outcome Alice)
    (B D : Nat → MeasurementFamily Question Outcome Bob)
    (epsilon delta gamma : ErrorProfile) : Prop :=
  POVMConsistencyBigO mu psi A B epsilon →
  POVMConsistencyBigO mu psi C B delta →
  POVMConsistencyBigO mu psi C D gamma →
  IsBigOAtTop
    (fun n => povmConsistencyValue (mu n) (psi n) (A n) (D n))
    (fun n => (epsilon n : Real) +
      2 * Real.sqrt ((delta n : Real) + (gamma n : Real)))

/-- The indexed consistency triangle with scale `epsilon + 2 * sqrt (delta + gamma)`.

Paper source: Fact `fact:triangle-for-simeq`.
-/
theorem povmConsistencyBigO_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex (Alice × Bob))
    (hpsi : ∀ n, ‖psi n‖ = 1)
    (A C : Nat → MeasurementFamily Question Outcome Alice)
    (B D : Nat → MeasurementFamily Question Outcome Bob)
    (epsilon delta gamma : ErrorProfile) :
    POVMConsistencyBigOTriangleLaw
      mu psi hpsi A C B D epsilon delta gamma := by
  unfold POVMConsistencyBigOTriangleLaw
  intro hAB hCB hCD
  unfold POVMConsistencyBigO IsBigOAtTop at hAB hCB hCD
  unfold IsBigOAtTop
  have hCB_CD :
      Asymptotics.IsBigO Filter.atTop
        (fun n =>
          povmConsistencyValue (mu n) (psi n) (C n) (B n) +
          povmConsistencyValue (mu n) (psi n) (C n) (D n))
        (fun n => (delta n : Real) + (gamma n : Real)) := by
    have h := hCB.add_add hCD
    have hscale :
        (fun n => ‖(delta n : Real)‖ + ‖(gamma n : Real)‖) =
          (fun n => (delta n : Real) + (gamma n : Real)) := by
      funext n
      rw [Real.norm_of_nonneg (delta n).property.1,
        Real.norm_of_nonneg (gamma n).property.1]
    rw [hscale] at h
    exact h
  have hsqrt := hCB_CD.sqrt <|
    Filter.Eventually.of_forall fun n =>
      add_nonneg (delta n).property.1 (gamma n).property.1
  have htwoSqrt :
      Asymptotics.IsBigO Filter.atTop
        (fun n => 2 * Real.sqrt
          (povmConsistencyValue (mu n) (psi n) (C n) (B n) +
            povmConsistencyValue (mu n) (psi n) (C n) (D n)))
        (fun n => 2 * Real.sqrt
          ((delta n : Real) + (gamma n : Real))) := by
    exact (hsqrt.const_mul_left (2 : Real)).const_mul_right (by norm_num)
  have hcombined := hAB.add_add htwoSqrt
  have hcombinedScale :
      (fun n =>
        ‖(epsilon n : Real)‖ +
          ‖2 * Real.sqrt ((delta n : Real) + (gamma n : Real))‖) =
        (fun n =>
          (epsilon n : Real) +
            2 * Real.sqrt ((delta n : Real) + (gamma n : Real))) := by
    funext n
    rw [Real.norm_of_nonneg (epsilon n).property.1,
      Real.norm_of_nonneg
        (mul_nonneg (by norm_num) (Real.sqrt_nonneg _))]
  rw [hcombinedScale] at hcombined
  refine Asymptotics.IsBigO.trans ?_ hcombined
  apply Asymptotics.IsBigO.of_bound 1
  exact Filter.Eventually.of_forall fun n => by
    rw [Real.norm_of_nonneg
      (povmConsistencyValue_nonneg
        (mu n) (psi n) (A n) (D n))]
    rw [Real.norm_of_nonneg <| add_nonneg
      (povmConsistencyValue_nonneg
        (mu n) (psi n) (A n) (B n))
      (mul_nonneg (by norm_num) (Real.sqrt_nonneg _))]
    simpa only [one_mul] using
      povmConsistencyValue_triangle_bound
        (mu n) (psi n) (hpsi n)
        (A n) (C n) (B n) (D n)

/-! ## Distance laws -/

/-- The exact finite squared-distance triangle contract, with factor two. -/
def FiniteMeasurementTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B C : MeasurementFamily Question Outcome Coord)
    (delta epsilon : NNReal) : Prop :=
  MeasurementFamilyDistanceBoundedBy mu psi A B delta →
  MeasurementFamilyDistanceBoundedBy mu psi B C epsilon →
  MeasurementFamilyDistanceBoundedBy mu psi A C
    (2 * (delta + epsilon))

/-- The indexed measurement-family triangle contract.

Paper source: Fact `fact:triangle`.
-/
def MeasurementFamiliesBigOTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex Coord)
    (A B C : Nat → MeasurementFamily Question Outcome Coord)
    (delta epsilon : ErrorProfile) : Prop :=
  MeasurementFamiliesBigO mu psi A B delta →
  MeasurementFamiliesBigO mu psi B C epsilon →
  IsBigOAtTop
    (fun n => measurementFamilyDistanceValue (mu n) (psi n) (A n) (C n))
    (fun n => (delta n : Real) + (epsilon n : Real))

/-- The indexed heterogeneous consistency data-processing contract.

Paper source: Fact `fact:data-processing`.
-/
def POVMConsistencyBigOPostprocessLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex (Alice × Bob))
    (A : Nat → MeasurementFamily Question Outcome Alice)
    (B : Nat → MeasurementFamily Question Outcome Bob)
    (f : Outcome → Outcome') (delta : ErrorProfile) : Prop :=
  POVMConsistencyBigO mu psi A B delta →
  POVMConsistencyBigO mu psi
    (fun n => MeasurementFamily.postprocess (A n) f)
    (fun n => MeasurementFamily.postprocess (B n) f) delta

/-- The finite squared-distance triangle theorem. -/
theorem finiteMeasurement_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B C : MeasurementFamily Question Outcome Coord)
    (delta epsilon : NNReal) :
    FiniteMeasurementTriangleLaw mu psi A B C delta epsilon := by
  intro hAB hBC
  unfold MeasurementFamilyDistanceBoundedBy at hAB hBC ⊢
  calc
    measurementFamilyDistanceValue mu psi A C ≤
        2 * (measurementFamilyDistanceValue mu psi A B +
          measurementFamilyDistanceValue mu psi B C) :=
      measurementFamilyDistanceValue_triangle_bound mu psi A B C
    _ ≤ 2 * ((delta : Real) + (epsilon : Real)) := by
      gcongr
    _ = ((2 * (delta + epsilon) : NNReal) : Real) := by
      norm_num

/-- The indexed measurement-family triangle theorem. -/
theorem measurementFamiliesBigO_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex Coord)
    (A B C : Nat → MeasurementFamily Question Outcome Coord)
    (delta epsilon : ErrorProfile) :
    MeasurementFamiliesBigOTriangleLaw mu psi A B C delta epsilon := by
  intro hAB hBC
  unfold MeasurementFamiliesBigO IsBigOAtTop at hAB hBC
  unfold IsBigOAtTop
  have hsum := hAB.add_add hBC
  have hscale :
      (fun n => ‖(delta n : Real)‖ + ‖(epsilon n : Real)‖) =
        (fun n => (delta n : Real) + (epsilon n : Real)) := by
    funext n
    rw [Real.norm_of_nonneg (delta n).property.1,
      Real.norm_of_nonneg (epsilon n).property.1]
  rw [hscale] at hsum
  refine Asymptotics.IsBigO.trans ?_ hsum
  apply Asymptotics.IsBigO.of_bound 2
  exact Filter.Eventually.of_forall fun n => by
    rw [Real.norm_of_nonneg
      (measurementFamilyDistanceValue_nonneg (mu n) (psi n) (A n) (C n))]
    rw [Real.norm_of_nonneg (add_nonneg
      (measurementFamilyDistanceValue_nonneg (mu n) (psi n) (A n) (B n))
      (measurementFamilyDistanceValue_nonneg (mu n) (psi n) (B n) (C n)))]
    exact measurementFamilyDistanceValue_triangle_bound
      (mu n) (psi n) (A n) (B n) (C n)

/-- Heterogeneous POVM consistency is preserved by common postprocessing. -/
theorem povmConsistencyBigO_postprocess
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat → PMF Question)
    (psi : Nat → EuclideanSpace Complex (Alice × Bob))
    (A : Nat → MeasurementFamily Question Outcome Alice)
    (B : Nat → MeasurementFamily Question Outcome Bob)
    (f : Outcome → Outcome') (delta : ErrorProfile) :
    POVMConsistencyBigOPostprocessLaw mu psi A B f delta := by
  unfold POVMConsistencyBigOPostprocessLaw
  intro hAB
  unfold POVMConsistencyBigO IsBigOAtTop at hAB ⊢
  refine Asymptotics.IsBigO.trans ?_ hAB
  apply Asymptotics.IsBigO.of_bound 1
  exact Filter.Eventually.of_forall fun n => by
    rw [Real.norm_of_nonneg
      (povmConsistencyValue_nonneg
        (mu n) (psi n)
        (MeasurementFamily.postprocess (A n) f)
        (MeasurementFamily.postprocess (B n) f))]
    rw [Real.norm_of_nonneg
      (povmConsistencyValue_nonneg
        (mu n) (psi n) (A n) (B n))]
    simpa only [one_mul] using
      povmConsistencyValue_postprocess_le
        (mu n) (psi n) (A n) (B n) f

end MIPStarRE.QPBT
