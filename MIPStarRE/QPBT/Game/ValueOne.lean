import MIPStarRE.QPBT.Game.Semantics

/-!
# Outcome weights and value-one strategies

This module isolates the finite Born weights implicit in `strategyValue`, proves
that they form a normalized distribution for every bundled finite strategy,
and packages the generic value-one criterion used by the Magic Square
construction.

Paper source: `magic-square.tex:335-367` (the final perfect-strategy argument).
Blueprint node: `F08-MAGIC-GAME`.
-/

open scoped BigOperators MatrixOrder Matrix ComplexOrder ENNReal

namespace MIPStarRE.QPBT

universe uQuestionA uQuestionB uOutcomeA uOutcomeB uAlice uBob

private noncomputable def strategyOutcomeOperator
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
    (S : FiniteGameStrategy G Alice Bob)
    (x : QuestionA) (y : QuestionB) (a : OutcomeA) (b : OutcomeB) :
    MIPStarRE.Quantum.Op (Alice × Bob) :=
  aliceLocal (Bob := Bob) ((S.toPureStrategy.alice x).effect a) *
    bobLocal (Alice := Alice) ((S.toPureStrategy.bob y).effect b)

/-- The Born weight of an answer pair for fixed questions and a finite strategy. -/
noncomputable def strategyOutcomeWeight
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
    (S : FiniteGameStrategy G Alice Bob)
    (x : QuestionA) (y : QuestionB) (a : OutcomeA) (b : OutcomeB) : Real :=
  Complex.re (inner Complex S.toPureStrategy.state
    (operatorAction (strategyOutcomeOperator S x y a b)
      S.toPureStrategy.state))

/-- Every answer-pair Born weight is nonnegative. -/
theorem strategyOutcomeWeight_nonneg
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
    (S : FiniteGameStrategy G Alice Bob)
    (x : QuestionA) (y : QuestionB) (a : OutcomeA) (b : OutcomeB) :
    0 ≤ strategyOutcomeWeight S x y a b := by
  let A := (S.toPureStrategy.alice x).effect a
  let B := (S.toPureStrategy.bob y).effect b
  have hA : Matrix.PosSemidef A :=
    Matrix.nonneg_iff_posSemidef.mp ((S.toPureStrategy.alice x).pos a)
  have hB : Matrix.PosSemidef B :=
    Matrix.nonneg_iff_posSemidef.mp ((S.toPureStrategy.bob y).pos b)
  have hAB : Matrix.PosSemidef (Matrix.kronecker A B) :=
    hA.kronecker hB
  have hop : strategyOutcomeOperator S x y a b = Matrix.kronecker A B := by
    simp only [strategyOutcomeOperator, aliceLocal, bobLocal, A, B, Matrix.kronecker]
    rw [← Matrix.mul_kronecker_mul]
    simp
  have hpositive :
      (Matrix.toEuclideanLin (strategyOutcomeOperator S x y a b)).IsPositive := by
    rw [Matrix.isPositive_toEuclideanLin_iff, hop]
    exact hAB
  simpa only [strategyOutcomeWeight, operatorAction, RCLike.re_to_complex] using
    hpositive.re_inner_nonneg_right S.toPureStrategy.state

private theorem sum_strategyOutcomeOperator
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
    (S : FiniteGameStrategy G Alice Bob) (x : QuestionA) (y : QuestionB) :
    (∑ a, ∑ b, strategyOutcomeOperator S x y a b) = 1 := by
  calc
    (∑ a, ∑ b, strategyOutcomeOperator S x y a b) =
        ∑ a, ∑ b, MIPStarRE.LDT.opTensor
          ((S.toPureStrategy.alice x).effect a)
          ((S.toPureStrategy.bob y).effect b) := by
      apply Finset.sum_congr rfl
      intro a _
      apply Finset.sum_congr rfl
      intro b _
      rw [← MIPStarRE.LDT.leftTensor_mul_rightTensor_eq_opTensor]
      rfl
    _ = MIPStarRE.LDT.opTensor
        (∑ a, (S.toPureStrategy.alice x).effect a)
        (∑ b, (S.toPureStrategy.bob y).effect b) := by
      rw [MIPStarRE.LDT.opTensor_sum_left_univ]
      apply Finset.sum_congr rfl
      intro a _
      rw [MIPStarRE.LDT.opTensor_sum_right_univ]
    _ = 1 := by
      rw [(S.toPureStrategy.alice x).sum_eq_one,
        (S.toPureStrategy.bob y).sum_eq_one]
      simp [MIPStarRE.LDT.opTensor]

/-- For fixed questions, the answer-pair Born weights sum exactly to one. -/
theorem sum_strategyOutcomeWeight
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
    (S : FiniteGameStrategy G Alice Bob) (x : QuestionA) (y : QuestionB) :
    (∑ a, ∑ b, strategyOutcomeWeight S x y a b) = 1 := by
  let psi := S.toPureStrategy.state
  have haction :
      (∑ a, ∑ b, operatorAction (strategyOutcomeOperator S x y a b) psi) = psi := by
    calc
      (∑ a, ∑ b, operatorAction (strategyOutcomeOperator S x y a b) psi) =
          operatorAction (∑ a, ∑ b, strategyOutcomeOperator S x y a b) psi := by
        simp [operatorAction, Matrix.toLpLin_apply, Matrix.sum_mulVec]
      _ = operatorAction 1 psi := by rw [sum_strategyOutcomeOperator]
      _ = psi := by simp [operatorAction, Matrix.toLpLin_apply]
  calc
    (∑ a, ∑ b, strategyOutcomeWeight S x y a b) =
        Complex.re (inner Complex psi
          (∑ a, ∑ b, operatorAction (strategyOutcomeOperator S x y a b) psi)) := by
      simp only [strategyOutcomeWeight, psi, inner_sum, Complex.re_sum]
    _ = Complex.re (inner Complex psi psi) := by rw [haction]
    _ = 1 := by
      rw [inner_self_eq_one_of_norm_eq_one S.toPureStrategy.normalized]
      norm_num

/--
A strategy has value one when every rejected answer tuple of every question in
the PMF support has zero Born weight.

This is the generic final step used by the perfect Magic Square strategy in
`magic-square.tex:335-367`; it adds no value-one or normalization premise.
-/
theorem strategyValue_eq_one_of_rejected_weight_eq_zero
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
    (S : FiniteGameStrategy G Alice Bob)
    (hreject : ∀ x y a b,
      G.questionDistribution (x, y) ≠ 0 →
      G.accepts x y a b = false →
      strategyOutcomeWeight S x y a b = 0) :
    strategyValue G S = 1 := by
  classical
  calc
    strategyValue G S =
        ∑ x, ∑ y, (G.questionDistribution (x, y)).toReal *
          ∑ a, ∑ b, strategyOutcomeWeight S x y a b := by
      unfold strategyValue
      apply Finset.sum_congr rfl
      intro x _
      apply Finset.sum_congr rfl
      intro y _
      by_cases hxy : G.questionDistribution (x, y) = 0
      · simp [hxy]
      · congr 1
        apply Finset.sum_congr rfl
        intro a _
        apply Finset.sum_congr rfl
        intro b _
        by_cases hab : G.accepts x y a b = true
        · simp [hab, strategyOutcomeWeight, strategyOutcomeOperator]
        · have hab' : G.accepts x y a b = false := Bool.eq_false_of_not_eq_true hab
          simp [hab', hreject x y a b hxy hab']
    _ = ∑ x, ∑ y, (G.questionDistribution (x, y)).toReal := by
      simp_rw [sum_strategyOutcomeWeight, mul_one]
    _ = ∑ xy : QuestionA × QuestionB,
        (G.questionDistribution xy).toReal := by
      rw [Fintype.sum_prod_type]
    _ = (∑ xy : QuestionA × QuestionB,
        G.questionDistribution xy).toReal := by
      rw [ENNReal.toReal_sum]
      exact fun xy _ => G.questionDistribution.apply_ne_top xy
    _ = (∑' xy : QuestionA × QuestionB,
        G.questionDistribution xy).toReal := by rw [tsum_fintype]
    _ = 1 := by rw [G.questionDistribution.tsum_coe]; norm_num

end MIPStarRE.QPBT
