import Mathlib.FieldTheory.Finite.Trace
import Mathlib.FieldTheory.Galois.NormalBasis

/-!
# Finite-field data for the quantum Pauli basis test

This module exposes the concrete characteristic-two field and the callable
coordinate/multiplication interface used by the QPBT layers.  The simultaneous
self-dual normal-basis construction is the tracked `G16` proof gap; its public
selector remains source-faithful and accepts only an odd extension exponent.
-/

namespace MIPStarRE.QPBT

structure FieldData (k : Nat) where
  basis : Module.Basis (Fin k) (ZMod 2) (GaloisField 2 k)
  generator : GaloisField 2 k
  normal : forall i, basis i = generator ^ (2 ^ (i : Nat))
  selfDual : forall i j,
    Algebra.trace (ZMod 2) (GaloisField 2 k) (basis i * basis j) =
      if i = j then 1 else 0

/- The simultaneous self-dual-normal basis existence theorem is G16. -/
noncomputable def fieldDataOfOddExponent
    (k : Nat) (hk : Odd k) : FieldData k := by
  sorry

theorem fieldData_nonempty_of_odd
    (k : Nat) (hk : Odd k) : Nonempty (FieldData k) :=
  ⟨fieldDataOfOddExponent k hk⟩

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
      D.coordinates (a * b) := by
  simpa [FieldData.multiplicationMatrix, FieldData.coordinates] using
    (LinearMap.toMatrix_mulVec_repr D.basis D.basis
      (Algebra.lmul (ZMod 2) (GaloisField 2 k) a) b)

end MIPStarRE.QPBT
