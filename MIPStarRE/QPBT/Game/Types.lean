import Mathlib.Computability.TuringMachine.Computable
import Mathlib.Data.Nat.Log
import Mathlib.Probability.Distributions.Uniform
import MIPStarRE.QPBT.Basic.Field

/-!
# Conditionally linear maps and samplers

This file formalizes the mathematical conditionally linear layer from
`conditionally-linear.tex:1-552`.  A certificate records the successive
coordinate factors and linear maps, while a sampler applies two certified maps
to one shared uniform field vector.
-/

namespace MIPStarRE.QPBT

noncomputable local instance (k : Nat) : Fintype (GaloisField 2 k) :=
  Fintype.ofFinite (GaloisField 2 k)

noncomputable local instance (k : Nat) : DecidableEq (GaloisField 2 k) :=
  Classical.decEq (GaloisField 2 k)

/-- The coordinate model of the field vector space used by CL maps. -/
abbrev FieldVector (k n : Nat) := Fin n -> GaloisField 2 k

/-- Keep the coordinates in `register` and set every other coordinate to zero. -/
noncomputable def restrictVector {k n : Nat} (register : Finset (Fin n))
    (x : FieldVector k n) : FieldVector k n :=
  fun i => if i ∈ register then x i else 0

/-- A source-faithful recursive certificate for a conditionally linear map. -/
inductive ConditionallyLinearCertificate (k n : Nat) :
    Finset (Fin n) -> Nat -> (FieldVector k n -> FieldVector k n) -> Prop
  | zero (remaining : Finset (Fin n)) :
      ConditionallyLinearCertificate k n remaining 0 (fun _ => 0)
  | step {remaining : Finset (Fin n)} {level : Nat}
      {toFun : FieldVector k n -> FieldVector k n}
      (head tail : Finset (Fin n))
      (disjoint : Disjoint head tail)
      (covers : head ∪ tail = remaining)
      (headMap : FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n)
      (head_supported : forall x i, i ∉ head -> headMap x i = 0)
      (head_depends : forall x, headMap (restrictVector head x) = headMap x)
      (next : LinearMap.range headMap -> FieldVector k n -> FieldVector k n)
      (next_certificate : forall pfx,
        ConditionallyLinearCertificate k n tail level (next pfx))
      (toFun_eq : forall x,
        toFun x = headMap (restrictVector head x) +
          next ⟨headMap (restrictVector head x),
            ⟨restrictVector head x, rfl⟩⟩ (restrictVector tail x)) :
      ConditionallyLinearCertificate k n remaining (level + 1) toFun

/-- A function together with a CL certificate on all coordinates. -/
structure ConditionallyLinearMap (k n level : Nat) where
  toFun : FieldVector k n -> FieldVector k n
  certificate : ConditionallyLinearCertificate k n Finset.univ level toFun

instance {k n level : Nat} : CoeFun (ConditionallyLinearMap k n level)
    (fun _ => FieldVector k n -> FieldVector k n) :=
  ⟨ConditionallyLinearMap.toFun⟩

private theorem ConditionallyLinearCertificate.promote
    {k n level : Nat}
    {toFun : FieldVector k n -> FieldVector k n}
    (certificate : ConditionallyLinearCertificate k n Finset.univ level toFun) :
    ConditionallyLinearCertificate k n Finset.univ (level + 1) toFun := by
  classical
  refine .step ∅ Finset.univ (by simp) (by simp) 0 ?_ ?_
      (fun _ => toFun) (fun _ => certificate) ?_
  · intro x i hi
    simp
  · intro x
    simp
  · intro x
    rw [show restrictVector Finset.univ x = x by
      funext i
      simp [restrictVector]]
    simp

private theorem ConditionallyLinearCertificate.raiseLevel
    {k n level : Nat} {toFun : FieldVector k n -> FieldVector k n}
    (certificate : ConditionallyLinearCertificate k n Finset.univ level toFun) :
    forall extra : Nat,
      ConditionallyLinearCertificate k n Finset.univ (level + extra) toFun := by
  intro extra
  induction extra with
  | zero => simpa using certificate
  | succ extra ih => simpa [Nat.add_assoc] using ih.promote

/-- Regard a CL map as a map at any higher level. -/
noncomputable def ConditionallyLinearMap.raiseLevel
    {k n level : Nat} (L : ConditionallyLinearMap k n level) (extra : Nat) :
    ConditionallyLinearMap k n (level + extra) :=
  ⟨L.toFun, L.certificate.raiseLevel extra⟩

private theorem ConditionallyLinearCertificate.raiseTo
    {k n level target : Nat} {toFun : FieldVector k n -> FieldVector k n}
    (certificate : ConditionallyLinearCertificate k n Finset.univ level toFun)
    (hlevel : level ≤ target) :
    ConditionallyLinearCertificate k n Finset.univ target toFun := by
  simpa [Nat.add_sub_of_le hlevel] using
    certificate.raiseLevel (target - level)

private def leftPart {k n₁ n₂ : Nat} (x : FieldVector k (n₁ + n₂)) :
    FieldVector k n₁ :=
  fun i => x (Fin.castAdd n₂ i)

private def rightPart {k n₁ n₂ : Nat} (x : FieldVector k (n₁ + n₂)) :
    FieldVector k n₂ :=
  fun i => x (Fin.natAdd n₁ i)

private def appendRegister {n₁ n₂ : Nat}
    (left : Finset (Fin n₁)) (right : Finset (Fin n₂)) :
    Finset (Fin (n₁ + n₂)) :=
  left.map (Fin.castAddEmb n₂) ∪ right.map (Fin.natAddEmb n₁)

private theorem mem_appendRegister_left {n₁ n₂ : Nat}
    (left : Finset (Fin n₁)) (right : Finset (Fin n₂)) (i : Fin n₁) :
    Fin.castAdd n₂ i ∈ appendRegister left right ↔ i ∈ left := by
  simp only [appendRegister, Finset.mem_union, Finset.mem_map]
  constructor
  · rintro (⟨j, hj, hji⟩ | ⟨j, hj, hji⟩)
    · have h : j = i := (Fin.castAddEmb n₂).injective hji
      simpa [h] using hj
    · exfalso
      change Fin.natAdd n₁ j = Fin.castAdd n₂ i at hji
      have hval : n₁ + j.val = i.val := congrArg Fin.val hji
      omega
  · intro hi
    exact Or.inl ⟨i, hi, rfl⟩

private theorem mem_appendRegister_right {n₁ n₂ : Nat}
    (left : Finset (Fin n₁)) (right : Finset (Fin n₂)) (i : Fin n₂) :
    Fin.natAdd n₁ i ∈ appendRegister left right ↔ i ∈ right := by
  simp only [appendRegister, Finset.mem_union, Finset.mem_map]
  constructor
  · rintro (⟨j, hj, hji⟩ | ⟨j, hj, hji⟩)
    · exfalso
      change Fin.castAdd n₂ j = Fin.natAdd n₁ i at hji
      have hval : j.val = n₁ + i.val := congrArg Fin.val hji
      omega
    · have h : j = i := (Fin.natAddEmb n₁).injective hji
      simpa [h] using hj
  · intro hi
    exact Or.inr ⟨i, hi, rfl⟩

private theorem appendRegister_union {n₁ n₂ : Nat}
    (leftHead leftTail : Finset (Fin n₁))
    (rightHead rightTail : Finset (Fin n₂)) :
    appendRegister leftHead rightHead ∪ appendRegister leftTail rightTail =
      appendRegister (leftHead ∪ leftTail) (rightHead ∪ rightTail) := by
  ext i
  refine Fin.addCases (fun j => ?_) (fun j => ?_) i <;>
    simp [mem_appendRegister_left, mem_appendRegister_right]

private theorem appendRegister_univ {n₁ n₂ : Nat} :
    appendRegister (Finset.univ : Finset (Fin n₁))
      (Finset.univ : Finset (Fin n₂)) = Finset.univ := by
  ext i
  refine Fin.addCases (fun j => ?_) (fun j => ?_) i <;>
    simp [mem_appendRegister_left, mem_appendRegister_right]

private theorem appendRegister_disjoint {n₁ n₂ : Nat}
    {leftHead leftTail : Finset (Fin n₁)}
    {rightHead rightTail : Finset (Fin n₂)}
    (hleft : Disjoint leftHead leftTail)
    (hright : Disjoint rightHead rightTail) :
    Disjoint (appendRegister leftHead rightHead)
      (appendRegister leftTail rightTail) := by
  rw [Finset.disjoint_left]
  intro i hiHead hiTail
  exact Fin.addCases
    (fun j hHead hTail => (Finset.disjoint_left.mp hleft)
      ((mem_appendRegister_left _ _ _).mp hHead)
      ((mem_appendRegister_left _ _ _).mp hTail))
    (fun j hHead hTail => (Finset.disjoint_left.mp hright)
      ((mem_appendRegister_right _ _ _).mp hHead)
      ((mem_appendRegister_right _ _ _).mp hTail))
    i hiHead hiTail

private theorem leftPart_restrictVector {k n₁ n₂ : Nat}
    (left : Finset (Fin n₁)) (right : Finset (Fin n₂))
    (x : FieldVector k (n₁ + n₂)) :
    leftPart (restrictVector (appendRegister left right) x) =
      restrictVector left (leftPart x) := by
  funext i
  simp [leftPart, restrictVector, mem_appendRegister_left]

private theorem rightPart_restrictVector {k n₁ n₂ : Nat}
    (left : Finset (Fin n₁)) (right : Finset (Fin n₂))
    (x : FieldVector k (n₁ + n₂)) :
    rightPart (restrictVector (appendRegister left right) x) =
      restrictVector right (rightPart x) := by
  funext i
  simp [rightPart, restrictVector, mem_appendRegister_right]

private noncomputable def directSumLinearMap {k n₁ n₂ : Nat}
    (left : FieldVector k n₁ →ₗ[GaloisField 2 k] FieldVector k n₁)
    (right : FieldVector k n₂ →ₗ[GaloisField 2 k] FieldVector k n₂) :
    FieldVector k (n₁ + n₂) →ₗ[GaloisField 2 k]
      FieldVector k (n₁ + n₂) where
  toFun x := Fin.append (left (leftPart x)) (right (rightPart x))
  map_add' x y := by
    funext i
    refine Fin.addCases (fun j => ?_) (fun j => ?_) i
    · simp only [Fin.append_left, Pi.add_apply]
      change left (leftPart x + leftPart y) j = _
      rw [map_add]
      rfl
    · simp only [Fin.append_right, Pi.add_apply]
      change right (rightPart x + rightPart y) j = _
      rw [map_add]
      rfl
  map_smul' c x := by
    funext i
    refine Fin.addCases (fun j => ?_) (fun j => ?_) i
    · simp only [Fin.append_left, Pi.smul_apply]
      change left (c • leftPart x) j = _
      rw [map_smul]
      rfl
    · simp only [Fin.append_right, Pi.smul_apply]
      change right (c • rightPart x) j = _
      rw [map_smul]
      rfl

private theorem directSumLinearMap_left {k n₁ n₂ : Nat}
    (left : FieldVector k n₁ →ₗ[GaloisField 2 k] FieldVector k n₁)
    (right : FieldVector k n₂ →ₗ[GaloisField 2 k] FieldVector k n₂)
    (x : FieldVector k (n₁ + n₂)) :
    leftPart (directSumLinearMap left right x) = left (leftPart x) := by
  funext i
  simp [directSumLinearMap, leftPart]

private theorem directSumLinearMap_right {k n₁ n₂ : Nat}
    (left : FieldVector k n₁ →ₗ[GaloisField 2 k] FieldVector k n₁)
    (right : FieldVector k n₂ →ₗ[GaloisField 2 k] FieldVector k n₂)
    (x : FieldVector k (n₁ + n₂)) :
    rightPart (directSumLinearMap left right x) = right (rightPart x) := by
  funext i
  simp [directSumLinearMap, rightPart]

private theorem ConditionallyLinearCertificate.directSumSameLevel
    {k n₁ n₂ level : Nat}
    {leftRemaining : Finset (Fin n₁)} {rightRemaining : Finset (Fin n₂)}
    {leftFun : FieldVector k n₁ -> FieldVector k n₁}
    {rightFun : FieldVector k n₂ -> FieldVector k n₂}
    (leftCertificate : ConditionallyLinearCertificate k n₁ leftRemaining level leftFun)
    (rightCertificate : ConditionallyLinearCertificate k n₂ rightRemaining level rightFun) :
    ConditionallyLinearCertificate k (n₁ + n₂)
      (appendRegister leftRemaining rightRemaining) level
      (fun x => Fin.append (leftFun (leftPart x)) (rightFun (rightPart x))) := by
  induction level generalizing leftRemaining rightRemaining leftFun rightFun with
  | zero =>
      cases leftCertificate
      cases rightCertificate
      change ConditionallyLinearCertificate k (n₁ + n₂)
        (appendRegister leftRemaining rightRemaining) 0
        (fun _ => Fin.append (0 : FieldVector k n₁) (0 : FieldVector k n₂))
      have hfun :
          (fun x : FieldVector k (n₁ + n₂) =>
            Fin.append (0 : FieldVector k n₁) (0 : FieldVector k n₂)) =
            (fun _ => 0) := by
        funext x i
        refine Fin.addCases (fun j => ?_) (fun j => ?_) i <;> simp
      rw [hfun]
      exact .zero (appendRegister leftRemaining rightRemaining)
  | succ level ih =>
      cases leftCertificate with
      | step leftHead leftTail leftDisjoint leftCovers leftMap leftSupported
          leftDepends leftNext leftNextCertificate leftToFun =>
        cases rightCertificate with
        | step rightHead rightTail rightDisjoint rightCovers rightMap rightSupported
            rightDepends rightNext rightNextCertificate rightToFun =>
          let head := appendRegister leftHead rightHead
          let tail := appendRegister leftTail rightTail
          let headMap := directSumLinearMap leftMap rightMap
          let leftPrefix : LinearMap.range headMap -> LinearMap.range leftMap :=
            fun pfx => ⟨leftPart pfx.1, by
              rcases pfx.property with ⟨x, hx⟩
              refine ⟨leftPart x, ?_⟩
              rw [← hx]
              exact (directSumLinearMap_left leftMap rightMap x).symm⟩
          let rightPrefix : LinearMap.range headMap -> LinearMap.range rightMap :=
            fun pfx => ⟨rightPart pfx.1, by
              rcases pfx.property with ⟨x, hx⟩
              refine ⟨rightPart x, ?_⟩
              rw [← hx]
              exact (directSumLinearMap_right leftMap rightMap x).symm⟩
          let next : LinearMap.range headMap ->
              FieldVector k (n₁ + n₂) -> FieldVector k (n₁ + n₂) :=
            fun pfx x => Fin.append
              (leftNext (leftPrefix pfx) (leftPart x))
              (rightNext (rightPrefix pfx) (rightPart x))
          refine .step head tail ?_ ?_ headMap ?_ ?_ next ?_ ?_
          · exact appendRegister_disjoint leftDisjoint rightDisjoint
          · simpa [head, tail, leftCovers, rightCovers] using
              appendRegister_union leftHead leftTail rightHead rightTail
          · intro x i hi
            exact Fin.addCases (fun j hnot => by
              change Fin.append (leftMap (leftPart x)) (rightMap (rightPart x))
                (Fin.castAdd n₂ j) = 0
              rw [Fin.append_left]
              apply leftSupported
              intro hj
              exact hnot ((mem_appendRegister_left leftHead rightHead j).mpr hj))
              (fun j hnot => by
              change Fin.append (leftMap (leftPart x)) (rightMap (rightPart x))
                (Fin.natAdd n₁ j) = 0
              rw [Fin.append_right]
              apply rightSupported
              intro hj
              exact hnot ((mem_appendRegister_right leftHead rightHead j).mpr hj))
              i hi
          · intro x
            change Fin.append
                (leftMap (leftPart (restrictVector head x)))
                (rightMap (rightPart (restrictVector head x))) =
              Fin.append (leftMap (leftPart x)) (rightMap (rightPart x))
            rw [show head = appendRegister leftHead rightHead by rfl]
            rw [leftPart_restrictVector, rightPart_restrictVector,
              leftDepends, rightDepends]
          · intro pfx
            exact ih (leftNextCertificate (leftPrefix pfx))
              (rightNextCertificate (rightPrefix pfx))
          · intro x
            let pfx : LinearMap.range headMap :=
              ⟨headMap (restrictVector head x),
                ⟨restrictVector head x, rfl⟩⟩
            let leftPfx : LinearMap.range leftMap :=
              ⟨leftMap (restrictVector leftHead (leftPart x)),
                ⟨restrictVector leftHead (leftPart x), rfl⟩⟩
            let rightPfx : LinearMap.range rightMap :=
              ⟨rightMap (restrictVector rightHead (rightPart x)),
                ⟨restrictVector rightHead (rightPart x), rfl⟩⟩
            have concretePfx_eq :
                (⟨headMap (restrictVector head x),
                  ⟨restrictVector head x, rfl⟩⟩ : LinearMap.range headMap) = pfx := by
              rfl
            have leftHead_eq :
                leftPart (headMap (restrictVector head x)) =
                  leftMap (restrictVector leftHead (leftPart x)) := by
              rw [show head = appendRegister leftHead rightHead by rfl]
              rw [directSumLinearMap_left, leftPart_restrictVector]
            have rightHead_eq :
                rightPart (headMap (restrictVector head x)) =
                  rightMap (restrictVector rightHead (rightPart x)) := by
              rw [show head = appendRegister leftHead rightHead by rfl]
              rw [directSumLinearMap_right, rightPart_restrictVector]
            have leftPrefix_eq : leftPrefix pfx = leftPfx := by
              apply Subtype.ext
              exact leftHead_eq
            have rightPrefix_eq : rightPrefix pfx = rightPfx := by
              apply Subtype.ext
              exact rightHead_eq
            apply funext
            refine Fin.addCases (fun j => ?_) (fun j => ?_)
            · simp only [Fin.append_left, Pi.add_apply]
              rw [concretePfx_eq]
              dsimp only [next]
              simp only [Fin.append_left]
              change leftFun (leftPart x) j =
                leftPart (headMap (restrictVector head x)) j +
                  leftNext (leftPrefix pfx)
                    (leftPart (restrictVector tail x)) j
              rw [leftHead_eq]
              rw [show tail = appendRegister leftTail rightTail by rfl]
              rw [leftPart_restrictVector, leftPrefix_eq]
              exact congrFun (leftToFun (leftPart x)) j
            · simp only [Fin.append_right, Pi.add_apply]
              rw [concretePfx_eq]
              dsimp only [next]
              simp only [Fin.append_right]
              change rightFun (rightPart x) j =
                rightPart (headMap (restrictVector head x)) j +
                  rightNext (rightPrefix pfx)
                    (rightPart (restrictVector tail x)) j
              rw [rightHead_eq]
              rw [show tail = appendRegister leftTail rightTail by rfl]
              rw [rightPart_restrictVector, rightPrefix_eq]
              exact congrFun (rightToFun (rightPart x)) j

/-- Form the coordinatewise direct sum of two CL maps. -/
noncomputable def ConditionallyLinearMap.directSum
    {k n₁ n₂ level₁ level₂ : Nat}
    (L : ConditionallyLinearMap k n₁ level₁)
    (R : ConditionallyLinearMap k n₂ level₂) :
    ConditionallyLinearMap k (n₁ + n₂) (max level₁ level₂) := by
  let level := max level₁ level₂
  let leftCertificate :=
    L.certificate.raiseTo (Nat.le_max_left level₁ level₂)
  let rightCertificate :=
    R.certificate.raiseTo (Nat.le_max_right level₁ level₂)
  let certificate := leftCertificate.directSumSameLevel rightCertificate
  exact {
    toFun := fun x => Fin.append (L (leftPart x)) (R (rightPart x))
    certificate := by
      simpa [level, appendRegister_univ] using certificate
  }

private noncomputable def flattenVectorEquiv (n k : Nat) :
    (Fin n -> Fin k -> ZMod 2) ≃ₗ[ZMod 2] FieldVector 1 (n * k) where
  toFun x := fun ij =>
    (GaloisField.equivZmodP 2).symm
      (x (finProdFinEquiv.symm ij).1 (finProdFinEquiv.symm ij).2)
  invFun y := fun i j =>
    (GaloisField.equivZmodP 2) (y (finProdFinEquiv (i, j)))
  left_inv x := by
    funext i j
    simp only [Equiv.symm_apply_apply]
    exact (GaloisField.equivZmodP 2).right_inv _
  right_inv y := by
    funext ij
    simp only [finProdFinEquiv_symm_apply]
    rw [show finProdFinEquiv (ij.divNat, ij.modNat) = ij by
      exact finProdFinEquiv.apply_symm_apply ij]
    exact (GaloisField.equivZmodP 2).left_inv _
  map_add' x y := by
    funext ij
    simp [map_add]
  map_smul' c x := by
    funext ij
    change (GaloisField.equivZmodP 2).symm
        (c • x (finProdFinEquiv.symm ij).1 (finProdFinEquiv.symm ij).2) =
      c • (GaloisField.equivZmodP 2).symm
        (x (finProdFinEquiv.symm ij).1 (finProdFinEquiv.symm ij).2)
    exact ((GaloisField.equivZmodP 2).symm.toLinearEquiv.map_smul c
      (x (finProdFinEquiv.symm ij).1 (finProdFinEquiv.symm ij).2))

/-- Expand each field coordinate in the selected binary basis. -/
noncomputable def downsizeVector {k : Nat} (D : FieldData k) (n : Nat) :
    FieldVector k n ≃ₗ[ZMod 2] FieldVector 1 (n * k) :=
  (LinearEquiv.piCongrRight (fun _ : Fin n => D.coordinates)).trans
    (flattenVectorEquiv n k)

private noncomputable def expandRegister {n : Nat} (k : Nat)
    (register : Finset (Fin n)) : Finset (Fin (n * k)) :=
  Finset.univ.filter fun ij => (finProdFinEquiv.symm ij).1 ∈ register

@[simp] private theorem mem_expandRegister {n k : Nat}
    {register : Finset (Fin n)} {ij : Fin (n * k)} :
    ij ∈ expandRegister k register ↔
      (finProdFinEquiv.symm ij).1 ∈ register := by
  simp [expandRegister]

@[simp] private theorem expandRegister_union {n k : Nat}
    (left right : Finset (Fin n)) :
    expandRegister k (left ∪ right) =
      expandRegister k left ∪ expandRegister k right := by
  ext ij
  simp

private theorem expandRegister_disjoint {n k : Nat}
    {left right : Finset (Fin n)} (h : Disjoint left right) :
    Disjoint (expandRegister k left) (expandRegister k right) := by
  rw [Finset.disjoint_left]
  intro ij hijLeft hijRight
  exact (Finset.disjoint_left.mp h) (by simpa using hijLeft)
    (by simpa using hijRight)

@[simp] private theorem expandRegister_univ {n k : Nat} :
    expandRegister k (Finset.univ : Finset (Fin n)) = Finset.univ := by
  ext ij
  simp

private theorem downsizeVector_restrict {k n : Nat}
    (D : FieldData k) (register : Finset (Fin n)) (x : FieldVector k n) :
    downsizeVector D n (restrictVector register x) =
      restrictVector (expandRegister k register) (downsizeVector D n x) := by
  ext ij
  simp only [downsizeVector, LinearEquiv.trans_apply, flattenVectorEquiv,
    restrictVector, mem_expandRegister]
  split <;> simp_all [restrictVector]

private theorem downsizeVector_symm_restrict {k n : Nat}
    (D : FieldData k) (register : Finset (Fin n))
    (y : FieldVector 1 (n * k)) :
    (downsizeVector D n).symm
        (restrictVector (expandRegister k register) y) =
      restrictVector register ((downsizeVector D n).symm y) := by
  apply (downsizeVector D n).injective
  rw [downsizeVector_restrict]
  simp

private noncomputable def binaryLinearOfZMod {m : Nat}
    (f : FieldVector 1 m →ₗ[ZMod 2] FieldVector 1 m) :
    FieldVector 1 m →ₗ[GaloisField 2 1] FieldVector 1 m where
  toFun := f
  map_add' := f.map_add
  map_smul' a x := by
    let c : ZMod 2 := GaloisField.equivZmodP 2 a
    have ha : a = algebraMap (ZMod 2) (GaloisField 2 1) c := by
      calc
        a = (GaloisField.equivZmodP 2).symm
            (GaloisField.equivZmodP 2 a) := by simp
        _ = (GaloisField.equivZmodP 2).symm
            (algebraMap (ZMod 2) (ZMod 2) c) := by simp [c]
        _ = algebraMap (ZMod 2) (GaloisField 2 1) c :=
          (GaloisField.equivZmodP 2).symm.commutes c
    rw [ha]
    have hsmul (z : FieldVector 1 m) :
        (algebraMap (ZMod 2) (GaloisField 2 1) c) • z = c • z := by
      ext i
      simp [Algebra.smul_def]
    simp only [RingHom.id_apply]
    rw [hsmul x, hsmul (f x)]
    exact f.map_smul c x

private noncomputable def downsizeLinearMap {k n : Nat}
    (D : FieldData k)
    (headMap : FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n) :
    FieldVector 1 (n * k) →ₗ[GaloisField 2 1] FieldVector 1 (n * k) :=
  binaryLinearOfZMod
    ((downsizeVector D n).toLinearMap.comp
      ((headMap.restrictScalars (ZMod 2)).comp
        (downsizeVector D n).symm.toLinearMap))

@[simp] private theorem downsizeLinearMap_apply {k n : Nat}
    (D : FieldData k)
    (headMap : FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n)
    (y : FieldVector 1 (n * k)) :
    downsizeLinearMap D headMap y =
      downsizeVector D n (headMap ((downsizeVector D n).symm y)) := rfl

private noncomputable def pullbackRange {k n : Nat}
    (D : FieldData k)
    (headMap : FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n)
    (pfx : LinearMap.range (downsizeLinearMap D headMap)) :
    LinearMap.range headMap := by
  refine ⟨(downsizeVector D n).symm pfx.1, ?_⟩
  rcases pfx.2 with ⟨y, hy⟩
  refine ⟨(downsizeVector D n).symm y, ?_⟩
  apply (downsizeVector D n).injective
  simpa using hy

private theorem pullbackRange_restrict {k n : Nat}
    (D : FieldData k)
    (headMap : FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n)
    (register : Finset (Fin n)) (y : FieldVector 1 (n * k)) :
    pullbackRange D headMap
        ⟨downsizeLinearMap D headMap
            (restrictVector (expandRegister k register) y),
          ⟨restrictVector (expandRegister k register) y, rfl⟩⟩ =
      ⟨headMap (restrictVector register ((downsizeVector D n).symm y)),
        ⟨restrictVector register ((downsizeVector D n).symm y), rfl⟩⟩ := by
  apply Subtype.ext
  simp only [pullbackRange, downsizeLinearMap_apply,
    LinearEquiv.symm_apply_apply, downsizeVector_symm_restrict]

private theorem ConditionallyLinearCertificate.downsize
    {k n level : Nat} {remaining : Finset (Fin n)}
    {toFun : FieldVector k n -> FieldVector k n}
    (D : FieldData k)
    (certificate :
      ConditionallyLinearCertificate k n remaining level toFun) :
    ConditionallyLinearCertificate 1 (n * k) (expandRegister k remaining) level
      (fun y => downsizeVector D n
        (toFun ((downsizeVector D n).symm y))) := by
  induction certificate with
  | zero remaining =>
      simpa using
        (ConditionallyLinearCertificate.zero (k := 1) (n := n * k)
          (expandRegister k remaining))
  | @step remaining level toFun head tail disjoint covers headMap
      headSupported headDepends next nextCertificate toFunEq ih =>
      let downsizedHead := downsizeLinearMap D headMap
      let downsizedNext : LinearMap.range downsizedHead ->
          FieldVector 1 (n * k) -> FieldVector 1 (n * k) :=
        fun pfx y => downsizeVector D n
          (next (pullbackRange D headMap pfx)
            ((downsizeVector D n).symm y))
      refine .step (expandRegister k head) (expandRegister k tail)
        (expandRegister_disjoint disjoint) ?_ downsizedHead ?_ ?_
        downsizedNext ?_ ?_
      · rw [← expandRegister_union, covers]
      · intro y ij hij
        have hsupported (z : FieldVector k n) :
            headMap z = restrictVector head (headMap z) := by
          ext i
          by_cases hi : i ∈ head
          · simp [restrictVector, hi]
          · simp [restrictVector, hi, headSupported z i hi]
        have htarget :
            downsizedHead y =
              restrictVector (expandRegister k head) (downsizedHead y) := by
          calc
            downsizedHead y = downsizeVector D n
                (headMap ((downsizeVector D n).symm y)) := rfl
            _ = downsizeVector D n
                (restrictVector head
                  (headMap ((downsizeVector D n).symm y))) :=
              congrArg (downsizeVector D n) (hsupported _)
            _ = restrictVector (expandRegister k head)
                (downsizeVector D n
                  (headMap ((downsizeVector D n).symm y))) :=
              downsizeVector_restrict D head _
            _ = restrictVector (expandRegister k head)
                (downsizedHead y) := rfl
        rw [htarget]
        simp [restrictVector, hij]
      · intro y
        simp only [downsizedHead, downsizeLinearMap_apply]
        rw [downsizeVector_symm_restrict, headDepends]
      · intro pfx
        simpa only [downsizedNext] using
          ih (pullbackRange D headMap pfx)
      · intro y
        let sourcePrefix : LinearMap.range headMap :=
          ⟨headMap (restrictVector head ((downsizeVector D n).symm y)),
            ⟨restrictVector head ((downsizeVector D n).symm y), rfl⟩⟩
        let targetPrefix : LinearMap.range downsizedHead :=
          ⟨downsizedHead (restrictVector (expandRegister k head) y),
            ⟨restrictVector (expandRegister k head) y, rfl⟩⟩
        have hprefix :
            pullbackRange D headMap targetPrefix = sourcePrefix := by
          dsimp only [targetPrefix, sourcePrefix, downsizedHead]
          exact pullbackRange_restrict D headMap head y
        change downsizeVector D n
            (toFun ((downsizeVector D n).symm y)) =
          downsizedHead (restrictVector (expandRegister k head) y) +
            downsizedNext targetPrefix
              (restrictVector (expandRegister k tail) y)
        rw [toFunEq, (downsizeVector D n).map_add]
        change
          downsizeVector D n
              (headMap (restrictVector head ((downsizeVector D n).symm y))) +
            downsizeVector D n
              (next sourcePrefix
                (restrictVector tail ((downsizeVector D n).symm y))) =
          downsizeVector D n
              (headMap ((downsizeVector D n).symm
                (restrictVector (expandRegister k head) y))) +
            downsizeVector D n
              (next (pullbackRange D headMap targetPrefix)
                ((downsizeVector D n).symm
                  (restrictVector (expandRegister k tail) y)))
        rw [downsizeVector_symm_restrict, downsizeVector_symm_restrict,
          hprefix]

/-- Conjugate a CL map through the selected binary coordinate equivalence. -/
noncomputable def ConditionallyLinearMap.downsize
    {k n level : Nat} (D : FieldData k)
    (L : ConditionallyLinearMap k n level) :
    ConditionallyLinearMap 1 (n * k) level where
  toFun y := downsizeVector D n
    (L.toFun ((downsizeVector D n).symm y))
  certificate := by
    simpa using L.certificate.downsize D

private theorem uniform_map_equiv
    {alpha beta : Type*} [Fintype alpha] [Nonempty alpha]
    [Fintype beta] [Nonempty beta] (equiv : alpha ≃ beta) :
    (PMF.uniformOfFintype alpha).map equiv =
      PMF.uniformOfFintype beta := by
  apply PMF.ext
  intro b
  rw [PMF.map_apply]
  simp only [PMF.uniformOfFintype_apply]
  rw [tsum_eq_single (equiv.symm b)]
  · simp [Fintype.card_congr equiv]
  · intro a ha
    simp only [ite_eq_right_iff]
    intro h
    have hab : a = equiv.symm b := by
      apply equiv.injective
      exact h.symm.trans (equiv.apply_symm_apply b).symm
    exact (ha hab).elim

private theorem uniform_product
    {alpha beta : Type*} [Fintype alpha] [Nonempty alpha]
    [Fintype beta] [Nonempty beta] :
    (PMF.uniformOfFintype alpha).bind (fun a =>
      (PMF.uniformOfFintype beta).map fun b => (a, b)) =
      PMF.uniformOfFintype (alpha × beta) := by
  apply PMF.ext
  rintro ⟨a, b⟩
  simp only [PMF.bind_apply, PMF.map_apply,
    PMF.uniformOfFintype_apply]
  rw [tsum_eq_single a]
  · rw [tsum_eq_single b]
    · simp [Fintype.card_prod, ENNReal.mul_inv]
    · intro y hy
      simp [hy.symm]
  · intro x hx
    simp [hx.symm]

private theorem uniform_fin_append
    {alpha : Type*} [Fintype alpha] [Nonempty alpha]
    (leftSize rightSize : Nat) :
    (PMF.uniformOfFintype (Fin leftSize -> alpha)).bind (fun left =>
      (PMF.uniformOfFintype (Fin rightSize -> alpha)).map fun right =>
        Fin.append left right) =
      PMF.uniformOfFintype (Fin (leftSize + rightSize) -> alpha) := by
  rw [← uniform_map_equiv (Fin.appendEquiv leftSize rightSize)]
  rw [← uniform_product]
  rw [PMF.map_bind]
  congr 1
  funext left
  rw [PMF.map_comp]
  rfl

@[simp] private theorem ConditionallyLinearMap.directSum_apply_append
    {k n₁ n₂ level₁ level₂ : Nat}
    (L : ConditionallyLinearMap k n₁ level₁)
    (R : ConditionallyLinearMap k n₂ level₂)
    (left : FieldVector k n₁) (right : FieldVector k n₂) :
    (L.directSum R) (Fin.append left right) =
      Fin.append (L left) (R right) := by
  have hleft : leftPart (Fin.append left right) = left := by
    funext i
    simp [leftPart]
  have hright : rightPart (Fin.append left right) = right := by
    funext i
    simp [rightPart]
  change Fin.append (L (leftPart (Fin.append left right)))
    (R (rightPart (Fin.append left right))) = _
  rw [hleft, hright]

/-- Two CL maps applied to one shared uniform seed. -/
structure CLSampler (k n level : Nat) where
  alice : ConditionallyLinearMap k n level
  bob : ConditionallyLinearMap k n level

/-- The CL distribution induced by a sampler's shared seed. -/
noncomputable def CLSampler.sample {k n level : Nat}
    (S : CLSampler k n level) :
    PMF (FieldVector k n × FieldVector k n) :=
  (PMF.uniformOfFintype (FieldVector k n)).map fun x =>
    (S.alice x, S.bob x)

/-- Form the independent coordinate direct sum of two CL samplers. -/
noncomputable def CLSampler.directSum
    {k n₁ n₂ level₁ level₂ : Nat}
    (S : CLSampler k n₁ level₁) (T : CLSampler k n₂ level₂) :
    CLSampler k (n₁ + n₂) (max level₁ level₂) where
  alice := S.alice.directSum T.alice
  bob := S.bob.directSum T.bob

/-- Direct sums turn the uniform seed into independent component seeds. -/
theorem CLSampler.sample_directSum
    {k n₁ n₂ level₁ level₂ : Nat}
    (S : CLSampler k n₁ level₁) (T : CLSampler k n₂ level₂) :
    (S.directSum T).sample =
      S.sample.bind fun left =>
        T.sample.map fun right =>
          (Fin.append left.1 right.1, Fin.append left.2 right.2) := by
  unfold CLSampler.sample
  rw [← uniform_fin_append n₁ n₂]
  rw [PMF.map_bind]
  rw [PMF.bind_map]
  congr 1
  funext left
  rw [PMF.map_comp]
  simp only [Function.comp_apply]
  rw [PMF.map_comp]
  congr 1
  funext right
  simp [CLSampler.directSum]

/-- Downsize both maps of a CL sampler in the same selected basis. -/
noncomputable def CLSampler.downsize
    {k n level : Nat} (D : FieldData k) (S : CLSampler k n level) :
    CLSampler 1 (n * k) level where
  alice := S.alice.downsize D
  bob := S.bob.downsize D

/-- Downsizing a sampler pushes its output distribution through coordinates. -/
theorem CLSampler.sample_downsize
    {k n level : Nat} (D : FieldData k) (S : CLSampler k n level) :
    (S.downsize D).sample =
      PMF.map (fun pair =>
        (downsizeVector D n pair.1, downsizeVector D n pair.2)) S.sample := by
  let equiv := downsizeVector D n
  have huniform :
      (PMF.uniformOfFintype (FieldVector k n)).map equiv =
        PMF.uniformOfFintype (FieldVector 1 (n * k)) :=
    uniform_map_equiv equiv.toEquiv
  change
    (PMF.uniformOfFintype (FieldVector 1 (n * k))).map
        (fun y =>
          (equiv (S.alice.toFun (equiv.symm y)),
            equiv (S.bob.toFun (equiv.symm y)))) =
      ((PMF.uniformOfFintype (FieldVector k n)).map
          (fun x => (S.alice.toFun x, S.bob.toFun x))).map
        (fun pair => (equiv pair.1, equiv pair.2))
  rw [← huniform, PMF.map_comp, PMF.map_comp]
  congr 1
  funext x
  simp

noncomputable section

/-! ## Executable conditionally-linear samplers

This section formalizes `conditionally-linear.tex:553-712`.  The logical
six-tape interface is serialized only at the `FinTM2` boundary; every public
query uses the canonical blank payloads from the paper-facing contract.
-/

/-- An admissible characteristic-two field family, indexed by positive naturals. -/
structure AdmissibleFieldFamily where
  exponent : Nat -> Nat
  exponent_odd : forall n, 0 < n -> Odd (exponent n)

/-- The cardinality of the indexed admissible field. -/
def AdmissibleFieldFamily.fieldSize
    (Q : AdmissibleFieldFamily) (n : Nat) : Nat :=
  2 ^ Q.exponent n

/-- The canonical F01 field data selected at a positive index. -/
noncomputable def AdmissibleFieldFamily.fieldData
    (Q : AdmissibleFieldFamily) (n : Nat) (hn : 0 < n) :
    FieldData (Q.exponent n) :=
  fieldDataOfOddExponent (Q.exponent n) (Q.exponent_odd n hn)

private theorem zmodTwo_eq_zero_or_one (x : ZMod 2) : x = 0 ∨ x = 1 := by
  have hlt : x.val < 2 := ZMod.val_lt x
  have hx : x.val = 0 ∨ x.val = 1 := by omega
  rcases hx with hx | hx
  · left
    apply ZMod.val_injective
    simp [hx]
  · right
    apply ZMod.val_injective
    rw [ZMod.val_one]
    exact hx

private def zmodTwoEquivBool : ZMod 2 ≃ Bool where
  toFun x := decide (x = 1)
  invFun bit := if bit then 1 else 0
  left_inv x := by
    rcases zmodTwo_eq_zero_or_one x with rfl | rfl <;> simp
  right_inv bit := by
    cases bit <;> simp

private noncomputable def fieldVectorBitsEquiv
    {k dimension : Nat} (D : FieldData k) :
    FieldVector k dimension ≃ (Fin (dimension * k) -> Bool) where
  toFun x ij := zmodTwoEquivBool
    (D.coordinates (x (finProdFinEquiv.symm ij).1)
      (finProdFinEquiv.symm ij).2)
  invFun bits i := D.coordinates.symm fun j =>
    zmodTwoEquivBool.symm (bits (finProdFinEquiv (i, j)))
  left_inv x := by
    funext i
    apply D.coordinates.injective
    funext j
    simp
  right_inv bits := by
    funext ij
    change zmodTwoEquivBool
        ((D.coordinates
          (D.coordinates.symm (fun j =>
            zmodTwoEquivBool.symm
              (bits (finProdFinEquiv ((finProdFinEquiv.symm ij).1, j))))))
          (finProdFinEquiv.symm ij).2) = bits ij
    rw [D.coordinates.apply_symm_apply, zmodTwoEquivBool.apply_symm_apply]
    exact congrArg bits (finProdFinEquiv.apply_symm_apply ij)

@[simp] private theorem fieldVectorBitsEquiv_apply
    {k dimension : Nat} (D : FieldData k) (x : FieldVector k dimension)
    (ij : Fin (dimension * k)) :
    fieldVectorBitsEquiv D x ij = zmodTwoEquivBool
      (D.coordinates (x (finProdFinEquiv.symm ij).1)
        (finProdFinEquiv.symm ij).2) :=
  rfl

private noncomputable def encodingOfBoolVectorEquiv
    {alpha : Type*} {width : Nat} (e : alpha ≃ (Fin width -> Bool)) :
    Computability.Encoding alpha Bool where
  encode x := List.ofFn (e x)
  decode bits := if h : bits.length = width then
    some (e.symm fun i => bits.get ⟨i.val, by omega⟩)
  else none
  decode_encode x := by
    simp only [List.length_ofFn, ↓reduceDIte]
    congr 1
    apply e.injective
    funext i
    simp

/-- The fixed-order F01 coordinate encoding of field vectors as bit strings. -/
noncomputable def AdmissibleFieldFamily.fieldCodec
    (Q : AdmissibleFieldFamily) (n dimension : Nat) (hn : 0 < n) :
    Computability.Encoding (FieldVector (Q.exponent n) dimension) Bool :=
  encodingOfBoolVectorEquiv (fieldVectorBitsEquiv (Q.fieldData n hn))

/-- The constant family of binary fields. -/
def binaryFieldFamily : AdmissibleFieldFamily where
  exponent := fun _ => 1
  exponent_odd := by
    intro n hn
    exact odd_one

/-- The paper's global-positive-index big-O relation. -/
def RuntimeBigO (f g : Nat -> Nat) : Prop :=
  Exists fun C : Real => 0 < C /\ forall n, 0 < n ->
    (f n : Real) <= C * (g n : Real)

/-- Six logical binary input tapes, in their fixed paper order. -/
abbrev SixTapeInput := Fin 6 -> List Bool

/-- Assemble the six logical tapes in order. -/
def SixTapeInput.ofLists
    (tape0 tape1 tape2 tape3 tape4 tape5 : List Bool) : SixTapeInput :=
  ![tape0, tape1, tape2, tape3, tape4, tape5]

/-- The canonical input used to compute a field exponent from an index. -/
def fieldExponentInput (n : Nat) : SixTapeInput :=
  SixTapeInput.ofLists (Computability.encodeNat n) [] [] [] [] []

namespace CLStage

/-- The stage immediately before a nonzero zero-based stage. -/
def pred {ell : Nat} (j : Fin ell) (h : 0 < j.val) : Fin ell :=
  ⟨j.val - 1, by omega⟩

/-- Include an earlier stage in the ambient stage type. -/
def castLE {ell : Nat} (j : Fin ell) (i : Fin (j.val + 1)) : Fin ell :=
  ⟨i.val, by omega⟩

/-- The last stage of a nonempty level family. -/
def last (ell : Nat) (h : 0 < ell) : Fin ell :=
  ⟨ell - 1, by omega⟩

end CLStage

/-- The two maps sampled by a CL sampler. -/
inductive CLSamplerSide
  | alice
  | bob
  deriving DecidableEq, Fintype

/-- The canonical one-bit side tag. -/
def CLSamplerSide.bits : CLSamplerSide -> List Bool
  | .alice => [false]
  | .bob => [true]

/-- Select one of the two maps carried by a CL sampler. -/
def CLSampler.side {k n ell : Nat} (S : CLSampler k n ell) :
    CLSamplerSide -> ConditionallyLinearMap k n ell
  | .alice => S.alice
  | .bob => S.bob

/-- A valid output prefix of the preceding marginal map. -/
abbrev CLPrefix {k n : Nat}
    (priorOutput : FieldVector k n -> FieldVector k n) :=
  {u : FieldVector k n // Exists fun x => u = priorOutput x}

/-- A vector supported on one selected coordinate factor. -/
abbrev CLFactorInput {k n : Nat} (factor : Finset (Fin n)) :=
  {y : FieldVector k n // forall i, i ∉ factor -> y i = 0}

/-- Data-valued marginal/factor decomposition satisfying the CL recursion laws. -/
structure CLQueryDecomposition
    {k n ell : Nat} (L : ConditionallyLinearMap k n ell) where
  marginal : (j : Fin ell) -> ConditionallyLinearMap k n (j.val + 1)
  priorOutput : Fin ell -> FieldVector k n -> FieldVector k n
  priorOutput_zero : forall (j : Fin ell), j.val = 0 ->
    priorOutput j = 0
  priorOutput_succ : forall (j : Fin ell) (h : 0 < j.val),
    priorOutput j = (marginal (CLStage.pred j h)).toFun
  factor : (j : Fin ell) -> CLPrefix (priorOutput j) -> Finset (Fin n)
  linear : (j : Fin ell) -> (u : CLPrefix (priorOutput j)) ->
    FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n
  factor_cover : forall (x : FieldVector k n) (i : Fin n),
    Exists fun j : Fin ell =>
      i ∈ factor j ⟨priorOutput j x, ⟨x, rfl⟩⟩
  factor_disjoint : forall (x : FieldVector k n) (j1 j2 : Fin ell),
    j1 ≠ j2 -> Disjoint
      (factor j1 ⟨priorOutput j1 x, ⟨x, rfl⟩⟩)
      (factor j2 ⟨priorOutput j2 x, ⟨x, rfl⟩⟩)
  linear_supported : forall (j : Fin ell) (u : CLPrefix (priorOutput j))
      (y : FieldVector k n) (i : Fin n),
    i ∉ factor j u -> linear j u y i = 0
  linear_depends : forall (j : Fin ell) (u : CLPrefix (priorOutput j))
      (y : FieldVector k n),
    linear j u (restrictVector (factor j u) y) = linear j u y
  marginal_sum : forall (j : Fin ell) (x : FieldVector k n),
    (marginal j).toFun x =
      ∑ i : Fin (j.val + 1),
        linear (CLStage.castLE j i)
          ⟨priorOutput (CLStage.castLE j i) x, ⟨x, rfl⟩⟩
          (restrictVector
            (factor (CLStage.castLE j i)
              ⟨priorOutput (CLStage.castLE j i) x, ⟨x, rfl⟩⟩) x)
  marginal_top : forall h : 0 < ell,
    (marginal (CLStage.last ell h)).toFun = L.toFun

/-- The four valid semantic query modes of an executable CL sampler. -/
inductive CLSamplerQuery
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell n : Nat) (hn : 0 < n)
    (associated : CLSampler (Q.exponent n) (s n) ell)
    (decomposition : (w : CLSamplerSide) ->
      CLQueryDecomposition (associated.side w))
  | dimension
  | marginal (w : CLSamplerSide) (j : Fin ell)
      (z : FieldVector (Q.exponent n) (s n))
  | linear (w : CLSamplerSide) (j : Fin ell)
      (u : CLPrefix ((decomposition w).priorOutput j))
      (y : CLFactorInput (k := Q.exponent n)
        ((decomposition w).factor j u))
  | factor (w : CLSamplerSide) (j : Fin ell)
      (u : CLPrefix ((decomposition w).priorOutput j))

variable {Q : AdmissibleFieldFamily} {s : Nat -> Nat}
  {ell n : Nat} {hn : 0 < n}

private abbrev CLSamplerQuery.FiniteCode
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell n : Nat) :=
  Unit ⊕
    (CLSamplerSide × Fin ell × FieldVector (Q.exponent n) (s n)) ⊕
    (CLSamplerSide × Fin ell × FieldVector (Q.exponent n) (s n) ×
      FieldVector (Q.exponent n) (s n)) ⊕
    (CLSamplerSide × Fin ell × FieldVector (Q.exponent n) (s n))

private def CLSamplerQuery.finiteCode :
    CLSamplerQuery Q s ell n hn A D -> CLSamplerQuery.FiniteCode Q s ell n
  | .dimension => .inl ()
  | .marginal w j z => .inr (.inl (w, j, z))
  | .linear w j u y => .inr (.inr (.inl (w, j, u.1, y.1)))
  | .factor w j u => .inr (.inr (.inr (w, j, u.1)))

private theorem CLSamplerQuery.finiteCode_injective :
    Function.Injective
      (CLSamplerQuery.finiteCode (Q := Q) (s := s) (ell := ell)
        (n := n) (hn := hn) (A := A) (D := D)) := by
  intro left right h
  cases left <;> cases right <;> simp_all [finiteCode]
  · rcases h with ⟨rfl, rfl, hu, hy⟩
    have hu' : _ = _ := Subtype.ext hu
    subst hu'
    exact ⟨HEq.rfl, heq_of_eq (Subtype.ext hy)⟩
  · rcases h with ⟨rfl, rfl, hu⟩
    exact heq_of_eq (Subtype.ext hu)

/-- Valid semantic sampler queries form a finite family at each index. -/
noncomputable instance CLSamplerQuery.instFintype
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell n : Nat) (hn : 0 < n)
    (A : CLSampler (Q.exponent n) (s n) ell)
    (D : (w : CLSamplerSide) -> CLQueryDecomposition (A.side w)) :
    Fintype (CLSamplerQuery Q s ell n hn A D) :=
  Fintype.ofInjective
    (CLSamplerQuery.finiteCode (Q := Q) (s := s) (ell := ell)
      (n := n) (hn := hn) (A := A) (D := D))
    CLSamplerQuery.finiteCode_injective

/-- Recover the family index of a typed query. -/
def CLSamplerQuery.index : CLSamplerQuery Q s ell n hn A D -> Nat :=
  fun _ => n

/-- The canonical six tapes for a typed query, with unused tapes blank. -/
def CLSamplerQuery.canonicalTapes :
    CLSamplerQuery Q s ell n hn A D -> SixTapeInput
  | .dimension =>
      SixTapeInput.ofLists (Computability.encodeNat n) [false, false]
        [] [] [] []
  | .marginal w j z =>
      SixTapeInput.ofLists (Computability.encodeNat n) w.bits [false, true]
        (Computability.encodeNat (j.val + 1))
        ((Q.fieldCodec n (s n) hn).encode z) []
  | .linear w j u y =>
      SixTapeInput.ofLists (Computability.encodeNat n) w.bits [true, false]
        (Computability.encodeNat (j.val + 1))
        ((Q.fieldCodec n (s n) hn).encode u.1)
        ((Q.fieldCodec n (s n) hn).encode y.1)
  | .factor w j u =>
      SixTapeInput.ofLists (Computability.encodeNat n) w.bits [true, true]
        (Computability.encodeNat (j.val + 1))
        ((Q.fieldCodec n (s n) hn).encode u.1) []

/-- The exact bit-string answer associated with a typed query. -/
def CLSamplerQuery.expectedOutput :
    CLSamplerQuery Q s ell n hn A D -> List Bool
  | .dimension => Computability.encodeNat (s n)
  | .marginal w j z =>
      (Q.fieldCodec n (s n) hn).encode ((D w).marginal j z)
  | .linear w j u y =>
      (Q.fieldCodec n (s n) hn).encode ((D w).linear j u y.1)
  | .factor w j u =>
      List.ofFn (fun i : Fin (s n) => decide (i ∈ (D w).factor j u))

/-- Injectively serialize the six ordered logical tapes onto one bit stack. -/
def packSixTapes (input : SixTapeInput) : List Bool :=
  (List.ofFn input).flatMap fun tape =>
    tape.flatMap (fun bit =>
      match bit with
      | false => [false, true]
      | true => [true, false]) ++ [false, false]

private def unpackDualRailTape : List Bool -> List Bool × List Bool
  | false :: false :: rest => ([], rest)
  | false :: true :: rest =>
      let decoded := unpackDualRailTape rest
      (false :: decoded.1, decoded.2)
  | true :: false :: rest =>
      let decoded := unpackDualRailTape rest
      (true :: decoded.1, decoded.2)
  | _ => ([], [])

private def unpackDualRailTapes : Nat -> List Bool -> List (List Bool)
  | 0, _ => []
  | count + 1, bits =>
      let decoded := unpackDualRailTape bits
      decoded.1 :: unpackDualRailTapes count decoded.2

private theorem unpackDualRailTape_encode (tape rest : List Bool) :
    unpackDualRailTape
        (tape.flatMap (fun bit =>
          match bit with
          | false => [false, true]
          | true => [true, false]) ++ [false, false] ++ rest) =
      (tape, rest) := by
  induction tape with
  | nil => rfl
  | cons bit tape ih =>
      have ih' :
          unpackDualRailTape
              (tape.flatMap (fun bit =>
                match bit with
                | false => [false, true]
                | true => [true, false]) ++ false :: false :: rest) =
            (tape, rest) := by
        simpa only [List.append_assoc, List.cons_append, List.nil_append] using ih
      cases bit <;> simp [unpackDualRailTape, ih']

private theorem unpackDualRailTapes_encode (tapes : List (List Bool)) :
    unpackDualRailTapes tapes.length
        (tapes.flatMap fun tape =>
          tape.flatMap (fun bit =>
            match bit with
            | false => [false, true]
            | true => [true, false]) ++ [false, false]) =
      tapes := by
  induction tapes with
  | nil => rfl
  | cons tape tapes ih =>
      simp only [List.length_cons, List.flatMap_cons]
      rw [unpackDualRailTapes]
      rw [unpackDualRailTape_encode]
      simp only [ih]

/-- Six-tape serialization is injective. -/
theorem packSixTapes_injective : Function.Injective packSixTapes := by
  intro left right h
  apply List.ofFn_injective
  have left_inverse := unpackDualRailTapes_encode (List.ofFn left)
  have right_inverse := unpackDualRailTapes_encode (List.ofFn right)
  simp only [List.length_ofFn] at left_inverse right_inverse
  have packed_eq :
      (List.ofFn left).flatMap (fun tape =>
          tape.flatMap (fun bit =>
            match bit with
            | false => [false, true]
            | true => [true, false]) ++ [false, false]) =
        (List.ofFn right).flatMap (fun tape =>
          tape.flatMap (fun bit =>
            match bit with
            | false => [false, true]
            | true => [true, false]) ++ [false, false]) := by
    simpa only [packSixTapes] using h
  rw [← left_inverse, ← right_inverse, packed_eq]

/-- A finite stack machine with Boolean input and output alphabets. -/
structure IndexedSixInputBitMachine where
  tm : Turing.FinTM2
  inputAlphabet : tm.Γ tm.k₀ ≃ Bool
  outputAlphabet : tm.Γ tm.k₁ ≃ Bool

/-- Operational execution of a packed six-tape query within a stated bound. -/
def IndexedSixInputBitMachine.outputsInTime
    (M : IndexedSixInputBitMachine) (input : SixTapeInput)
    (output : List Bool) (bound : Nat) :=
  Turing.TM2OutputsInTime M.tm
    ((packSixTapes input).map M.inputAlphabet.symm)
    (some (output.map M.outputAlphabet.symm)) bound

/-- One genuine operational execution with its certified bound. -/
structure IndexedSixInputBitMachine.Execution
    (M : IndexedSixInputBitMachine) (input : SixTapeInput)
    (output : List Bool) where
  bound : Nat
  runInTime : M.outputsInTime input output bound

/-- The exact number of transitions in an operational execution. -/
def IndexedSixInputBitMachine.Execution.steps
    {M : IndexedSixInputBitMachine} {input : SixTapeInput}
    {output : List Bool} (execution : M.Execution input output) : Nat :=
  execution.runInTime.toEvalsTo.steps

/-- Intrinsic code computing the admissible exponent from every positive index. -/
structure FieldExponentProgram (Q : AdmissibleFieldFamily) where
  machine : IndexedSixInputBitMachine
  execution : forall n, 0 < n ->
    machine.Execution (fieldExponentInput n)
      (Computability.encodeNat (Q.exponent n))

/-- Forget the resource bound of an exponent-program execution. -/
def FieldExponentProgram.correct
    (P : FieldExponentProgram Q) (n : Nat) (hn : 0 < n) :
    Turing.TM2Outputs P.machine.tm
      ((packSixTapes (fieldExponentInput n)).map
        P.machine.inputAlphabet.symm)
      (some ((Computability.encodeNat (Q.exponent n)).map
        P.machine.outputAlphabet.symm)) :=
  Turing.TM2OutputsInTime.toTM2Outputs (P.execution n hn).runInTime

/-- The exact transition count of the exponent program at an index. -/
def FieldExponentProgram.steps
    (P : FieldExponentProgram Q) (n : Nat) (hn : 0 < n) : Nat :=
  (P.execution n hn).steps

/-- A source sampler with chosen CL data and genuine query/exponent executions. -/
structure ExecutableCLSampler
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell : Nat) where
  associated : forall n, CLSampler (Q.exponent n) (s n) ell
  decomposition : forall n (w : CLSamplerSide),
    CLQueryDecomposition ((associated n).side w)
  machine : IndexedSixInputBitMachine
  execution : forall n (hn : 0 < n)
      (query : CLSamplerQuery Q s ell n hn (associated n) (decomposition n)),
    machine.Execution query.canonicalTapes query.expectedOutput
  fieldProgram : FieldExponentProgram Q

/-- Forget the resource bound of a source sampler execution. -/
def ExecutableCLSampler.correct
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n)
    (query : CLSamplerQuery Q s ell n hn (S.associated n) (S.decomposition n)) :
    Turing.TM2Outputs S.machine.tm
      ((packSixTapes query.canonicalTapes).map S.machine.inputAlphabet.symm)
      (some (query.expectedOutput.map S.machine.outputAlphabet.symm)) :=
  Turing.TM2OutputsInTime.toTM2Outputs (S.execution n hn query).runInTime

/-- The exact transition count of one valid sampler query. -/
def ExecutableCLSampler.executedSteps
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n)
    (query : CLSamplerQuery Q s ell n hn (S.associated n) (S.decomposition n)) : Nat :=
  (S.execution n hn query).steps

/-- The finite set of all valid semantic queries at one positive index. -/
noncomputable def ExecutableCLSampler.validQueries
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    Finset (CLSamplerQuery Q s ell n hn (S.associated n) (S.decomposition n)) :=
  Finset.univ

/-- The exact maximum transition count over valid queries at an index. -/
noncomputable def ExecutableCLSampler.queryTime
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) : Nat :=
  (S.validQueries n hn).sup (S.executedSteps n hn)

/-- `queryTime` is definitionally the valid-query maximum. -/
theorem ExecutableCLSampler.queryTime_eq_validQueryMax
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    S.queryTime n hn =
      (S.validQueries n hn).sup (S.executedSteps n hn) :=
  rfl

/-- Source time charges both sampler queries and intrinsic exponent computation. -/
noncomputable def ExecutableCLSampler.time
    (S : ExecutableCLSampler Q s ell) (n : Nat) : Nat :=
  if hn : 0 < n then
    Nat.max (S.queryTime n hn) (S.fieldProgram.steps n hn)
  else 0

/-- At a positive index, source time is the exact maximum of its two components. -/
theorem ExecutableCLSampler.time_eq_max
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    S.time n = Nat.max (S.queryTime n hn) (S.fieldProgram.steps n hn) := by
  simp [ExecutableCLSampler.time, hn]

/-- The exact shared-seed distribution associated with an executable sampler. -/
noncomputable def ExecutableCLSampler.sample
    (S : ExecutableCLSampler Q s ell) (n : Nat) :
    PMF (FieldVector (Q.exponent n) (s n) ×
      FieldVector (Q.exponent n) (s n)) :=
  (S.associated n).sample

/-- The field-vector dimension returned by the sampler. -/
def ExecutableCLSampler.dimension
    (_S : ExecutableCLSampler Q s ell) (n : Nat) : Nat :=
  s n

/-- One of the two associated conditionally-linear maps. -/
def ExecutableCLSampler.associatedMap
    (S : ExecutableCLSampler Q s ell) (n : Nat) (w : CLSamplerSide) :
    ConditionallyLinearMap (Q.exponent n) (s n) ell :=
  (S.associated n).side w

private theorem FieldData.basis_zero_eq_one (D : FieldData 1) :
    D.basis 0 = 1 := by
  have hb : D.basis 0 ≠ 0 := D.basis.ne_zero 0
  apply (GaloisField.equivZmodP 2).injective
  rw [map_one]
  rcases zmodTwo_eq_zero_or_one
      (GaloisField.equivZmodP 2 (D.basis 0)) with hz | hz
  · exfalso
    apply hb
    apply (GaloisField.equivZmodP 2).injective
    simpa using hz
  · exact hz

private theorem FieldData.coordinates_one_eq (D : FieldData 1)
    (x : GaloisField 2 1) :
    D.coordinates x 0 = GaloisField.equivZmodP 2 x := by
  have hx : D.coordinates x 0 • D.basis 0 = x := by
    simpa [FieldData.coordinates] using D.basis.sum_repr x
  rw [D.basis_zero_eq_one] at hx
  have mapped := congrArg (GaloisField.equivZmodP 2) hx
  simpa using mapped

private theorem flatten_ofFn_singleton {alpha : Type*} {width : Nat}
    (f : Fin width -> alpha) :
    (List.ofFn fun i => [f i]).flatten = List.ofFn f := by
  induction width with
  | zero => simp
  | succ width ih =>
      simp only [List.ofFn_succ, List.flatten_cons, List.singleton_append]
      rw [ih]

private theorem AdmissibleFieldFamily.fieldCodec_encode_downsize
    (Q : AdmissibleFieldFamily) (n dimension : Nat) (hn : 0 < n)
    (x : FieldVector (Q.exponent n) dimension) :
    (binaryFieldFamily.fieldCodec n (dimension * Q.exponent n) hn).encode
      (downsizeVector (Q.fieldData n hn) dimension x) =
      (Q.fieldCodec n dimension hn).encode x := by
  change List.ofFn
      (fieldVectorBitsEquiv (binaryFieldFamily.fieldData n hn)
        (downsizeVector (Q.fieldData n hn) dimension x)) =
    List.ofFn (fieldVectorBitsEquiv (Q.fieldData n hn) x)
  change List.ofFn
      (fieldVectorBitsEquiv (fieldDataOfOddExponent 1 odd_one)
        (downsizeVector (Q.fieldData n hn) dimension x)) =
    List.ofFn (fieldVectorBitsEquiv (Q.fieldData n hn) x)
  rw [List.ofFn_mul]
  simp only [List.ofFn_succ, List.ofFn_zero]
  rw [flatten_ofFn_singleton]
  congr 1
  funext i
  rw [show
    (⟨i.val * 1 + (0 : Fin 1).val, by omega⟩ :
      Fin ((dimension * Q.exponent n) * 1)) =
        finProdFinEquiv (i, (0 : Fin 1)) by
    apply Fin.ext
    simp [finProdFinEquiv]]
  simp only [fieldVectorBitsEquiv_apply, Equiv.symm_apply_apply]
  rw [(fieldDataOfOddExponent 1 odd_one).coordinates_one_eq]
  simp [downsizeVector, flattenVectorEquiv]

private noncomputable def zeroConditionallyLinearMap
    (k n ell : Nat) : ConditionallyLinearMap k n ell where
  toFun := fun _ => 0
  certificate := by
    simpa using
      (ConditionallyLinearCertificate.zero (k := k) (n := n) Finset.univ).raiseLevel ell

private noncomputable def zeroCLSampler (k n ell : Nat) : CLSampler k n ell where
  alice := zeroConditionallyLinearMap k n ell
  bob := zeroConditionallyLinearMap k n ell

private def CLQueryDecomposition.basePrefix
    {k n ell : Nat} {L : ConditionallyLinearMap k n ell}
    (D : CLQueryDecomposition L) (j : Fin ell) : CLPrefix (D.priorOutput j) :=
  ⟨D.priorOutput j 0, ⟨0, rfl⟩⟩

private noncomputable def CLQueryDecomposition.zeroExpand
    {sourceK sourceN ell : Nat} {L : ConditionallyLinearMap sourceK sourceN ell}
    (D : CLQueryDecomposition L) (extension : Nat) :
    CLQueryDecomposition
      (zeroConditionallyLinearMap 1 (sourceN * extension) ell) where
  marginal j := zeroConditionallyLinearMap 1 (sourceN * extension) (j.val + 1)
  priorOutput _ := 0
  priorOutput_zero _ _ := rfl
  priorOutput_succ _ _ := rfl
  factor j _ := expandRegister extension (D.factor j (D.basePrefix j))
  linear _ _ := 0
  factor_cover x ij := by
    rcases D.factor_cover (0 : FieldVector sourceK sourceN)
        (finProdFinEquiv.symm ij).1 with ⟨j, hj⟩
    refine ⟨j, ?_⟩
    simpa only [mem_expandRegister, basePrefix] using hj
  factor_disjoint x j1 j2 hne := by
    exact expandRegister_disjoint
      (D.factor_disjoint (0 : FieldVector sourceK sourceN) j1 j2 hne)
  linear_supported _ _ _ _ _ := rfl
  linear_depends _ _ _ := rfl
  marginal_sum j x := by
    simp [zeroConditionallyLinearMap]
  marginal_top h := rfl

private noncomputable def CLQueryDecomposition.pullbackPrefix
    {k n ell : Nat} {L : ConditionallyLinearMap k n ell}
    (F : FieldData k) (D : CLQueryDecomposition L) (j : Fin ell)
    (u : CLPrefix (fun y =>
      downsizeVector F n (D.priorOutput j ((downsizeVector F n).symm y)))) :
    CLPrefix (D.priorOutput j) := by
  refine ⟨(downsizeVector F n).symm u.1, ?_⟩
  rcases u.2 with ⟨y, hy⟩
  refine ⟨(downsizeVector F n).symm y, ?_⟩
  rw [hy]
  simp

private noncomputable def CLQueryDecomposition.downsize
    {k n ell : Nat} {L : ConditionallyLinearMap k n ell}
    (F : FieldData k) (D : CLQueryDecomposition L) :
    CLQueryDecomposition (L.downsize F) where
  marginal j := (D.marginal j).downsize F
  priorOutput j y :=
    downsizeVector F n (D.priorOutput j ((downsizeVector F n).symm y))
  priorOutput_zero j hj := by
    rw [D.priorOutput_zero j hj]
    funext y
    simp
  priorOutput_succ j hj := by
    rw [D.priorOutput_succ j hj]
    rfl
  factor j u := expandRegister k (D.factor j (D.pullbackPrefix F j u))
  linear j u := downsizeLinearMap F (D.linear j (D.pullbackPrefix F j u))
  factor_cover x ij := by
    rcases D.factor_cover ((downsizeVector F n).symm x)
        (finProdFinEquiv.symm ij).1 with ⟨j, hj⟩
    refine ⟨j, ?_⟩
    simpa only [mem_expandRegister, pullbackPrefix,
      LinearEquiv.symm_apply_apply] using hj
  factor_disjoint x j1 j2 hne := by
    apply expandRegister_disjoint
    simpa only [pullbackPrefix, LinearEquiv.symm_apply_apply] using
      D.factor_disjoint ((downsizeVector F n).symm x) j1 j2 hne
  linear_supported j u y ij hij := by
    let sourceFactor := D.factor j (D.pullbackPrefix F j u)
    let sourceLinear := D.linear j (D.pullbackPrefix F j u)
    have hsupported (z : FieldVector k n) :
        sourceLinear z = restrictVector sourceFactor (sourceLinear z) := by
      ext i
      by_cases hi : i ∈ sourceFactor
      · simp [restrictVector, hi]
      · rw [restrictVector, if_neg hi]
        exact D.linear_supported j (D.pullbackPrefix F j u) z i
          (by simpa only [sourceFactor] using hi)
    have htarget :
        downsizeLinearMap F sourceLinear y =
          restrictVector (expandRegister k sourceFactor)
            (downsizeLinearMap F sourceLinear y) := by
      calc
        downsizeLinearMap F sourceLinear y =
            downsizeVector F n (sourceLinear ((downsizeVector F n).symm y)) := rfl
        _ = downsizeVector F n
            (restrictVector sourceFactor
              (sourceLinear ((downsizeVector F n).symm y))) :=
          congrArg (downsizeVector F n) (hsupported _)
        _ = restrictVector (expandRegister k sourceFactor)
            (downsizeVector F n
              (sourceLinear ((downsizeVector F n).symm y))) :=
          downsizeVector_restrict F sourceFactor _
        _ = restrictVector (expandRegister k sourceFactor)
            (downsizeLinearMap F sourceLinear y) := rfl
    rw [htarget]
    simp [restrictVector, sourceFactor, hij]
  linear_depends j u y := by
    change downsizeVector F n
        (D.linear j (D.pullbackPrefix F j u)
          ((downsizeVector F n).symm
            (restrictVector
              (expandRegister k (D.factor j (D.pullbackPrefix F j u))) y))) = _
    rw [downsizeVector_symm_restrict, D.linear_depends]
    rfl
  marginal_sum j x := by
    change downsizeVector F n
        ((D.marginal j).toFun ((downsizeVector F n).symm x)) = _
    rw [D.marginal_sum, map_sum]
    apply Finset.sum_congr rfl
    intro i hi
    let stage := CLStage.castLE j i
    let sourcePrefix : CLPrefix (D.priorOutput stage) :=
      ⟨D.priorOutput stage ((downsizeVector F n).symm x),
        ⟨(downsizeVector F n).symm x, rfl⟩⟩
    let targetPrefix : CLPrefix (fun y =>
        downsizeVector F n
          (D.priorOutput stage ((downsizeVector F n).symm y))) :=
      ⟨downsizeVector F n
          (D.priorOutput stage ((downsizeVector F n).symm x)), ⟨x, rfl⟩⟩
    have hp : D.pullbackPrefix F stage targetPrefix = sourcePrefix := by
      apply Subtype.ext
      simp [pullbackPrefix, sourcePrefix, targetPrefix]
    change downsizeVector F n
        (D.linear stage sourcePrefix
          (restrictVector
            (D.factor stage sourcePrefix)
            ((downsizeVector F n).symm x))) = _
    change _ = downsizeLinearMap F
        (D.linear stage (D.pullbackPrefix F stage targetPrefix))
        (restrictVector
          (expandRegister k
            (D.factor stage (D.pullbackPrefix F stage targetPrefix))) x)
    rw [hp]
    change _ = downsizeVector F n
      (D.linear stage sourcePrefix
        ((downsizeVector F n).symm
          (restrictVector (expandRegister k (D.factor stage sourcePrefix)) x)))
    rw [← downsizeVector_symm_restrict]
  marginal_top h := by
    funext x
    change downsizeVector F n
        ((D.marginal (CLStage.last ell h)).toFun ((downsizeVector F n).symm x)) =
      downsizeVector F n (L.toFun ((downsizeVector F n).symm x))
    rw [D.marginal_top h]

private noncomputable def ExecutableCLSampler.downsizedAssociated
    (S : ExecutableCLSampler Q s ell) (n : Nat) :
    CLSampler 1 (s n * Q.exponent n) ell :=
  if hn : 0 < n then
    (S.associated n).downsize (Q.fieldData n hn)
  else
    zeroCLSampler 1 (s n * Q.exponent n) ell

private noncomputable def ExecutableCLSampler.downsizedDecomposition
    (S : ExecutableCLSampler Q s ell) (n : Nat) (w : CLSamplerSide) :
    CLQueryDecomposition ((S.downsizedAssociated n).side w) := by
  by_cases hn : 0 < n
  · rw [downsizedAssociated, dif_pos hn]
    cases w
    · simpa [CLSampler.side, CLSampler.downsize] using
        (S.decomposition n .alice).downsize (Q.fieldData n hn)
    · simpa [CLSampler.side, CLSampler.downsize] using
        (S.decomposition n .bob).downsize (Q.fieldData n hn)
  · rw [downsizedAssociated, dif_neg hn]
    cases w
    · simpa [CLSampler.side, zeroCLSampler] using
        (S.decomposition n .alice).zeroExpand (Q.exponent n)
    · simpa [CLSampler.side, zeroCLSampler] using
        (S.decomposition n .bob).zeroExpand (Q.exponent n)

private theorem ExecutableCLSampler.downsizedAssociated_eq
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    S.downsizedAssociated n =
      (S.associated n).downsize (Q.fieldData n hn) := by
  rw [downsizedAssociated, dif_pos hn]

private theorem ExecutableCLSampler.downsizedAssociatedMap_eq
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n)
    (w : CLSamplerSide) :
    (S.downsizedAssociated n).side w =
      ((S.associated n).side w).downsize (Q.fieldData n hn) := by
  rw [S.downsizedAssociated_eq n hn]
  cases w <;> rfl

private theorem ExecutableCLSampler.downsizedSample_eq
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    (S.downsizedAssociated n).sample = PMF.map (fun pair =>
      (downsizeVector (Q.fieldData n hn) (s n) pair.1,
       downsizeVector (Q.fieldData n hn) (s n) pair.2)) (S.sample n) := by
  rw [S.downsizedAssociated_eq n hn]
  simpa only [ExecutableCLSampler.sample] using
    CLSampler.sample_downsize (Q.fieldData n hn) (S.associated n)

private theorem ExecutableCLSampler.downsizedDimension_eq
    (_S : ExecutableCLSampler Q s ell) (n : Nat) :
    s n * Q.exponent n = s n * Nat.log 2 (Q.fieldSize n) := by
  simp [AdmissibleFieldFamily.fieldSize, Nat.log_pow (by omega : 1 < 2)]

private noncomputable def ExecutableCLSampler.compiledDownsize
    (S : ExecutableCLSampler Q s ell)
    (machine : IndexedSixInputBitMachine)
    (execution : forall n (hn : 0 < n)
      (query : CLSamplerQuery binaryFieldFamily
        (fun index => s index * Q.exponent index) ell n hn
        (S.downsizedAssociated n) (S.downsizedDecomposition n)),
      machine.Execution query.canonicalTapes query.expectedOutput)
    (fieldProgram : FieldExponentProgram binaryFieldFamily) :
    ExecutableCLSampler binaryFieldFamily
      (fun n => s n * Q.exponent n) ell where
  associated := S.downsizedAssociated
  decomposition := S.downsizedDecomposition
  machine := machine
  execution := execution
  fieldProgram := fieldProgram

private structure ExecutableCLSampler.DownsizeCompiler
    (S : ExecutableCLSampler Q s ell) where
  machine : IndexedSixInputBitMachine
  execution : forall n (hn : 0 < n)
      (query : CLSamplerQuery binaryFieldFamily
        (fun index => s index * Q.exponent index) ell n hn
        (S.downsizedAssociated n) (S.downsizedDecomposition n)),
    machine.Execution query.canonicalTapes query.expectedOutput
  fieldProgram : FieldExponentProgram binaryFieldFamily
  runtime : forall _hEll : 1 <= ell,
    RuntimeBigO
      (S.compiledDownsize machine execution fieldProgram).time
      (fun n => S.time n * Nat.log 2 (Q.fieldSize n))

private theorem ExecutableCLSampler.downsizeCompiler_exists
    (S : ExecutableCLSampler Q s ell) :
    Nonempty (ExecutableCLSampler.DownsizeCompiler S) := by
  sorry

/-- Downsize an executable sampler to its binary-coordinate realization. -/
noncomputable def ExecutableCLSampler.downsize
    (S : ExecutableCLSampler Q s ell) :
    ExecutableCLSampler binaryFieldFamily
      (fun n => s n * Q.exponent n) ell :=
  let compiler : ExecutableCLSampler.DownsizeCompiler S :=
    Classical.choice S.downsizeCompiler_exists
  S.compiledDownsize compiler.machine compiler.execution compiler.fieldProgram

/-- Downsizing expands dimension by the binary logarithm of the field size. -/
theorem ExecutableCLSampler.downsize_dimension
    (S : ExecutableCLSampler Q s ell) (n : Nat) (_hn : 0 < n) :
    S.downsize.dimension n = s n * Nat.log 2 (Q.fieldSize n) := by
  change s n * Q.exponent n = s n * Nat.log 2 (Q.fieldSize n)
  exact S.downsizedDimension_eq n

/-- Downsizing conjugates each associated CL map by the selected field basis. -/
theorem ExecutableCLSampler.downsize_associated
    (S : ExecutableCLSampler Q s ell) (_hEll : 1 <= ell)
    (n : Nat) (hn : 0 < n) (w : CLSamplerSide) :
    S.downsize.associatedMap n w =
      ((S.associatedMap n w).downsize (Q.fieldData n hn)) := by
  change (S.downsizedAssociated n).side w =
    ((S.associated n).side w).downsize (Q.fieldData n hn)
  exact S.downsizedAssociatedMap_eq n hn w

/-- Downsizing pushes the shared-seed distribution through the basis map. -/
theorem ExecutableCLSampler.sample_downsize
    (S : ExecutableCLSampler Q s ell) (_hEll : 1 <= ell)
    (n : Nat) (hn : 0 < n) :
    S.downsize.sample n = PMF.map (fun pair =>
      (downsizeVector (Q.fieldData n hn) (s n) pair.1,
       downsizeVector (Q.fieldData n hn) (s n) pair.2)) (S.sample n) := by
  change (S.downsizedAssociated n).sample = PMF.map (fun pair =>
    (downsizeVector (Q.fieldData n hn) (s n) pair.1,
     downsizeVector (Q.fieldData n hn) (s n) pair.2)) (S.sample n)
  exact S.downsizedSample_eq n hn

/-- The binary sampler runs in source time times the field exponent. -/
theorem ExecutableCLSampler.downsize_time
    (S : ExecutableCLSampler Q s ell) (hEll : 1 <= ell) :
    RuntimeBigO S.downsize.time
      (fun n => S.time n * Nat.log 2 (Q.fieldSize n)) := by
  sorry

end

end MIPStarRE.QPBT
