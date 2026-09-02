import MIPStarRE.QPBT.Basic.Field

/-!
# Admissible parameters for the quantum Pauli basis test

This module records the project-owned parameter tuple and the source-faithful
admissibility predicate for the Pauli basis test.

Source: `references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex:60-63`,
`def:admissible`.
-/

namespace MIPStarRE.QPBT

/-- The natural-valued parameter tuple `(q, m, d)` of the Pauli basis test. -/
structure Parameters where
  q : Nat
  m : Nat
  d : Nat
  deriving DecidableEq

/-- A parameter tuple is admissible exactly when its field-size exponent is odd,
its field size is the corresponding power of two, and `m` divides `q`.

Source label: `def:admissible`.
-/
def Parameters.Admissible (params : Parameters) : Prop :=
  Exists fun k : Nat =>
    Odd k ∧ params.q = 2 ^ k ∧ Dvd.dvd params.m params.q

end MIPStarRE.QPBT
