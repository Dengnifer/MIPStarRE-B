import Mathlib.Analysis.Fourier.FiniteAbelian.Orthogonality
import Mathlib.Analysis.SpecialFunctions.Complex.CircleAddChar
import MIPStarRE.QPBT.Basic.Field
import MIPStarRE.QPBT.Basic.Approximation

/-!
# Generalized Pauli observables

This module formalizes the characteristic-two generalized Pauli observables,
their Fourier and computational projective measurements, and the corresponding
tensor-power identities from `pauli.tex:1-110`.

Paper equations: `eq:pauli-fp`, `eq:twisted-fq`, `eq:fourier-f`,
`eq:pauli-obs-proj-single`, `eq:pauli-inversion-0-single`,
`eq:pauli-obs-proj`, and `eq:pauli-inversion-0`.
-/

open scoped BigOperators MatrixOrder Matrix ComplexOrder

namespace MIPStarRE.QPBT

noncomputable local instance (k : Nat) : Fintype (GaloisField 2 k) :=
  Fintype.ofFinite (GaloisField 2 k)
noncomputable local instance (k : Nat) : DecidableEq (GaloisField 2 k) :=
  Classical.decEq (GaloisField 2 k)

private noncomputable def traceCharacter (k : Nat) (c : GaloisField 2 k) :
    AddChar (GaloisField 2 k) Complex :=
  ZMod.stdAddChar.compAddMonoidHom
    { toFun := fun x => fieldTrace k (c * x)
      map_zero' := by simp
      map_add' := by intro x y; simp [mul_add] }

private theorem fieldTrace_mul_nondegenerate (k : Nat)
    {c : GaloisField 2 k} (hc : c ≠ 0) :
    ∃ x : GaloisField 2 k, fieldTrace k (c * x) ≠ 0 := by
  by_contra! h
  apply hc
  have htr :=
    (traceForm_nondegenerate (ZMod 2) (GaloisField 2 k)).1 c
  simp_rw [Algebra.traceForm_apply] at htr
  exact htr (by simpa only [fieldTrace] using h)

private theorem traceCharacter_eq_zero_iff (k : Nat) (c : GaloisField 2 k) :
    traceCharacter k c = 0 ↔ c = 0 := by
  constructor
  · intro h
    by_contra hc
    obtain ⟨x, hx⟩ := fieldTrace_mul_nondegenerate k hc
    have happ := DFunLike.congr_fun h x
    have hphase :
        ZMod.stdAddChar (fieldTrace k (c * x)) =
          ZMod.stdAddChar (0 : ZMod 2) := by
      simpa [traceCharacter] using happ
    exact hx (ZMod.injective_stdAddChar hphase)
  · rintro rfl
    ext x
    simp [traceCharacter]

private theorem traceCharacter_expect (k : Nat) (c : GaloisField 2 k) :
    (∑ x, ZMod.stdAddChar (fieldTrace k (c * x))) /
        (Fintype.card (GaloisField 2 k) : Complex) =
      if c = 0 then 1 else 0 := by
  rw [← Fintype.expect_eq_sum_div_card]
  change Finset.univ.expect (traceCharacter k c) = _
  rw [AddChar.expect_eq_ite]
  simp only [traceCharacter_eq_zero_iff]

/-- The two Pauli measurement bases used by the QPBT. -/
inductive PauliBasis
  | X
  | Z
  deriving DecidableEq, Fintype

/-- The generalized Pauli shift `X(a)` on the computational basis. -/
noncomputable def pauliX (k : Nat) (a : GaloisField 2 k) :
    MIPStarRE.Quantum.Op (GaloisField 2 k) :=
  fun row column => if row = column + a then 1 else 0

/-- The generalized Pauli phase `Z(b)`, using the absolute field trace. -/
noncomputable def pauliZ (k : Nat) (b : GaloisField 2 k) :
    MIPStarRE.Quantum.Op (GaloisField 2 k) :=
  fun row column => if row = column then
    ZMod.stdAddChar (fieldTrace k (b * row)) else 0

/-- Select the generalized Pauli observable in basis `W`. -/
noncomputable def pauliObservable (k : Nat) (W : PauliBasis)
    (a : GaloisField 2 k) : MIPStarRE.Quantum.Op (GaloisField 2 k) :=
  match W with
  | .X => pauliX k a
  | .Z => pauliZ k a

private noncomputable def fourierVector (k : Nat) (b : GaloisField 2 k) :
    GaloisField 2 k -> Complex :=
  fun x => ZMod.stdAddChar (-(fieldTrace k (b * x)))

private noncomputable def computationalVector (k : Nat) (b : GaloisField 2 k) :
    GaloisField 2 k -> Complex :=
  fun x => if x = b then 1 else 0

private noncomputable def pauliProjectorEffect (k : Nat) (W : PauliBasis)
    (b : GaloisField 2 k) : MIPStarRE.Quantum.Op (GaloisField 2 k) :=
  match W with
  | .X => fun row column =>
      (Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
        ZMod.stdAddChar (fieldTrace k (b * (column - row)))
  | .Z => fun row column => if row = b ∧ column = b then 1 else 0

private theorem pauliProjectorEffect_pos (k : Nat) (W : PauliBasis)
    (b : GaloisField 2 k) : 0 ≤ pauliProjectorEffect k W b := by
  rw [Matrix.nonneg_iff_posSemidef]
  cases W with
  | X =>
      have heffect : pauliProjectorEffect k PauliBasis.X b =
          (Fintype.card (GaloisField 2 k) : Complex)⁻¹ •
            Matrix.vecMulVec (fourierVector k b) (star (fourierVector k b)) := by
        ext row column
        simp only [pauliProjectorEffect, Matrix.smul_apply, smul_eq_mul,
          Matrix.vecMulVec_apply, Pi.star_apply, fourierVector]
        have hconj :
            star (ZMod.stdAddChar (-(fieldTrace k (b * column)))) =
              ZMod.stdAddChar (fieldTrace k (b * column)) := by
          simpa only [Complex.star_def, neg_neg] using
            (AddChar.map_neg_eq_conj ZMod.stdAddChar
              (-(fieldTrace k (b * column)))).symm
        rw [hconj]
        rw [← AddChar.map_add_eq_mul]
        congr 2
        simp only [CharTwo.neg_eq, CharTwo.sub_eq_add, mul_add, map_add]
        ac_rfl
      rw [heffect]
      apply Matrix.PosSemidef.smul
        (Matrix.posSemidef_vecMulVec_self_star (fourierVector k b))
      positivity
  | Z =>
      have heffect : pauliProjectorEffect k PauliBasis.Z b =
          Matrix.vecMulVec (computationalVector k b) (star (computationalVector k b)) := by
        ext row column
        simp only [pauliProjectorEffect, Matrix.vecMulVec_apply, Pi.star_apply,
          computationalVector]
        by_cases hr : row = b <;> by_cases hc : column = b <;> simp [hr, hc]
      rw [heffect]
      exact Matrix.posSemidef_vecMulVec_self_star (computationalVector k b)

private theorem pauliProjectorEffect_sum (k : Nat) (W : PauliBasis) :
    ∑ b, pauliProjectorEffect k W b = 1 := by
  classical
  ext row column
  cases W with
  | Z =>
      by_cases h : row = column
      · subst column
        simp [pauliProjectorEffect, Matrix.sum_apply]
      · simp [pauliProjectorEffect, Matrix.sum_apply, h, Ne.symm h]
  | X =>
      rw [Matrix.one_apply]
      simp only [pauliProjectorEffect, Matrix.sum_apply]
      rw [← Finset.mul_sum]
      have horth := traceCharacter_expect k (column - row)
      rw [div_eq_mul_inv] at horth
      have hsum :
          (∑ i, ZMod.stdAddChar (fieldTrace k (i * (column - row)))) =
            ∑ i, ZMod.stdAddChar (fieldTrace k ((column - row) * i)) := by
        apply Finset.sum_congr rfl
        intro i _
        rw [mul_comm]
      rw [hsum]
      rw [show (Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
          ∑ x, ZMod.stdAddChar (fieldTrace k ((column - row) * x)) =
          (∑ x, ZMod.stdAddChar (fieldTrace k ((column - row) * x))) *
            (Fintype.card (GaloisField 2 k) : Complex)⁻¹ by ac_rfl]
      rw [horth]
      by_cases h : row = column
      · subst column
        simp
      · rw [if_neg h, if_neg (sub_ne_zero.mpr (Ne.symm h))]

/-- The rank-one Fourier (`X`) or computational (`Z`) projective measurement. -/
noncomputable def pauliProjector (k : Nat) (W : PauliBasis) :
    MIPStarRE.Quantum.Measurement (GaloisField 2 k) (GaloisField 2 k) :=
  MIPStarRE.Quantum.Measurement.ofSumEqOne
    (pauliProjectorEffect k W) (pauliProjectorEffect_pos k W)
    (pauliProjectorEffect_sum k W)

private theorem pauliProjector_X_apply (k : Nat)
    (b row column : GaloisField 2 k) :
    (pauliProjector k PauliBasis.X).effect b row column =
      (Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
        ZMod.stdAddChar (fieldTrace k (b * (column - row))) := rfl

private theorem pauliProjector_Z_apply (k : Nat)
    (b row column : GaloisField 2 k) :
    (pauliProjector k PauliBasis.Z).effect b row column =
      if row = b ∧ column = b then 1 else 0 := rfl

/-- Same-basis generalized Pauli observables add their field labels. -/
theorem pauli_mul (k : Nat) (W : PauliBasis)
    (a a' : GaloisField 2 k) :
    pauliObservable k W a * pauliObservable k W a' =
      pauliObservable k W (a + a') := by
  classical
  ext row column
  cases W with
  | X =>
      simp only [pauliObservable, pauliX, Matrix.mul_apply, ite_mul, one_mul,
        zero_mul]
      rw [Fintype.sum_eq_single (column + a')]
      · simp [add_comm, add_left_comm]
      · intro x hx
        simp [hx]
  | Z =>
      by_cases h : row = column
      · subst row
        simp [pauliObservable, pauliZ, Matrix.mul_apply,
          ← AddChar.map_add_eq_mul, add_mul]
      · simp [pauliObservable, pauliZ, Matrix.mul_apply, h]

/-- Every characteristic-two generalized Pauli observable squares to identity. -/
theorem pauli_sq (k : Nat) (W : PauliBasis) (a : GaloisField 2 k) :
    pauliObservable k W a ^ 2 = 1 := by
  rw [pow_two, pauli_mul]
  have haa : a + a = 0 := by
    have htwo : (2 : GaloisField 2 k) = 0 :=
      CharP.cast_eq_zero (GaloisField 2 k) 2
    calc
      a + a = (2 : GaloisField 2 k) * a := by ring
      _ = 0 := by rw [htwo, zero_mul]
  rw [haa]
  ext row column
  cases W <;> simp [pauliObservable, pauliX, pauliZ, Matrix.one_apply]

/-- Paper equation `eq:twisted-fq` for characteristic two. -/
theorem pauli_twistedCommutation (k : Nat)
    (a b : GaloisField 2 k) :
    pauliX k a * pauliZ k b =
      ZMod.stdAddChar (N := 2) (-(fieldTrace k (a * b))) •
        (pauliZ k b * pauliX k a) := by
  classical
  ext row column
  simp only [pauliX, pauliZ, Matrix.mul_apply, ite_mul, one_mul, zero_mul,
    Matrix.smul_apply, smul_eq_mul]
  have hleft :
      (∑ x, if row = x + a then
          if x = column then ZMod.stdAddChar (fieldTrace k (b * x)) else 0
        else 0) =
        if row = column + a then
          ZMod.stdAddChar (fieldTrace k (b * column)) else 0 := by
    rw [Fintype.sum_eq_single column]
    · simp
    · intro x hx
      simp [hx]
  rw [hleft]
  simp only [mul_ite, mul_zero]
  have hright :
      (∑ x, if row = x then
          if x = column + a then
            ZMod.stdAddChar (fieldTrace k (b * row)) * 1 else 0
        else 0) =
        if row = column + a then
          ZMod.stdAddChar (fieldTrace k (b * row)) else 0 := by
    rw [Fintype.sum_eq_single row]
    · simp
    · intro x hx
      simp [hx.symm]
  rw [hright]
  by_cases h : row = column + a
  · subst row
    simp only [if_true]
    rw [← AddChar.map_add_eq_mul]
    congr 1
    simp only [map_add, fieldTrace, mul_add,
      CharTwo.neg_eq, mul_comm a b]
    symm
    calc
      (fieldTrace k) (b * a) +
          ((fieldTrace k) (b * column) + (fieldTrace k) (b * a)) =
          (fieldTrace k) (b * column) +
            ((fieldTrace k) (b * a) + (fieldTrace k) (b * a)) := by
        ac_rfl
      _ = (fieldTrace k) (b * column) := by
        rw [CharTwo.add_self_eq_zero, add_zero]
  · simp [h]

/-- Paper equation `eq:pauli-obs-proj-single`. -/
theorem pauliObservable_eq_sum_projectors (k : Nat) (W : PauliBasis)
    (a : GaloisField 2 k) :
    pauliObservable k W a =
      ∑ b, ZMod.stdAddChar (N := 2) (fieldTrace k (a * b)) •
        (pauliProjector k W).effect b := by
  classical
  ext row column
  cases W with
  | Z =>
      by_cases h : row = column
      · subst column
        simp only [pauliObservable, pauliZ, Matrix.sum_apply,
          Matrix.smul_apply, smul_eq_mul, pauliProjector_Z_apply]
        rw [Fintype.sum_eq_single row]
        · simp
        · intro x hx
          simp [hx.symm]
      · simp only [pauliObservable, pauliZ, if_neg h, Matrix.sum_apply,
          Matrix.smul_apply, smul_eq_mul, pauliProjector_Z_apply]
        symm
        apply Fintype.sum_eq_zero
        intro x
        by_cases hr : row = x <;> by_cases hc : column = x
        · exact (h (hr.trans hc.symm)).elim
        · simp [hr, hc]
        · simp [hr, hc]
        · simp [hr, hc]
  | X =>
      simp only [pauliObservable, pauliX, Matrix.sum_apply,
        Matrix.smul_apply, smul_eq_mul, pauliProjector_X_apply]
      have hphase (b : GaloisField 2 k) :
          ZMod.stdAddChar (fieldTrace k (a * b)) *
              ((Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
                ZMod.stdAddChar (fieldTrace k (b * (column - row)))) =
            (Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
              ZMod.stdAddChar (fieldTrace k ((a + column - row) * b)) := by
        rw [show ZMod.stdAddChar (fieldTrace k (a * b)) *
              ((Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
                ZMod.stdAddChar (fieldTrace k (b * (column - row)))) =
            (Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
              (ZMod.stdAddChar (fieldTrace k (a * b)) *
                ZMod.stdAddChar (fieldTrace k (b * (column - row)))) by ac_rfl,
          ← AddChar.map_add_eq_mul]
        congr 2
        rw [← map_add]
        congr 1
        simp only [CharTwo.sub_eq_add, add_mul]
        ring
      simp_rw [hphase]
      rw [← Finset.mul_sum]
      have horth := traceCharacter_expect k (a + column - row)
      rw [div_eq_mul_inv] at horth
      rw [show (Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
          ∑ b, ZMod.stdAddChar (fieldTrace k ((a + column - row) * b)) =
          (∑ b, ZMod.stdAddChar (fieldTrace k ((a + column - row) * b))) *
            (Fintype.card (GaloisField 2 k) : Complex)⁻¹ by ac_rfl,
        horth]
      by_cases h : row = column + a
      · subst row
        simp [add_comm]
      · rw [if_neg h, if_neg]
        intro hz
        apply h
        have : a + column = row := sub_eq_zero.mp hz
        simpa [add_comm] using this.symm

/-- Paper equation `eq:pauli-inversion-0-single`. -/
theorem pauliProjector_eq_expect_observables (k : Nat) (W : PauliBasis)
    (b : GaloisField 2 k) :
    (pauliProjector k W).effect b =
      (Fintype.card (GaloisField 2 k) : Complex)⁻¹ •
        ∑ a, ZMod.stdAddChar (N := 2) (-(fieldTrace k (a * b))) •
          pauliObservable k W a := by
  classical
  ext row column
  cases W with
  | X =>
      simp only [pauliProjector_X_apply, Matrix.smul_apply, smul_eq_mul,
        Matrix.sum_apply, pauliObservable, pauliX]
      have hsum :
          (∑ a, ZMod.stdAddChar (-(fieldTrace k (a * b))) *
              (if row = column + a then 1 else 0)) =
            ZMod.stdAddChar (-(fieldTrace k ((row - column) * b))) := by
        rw [Fintype.sum_eq_single (row - column)]
        · simp
        · intro x hx
          by_cases h : row = column + x
          · exfalso
            apply hx
            apply eq_sub_of_add_eq
            simpa [add_comm] using h.symm
          · simp [h]
      rw [hsum]
      congr 1
      congr 1
      simp only [CharTwo.neg_eq]
      congr 1
      rw [CharTwo.sub_eq_add, CharTwo.sub_eq_add]
      ac_rfl
  | Z =>
      simp only [pauliProjector_Z_apply, Matrix.smul_apply, smul_eq_mul,
        Matrix.sum_apply, pauliObservable, pauliZ]
      by_cases hrc : row = column
      · subst column
        simp only [if_true]
        have hphase (a : GaloisField 2 k) :
            ZMod.stdAddChar (-(fieldTrace k (a * b))) *
                ZMod.stdAddChar (fieldTrace k (a * row)) =
              ZMod.stdAddChar (fieldTrace k ((row - b) * a)) := by
          rw [← AddChar.map_add_eq_mul]
          congr 2
          simp only [CharTwo.neg_eq]
          rw [← map_add]
          congr 1
          rw [CharTwo.sub_eq_add, add_mul]
          ac_rfl
        simp_rw [hphase]
        have horth := traceCharacter_expect k (row - b)
        rw [div_eq_mul_inv] at horth
        rw [show (Fintype.card (GaloisField 2 k) : Complex)⁻¹ *
            ∑ a, ZMod.stdAddChar (fieldTrace k ((row - b) * a)) =
            (∑ a, ZMod.stdAddChar (fieldTrace k ((row - b) * a))) *
              (Fintype.card (GaloisField 2 k) : Complex)⁻¹ by ac_rfl,
          horth]
        by_cases hrb : row = b
        · subst row
          simp
        · rw [if_neg, if_neg (sub_ne_zero.mpr hrb)]
          simp [hrb]
      · simp only [if_neg hrc]
        have hdelta : ¬(row = b ∧ column = b) := by
          intro hb
          exact hrc (hb.1.trans hb.2.symm)
        rw [if_neg hdelta]
        simp

/-- The standard bilinear dot product on finite-field vectors. -/
noncomputable def fieldDotProduct {k n : Nat}
    (a b : Fin n -> GaloisField 2 k) : GaloisField 2 k :=
  ∑ i, a i * b i

private theorem fieldDotProduct_comm {k n : Nat}
    (a b : Fin n -> GaloisField 2 k) :
    fieldDotProduct a b = fieldDotProduct b a := by
  unfold fieldDotProduct
  apply Finset.sum_congr rfl
  intro i _
  rw [mul_comm]

private theorem fieldDotProduct_add_left {k n : Nat}
    (a b c : Fin n -> GaloisField 2 k) :
    fieldDotProduct (a + b) c = fieldDotProduct a c + fieldDotProduct b c := by
  simp [fieldDotProduct, add_mul, Finset.sum_add_distrib]

private noncomputable def traceVectorCharacter (k n : Nat)
    (c : Fin n -> GaloisField 2 k) :
    AddChar (Fin n -> GaloisField 2 k) Complex :=
  ZMod.stdAddChar.compAddMonoidHom
    { toFun := fun x => fieldTrace k (fieldDotProduct c x)
      map_zero' := by simp [fieldDotProduct]
      map_add' := by
        intro x y
        simp [fieldDotProduct, mul_add, Finset.sum_add_distrib] }

private theorem traceVectorCharacter_eq_zero_iff (k n : Nat)
    (c : Fin n -> GaloisField 2 k) :
    traceVectorCharacter k n c = 0 ↔ c = 0 := by
  constructor
  · intro h
    by_contra hc
    obtain ⟨i, hi⟩ : ∃ i, c i ≠ 0 := by
      simpa [funext_iff] using hc
    obtain ⟨x, hx⟩ := fieldTrace_mul_nondegenerate k hi
    have happ := DFunLike.congr_fun h (Pi.single i x)
    have hdot : fieldDotProduct c (Pi.single i x) = c i * x := by
      unfold fieldDotProduct
      rw [Finset.sum_eq_single i]
      · simp
      · intro j _ hji
        simp [hji]
      · intro hiu
        exact (hiu (by simp)).elim
    have hphase : ZMod.stdAddChar (fieldTrace k (c i * x)) =
        ZMod.stdAddChar (0 : ZMod 2) := by
      simpa [traceVectorCharacter, hdot] using happ
    exact hx (ZMod.injective_stdAddChar hphase)
  · rintro rfl
    ext x
    simp [traceVectorCharacter, fieldDotProduct]

private theorem traceVectorCharacter_expect (k n : Nat)
    (c : Fin n -> GaloisField 2 k) :
    (∑ x, ZMod.stdAddChar (fieldTrace k (fieldDotProduct c x))) /
        (Fintype.card (Fin n -> GaloisField 2 k) : Complex) =
      if c = 0 then 1 else 0 := by
  rw [← Fintype.expect_eq_sum_div_card]
  change Finset.univ.expect (traceVectorCharacter k n c) = _
  rw [AddChar.expect_eq_ite]
  simp only [traceVectorCharacter_eq_zero_iff]

/-- The product-basis matrix of the coordinatewise generalized Pauli tensor. -/
noncomputable def pauliTensor (k n : Nat) (W : PauliBasis)
    (a : Fin n -> GaloisField 2 k) :
    MIPStarRE.Quantum.Op (Fin n -> GaloisField 2 k) :=
  match W with
  | .X => fun row column =>
      if row = fun i => column i + a i then 1 else 0
  | .Z => fun row column =>
      if row = column then
        ZMod.stdAddChar (fieldTrace k (fieldDotProduct a row)) else 0

private noncomputable def tensorFourierVector (k n : Nat)
    (b : Fin n -> GaloisField 2 k) :
    (Fin n -> GaloisField 2 k) -> Complex :=
  fun x => ZMod.stdAddChar (-(fieldTrace k (fieldDotProduct b x)))

private noncomputable def tensorComputationalVector (k n : Nat)
    (b : Fin n -> GaloisField 2 k) :
    (Fin n -> GaloisField 2 k) -> Complex :=
  fun x => if x = b then 1 else 0

private noncomputable def pauliTensorProjectorEffect (k n : Nat)
    (W : PauliBasis) (b : Fin n -> GaloisField 2 k) :
    MIPStarRE.Quantum.Op (Fin n -> GaloisField 2 k) :=
  match W with
  | .X => fun row column =>
      (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
        ZMod.stdAddChar
          (fieldTrace k (fieldDotProduct b (column - row)))
  | .Z => fun row column => if row = b ∧ column = b then 1 else 0

private theorem pauliTensorProjectorEffect_pos (k n : Nat)
    (W : PauliBasis) (b : Fin n -> GaloisField 2 k) :
    0 ≤ pauliTensorProjectorEffect k n W b := by
  rw [Matrix.nonneg_iff_posSemidef]
  cases W with
  | X =>
      have heffect : pauliTensorProjectorEffect k n PauliBasis.X b =
          (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ •
            Matrix.vecMulVec (tensorFourierVector k n b)
              (star (tensorFourierVector k n b)) := by
        ext row column
        simp only [pauliTensorProjectorEffect, Matrix.smul_apply, smul_eq_mul,
          Matrix.vecMulVec_apply, Pi.star_apply, tensorFourierVector]
        have hconj :
            star (ZMod.stdAddChar
                (-(fieldTrace k (fieldDotProduct b column)))) =
              ZMod.stdAddChar (fieldTrace k (fieldDotProduct b column)) := by
          simpa only [Complex.star_def, neg_neg] using
            (AddChar.map_neg_eq_conj ZMod.stdAddChar
              (-(fieldTrace k (fieldDotProduct b column)))).symm
        rw [hconj, ← AddChar.map_add_eq_mul]
        congr 2
        have hdot : fieldDotProduct b (column - row) =
            fieldDotProduct b column - fieldDotProduct b row := by
          simp [fieldDotProduct, Pi.sub_apply, mul_sub,
            Finset.sum_sub_distrib]
        rw [hdot, map_sub]
        simp [CharTwo.neg_eq, CharTwo.sub_eq_add, add_comm]
      rw [heffect]
      apply Matrix.PosSemidef.smul
        (Matrix.posSemidef_vecMulVec_self_star (tensorFourierVector k n b))
      positivity
  | Z =>
      have heffect : pauliTensorProjectorEffect k n PauliBasis.Z b =
          Matrix.vecMulVec (tensorComputationalVector k n b)
            (star (tensorComputationalVector k n b)) := by
        ext row column
        simp only [pauliTensorProjectorEffect, Matrix.vecMulVec_apply,
          Pi.star_apply, tensorComputationalVector]
        by_cases hr : row = b <;> by_cases hc : column = b <;> simp [hr, hc]
      rw [heffect]
      exact Matrix.posSemidef_vecMulVec_self_star
        (tensorComputationalVector k n b)

private theorem pauliTensorProjectorEffect_sum (k n : Nat)
    (W : PauliBasis) : ∑ b, pauliTensorProjectorEffect k n W b = 1 := by
  classical
  ext row column
  cases W with
  | Z =>
      by_cases h : row = column
      · subst column
        simp [pauliTensorProjectorEffect, Matrix.sum_apply]
      · simp [pauliTensorProjectorEffect, Matrix.sum_apply, h, Ne.symm h]
  | X =>
      rw [Matrix.one_apply]
      simp only [pauliTensorProjectorEffect, Matrix.sum_apply]
      rw [← Finset.mul_sum]
      have horth := traceVectorCharacter_expect k n (column - row)
      rw [div_eq_mul_inv] at horth
      have hsum :
          (∑ b, ZMod.stdAddChar
              (fieldTrace k (fieldDotProduct b (column - row)))) =
            ∑ b, ZMod.stdAddChar
              (fieldTrace k (fieldDotProduct (column - row) b)) := by
        apply Finset.sum_congr rfl
        intro b _
        congr 2
        unfold fieldDotProduct
        apply Finset.sum_congr rfl
        intro i _
        rw [mul_comm]
      rw [hsum]
      rw [show (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
          ∑ b, ZMod.stdAddChar
            (fieldTrace k (fieldDotProduct (column - row) b)) =
          (∑ b, ZMod.stdAddChar
            (fieldTrace k (fieldDotProduct (column - row) b))) *
            (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ by ac_rfl,
        horth]
      by_cases h : row = column
      · subst column
        simp
      · rw [if_neg h, if_neg]
        exact sub_ne_zero.mpr (Ne.symm h)

/-- The product Fourier (`X`) or computational (`Z`) rank-one measurement. -/
noncomputable def pauliTensorProjector (k n : Nat) (W : PauliBasis) :
    MIPStarRE.Quantum.Measurement
      (Fin n -> GaloisField 2 k) (Fin n -> GaloisField 2 k) :=
  MIPStarRE.Quantum.Measurement.ofSumEqOne
    (pauliTensorProjectorEffect k n W)
    (pauliTensorProjectorEffect_pos k n W)
    (pauliTensorProjectorEffect_sum k n W)

private theorem pauliTensorProjector_X_apply (k n : Nat)
    (b row column : Fin n -> GaloisField 2 k) :
    (pauliTensorProjector k n PauliBasis.X).effect b row column =
      (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
        ZMod.stdAddChar
          (fieldTrace k (fieldDotProduct b (column - row))) := rfl

private theorem pauliTensorProjector_Z_apply (k n : Nat)
    (b row column : Fin n -> GaloisField 2 k) :
    (pauliTensorProjector k n PauliBasis.Z).effect b row column =
      if row = b ∧ column = b then 1 else 0 := rfl

/-- The tensor generalized-Pauli twisted commutation relation. -/
theorem pauliTensor_twistedCommutation (k n : Nat)
    (a b : Fin n -> GaloisField 2 k) :
    pauliTensor k n PauliBasis.X a * pauliTensor k n PauliBasis.Z b =
      ZMod.stdAddChar (N := 2)
          (-(fieldTrace k (fieldDotProduct a b))) •
        (pauliTensor k n PauliBasis.Z b *
          pauliTensor k n PauliBasis.X a) := by
  classical
  ext row column
  simp only [pauliTensor, Matrix.mul_apply, ite_mul, one_mul, zero_mul,
    Matrix.smul_apply, smul_eq_mul]
  have hleft :
      (∑ x, if row = (fun i => x i + a i) then
          if x = column then
            ZMod.stdAddChar (fieldTrace k (fieldDotProduct b x)) else 0
        else 0) =
        if row = (fun i => column i + a i) then
          ZMod.stdAddChar (fieldTrace k (fieldDotProduct b column)) else 0 := by
    rw [Fintype.sum_eq_single column]
    · simp
    · intro x hx
      simp [hx]
  rw [hleft]
  simp only [mul_ite, mul_zero]
  have hright :
      (∑ x, if row = x then
          if x = (fun i => column i + a i) then
            ZMod.stdAddChar (fieldTrace k (fieldDotProduct b row)) * 1 else 0
        else 0) =
        if row = (fun i => column i + a i) then
          ZMod.stdAddChar (fieldTrace k (fieldDotProduct b row)) else 0 := by
    rw [Fintype.sum_eq_single row]
    · simp
    · intro x hx
      simp [hx.symm]
  rw [hright]
  by_cases h : row = (fun i => column i + a i)
  · subst row
    simp only [if_true]
    rw [← AddChar.map_add_eq_mul]
    congr 1
    have hdot :
        fieldDotProduct b (fun i => column i + a i) =
          fieldDotProduct b column + fieldDotProduct b a := by
      simp [fieldDotProduct, mul_add, Finset.sum_add_distrib]
    have hcomm : fieldDotProduct b a = fieldDotProduct a b := by
      unfold fieldDotProduct
      apply Finset.sum_congr rfl
      intro i _
      rw [mul_comm]
    rw [hdot, map_add, hcomm]
    simp only [CharTwo.neg_eq]
    symm
    calc
      (fieldTrace k) (fieldDotProduct a b) +
          ((fieldTrace k) (fieldDotProduct b column) +
            (fieldTrace k) (fieldDotProduct a b)) =
          (fieldTrace k) (fieldDotProduct b column) +
            ((fieldTrace k) (fieldDotProduct a b) +
              (fieldTrace k) (fieldDotProduct a b)) := by
        ac_rfl
      _ = (fieldTrace k) (fieldDotProduct b column) := by
        rw [CharTwo.add_self_eq_zero, add_zero]
  · simp [h]

/-- Paper equation `eq:pauli-obs-proj`. -/
theorem pauliTensor_eq_sum_projectors (k n : Nat) (W : PauliBasis)
    (a : Fin n -> GaloisField 2 k) :
    pauliTensor k n W a =
      ∑ b, ZMod.stdAddChar (N := 2)
          (fieldTrace k (fieldDotProduct a b)) •
        (pauliTensorProjector k n W).effect b := by
  classical
  ext row column
  cases W with
  | Z =>
      by_cases h : row = column
      · subst column
        simp only [pauliTensor, Matrix.sum_apply, Matrix.smul_apply,
          smul_eq_mul, pauliTensorProjector_Z_apply]
        rw [Fintype.sum_eq_single row]
        · simp
        · intro x hx
          simp [hx.symm]
      · simp only [pauliTensor, if_neg h, Matrix.sum_apply,
          Matrix.smul_apply, smul_eq_mul, pauliTensorProjector_Z_apply]
        symm
        apply Fintype.sum_eq_zero
        intro x
        by_cases hr : row = x <;> by_cases hc : column = x
        · exact (h (hr.trans hc.symm)).elim
        · simp [hr, hc]
        · simp [hr, hc]
        · simp [hr, hc]
  | X =>
      simp only [pauliTensor, Matrix.sum_apply, Matrix.smul_apply,
        smul_eq_mul, pauliTensorProjector_X_apply]
      have hphase (b : Fin n -> GaloisField 2 k) :
          ZMod.stdAddChar (fieldTrace k (fieldDotProduct a b)) *
              ((Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
                ZMod.stdAddChar
                  (fieldTrace k (fieldDotProduct b (column - row)))) =
            (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
              ZMod.stdAddChar
                (fieldTrace k (fieldDotProduct (a + column - row) b)) := by
        rw [show ZMod.stdAddChar (fieldTrace k (fieldDotProduct a b)) *
              ((Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
                ZMod.stdAddChar
                  (fieldTrace k (fieldDotProduct b (column - row)))) =
            (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
              (ZMod.stdAddChar (fieldTrace k (fieldDotProduct a b)) *
                ZMod.stdAddChar
                  (fieldTrace k (fieldDotProduct b (column - row)))) by ac_rfl,
          ← AddChar.map_add_eq_mul]
        congr 2
        rw [← map_add]
        congr 1
        rw [fieldDotProduct_comm b (column - row),
          ← fieldDotProduct_add_left]
        congr 1
        ext i
        simp [CharTwo.sub_eq_add, add_assoc]
      simp_rw [hphase]
      rw [← Finset.mul_sum]
      have horth := traceVectorCharacter_expect k n (a + column - row)
      rw [div_eq_mul_inv] at horth
      rw [show (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
          ∑ b, ZMod.stdAddChar
            (fieldTrace k (fieldDotProduct (a + column - row) b)) =
          (∑ b, ZMod.stdAddChar
            (fieldTrace k (fieldDotProduct (a + column - row) b))) *
            (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ by ac_rfl,
        horth]
      by_cases h : row = (fun i => column i + a i)
      · rw [h]
        have hz : a + column - (fun i => column i + a i) = 0 := by
          ext i
          simp [Pi.add_apply, Pi.sub_apply, add_comm]
        simp only [if_pos hz]
        simp only [if_true]
      · rw [if_neg h, if_neg]
        intro hz
        apply h
        ext i
        have hi := congrFun (sub_eq_zero.mp hz) i
        simpa [Pi.add_apply, Pi.sub_apply, add_comm] using hi.symm

/-- Paper equation `eq:pauli-inversion-0`. -/
theorem pauliTensorProjector_eq_expect_observables
    (k n : Nat) (W : PauliBasis)
    (b : Fin n -> GaloisField 2 k) :
    (pauliTensorProjector k n W).effect b =
      (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ •
        ∑ a, ZMod.stdAddChar (N := 2)
          (-(fieldTrace k (fieldDotProduct a b))) •
            pauliTensor k n W a := by
  classical
  ext row column
  cases W with
  | X =>
      simp only [pauliTensorProjector_X_apply, Matrix.smul_apply,
        smul_eq_mul, Matrix.sum_apply, pauliTensor]
      have hsum :
          (∑ a, ZMod.stdAddChar
                (-(fieldTrace k (fieldDotProduct a b))) *
              (if row = (fun i => column i + a i) then 1 else 0)) =
            ZMod.stdAddChar
              (-(fieldTrace k (fieldDotProduct (row - column) b))) := by
        rw [Fintype.sum_eq_single (row - column)]
        · have hshift : row = fun i => column i + (row - column) i := by
            ext i
            simp [Pi.sub_apply]
          rw [if_pos hshift, mul_one]
        · intro x hx
          by_cases h : row = (fun i => column i + x i)
          · exfalso
            apply hx
            ext i
            apply eq_sub_of_add_eq
            simpa [add_comm] using (congrFun h i).symm
          · simp [h]
      rw [hsum]
      congr 1
      congr 1
      simp only [CharTwo.neg_eq]
      congr 1
      rw [fieldDotProduct_comm b (column - row)]
      congr 1
      ext i
      simp [Pi.sub_apply, CharTwo.sub_eq_add, add_comm]
  | Z =>
      simp only [pauliTensorProjector_Z_apply, Matrix.smul_apply,
        smul_eq_mul, Matrix.sum_apply, pauliTensor]
      by_cases hrc : row = column
      · subst column
        simp only [if_true]
        have hphase (a : Fin n -> GaloisField 2 k) :
            ZMod.stdAddChar (-(fieldTrace k (fieldDotProduct a b))) *
                ZMod.stdAddChar (fieldTrace k (fieldDotProduct a row)) =
              ZMod.stdAddChar
                (fieldTrace k (fieldDotProduct (row - b) a)) := by
          rw [← AddChar.map_add_eq_mul]
          congr 2
          simp only [CharTwo.neg_eq]
          rw [← map_add]
          congr 1
          rw [fieldDotProduct_comm a b, fieldDotProduct_comm a row,
            ← fieldDotProduct_add_left]
          congr 1
          ext i
          simp [Pi.sub_apply, CharTwo.sub_eq_add, add_comm]
        simp_rw [hphase]
        have horth := traceVectorCharacter_expect k n (row - b)
        rw [div_eq_mul_inv] at horth
        rw [show (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ *
            ∑ a, ZMod.stdAddChar
              (fieldTrace k (fieldDotProduct (row - b) a)) =
            (∑ a, ZMod.stdAddChar
              (fieldTrace k (fieldDotProduct (row - b) a))) *
              (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ by ac_rfl,
          horth]
        by_cases hrb : row = b
        · subst row
          simp
        · rw [if_neg, if_neg (sub_ne_zero.mpr hrb)]
          simp [hrb]
      · simp only [if_neg hrc]
        have hdelta : ¬(row = b ∧ column = b) := by
          intro hb
          exact hrc (hb.1.trans hb.2.symm)
        rw [if_neg hdelta]
        simp

end MIPStarRE.QPBT
