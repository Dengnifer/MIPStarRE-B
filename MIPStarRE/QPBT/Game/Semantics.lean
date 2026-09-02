import Mathlib.LinearAlgebra.Matrix.Rank
import Mathlib.Order.ConditionallyCompleteLattice.Basic
import Mathlib.Probability.ProbabilityMassFunction.Constructions
import MIPStarRE.QPBT.Basic.Approximation

/-!
# Finite two-player game and strategy semantics

This module formalizes the finite game, tensor-product strategy, value,
commutation, consistency, symmetry, Schmidt-rank, and entanglement-requirement
definitions from `MIP* = RE`.

Paper source: Definitions `def:game`, `def:tensor-product-strategy`,
`def:tensor-product-value`, `def:projective-strategy`, `rem:symmetric-games`,
`def:comm-strategy`, `def:consistent-measurement`, `def:consistent-strategy`,
`def:spcc`, and `def:ent`.

Blueprint node: `F04A-GAME-SEMANTICS`.
-/

open scoped BigOperators MatrixOrder Matrix ComplexOrder ENNReal

namespace MIPStarRE.QPBT

universe uQuestionA uQuestionB uOutcomeA uOutcomeB uAlice uBob uCoord

/-- A finite two-player one-round game.

Paper source: Definition `def:game`.
-/
structure FiniteGame
    (QuestionA : Type uQuestionA) (QuestionB : Type uQuestionB)
    (OutcomeA : Type uOutcomeA) (OutcomeB : Type uOutcomeB)
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB] where
  questionDistribution : PMF (QuestionA × QuestionB)
  accepts : QuestionA -> QuestionB -> OutcomeA -> OutcomeB -> Bool

/-- The data-free, game-indexed wrapper around a finite pure strategy.

Paper source: Definition `def:tensor-product-strategy`.
-/
structure FiniteGameStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (Alice : Type uAlice) (Bob : Type uBob)
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob] where
  toPureStrategy :
    PureStrategy QuestionA QuestionB OutcomeA OutcomeB Alice Bob

/-- The tensor-product success value of one strategy in a finite game.

Paper source: Definition `def:tensor-product-value`.
-/
noncomputable def strategyValue
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteGameStrategy G Alice Bob) : Real :=
  ∑ x, ∑ y, (G.questionDistribution (x, y)).toReal *
    ∑ a, ∑ b,
        if G.accepts x y a b then
          Complex.re (inner Complex S.toPureStrategy.state
            (operatorAction
              (aliceLocal (Bob := Bob) ((S.toPureStrategy.alice x).effect a) *
                bobLocal (Alice := Alice) ((S.toPureStrategy.bob y).effect b))
              S.toPureStrategy.state))
        else 0

/-- The strategy succeeds with probability at least `nu`.

Paper source: Definition `def:tensor-product-value`.
-/
def StrategyWinsWithProbability
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteGameStrategy G Alice Bob) (nu : Real) : Prop :=
  strategyValue G S >= nu

/-- Every Alice and Bob measurement in the strategy is projective.

Paper source: Definition `def:projective-strategy`.
-/
def ProjectiveStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    {G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB}
    (S : FiniteGameStrategy G Alice Bob) : Prop :=
  ProjectiveMeasurementFamily S.toPureStrategy.alice ∧
    ProjectiveMeasurementFamily S.toPureStrategy.bob

/-- Alice's and Bob's effects commute on the support of the question PMF.

Paper source: Definition `def:comm-strategy`.
-/
def SupportCommutingStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Coord : Type uCoord}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Coord] [DecidableEq Coord]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteGameStrategy G Coord Coord) : Prop :=
  forall x y, G.questionDistribution (x, y) != 0 -> forall a b,
    (S.toPureStrategy.alice x).effect a * (S.toPureStrategy.bob y).effect b =
      (S.toPureStrategy.bob y).effect b * (S.toPureStrategy.alice x).effect a

/-- Every measurement family is consistent on the shared bipartite state.

Paper source: Definitions `def:consistent-measurement` and
`def:consistent-strategy`.
-/
def ConsistentStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Coord : Type uCoord}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Coord] [DecidableEq Coord]
    {G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB}
    (S : FiniteGameStrategy G Coord Coord) : Prop :=
  (forall x, MeasurementConsistentOn S.toPureStrategy.state
      (S.toPureStrategy.alice x)) ∧
    forall y, MeasurementConsistentOn S.toPureStrategy.state
      (S.toPureStrategy.bob y)

/-- A projective, consistent, support-commuting strategy.

Paper source: Definition `def:spcc`.
-/
def PCCStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Coord : Type uCoord}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Coord] [DecidableEq Coord]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteGameStrategy G Coord Coord) : Prop :=
  ProjectiveStrategy S ∧ ConsistentStrategy S ∧ SupportCommutingStrategy G S

/-- Symmetry of a game under exchanging the two players.

Paper source: Definition `rem:symmetric-games`.
-/
def SymmetricGame
    {Question : Type uQuestionA} {Outcome : Type uOutcomeA}
    [Fintype Question] [DecidableEq Question]
    [Fintype Outcome] [DecidableEq Outcome]
    (G : FiniteGame Question Question Outcome Outcome) : Prop :=
  (forall x y, G.questionDistribution (x, y) =
      G.questionDistribution (y, x)) ∧
    forall x y a b, G.accepts x y a b = G.accepts y x b a

/-- Symmetry of the state and measurement operators under exchanging players.

Paper source: Definition `rem:symmetric-games`.
-/
def SymmetricStrategy
    {Question : Type uQuestionA} {Outcome : Type uOutcomeA}
    {Coord : Type uCoord}
    [Fintype Question] [DecidableEq Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    {G : FiniteGame Question Question Outcome Outcome}
    (S : FiniteGameStrategy G Coord Coord) : Prop :=
  (forall i j, S.toPureStrategy.state (i, j) =
      S.toPureStrategy.state (j, i)) ∧
    forall x a, (S.toPureStrategy.alice x).effect a =
      (S.toPureStrategy.bob x).effect a

/-- A symmetric projective, consistent, support-commuting strategy.

Paper source: Definition `def:spcc`.
-/
def SPCCStrategy
    {Question : Type uQuestionA} {Outcome : Type uOutcomeA}
    {Coord : Type uCoord}
    [Fintype Question] [DecidableEq Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (G : FiniteGame Question Question Outcome Outcome)
    (S : FiniteGameStrategy G Coord Coord) : Prop :=
  PCCStrategy G S ∧ SymmetricStrategy S

/-- Canonical representatives of all finite-dimensional strategies for `G`. -/
abbrev FiniteDimensionalGameStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB) :=
  Sigma fun aliceDim : Nat => Sigma fun bobDim : Nat =>
    FiniteGameStrategy G (Fin aliceDim) (Fin bobDim)

/-- The value of a canonical finite-dimensional game strategy. -/
noncomputable def FiniteDimensionalGameStrategy.value
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteDimensionalGameStrategy G) : Real :=
  strategyValue G S.2.2

/-- The supremum of success values over all finite-dimensional strategies.

Paper source: Definition `def:tensor-product-value`.
-/
noncomputable def gameValue
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB) : Real :=
  sSup (Set.range (FiniteDimensionalGameStrategy.value G))

/-- The Schmidt rank of a state, defined as its coefficient-matrix rank.

Paper source: discussion preceding Definition `def:ent`.
-/
noncomputable def schmidtRank
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Alice] [Fintype Bob]
    (psi : EuclideanSpace Complex (Alice × Bob)) : Nat :=
  Matrix.rank (fun i j => psi (i, j))

/-- The Schmidt rank of a canonical finite-dimensional game strategy. -/
noncomputable def FiniteDimensionalGameStrategy.schmidtRank
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    {G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB}
    (S : FiniteDimensionalGameStrategy G) : Nat :=
  MIPStarRE.QPBT.schmidtRank S.2.2.toPureStrategy.state

/-- The least Schmidt-rank bound attaining `nu`, or infinity if none exists.

Paper source: Definition `def:ent`.
-/
noncomputable def entanglementRequirement
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (nu : Set.Icc (0 : Real) 1) : WithTop Nat :=
  sInf {d : WithTop Nat | exists S : FiniteDimensionalGameStrategy G,
    FiniteDimensionalGameStrategy.value G S >= (nu : Real) ∧
      (FiniteDimensionalGameStrategy.schmidtRank S : WithTop Nat) <= d}

/-- A value-one PCC strategy in a common canonical finite dimension. -/
def HasValueOnePCCStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB) : Prop :=
  exists dim : Nat, exists S : FiniteGameStrategy G (Fin dim) (Fin dim),
    PCCStrategy G S ∧ strategyValue G S = 1

end MIPStarRE.QPBT
