import MIPStarRE.QPBT.Game.Semantics
import MIPStarRE.QPBT.Game.Types

/-!
# The finite Magic Square game

This file formalizes the finite question and answer alphabets, type graph, and
acceptance predicate of the Magic Square game used by the quantum Pauli basis
test.

Paper source: `magic-square.tex:11-100`, label `sec:ms`.
Blueprint node: `F08-MAGIC-GAME`.
-/

open scoped BigOperators

namespace MIPStarRE.QPBT

/-- The six constraint questions and nine variable questions of the Magic
Square game. -/
inductive MagicSquareQuestionType
  | constraint (i : Fin 6)
  | variable (j : Fin 9)
  deriving DecidableEq, Fintype

/-- The Magic Square question alphabet contains six constraint tags and nine
variable tags. -/
theorem magicSquareQuestionType_card :
    Fintype.card MagicSquareQuestionType = 15 := by
  native_decide

namespace MagicSquare

/-- The variable in `slot` of a constraint. Constraints zero through two are
rows; constraints three through five are columns. -/
def variableAt (i : Fin 6) (slot : Fin 3) : Fin 9 :=
  if h : i.val < 3 then
    ⟨3 * i.val + slot.val, by omega⟩
  else
    ⟨i.val - 3 + 3 * slot.val, by omega⟩

/-- The first five constraints have even parity and the final column has odd
parity. -/
def targetParity (i : Fin 6) : ZMod 2 :=
  if i.val = 5 then 1 else 0

/-- The answer type depends on whether the player receives a constraint or a
single variable. -/
def AnswerFiber : MagicSquareQuestionType -> Type
  | .constraint _ => Fin 3 -> ZMod 2
  | .variable _ => ZMod 2

instance (t : MagicSquareQuestionType) : Fintype (AnswerFiber t) := by
  cases t <;> simp [AnswerFiber] <;> infer_instance

instance (t : MagicSquareQuestionType) : DecidableEq (AnswerFiber t) := by
  cases t <;> simp [AnswerFiber] <;> infer_instance

/-- The uniform answer alphabet used by the finite-game interface. -/
abbrev Answer := Sigma AnswerFiber

/-- Inject an answer from a question-indexed fiber into the uniform alphabet. -/
def Answer.encode {t : MagicSquareQuestionType} (a : AnswerFiber t) : Answer :=
  ⟨t, a⟩

/-- Decode a uniform answer at an expected question tag. A mismatched tag is
rejected instead of being assigned a default answer. -/
def Answer.decode (t : MagicSquareQuestionType) : Answer -> Option (AnswerFiber t)
  | ⟨u, a⟩ => if h : u = t then some (h ▸ a) else none

@[simp] theorem Answer.decode_encode {t : MagicSquareQuestionType}
    (a : AnswerFiber t) : Answer.decode t (Answer.encode a) = some a := by
  simp [Answer.decode, Answer.encode]

theorem Answer.encode_injective (t : MagicSquareQuestionType) :
    Function.Injective (@Answer.encode t) := by
  intro a b h
  have := congrArg (Answer.decode t) h
  simpa using this

theorem Answer.decode_eq_some_iff {t : MagicSquareQuestionType}
    (answer : Answer) (a : AnswerFiber t) :
    Answer.decode t answer = some a ↔ answer = Answer.encode a := by
  rcases answer with ⟨u, b⟩
  by_cases h : u = t
  · subst u
    simp [Answer.decode, Answer.encode]
  · simp [Answer.decode, Answer.encode, h]

theorem Answer.decode_eq_none_iff (t : MagicSquareQuestionType)
    (answer : Answer) :
    Answer.decode t answer = none ↔ answer.1 ≠ t := by
  rcases answer with ⟨u, b⟩
  simp [Answer.decode]

@[simp] theorem variableAt_val_of_row (i : Fin 6) (slot : Fin 3)
    (hi : i.val < 3) :
    (variableAt i slot).val = 3 * i.val + slot.val := by
  simp [variableAt, hi]

@[simp] theorem variableAt_val_of_column (i : Fin 6) (slot : Fin 3)
    (hi : ¬i.val < 3) :
    (variableAt i slot).val = i.val - 3 + 3 * slot.val := by
  simp [variableAt, hi]

/-- Each constraint contains three distinct variables. -/
theorem variableAt_injective :
    ∀ i : Fin 6, Function.Injective (variableAt i) := by
  native_decide

/-- The zero-based row/column formula agrees with all eighteen incidences in
Figure `fig:type-graph-ms`. -/
theorem variableAt_exhaustive_table :
    (List.ofFn (fun s : Fin 3 => (variableAt 0 s).val) = [0, 1, 2]) ∧
    (List.ofFn (fun s : Fin 3 => (variableAt 1 s).val) = [3, 4, 5]) ∧
    (List.ofFn (fun s : Fin 3 => (variableAt 2 s).val) = [6, 7, 8]) ∧
    (List.ofFn (fun s : Fin 3 => (variableAt 3 s).val) = [0, 3, 6]) ∧
    (List.ofFn (fun s : Fin 3 => (variableAt 4 s).val) = [1, 4, 7]) ∧
    (List.ofFn (fun s : Fin 3 => (variableAt 5 s).val) = [2, 5, 8]) := by
  native_decide

@[simp] theorem targetParity_eq_one_iff :
    ∀ i : Fin 6, targetParity i = 1 ↔ i.val = 5 := by
  native_decide

@[simp] theorem targetParity_eq_zero_iff :
    ∀ i : Fin 6, targetParity i = 0 ↔ i.val ≠ 5 := by
  native_decide

/-- Acceptance of a correctly typed constraint-variable incidence. -/
def incidenceAccepts (i : Fin 6) (slot : Fin 3)
    (constraintAnswer : AnswerFiber (.constraint i))
    (variableAnswer : AnswerFiber (.variable (variableAt i slot))) : Bool :=
  decide ((∑ s : Fin 3, constraintAnswer s) = targetParity i) &&
    decide (constraintAnswer slot = variableAnswer)

@[simp] theorem incidenceAccepts_eq_true_iff (i : Fin 6) (slot : Fin 3)
    (constraintAnswer : AnswerFiber (.constraint i))
    (variableAnswer : AnswerFiber (.variable (variableAt i slot))) :
    incidenceAccepts i slot constraintAnswer variableAnswer = true ↔
      (∑ s : Fin 3, constraintAnswer s) = targetParity i ∧
        constraintAnswer slot = variableAnswer := by
  simp [incidenceAccepts]

/-- A source occurrence for one of the 36 oriented edges. -/
inductive OrientedIncidence
  | forward (constraint : Fin 6) (slot : Fin 3)
  | reverse (constraint : Fin 6) (slot : Fin 3)
  deriving DecidableEq, Fintype

/-- Interpret an oriented incidence as an ordered pair of question tags. -/
def OrientedIncidence.endpoints :
    OrientedIncidence -> MagicSquareQuestionType × MagicSquareQuestionType
  | .forward i slot => (.constraint i, .variable (variableAt i slot))
  | .reverse i slot => (.variable (variableAt i slot), .constraint i)

/-- Reversing an incidence exchanges its endpoints. -/
def OrientedIncidence.flip : OrientedIncidence -> OrientedIncidence
  | .forward i slot => .reverse i slot
  | .reverse i slot => .forward i slot

@[simp] theorem OrientedIncidence.endpoints_reverse (edge : OrientedIncidence) :
    edge.flip.endpoints = edge.endpoints.swap := by
  cases edge <;> rfl

theorem OrientedIncidence.endpoints_injective :
    Function.Injective OrientedIncidence.endpoints := by
  native_decide

/-- The exact 36-element ordered support of the game. -/
def orderedIncidences :
    Finset (MagicSquareQuestionType × MagicSquareQuestionType) :=
  Finset.univ.image OrientedIncidence.endpoints

theorem mem_orderedIncidences_iff :
    ∀ left right : MagicSquareQuestionType,
    (left, right) ∈ orderedIncidences ↔
      ∃ i : Fin 6, ∃ slot : Fin 3,
        (left = .constraint i ∧ right = .variable (variableAt i slot)) ∨
        (left = .variable (variableAt i slot) ∧ right = .constraint i) := by
  native_decide

theorem orderedIncidences_card : orderedIncidences.card = 36 := by
  native_decide

/-- Before orientation, the graph has six constraints with three incidences
each. -/
theorem incidences_card :
    (Finset.univ : Finset (Fin 6 × Fin 3)).card = 18 := by
  native_decide

theorem orderedIncidences_symmetric :
    ∀ left right : MagicSquareQuestionType,
    (left, right) ∈ orderedIncidences ↔ (right, left) ∈ orderedIncidences := by
  native_decide

/-- Every variable occurs in exactly one row and one column. -/
theorem variable_incidence_card : ∀ j : Fin 9,
    (Finset.univ.filter fun edge : Fin 6 × Fin 3 =>
      variableAt edge.1 edge.2 = j).card = 2 := by
  native_decide

end MagicSquare

/-- Compatibility aliases for the blueprint's top-level finite alphabet. -/
abbrev MagicSquareAnswerFiber := MagicSquare.AnswerFiber
abbrev MagicSquareAnswer := MagicSquare.Answer

instance : Fintype MagicSquareAnswer := inferInstance
instance : DecidableEq MagicSquareAnswer := inferInstance

/-- The global answer alphabet has six eight-element fibers and nine
two-element fibers. -/
theorem magicSquareAnswer_card : Fintype.card MagicSquareAnswer = 66 := by
  native_decide

namespace MagicSquareAnswer

/-- Compatibility spelling for injecting an indexed answer into the global
Magic Square answer alphabet. -/
def encode {t : MagicSquareQuestionType}
    (answer : MagicSquareAnswerFiber t) : MagicSquareAnswer :=
  MagicSquare.Answer.encode answer

/-- Compatibility spelling for fail-closed decoding at an expected tag. -/
def decode (t : MagicSquareQuestionType) :
    MagicSquareAnswer -> Option (MagicSquareAnswerFiber t) :=
  MagicSquare.Answer.decode t

@[simp] theorem decode_encode {t : MagicSquareQuestionType}
    (answer : MagicSquareAnswerFiber t) :
    decode t (encode answer) = some answer := by
  exact MagicSquare.Answer.decode_encode answer

theorem encode_injective (t : MagicSquareQuestionType) :
    Function.Injective (@encode t) := by
  exact MagicSquare.Answer.encode_injective t

theorem decode_eq_some_iff {t : MagicSquareQuestionType}
    (answer : MagicSquareAnswer) (value : MagicSquareAnswerFiber t) :
    decode t answer = some value ↔ answer = encode value := by
  exact MagicSquare.Answer.decode_eq_some_iff answer value

theorem decode_eq_none_iff (t : MagicSquareQuestionType)
    (answer : MagicSquareAnswer) :
    decode t answer = none ↔ answer.1 ≠ t := by
  exact MagicSquare.Answer.decode_eq_none_iff t answer

end MagicSquareAnswer

/-- The symmetric type graph containing both orientations of all eighteen
constraint-variable incidences. -/
def magicSquareGraph : TypeGraph MagicSquareQuestionType where
  orderedEdges := MagicSquare.orderedIncidences
  symmetric := MagicSquare.orderedIncidences_symmetric
  nonempty := by native_decide

theorem magicSquareGraph_mem_iff (left right : MagicSquareQuestionType) :
    (left, right) ∈ magicSquareGraph.orderedEdges ↔
      ∃ i : Fin 6, ∃ slot : Fin 3,
        (left = .constraint i ∧
            right = .variable (MagicSquare.variableAt i slot)) ∨
        (left = .variable (MagicSquare.variableAt i slot) ∧
            right = .constraint i) := by
  exact MagicSquare.mem_orderedIncidences_iff left right

theorem magicSquareGraph_orderedEdges_card :
    magicSquareGraph.orderedEdges.card = 36 := by
  exact MagicSquare.orderedIncidences_card

@[simp] theorem magicSquareGraph_distribution_apply
    (left right : MagicSquareQuestionType) :
    magicSquareGraph.distribution (left, right) =
      if (left, right) ∈ magicSquareGraph.orderedEdges
      then (36 : ENNReal)⁻¹ else 0 := by
  simpa [magicSquareGraph_orderedEdges_card] using
    TypeGraph.distribution_apply magicSquareGraph left right

theorem magicSquareGraph_distribution_ne_zero_iff
    (left right : MagicSquareQuestionType) :
    magicSquareGraph.distribution (left, right) ≠ 0 ↔
      (left, right) ∈ magicSquareGraph.orderedEdges := by
  simp [magicSquareGraph_distribution_apply]

/-- Find the unique slot witnessing that a variable belongs to a constraint. -/
def MagicSquare.incidentSlot? (i : Fin 6) (j : Fin 9) : Option (Fin 3) :=
  Fin.find? fun slot : Fin 3 => decide (MagicSquare.variableAt i slot = j)

theorem MagicSquare.incidentSlot?_eq_some_iff :
    ∀ (i : Fin 6) (j : Fin 9) (slot : Fin 3),
    MagicSquare.incidentSlot? i j = some slot ↔
      MagicSquare.variableAt i slot = j := by
  native_decide

theorem MagicSquare.incidentSlot?_eq_none_iff :
    ∀ (i : Fin 6) (j : Fin 9),
    MagicSquare.incidentSlot? i j = none ↔
      ∀ slot : Fin 3, MagicSquare.variableAt i slot ≠ j := by
  native_decide

private def magicSquareAcceptsForward (i : Fin 6) (j : Fin 9)
    (constraintAnswer : MagicSquare.AnswerFiber (.constraint i))
    (variableAnswer : MagicSquare.AnswerFiber (.variable j)) : Bool :=
  match MagicSquare.incidentSlot? i j with
  | none => false
  | some slot =>
      MagicSquare.incidenceAccepts i slot constraintAnswer variableAnswer

private def magicSquareAcceptsAtQuestions (i : Fin 6) (j : Fin 9)
    (constraintAnswer variableAnswer : MagicSquareAnswer) : Bool :=
  match MagicSquare.Answer.decode (.constraint i) constraintAnswer,
      MagicSquare.Answer.decode (.variable j) variableAnswer with
  | some a, some b => magicSquareAcceptsForward i j a b
  | _, _ => false

/-- The total, fail-closed verifier predicate. Both answers are decoded at
their actual question tags; unsupported pairs and tag mismatches reject. -/
def magicSquareAccepts
    (left right : MagicSquareQuestionType)
    (leftAnswer rightAnswer : MagicSquareAnswer) : Bool :=
  match left, right with
  | .constraint i, .variable j =>
      magicSquareAcceptsAtQuestions i j leftAnswer rightAnswer
  | .variable j, .constraint i =>
      magicSquareAcceptsAtQuestions i j rightAnswer leftAnswer
  | _, _ => false

@[simp] theorem magicSquareAccepts_forward
    (i : Fin 6) (slot : Fin 3)
    (constraintAnswer : MagicSquare.AnswerFiber (.constraint i))
    (variableAnswer :
      MagicSquare.AnswerFiber (.variable (MagicSquare.variableAt i slot))) :
    magicSquareAccepts (.constraint i)
        (.variable (MagicSquare.variableAt i slot))
        (MagicSquare.Answer.encode constraintAnswer)
        (MagicSquare.Answer.encode variableAnswer) =
      MagicSquare.incidenceAccepts i slot constraintAnswer variableAnswer := by
  have hslot : MagicSquare.incidentSlot? i (MagicSquare.variableAt i slot) =
      some slot :=
    (MagicSquare.incidentSlot?_eq_some_iff i
      (MagicSquare.variableAt i slot) slot).2 rfl
  simp [magicSquareAccepts, magicSquareAcceptsAtQuestions,
    magicSquareAcceptsForward, hslot]

@[simp] theorem magicSquareAccepts_reverse
    (i : Fin 6) (slot : Fin 3)
    (constraintAnswer : MagicSquare.AnswerFiber (.constraint i))
    (variableAnswer :
      MagicSquare.AnswerFiber (.variable (MagicSquare.variableAt i slot))) :
    magicSquareAccepts (.variable (MagicSquare.variableAt i slot))
        (.constraint i)
        (MagicSquare.Answer.encode variableAnswer)
        (MagicSquare.Answer.encode constraintAnswer) =
      MagicSquare.incidenceAccepts i slot constraintAnswer variableAnswer := by
  have hslot : MagicSquare.incidentSlot? i (MagicSquare.variableAt i slot) =
      some slot :=
    (MagicSquare.incidentSlot?_eq_some_iff i
      (MagicSquare.variableAt i slot) slot).2 rfl
  simp [magicSquareAccepts, magicSquareAcceptsAtQuestions,
    magicSquareAcceptsForward, hslot]

theorem magicSquareAccepts_eq_false_of_left_decode_none :
    ∀ (left right : MagicSquareQuestionType)
      (leftAnswer rightAnswer : MagicSquareAnswer),
    MagicSquare.Answer.decode left leftAnswer = none →
    magicSquareAccepts left right leftAnswer rightAnswer = false := by
  native_decide

theorem magicSquareAccepts_eq_false_of_right_decode_none :
    ∀ (left right : MagicSquareQuestionType)
      (leftAnswer rightAnswer : MagicSquareAnswer),
    MagicSquare.Answer.decode right rightAnswer = none →
    magicSquareAccepts left right leftAnswer rightAnswer = false := by
  native_decide

theorem magicSquareAccepts_eq_false_of_not_mem :
    ∀ (left right : MagicSquareQuestionType)
      (leftAnswer rightAnswer : MagicSquareAnswer),
    (left, right) ∉ magicSquareGraph.orderedEdges →
    magicSquareAccepts left right leftAnswer rightAnswer = false := by
  native_decide

@[simp] theorem magicSquareAccepts_constraint_constraint
    (i i' : Fin 6) (leftAnswer rightAnswer : MagicSquareAnswer) :
    magicSquareAccepts (.constraint i) (.constraint i')
      leftAnswer rightAnswer = false := rfl

@[simp] theorem magicSquareAccepts_variable_variable
    (j j' : Fin 9) (leftAnswer rightAnswer : MagicSquareAnswer) :
    magicSquareAccepts (.variable j) (.variable j')
      leftAnswer rightAnswer = false := rfl

theorem magicSquareAccepts_symmetric
    (left right : MagicSquareQuestionType)
    (leftAnswer rightAnswer : MagicSquareAnswer) :
    magicSquareAccepts left right leftAnswer rightAnswer =
      magicSquareAccepts right left rightAnswer leftAnswer := by
  cases left <;> cases right <;> simp only [magicSquareAccepts]

/-- The Magic Square game with the uniform distribution on its 36 oriented
constraint-variable incidences. -/
noncomputable def magicSquareGame :
    FiniteGame MagicSquareQuestionType MagicSquareQuestionType
      MagicSquareAnswer MagicSquareAnswer where
  questionDistribution := magicSquareGraph.distribution
  accepts := magicSquareAccepts

/-- The finite Magic Square game is symmetric under exchanging the players. -/
theorem magicSquareGame_symmetric : SymmetricGame magicSquareGame := by
  constructor
  · intro left right
    change magicSquareGraph.distribution (left, right) =
      magicSquareGraph.distribution (right, left)
    rw [magicSquareGraph_distribution_apply,
      magicSquareGraph_distribution_apply]
    simp only [magicSquareGraph.symmetric]
  · intro left right leftAnswer rightAnswer
    change magicSquareAccepts left right leftAnswer rightAnswer =
      magicSquareAccepts right left rightAnswer leftAnswer
    exact magicSquareAccepts_symmetric left right leftAnswer rightAnswer

end MIPStarRE.QPBT
