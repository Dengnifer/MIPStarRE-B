import Mathlib.Analysis.Asymptotics.Defs
import Mathlib.Probability.ProbabilityMassFunction.Constructions
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
