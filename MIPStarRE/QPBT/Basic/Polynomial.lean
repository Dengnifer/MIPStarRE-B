import Mathlib.RingTheory.MvPolynomial.Basic
import MIPStarRE.QPBT.Basic.Field

open scoped BigOperators

namespace MIPStarRE.QPBT

abbrev BooleanPoint (m : Nat) := Fin m -> ZMod 2

abbrev FieldPoint (k m : Nat) := Fin m -> GaloisField 2 k

noncomputable abbrev IndividualDegreePolynomial (k m d : Nat) :=
  MvPolynomial.restrictDegree (Fin m) (GaloisField 2 k) d

noncomputable def booleanPointToField {k m : Nat} (y : BooleanPoint m) :
    FieldPoint k m :=
  fun i => algebraMap (ZMod 2) (GaloisField 2 k) (y i)

noncomputable def evalIndividualDegreePolynomial {k m d : Nat}
    (f : IndividualDegreePolynomial k m d) (x : FieldPoint k m) :
    GaloisField 2 k :=
  MvPolynomial.eval x f.1

noncomputable def indicatorPolynomial {k m : Nat} (y : BooleanPoint m) :
    IndividualDegreePolynomial k m 1 := by
  classical
  let p : MvPolynomial (Fin m) (GaloisField 2 k) :=
    ∏ i, if y i = 1 then MvPolynomial.X i
      else MvPolynomial.C 1 - MvPolynomial.X i
  refine ⟨p, ?_⟩
  rw [MvPolynomial.mem_restrictDegree_iff_sup]
  have hdeg : p.degrees ≤ ∑ s : Fin m, ({s} : Multiset (Fin m)) := by
    dsimp [p]
    refine MvPolynomial.degrees_prod_le.trans ?_
    refine Finset.sum_le_sum (fun s hs => ?_)
    by_cases h : y s = 1
    · simp [h, MvPolynomial.degrees_X' (R := GaloisField 2 k)]
    · rw [if_neg h]
      refine MvPolynomial.degrees_sub_le.trans ?_
      rw [MvPolynomial.degrees_one, Multiset.zero_union]
      exact MvPolynomial.degrees_X' (σ := Fin m) (R := GaloisField 2 k) s
  intro n
  refine le_trans (Multiset.count_le_of_le n hdeg) ?_
  have hcount : Multiset.count n (∑ s : Fin m, ({s} : Multiset (Fin m))) = 1 := by
    rw [← Multiset.coe_countAddMonoidHom, map_sum]
    change (∑ s : Fin m, Multiset.count n ({s} : Multiset (Fin m))) = 1
    have hs := Finset.sum_eq_single (s := (Finset.univ : Finset (Fin m)))
      (f := fun s : Fin m => Multiset.count n ({s} : Multiset (Fin m))) n
      (by
        intro b _ hbn
        simp [hbn, eqComm])
      (by
        intro hn
        exact (hn (Finset.mem_univ _)).elim)
    simpa using hs
  simpa [hcount]

noncomputable def indicatorVector {k m : Nat} (x : FieldPoint k m) :
    BooleanPoint m -> GaloisField 2 k :=
  fun y => evalIndividualDegreePolynomial (indicatorPolynomial y) x

noncomputable def lowDegreeEncode (k m : Nat) :
    (BooleanPoint m -> GaloisField 2 k) →ₗ[GaloisField 2 k]
      IndividualDegreePolynomial k m 1 := by
  classical
  refine
    { toFun := fun a => ∑ y, a y • indicatorPolynomial y
      map_add' := ?_
      map_smul' := ?_ }
  · intro a b
    simp [add_smul, Finset.sum_add_distrib]
  · intro c a
    simp [Finset.smul_sum, smul_smul, mul_comm]

@[simp] theorem indicatorPolynomial_eval_boolean {k m : Nat}
    (x y : BooleanPoint m) :
    evalIndividualDegreePolynomial (indicatorPolynomial (k := k) y)
      (booleanPointToField x) = if x = y then 1 else 0 := by
  classical
  have bool_cases : ∀ z : ZMod 2, z = 0 ∨ z = 1 := by
    intro z
    fin_cases z
    · exact Or.inl rfl
    · exact Or.inr rfl
  have factor_eval (u v : BooleanPoint m) (i : Fin m) :
      MvPolynomial.eval (R := GaloisField 2 k) (booleanPointToField u)
          (if v i = 1 then MvPolynomial.X i else MvPolynomial.C 1 - MvPolynomial.X i) =
        (if u i = v i then 1 else 0 : GaloisField 2 k) := by
    rcases bool_cases (v i) with hv | hv <;>
      rcases bool_cases (u i) with hu | hu <;>
        simp [hv, hu, booleanPointToField]
  simp only [indicatorPolynomial, evalIndividualDegreePolynomial,
    Submodule.coe_mk, map_prod]
  by_cases hxy : x = y
  · subst y
    rw [if_pos rfl]
    apply Finset.prod_eq_one
    intro j hj
    simpa using (factor_eval x x j)
  · obtain ⟨i, hi⟩ : ∃ i, x i ≠ y i := by
      apply not_forall.mp
      intro hall
      exact hxy (funext hall)
    rw [if_neg hxy]
    apply Finset.prod_eq_zero (Finset.mem_univ i)
    simpa [hi] using (factor_eval x y i)

theorem lowDegreeEncode_eval {k m : Nat}
    (a : BooleanPoint m -> GaloisField 2 k) (x : FieldPoint k m) :
    evalIndividualDegreePolynomial (lowDegreeEncode k m a) x =
      ∑ y, a y * indicatorVector x y := by
  simp [lowDegreeEncode, indicatorVector, evalIndividualDegreePolynomial,
    map_sum, map_smul, smul_eq_mul]

@[simp] theorem lowDegreeEncode_eval_boolean {k m : Nat}
    (a : BooleanPoint m -> GaloisField 2 k) (y : BooleanPoint m) :
    evalIndividualDegreePolynomial (lowDegreeEncode k m a)
      (booleanPointToField y) = a y := by
  rw [lowDegreeEncode_eval]
  classical
  simp [indicatorVector]

theorem lowDegreeEncode_injective (k m : Nat) :
    Function.Injective (lowDegreeEncode k m) := by
  intro a b hab
  funext y
  have := congrArg (fun f =>
    evalIndividualDegreePolynomial f (booleanPointToField y)) hab
  simpa using this

end MIPStarRE.QPBT
