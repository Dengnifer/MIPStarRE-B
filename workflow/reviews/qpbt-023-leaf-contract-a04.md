# QPBT-023 callable leaf contract (A04)

## Candidate verdict

This candidate separates the paper's mathematical and computational field
claims, freezes the QPBT measurement surface, and splits the old overloaded F04
node into finite, asymptotic, consistency, and law contracts. It adds no public
assumption. The exact declaration surfaces below are bound from structured
metadata by marker and SHA-256 and were derived from A03's clean elaborated
probes at the pinned project.

Immutable input evidence:

- base HEAD `942f9438b991ece8942815db16c019b92d9cdd8e`, tree
  `09123f4b25c892a146aabaa77d73cf0c5f35a0c6`;
- A01 scope handoff SHA-256
  `eceb7c85e601545f41161e28345dd61c498911190489fb8ca28d391369440e8f`;
- A02 source-integrity SHA-256
  `a52001d4589465b7ffe72e852f1d818d411a8ddbb442b34e5bc0568b7a36d747`;
- A03 pinned-API SHA-256
  `6bddc1560c4a2133e8a2ff70aab3e1790c6488469c32212e0bdcafe956cc301c`;
- pinned Mathlib `81a5d257c8e410db227a6665ed08f64fea08e997`; and
- authenticated MIPStarRE upstream
  `507e81220d95266ff3d589d125b2f87c7300a9fb`.

## Writer split

The two immediate writer lanes have no path overlap.

| Lane | Sole Lean path | Exact imports | Scoped command |
| --- | --- | --- | --- |
| Field | `MIPStarRE/QPBT/Basic/Field.lean` | `Mathlib.FieldTheory.Finite.Trace`; `Mathlib.FieldTheory.Galois.NormalBasis` | `lake env lean MIPStarRE/QPBT/Basic/Field.lean` |
| Approximation | `MIPStarRE/QPBT/Basic/Approximation.lean` | `Mathlib.Analysis.Asymptotics.Defs`; `Mathlib.Probability.ProbabilityMassFunction.Constructions`; `MIPStarRE.Quantum.Measurement`; `MIPStarRE.Quantum.FiniteHilbert` | `lake env lean MIPStarRE/QPBT/Basic/Approximation.lean` |

The Approximation lane implements F03 and the finite F04 foundation first.
The asymptotic, consistency, and law nodes are explicit sequential dependents
in that same file; they are not inferred work and do not create a second
simultaneous owner.

## Exact signatures

### Field

<!-- BEGIN F01-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

structure FieldData (k : Nat) where
  basis : Module.Basis (Fin k) (ZMod 2) (GaloisField 2 k)
  generator : GaloisField 2 k
  normal : forall i, basis i = generator ^ (2 ^ (i : Nat))
  selfDual : forall i j,
    Algebra.trace (ZMod 2) (GaloisField 2 k) (basis i * basis j) =
      if i = j then 1 else 0

noncomputable def fieldDataOfOddExponent
    (k : Nat) (hk : Odd k) : FieldData k

theorem fieldData_nonempty_of_odd
    (k : Nat) (hk : Odd k) : Nonempty (FieldData k)

noncomputable def fieldTrace (k : Nat) :
    GaloisField 2 k →ₗ[ZMod 2] ZMod 2 :=
  Algebra.trace (ZMod 2) (GaloisField 2 k)

noncomputable def FieldData.coordinates {k : Nat} (D : FieldData k) :
    GaloisField 2 k ≃ₗ[ZMod 2] (Fin k → ZMod 2) :=
  D.basis.equivFun

noncomputable def FieldData.multiplicationMatrix
    {k : Nat} (D : FieldData k) (a : GaloisField 2 k) :
    Matrix (Fin k) (Fin k) (ZMod 2) :=
  LinearMap.toMatrix D.basis D.basis
    (Algebra.lmul (ZMod 2) (GaloisField 2 k) a)

theorem FieldData.multiplicationMatrix_mulVec_coordinates
    {k : Nat} (D : FieldData k) (a b : GaloisField 2 k) :
    Matrix.mulVec (D.multiplicationMatrix a) (D.coordinates b) =
      D.coordinates (a * b)

end MIPStarRE.QPBT
```
<!-- END F01-SIGNATURES -->

`fieldDataOfOddExponent` is the one G16-declared minimal-skeleton hole. Its
only inputs are `k` and `Odd k`; it is never replaced by a basis, witness,
algorithm, or obligation premise. `fieldData_nonempty_of_odd` makes the
source-faithful existence claim visible and is derivable from the selected
data without another hole. In the proof-complete stage the selector must be
defined from a genuine simultaneous-existence proof.

The paper's stronger quantifier order, one deterministic algorithm working for
every positive odd `k` and returning compatible multiplication tables in
polynomial time, remains K03A. It is not claimed by this noncomputable F01
selection.

### Measurements

<!-- BEGIN F03-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uQuestion uOutcome uOutcome' uCoord

abbrev MeasurementFamily
    (Question : Type uQuestion) (Outcome : Type uOutcome)
    (Coord : Type uCoord)
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord] :=
  Question → MIPStarRE.Quantum.Measurement Outcome Coord

def ProjectiveMeasurementFamily
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (M : MeasurementFamily Question Outcome Coord) : Prop :=
  forall x a, (M x).effect a * (M x).effect a = (M x).effect a

namespace MeasurementFamily

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
      ∑ a ∈ Finset.univ.filter (fun a => f a = b), (M x).effect a

theorem postprocess_effect_eq_zero_of_not_mem_range
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'} {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Coord] [DecidableEq Coord]
    (M : MeasurementFamily Question Outcome Coord)
    (f : Outcome → Outcome') (x : Question) (b : Outcome')
    (hb : b ∉ Set.range f) :
    (postprocess M f x).effect b = 0

end MeasurementFamily

abbrev BinaryObservable (Coord : Type uCoord)
    [Fintype Coord] [DecidableEq Coord] :=
  { O : MIPStarRE.Quantum.Op Coord //
      O ∈ Matrix.unitaryGroup Coord Complex ∧ O * O = 1 }

noncomputable def observableOfMeasurement
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (M : MIPStarRE.Quantum.Measurement (ZMod 2) Coord)
    (hM : forall b, M.effect b * M.effect b = M.effect b) :
    BinaryObservable Coord

@[simp] theorem observableOfMeasurement_val
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (M : MIPStarRE.Quantum.Measurement (ZMod 2) Coord)
    (hM : forall b, M.effect b * M.effect b = M.effect b) :
    (observableOfMeasurement M hM : MIPStarRE.Quantum.Op Coord) =
      M.effect 0 - M.effect 1

end MIPStarRE.QPBT
```
<!-- END F03-SIGNATURES -->

The family alias intentionally leaves `Question` unrestricted. Finiteness
enters only at games and averages. Postprocessing is the exact qualified fiber
sum, and the empty-fiber theorem is callable. The binary observable requires
projectivity, returns a certified unitary involution, and fixes the paper's
outcome-0-minus-outcome-1 sign by a public value theorem.

### Approximation finite foundation

<!-- BEGIN F04-FINITE-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uQuestion uOutcome uCoord
universe uQuestionA uQuestionB uOutcomeA uOutcomeB uAlice uBob
universe uSource uTarget uAuxAlice uAuxBob
universe uAliceJunk uAliceIdeal uBobJunk uBobIdeal

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

noncomputable def isometryMatrix
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source] [Fintype Target]
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target) : Matrix Target Source Complex :=
  Matrix.toEuclideanLin.symm V.toLinearMap

noncomputable def isometryAdjointMatrix
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source] [Fintype Target]
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target) : Matrix Source Target Complex :=
  (isometryMatrix V)ᴴ

noncomputable def conjugateByIsometry
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source] [Fintype Target]
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target)
    (A : MIPStarRE.Quantum.Op Source) : MIPStarRE.Quantum.Op Target :=
  isometryMatrix V * A * isometryAdjointMatrix V

theorem isometryMatrix_adjoint_mul_self
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source] [Fintype Target]
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target) :
    (isometryMatrix V)ᴴ * isometryMatrix V = 1

def aliceLocal
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (A : MIPStarRE.Quantum.Op Alice) :
    MIPStarRE.Quantum.Op (Alice × Bob) :=
  Matrix.kronecker A 1

def bobLocal
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (B : MIPStarRE.Quantum.Op Bob) :
    MIPStarRE.Quantum.Op (Alice × Bob) :=
  Matrix.kronecker 1 B

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

theorem BipartiteIsometry.tensorMatrix_adjoint_mul_self
    {Alice : Type uAlice} {Bob : Type uBob}
    {AuxAlice : Type uAuxAlice} {AuxBob : Type uAuxBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob]
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob) :
    V.tensorMatrixᴴ * V.tensorMatrix = 1

noncomputable def BipartiteIsometry.tensorIsometry
    {Alice : Type uAlice} {Bob : Type uBob}
    {AuxAlice : Type uAuxAlice} {AuxBob : Type uAuxBob}
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob]
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob) :
    EuclideanSpace Complex (Alice × Bob) →ₗᵢ[Complex]
      EuclideanSpace Complex (AuxAlice × AuxBob)

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

def localProductToJunkIdeal
    (AliceJunk : Type uAliceJunk) (AliceIdeal : Type uAliceIdeal)
    (BobJunk : Type uBobJunk) (BobIdeal : Type uBobIdeal) :
    ((AliceJunk × AliceIdeal) × (BobJunk × BobIdeal)) ≃
      ((AliceJunk × BobJunk) × (AliceIdeal × BobIdeal))

noncomputable def reindexState
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [Fintype Target] (e : Source ≃ Target) :
    EuclideanSpace Complex Source ≃ₗᵢ[Complex]
      EuclideanSpace Complex Target :=
  LinearIsometryEquiv.piLpCongrLeft 2 Complex Complex e

def reindexOperator
    {Source : Type uSource} {Target : Type uTarget}
    [Fintype Source] [DecidableEq Source]
    [Fintype Target] [DecidableEq Target] (e : Source ≃ Target) :
    MIPStarRE.Quantum.Op Source ≃ₐ[Complex]
      MIPStarRE.Quantum.Op Target :=
  Matrix.reindexAlgEquiv Complex Complex e

noncomputable def operatorAction
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (A : MIPStarRE.Quantum.Op Coord)
    (psi : EuclideanSpace Complex Coord) :
    EuclideanSpace Complex Coord :=
  Matrix.toEuclideanLin A psi

noncomputable def stateDependentDistance
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex Coord)
    (A B : MIPStarRE.Quantum.Op Coord) : Real :=
  ‖operatorAction (A - B) psi‖ ^ 2

theorem stateDependentDistance_nonneg
    {Coord : Type uCoord} [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex Coord)
    (A B : MIPStarRE.Quantum.Op Coord) :
    0 ≤ stateDependentDistance psi A B

noncomputable def operatorFamilyDistanceValue
    {Question : Type uQuestion} {Coord : Type uCoord}
    [Fintype Question] [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : Question → MIPStarRE.Quantum.Op Coord) : Real :=
  ∑ x, (mu x).toReal * stateDependentDistance psi (A x) (B x)

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

noncomputable def operatorOutcomeFamilyDistanceValue
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question] [Fintype Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : Question → Outcome → MIPStarRE.Quantum.Op Coord) : Real :=
  ∑ x, (mu x).toReal *
    ∑ a, stateDependentDistance psi (A x a) (B x a)

def OperatorFamilyDistanceBoundedBy
    {Question : Type uQuestion} {Coord : Type uCoord}
    [Fintype Question] [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : Question → MIPStarRE.Quantum.Op Coord)
    (delta : NNReal) : Prop :=
  operatorFamilyDistanceValue mu psi A B ≤ (delta : Real)

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

end MIPStarRE.QPBT
```
<!-- END F04-FINITE-SIGNATURES -->

The two local conjugations are deliberately side-specific. Their targets stay
factored at call sites, and the junk/ideal regrouping is a named equivalence.
The finite `...Value` functions return exact real numbers; the `...BoundedBy`
predicates use explicit nonnegative bounds and are not the paper's Big-O
relations.

### Approximation indexed relations

<!-- BEGIN F04-ASYMPTOTIC-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uQuestion uOutcome uCoord
universe uQuestionA uQuestionB uOutcomeA uOutcomeB uAlice uBob

abbrev ErrorProfile := Nat -> Set.Icc (0 : Real) 1

def IsBigOAtTop (value scale : Nat -> Real) : Prop :=
  Asymptotics.IsBigO Filter.atTop value scale

def StateFamiliesBigO
    {Coord : Type uCoord} [Fintype Coord]
    (psi phi : Nat -> EuclideanSpace Complex Coord)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop (fun n => ‖psi n - phi n‖ ^ 2)
    (fun n => (delta n : Real))

def OperatorFamiliesBigO
    {Question : Type uQuestion} {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex Coord)
    (A B : Nat -> Question -> MIPStarRE.Quantum.Op Coord)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop
    (fun n => operatorFamilyDistanceValue (mu n) (psi n) (A n) (B n))
    (fun n => (delta n : Real))

def MeasurementFamiliesBigO
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex Coord)
    (A B : Nat -> MeasurementFamily Question Outcome Coord)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop
    (fun n => measurementFamilyDistanceValue (mu n) (psi n) (A n) (B n))
    (fun n => (delta n : Real))

noncomputable def aliceQuestionMarginal
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    (mu : PMF (QuestionA × QuestionB)) : PMF QuestionA :=
  mu.map Prod.fst

noncomputable def bobQuestionMarginal
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    (mu : PMF (QuestionA × QuestionB)) : PMF QuestionB :=
  mu.map Prod.snd

inductive StrategyStateChoice
  | first
  | second

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
    (mu : Nat -> PMF (QuestionA × QuestionB))
    (S T : Nat ->
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

end MIPStarRE.QPBT
```
<!-- END F04-ASYMPTOTIC-SIGNATURES -->

The error profile preserves the paper's input domain `[0,1]`, while
`IsBigOAtTop` deliberately accepts an arbitrary real-valued scale. Derived
sums and square-root expressions therefore need no unmentioned clamping.
`StrategyFamiliesBigO` consumes the joint question PMF through named
marginals and makes the choice of comparison state explicit.

### Approximation consistency

<!-- BEGIN F04-CONSISTENCY-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uQuestion uOutcome uCoord uAlice uBob

def MeasurementConsistentOn
    {Outcome : Type uOutcome} {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex (Coord × Coord))
    (M : MIPStarRE.Quantum.Measurement Outcome Coord) : Prop :=
  ∀ a,
    operatorAction (aliceLocal (Bob := Coord) (M.effect a)) psi =
      operatorAction (bobLocal (Alice := Coord) (M.effect a)) psi

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

def POVMConsistencyBigO
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex (Alice × Bob))
    (A : Nat -> MeasurementFamily Question Outcome Alice)
    (B : Nat -> MeasurementFamily Question Outcome Bob)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop
    (fun n => povmConsistencyValue (mu n) (psi n) (A n) (B n))
    (fun n => (delta n : Real))

def POVMConsistencyBigOTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex (Alice × Bob))
    (A C : Nat -> MeasurementFamily Question Outcome Alice)
    (B D : Nat -> MeasurementFamily Question Outcome Bob)
    (epsilon delta gamma : ErrorProfile) : Prop :=
  POVMConsistencyBigO mu psi A B epsilon ->
  POVMConsistencyBigO mu psi C B delta ->
  POVMConsistencyBigO mu psi C D gamma ->
  IsBigOAtTop
    (fun n => povmConsistencyValue (mu n) (psi n) (A n) (D n))
    (fun n => (epsilon n : Real) +
      2 * Real.sqrt ((delta n : Real) + (gamma n : Real)))

theorem povmConsistencyBigO_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex (Alice × Bob))
    (A C : Nat -> MeasurementFamily Question Outcome Alice)
    (B D : Nat -> MeasurementFamily Question Outcome Bob)
    (epsilon delta gamma : ErrorProfile) :
    POVMConsistencyBigOTriangleLaw
      mu psi A C B D epsilon delta gamma

end MIPStarRE.QPBT
```
<!-- END F04-CONSISTENCY-SIGNATURES -->

`MeasurementConsistentOn` is Definition 3.2's exact action equality. The
finite consistency value follows Definition 4.8's off-diagonal sum, while
the indexed wrapper and theorem obligation expose Proposition 4.29's three
premises and its exact derived scale.

### Approximation distance laws

<!-- BEGIN F04-DISTANCE-LAWS-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uQuestion uOutcome uOutcome' uCoord

def FiniteMeasurementTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B C : MeasurementFamily Question Outcome Coord)
    (delta epsilon : NNReal) : Prop :=
  MeasurementFamilyDistanceBoundedBy mu psi A B delta ->
  MeasurementFamilyDistanceBoundedBy mu psi B C epsilon ->
  MeasurementFamilyDistanceBoundedBy mu psi A C
    (2 * (delta + epsilon))

def MeasurementFamiliesBigOTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex Coord)
    (A B C : Nat -> MeasurementFamily Question Outcome Coord)
    (delta epsilon : ErrorProfile) : Prop :=
  MeasurementFamiliesBigO mu psi A B delta ->
  MeasurementFamiliesBigO mu psi B C epsilon ->
  IsBigOAtTop
    (fun n => measurementFamilyDistanceValue (mu n) (psi n) (A n) (C n))
    (fun n => (delta n : Real) + (epsilon n : Real))

def MeasurementFamiliesPostprocessLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'} {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex Coord)
    (A B : Nat -> MeasurementFamily Question Outcome Coord)
    (f : Outcome -> Outcome') (delta : ErrorProfile) : Prop :=
  MeasurementFamiliesBigO mu psi A B delta ->
  MeasurementFamiliesBigO mu psi
    (fun n => MeasurementFamily.postprocess (A n) f)
    (fun n => MeasurementFamily.postprocess (B n) f) delta

theorem finiteMeasurement_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B C : MeasurementFamily Question Outcome Coord)
    (delta epsilon : NNReal) :
    FiniteMeasurementTriangleLaw mu psi A B C delta epsilon

theorem measurementFamiliesBigO_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex Coord)
    (A B C : Nat -> MeasurementFamily Question Outcome Coord)
    (delta epsilon : ErrorProfile) :
    MeasurementFamiliesBigOTriangleLaw mu psi A B C delta epsilon

theorem measurementFamiliesBigO_postprocess
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'} {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex Coord)
    (A B : Nat -> MeasurementFamily Question Outcome Coord)
    (f : Outcome -> Outcome') (delta : ErrorProfile) :
    MeasurementFamiliesPostprocessLaw mu psi A B f delta

end MIPStarRE.QPBT
```
<!-- END F04-DISTANCE-LAWS-SIGNATURES -->

The three `...Law` definitions freeze the exact statements elaborated by A03;
the three theorem names are the corresponding proof obligations. They are not
allowed minimal-skeleton holes. The finite triangle exposes the factor two
from squared norms, while the paper-facing Big-O statement absorbs constant
factors. Postprocessing is the same explicit map on both families.

## Source anchors and integrity

All anchors below were checked against the split files under the pinned
`references/2001.04383v3` tree. The generated range is the line range in the
split file; the original range is the corresponding range in the concatenated
source manifest.

| Node | Primary anchor | Additional anchors | Verdict |
| --- | --- | --- | --- |
| F01-FIELD | `dependencies/finite-fields.tex:1-412` (`sec:finite-fields`; original 1317-1728) | none | faithful boundary; source existence and algorithm are separated |
| F03-MEASUREMENT | `dependencies/measurements.tex:3-47` (`def:bracket`; original 1856-1900) | `dependencies/magic-square.tex:147-173` (`thm:ms-from-ac`); `qpbt/qpbt-game-and-soundness.tex:383-410` (`eq:gonna-expand-A`) | faithful boundary; qualified measurement API and sign order are explicit |
| F04-DISTANCE | `dependencies/strategies-distance.tex:20-32` (`def:tensor-product-strategy`; original 2903-2915) | `strategies-distance.tex:252-265` (`def:povm-distance`); `qpbt/appendix-preliminaries.tex:49-53`; `qpbt/qpbt-game-and-soundness.tex:533-545` (`thm:pauli`) | faithful boundary; finite values and NNReal bounds are distinct |
| F04-ASYMPTOTIC | `dependencies/strategies-distance.tex:213-224` (`def:state-distance`; original 3096-3107) | `strategies-distance.tex:252-282`; `qpbt/appendix-preliminaries.tex:49-53` | faithful boundary; indexed `IsBigO atTop` is not replaced by a finite bound |
| F04-CONSISTENCY | `dependencies/strategies-distance.tex:226-250` (`def:consistency`; original 3109-3133) | `strategies-distance.tex:138-150` (`def:consistent-measurement`; original 3021-3033); `strategies-distance.tex:383-388` (`fact:triangle-for-simeq`) | faithful boundary; exact, finite, and indexed relations are separate |
| F04-DISTANCE-LAWS | `dependencies/strategies-distance.tex:377-395` (`fact:triangle`; original 3260-3278) | postprocessing definition and finite distance anchors carried by F03/F04-DISTANCE | exact statement contracts; proofs remain downstream obligations |

The F04 consistency anchor at `def:consistent-measurement` was missing from
the first A04 draft. It was restored before freeze at split lines 138-150
(original 3021-3033), regenerated through every affected chapter, and checked
with the source validator. This is a source-fidelity correction, not a change
to the theorem's public assumptions, so no separate issue is opened.

## Skeleton and gap policy

The minimal skeleton plan has exactly two declared proof holes:

| Declaration | Stage | Discharge owner |
| --- | --- | --- |
| `MIPStarRE.QPBT.fieldDataOfOddExponent` | minimal skeleton only | G16/QPBT-023: prove simultaneous self-dual-normal-basis existence, then define the selector |
| `MIPStarRE.QPBT.pauliSoundness` | minimal skeleton only | QPBT main-theorem implementation frontier |

The F01 selector is source-faithful: its public inputs are only `k` and
`Odd k`, and no caller-supplied basis, witness package, repair premise, or
algorithm is introduced. The K03A uniform deterministic construction and its
polynomial-time table output remain a separate contract. The checker and
README therefore use the amended gate `no unintended sorry/axiom/constant;
only the two declared skeleton holes`; proof-complete entries permit zero
holes. None of the F03/F04 law declarations is a skeleton hole.

## Scout authentication and dispositions

| Scout | Immutable evidence | Disposition |
| --- | --- | --- |
| A02 source-integrity | `workflow/reviews/qpbt-023-source-integrity-a02.md`, SHA-256 `a52001d4589465b7ffe72e852f1d818d411a8ddbb442b34e5bc0568b7a36d747` | accepted after replacing timing sentinels and rechecking the clean exact base; its blockers drove the source anchors, finite/Big-O split, and F01 existence/algorithm split |
| A03 pinned-Lean-API | source report `/tmp/i023-scout-a03-lean-api.md`, SHA-256 `6bddc1560c4a2133e8a2ff70aab3e1790c6488469c32212e0bdcafe956cc301c`; canonical normalized copy SHA-256 `6de9ef8ea6407045c0ebb74288750d6e86f2fdb6fdefc67c97c4dd73df3c93d3` | accepted as API evidence; canonical copy differs only by one normalized trailing-space byte, and all six marker blocks below are hashed independently |

A02's finite-bound versus indexed-`O` warning is resolved by F04-DISTANCE,
F04-ASYMPTOTIC, and F04-DISTANCE-LAWS. Its provenance warning is resolved by
the immutable source table and marker-bound signatures. A03's probes determine
names and elaborated types, but do not assert that any law is proved.

## Validation and accounting

A04 started from parent commit `4d9cee83d413bf90334f668bbdcfa0bcbd3b3d75`
(tree `c333cb6b5d0422fbf2268ac057f3d4e553da6e22`), whose only prior change was
the independently committed A05 README synchronization. The immutable issue
base remains HEAD `942f9438b991ece8942815db16c019b92d9cdd8e`, tree
`09123f4b25c892a146aabaa77d73cf0c5f35a0c6`.

The A04 candidate diff is restricted to the following paths (the report and
paper-gap note are newly created):

```text
blueprint/check.py
blueprint/generated/graph.dot
blueprint/generated/graph.json
blueprint/metadata/gaps.json
blueprint/metadata/nodes.json
blueprint/src/generated/chapter-02-entries.tex
blueprint/src/generated/chapter-03-entries.tex
blueprint/src/generated/chapter-04-entries.tex
blueprint/src/generated/chapter-05-entries.tex
blueprint/src/generated/chapter-06-entries.tex
blueprint/src/generated/chapter-07-entries.tex
blueprint/src/generated/chapter-08-entries.tex
blueprint/src/generated/chapter-09-entries.tex
blueprint/src/generated/chapter-10-entries.tex
blueprint/src/generated/chapter-11-entries.tex
blueprint/src/generated/chapter-12-entries.tex
blueprint/src/generated/gaps.tex
blueprint/tests/test_check.py
docs/paper-gaps/self-dual-normal-basis.md
workflow/reviews/qpbt-023-leaf-contract-a04.md
```

The deterministic generator was run six times (two contract/source passes and
four renderer passes). The observed checker test count is five invocations:
four passes and one intentional stale-test failure exposed while the schema
migration was being completed. Final gates are all green:

```text
python3 -m unittest blueprint.tests.test_check       28/28 passed
python3 blueprint/check.py --check --source-root ...  51 nodes, 12 chapters
python3 blueprint/check.py --check                   51 nodes, 12 chapters
python3 scripts/workflow.py validate                 valid (31 issues, 18 PRs, 354 sessions, 7 stages)
git diff --check                                     clean
make -C blueprint pdf                                OK: 35 pages; 160 identifiers extractable
```

The PDF command uses the generated renderer's local 8pt contract layout and
discretionary breaks for long metadata; it does not alter the machine-visible
metadata or signature hashes. No Lean command, Lake build, hot-cache action,
network request, endpoint call, GitHub operation, or credential access was
performed by A04. Token usage is `null` because the collaboration backend does
not expose it.

Measured A04 elapsed time from canonical continuation start
`2026-09-01T09:29:01.788902Z` to the final validation cutoff is recorded in
`2026-09-01T10:04:55.788350Z`; measured elapsed `2153.999448` seconds. The
session metric is also imported by the root coordinator. Action counts are:
six generator runs, five checker-test invocations (one migration diagnostic
and four final passes), repeated source/check validations after each
regeneration, six PDF invocations (one initial layout diagnostic, one
intermediate overflow diagnostic, and four passing renderer layouts), zero
compile attempts, zero cache hits, zero retries, and zero new issues. The only
incident was the initial PDF overflow; the renderer's bounded local
typography/breaking change resolved it.

## Fresh reviewer briefs

These are handoff definitions for root to register as fresh read-only sessions
after this candidate commit. They have disjoint review emphasis and neither
may write the candidate worktree.

1. `i023-reviewer-a05-blueprint-contract`: inspect the candidate head/tree,
   all 20 owned paths, metadata schema, generated graph/chapter determinism,
   six signature-manifest hashes, checker adversarial tests, skeleton plan,
   paper-gap note, and the complete validation transcript. Run
   `python3 -m unittest blueprint.tests.test_check`,
   `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3`,
   `python3 blueprint/check.py --check`, `python3 scripts/workflow.py validate`,
   and `git diff --check`. Report findings first with `path:line` anchors.
2. `i023-reviewer-a06-statement-integrity`: read the pinned source sections
   before the diff; independently check F01's simultaneous-existence versus
   K03A algorithm split, F03's postprocess/effect sign and provenance, every
   F04 finite/asymptotic/consistency/law quantifier and constant, G16's
   declared hole policy, and absence of public obligation inputs. Run the two
   blueprint check commands above plus a source-anchor audit. Report any
   fidelity mismatch as a blocker and otherwise state residual proof risk.

Root should issue both reviewers against the immutable candidate head and
record their manifests, timing, and dispositions before accepting this freeze.
