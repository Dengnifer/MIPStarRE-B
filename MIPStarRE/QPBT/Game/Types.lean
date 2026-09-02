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

end MIPStarRE.QPBT
