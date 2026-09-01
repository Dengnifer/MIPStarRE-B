# QPBT-035 callable contract freeze (A02)

Session: `i035-orchestrator-a02-q014-contract`

## Candidate verdict

The QPBT-014 leaf surface is frozen into four disjoint new writer lanes.  With
the integrated Field and Approximation lanes, the checker admits exactly the
closed set `field`, `approximation`, `polynomial`, `pauli`, `types`, and
`parameters`; an adversarial test rejects every other value.  The contract
resolves QPBT-033 findings 1-3, 5, and 7 without inventing a public assumption:
Boolean coordinate indices are distinct from field evaluation points; Pauli
algebra retains the negative trace-valued phase and exact matrix multiplication
order; conditionally-linear maps carry a recursive certificate; type graphs
preserve loops and both orientations; and questions and answers remain
dependent fibers.

The immutable A02 base is commit
`50c4a9ce9fc9446b04c1c309951f05cc6a49766c`, tree
`a0248f602cc2648742a8d2636c7af15ccd9a039a`.  The final candidate commit and
tree are reported out of band because a tracked report cannot contain the hash
of the commit that contains itself.

## Exact writer split

| Lane | Sole Lean path | Exact direct imports | Scoped command |
| --- | --- | --- | --- |
| Polynomial | `MIPStarRE/QPBT/Basic/Polynomial.lean` | `Mathlib.RingTheory.MvPolynomial.Basic`; `MIPStarRE.QPBT.Basic.Field` | `lake env lean MIPStarRE/QPBT/Basic/Polynomial.lean` |
| Pauli | `MIPStarRE/QPBT/Basic/Pauli.lean` | `Mathlib.Analysis.Fourier.FiniteAbelian.Orthogonality`; `Mathlib.Analysis.SpecialFunctions.Complex.CircleAddChar`; `MIPStarRE.QPBT.Basic.Field`; `MIPStarRE.QPBT.Basic.Approximation` | `lake env lean MIPStarRE/QPBT/Basic/Pauli.lean` |
| Types | `MIPStarRE/QPBT/Game/Types.lean` | `Mathlib.Probability.Distributions.Uniform`; `MIPStarRE.QPBT.Basic.Field` | `lake env lean MIPStarRE/QPBT/Game/Types.lean` |
| Parameters | `MIPStarRE/QPBT/Game/Parameters.lean` | `MIPStarRE.QPBT.Basic.Field` | `lake env lean MIPStarRE/QPBT/Game/Parameters.lean` |

F06 precedes F07 inside the sole Types owner.  There is no Lean import edge
among the four new files.

## Exact signatures

The nontrivial declarations below intentionally omit bodies.  A02 separately
elaborated the same declarations with temporary `sorry` bodies under `/tmp`;
those probe placeholders are not implementation proof debt and authorize no
`sorry` in a leaf candidate.

### F02 Polynomial

<!-- BEGIN F02-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

abbrev BooleanPoint (m : Nat) := Fin m -> ZMod 2
abbrev FieldPoint (k m : Nat) := Fin m -> GaloisField 2 k

noncomputable abbrev IndividualDegreePolynomial (k m d : Nat) :=
  MvPolynomial.restrictDegree (Fin m) (GaloisField 2 k) d

noncomputable def booleanPointToField {k m : Nat} (y : BooleanPoint m) :
    FieldPoint k m

noncomputable def evalIndividualDegreePolynomial {k m d : Nat}
    (f : IndividualDegreePolynomial k m d) (x : FieldPoint k m) :
    GaloisField 2 k :=
  MvPolynomial.eval x f.1

noncomputable def indicatorPolynomial {k m : Nat} (y : BooleanPoint m) :
    IndividualDegreePolynomial k m 1

noncomputable def indicatorVector {k m : Nat} (x : FieldPoint k m) :
    BooleanPoint m -> GaloisField 2 k :=
  fun y => evalIndividualDegreePolynomial (indicatorPolynomial y) x

noncomputable def lowDegreeEncode (k m : Nat) :
    (BooleanPoint m -> GaloisField 2 k) →ₗ[GaloisField 2 k]
      IndividualDegreePolynomial k m 1

@[simp] theorem indicatorPolynomial_eval_boolean {k m : Nat}
    (x y : BooleanPoint m) :
    evalIndividualDegreePolynomial (indicatorPolynomial (k := k) y)
      (booleanPointToField x) = if x = y then 1 else 0

theorem lowDegreeEncode_eval {k m : Nat}
    (a : BooleanPoint m -> GaloisField 2 k) (x : FieldPoint k m) :
    evalIndividualDegreePolynomial (lowDegreeEncode k m a) x =
      ∑ y, a y * indicatorVector x y

@[simp] theorem lowDegreeEncode_eval_boolean {k m : Nat}
    (a : BooleanPoint m -> GaloisField 2 k) (y : BooleanPoint m) :
    evalIndividualDegreePolynomial (lowDegreeEncode k m a)
      (booleanPointToField y) = a y

theorem lowDegreeEncode_injective (k m : Nat) :
    Function.Injective (lowDegreeEncode k m)

end MIPStarRE.QPBT
```
<!-- END F02-SIGNATURES -->

`indicatorPolynomial y` is the paper product with factor `X i` when
`y i = 1` and `1 - X i` when `y i = 0`.  Its subtype proof establishes the
individual degree bound.  `lowDegreeEncode` is a linear map, so linearity is
part of the callable type; Boolean interpolation proves injectivity.  No
`FieldData` value or field basis is accepted.

### F05 Pauli

<!-- BEGIN F05-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

noncomputable local instance (k : Nat) : Fintype (GaloisField 2 k) :=
  Fintype.ofFinite (GaloisField 2 k)
noncomputable local instance (k : Nat) : DecidableEq (GaloisField 2 k) :=
  Classical.decEq (GaloisField 2 k)

inductive PauliBasis
  | X
  | Z
  deriving DecidableEq, Fintype

noncomputable def pauliX (k : Nat) (a : GaloisField 2 k) :
    MIPStarRE.Quantum.Op (GaloisField 2 k)

noncomputable def pauliZ (k : Nat) (b : GaloisField 2 k) :
    MIPStarRE.Quantum.Op (GaloisField 2 k)

noncomputable def pauliObservable (k : Nat) (W : PauliBasis)
    (a : GaloisField 2 k) : MIPStarRE.Quantum.Op (GaloisField 2 k)

noncomputable def pauliProjector (k : Nat) (W : PauliBasis) :
    MIPStarRE.Quantum.Measurement (GaloisField 2 k) (GaloisField 2 k)

theorem pauli_mul (k : Nat) (W : PauliBasis)
    (a a' : GaloisField 2 k) :
    pauliObservable k W a * pauliObservable k W a' =
      pauliObservable k W (a + a')

theorem pauli_sq (k : Nat) (W : PauliBasis) (a : GaloisField 2 k) :
    pauliObservable k W a ^ 2 = 1

theorem pauli_twistedCommutation (k : Nat)
    (a b : GaloisField 2 k) :
    pauliX k a * pauliZ k b =
      ZMod.stdAddChar (N := 2) (-(fieldTrace k (a * b))) •
        (pauliZ k b * pauliX k a)

theorem pauliObservable_eq_sum_projectors (k : Nat) (W : PauliBasis)
    (a : GaloisField 2 k) :
    pauliObservable k W a =
      ∑ b, ZMod.stdAddChar (N := 2) (fieldTrace k (a * b)) •
        (pauliProjector k W).effect b

theorem pauliProjector_eq_expect_observables (k : Nat) (W : PauliBasis)
    (b : GaloisField 2 k) :
    (pauliProjector k W).effect b =
      (Fintype.card (GaloisField 2 k) : Complex)⁻¹ •
        ∑ a, ZMod.stdAddChar (N := 2) (-(fieldTrace k (a * b))) •
          pauliObservable k W a

noncomputable def fieldDotProduct {k n : Nat}
    (a b : Fin n -> GaloisField 2 k) : GaloisField 2 k :=
  ∑ i, a i * b i

noncomputable def pauliTensor (k n : Nat) (W : PauliBasis)
    (a : Fin n -> GaloisField 2 k) :
    MIPStarRE.Quantum.Op (Fin n -> GaloisField 2 k)

noncomputable def pauliTensorProjector (k n : Nat) (W : PauliBasis) :
    MIPStarRE.Quantum.Measurement
      (Fin n -> GaloisField 2 k) (Fin n -> GaloisField 2 k)

theorem pauliTensor_twistedCommutation (k n : Nat)
    (a b : Fin n -> GaloisField 2 k) :
    pauliTensor k n PauliBasis.X a * pauliTensor k n PauliBasis.Z b =
      ZMod.stdAddChar (N := 2) (-(fieldTrace k (fieldDotProduct a b))) •
        (pauliTensor k n PauliBasis.Z b * pauliTensor k n PauliBasis.X a)

theorem pauliTensor_eq_sum_projectors (k n : Nat) (W : PauliBasis)
    (a : Fin n -> GaloisField 2 k) :
    pauliTensor k n W a =
      ∑ b, ZMod.stdAddChar (N := 2) (fieldTrace k (fieldDotProduct a b)) •
        (pauliTensorProjector k n W).effect b

theorem pauliTensorProjector_eq_expect_observables
    (k n : Nat) (W : PauliBasis) (b : Fin n -> GaloisField 2 k) :
    (pauliTensorProjector k n W).effect b =
      (Fintype.card (Fin n -> GaloisField 2 k) : Complex)⁻¹ •
        ∑ a, ZMod.stdAddChar (N := 2)
          (-(fieldTrace k (fieldDotProduct a b))) • pauliTensor k n W a

end MIPStarRE.QPBT
```
<!-- END F05-SIGNATURES -->

`pauliX` has row/column entry `1` exactly when `row = column + a`;
`pauliZ` has diagonal entry
`ZMod.stdAddChar (fieldTrace k (b * row))`.  The displayed G09 equation retains
paper order `X*Z = phase • (Z*X)` and the negative trace.  Arbitrary cross-basis
commutation is not present.

F05 owns `pauli.tex:1-110`, the core generalized Pauli, projector, and Fourier
algebra.  F10 continues to own `pauli.tex:112-210`, including EPR and
qudit-to-qubit identities.  F05 imports integrated F03 for the qualified
measurement layer but uses only `MIPStarRE.Quantum.Op` and
`MIPStarRE.Quantum.Measurement`; it does not call the still-unimplemented
`BinaryObservable`/`observableOfMeasurement` slice.

### F06 conditionally-linear maps and samplers

<!-- BEGIN F06-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

noncomputable local instance (k : Nat) : Fintype (GaloisField 2 k) :=
  Fintype.ofFinite (GaloisField 2 k)
noncomputable local instance (k : Nat) : DecidableEq (GaloisField 2 k) :=
  Classical.decEq (GaloisField 2 k)

abbrev FieldVector (k n : Nat) := Fin n -> GaloisField 2 k

noncomputable def restrictVector {k n : Nat} (register : Finset (Fin n))
    (x : FieldVector k n) : FieldVector k n

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

structure ConditionallyLinearMap (k n level : Nat) where
  toFun : FieldVector k n -> FieldVector k n
  certificate : ConditionallyLinearCertificate k n Finset.univ level toFun

instance {k n level : Nat} : CoeFun (ConditionallyLinearMap k n level)
    (fun _ => FieldVector k n -> FieldVector k n) :=
  ⟨ConditionallyLinearMap.toFun⟩

noncomputable def ConditionallyLinearMap.raiseLevel
    {k n level : Nat} (L : ConditionallyLinearMap k n level) (extra : Nat) :
    ConditionallyLinearMap k n (level + extra)

noncomputable def ConditionallyLinearMap.directSum
    {k n₁ n₂ level₁ level₂ : Nat}
    (L : ConditionallyLinearMap k n₁ level₁)
    (R : ConditionallyLinearMap k n₂ level₂) :
    ConditionallyLinearMap k (n₁ + n₂) (max level₁ level₂)

noncomputable def downsizeVector {k : Nat} (D : FieldData k) (n : Nat) :
    FieldVector k n ≃ₗ[ZMod 2] FieldVector 1 (n * k)

noncomputable def ConditionallyLinearMap.downsize
    {k n level : Nat} (D : FieldData k)
    (L : ConditionallyLinearMap k n level) :
    ConditionallyLinearMap 1 (n * k) level

structure CLSampler (k n level : Nat) where
  alice : ConditionallyLinearMap k n level
  bob : ConditionallyLinearMap k n level

noncomputable def CLSampler.sample {k n level : Nat}
    (S : CLSampler k n level) :
    PMF (FieldVector k n × FieldVector k n)

noncomputable def CLSampler.directSum
    {k n₁ n₂ level₁ level₂ : Nat}
    (S : CLSampler k n₁ level₁) (T : CLSampler k n₂ level₂) :
    CLSampler k (n₁ + n₂) (max level₁ level₂)

noncomputable def CLSampler.downsize
    {k n level : Nat} (D : FieldData k) (S : CLSampler k n level) :
    CLSampler 1 (n * k) level

theorem CLSampler.sample_downsize
    {k n level : Nat} (D : FieldData k) (S : CLSampler k n level) :
    (S.downsize D).sample =
      PMF.map (fun pair =>
        (downsizeVector D n pair.1, downsizeVector D n pair.2)) S.sample

end MIPStarRE.QPBT
```
<!-- END F06-SIGNATURES -->

The certificate is not a caller-supplied generic proposition.  At level zero
it has the unique zero function.  A successor partitions the current register
into disjoint complementary head/tail coordinate registers, applies a linear
head map supported on and determined by the head, and selects a recursively
certified tail function using an actual element of the head-map range.  Thus
the source recursion and its prefix dependency are data, not an obligation
input.

`CLSampler.sample` maps one uniform ambient field vector through Alice's and
Bob's certified maps.  The source direct-sum and downsizing operations are
named.  `FieldData` is reused only by downsizing, exactly where the paper uses
the selected basis; no FieldData declaration or caller gate is moved into this
file.  Executable Turing interfaces and raw binary representations remain
K03-K04.

### F07 typed finite interfaces

<!-- BEGIN F07-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uType uQuestion uAnswer

structure TypeGraph (TypeId : Type uType)
    [Fintype TypeId] [DecidableEq TypeId] where
  orderedEdges : Finset (TypeId × TypeId)
  symmetric : forall u v,
    (u, v) ∈ orderedEdges ↔ (v, u) ∈ orderedEdges
  nonempty : orderedEdges.Nonempty

noncomputable def TypeGraph.distribution
    {TypeId : Type uType} [Fintype TypeId] [DecidableEq TypeId]
    (G : TypeGraph TypeId) : PMF (TypeId × TypeId) :=
  PMF.uniformOfFinset G.orderedEdges G.nonempty

@[simp] theorem TypeGraph.distribution_apply
    {TypeId : Type uType} [Fintype TypeId] [DecidableEq TypeId]
    (G : TypeGraph TypeId) (u v : TypeId) :
    G.distribution (u, v) =
      if (u, v) ∈ G.orderedEdges
      then (G.orderedEdges.card : ENNReal)⁻¹ else 0

abbrev TypedQuestion
    (TypeId : Type uType) (Question : TypeId -> Type uQuestion) :=
  Sigma Question

structure TypedSampler (TypeId : Type uType)
    [Fintype TypeId] [DecidableEq TypeId] (k n level : Nat) where
  graph : TypeGraph TypeId
  alice : TypeId -> ConditionallyLinearMap k n level
  bob : TypeId -> ConditionallyLinearMap k n level

noncomputable def TypedSampler.sample
    {TypeId : Type uType} [Fintype TypeId] [DecidableEq TypeId]
    {k n level : Nat} (S : TypedSampler TypeId k n level) :
    PMF (((t : TypeId) × FieldVector k n) ×
      ((t : TypeId) × FieldVector k n))

theorem TypedSampler.sample_types
    {TypeId : Type uType} [Fintype TypeId] [DecidableEq TypeId]
    {k n level : Nat} (S : TypedSampler TypeId k n level) :
    PMF.map (fun questions :
      ((t : TypeId) × FieldVector k n) ×
        ((t : TypeId) × FieldVector k n) =>
        (questions.1.1, questions.2.1)) S.sample =
      S.graph.distribution

structure TypedDecider
    (TypeId : Type uType)
    (AliceQuestion BobQuestion : TypeId -> Type uQuestion)
    (AliceAnswer BobAnswer : TypeId -> Type uAnswer) where
  decide : forall leftType rightType,
    AliceQuestion leftType -> BobQuestion rightType ->
    AliceAnswer leftType -> BobAnswer rightType -> Bool

def TypedDecider.accepts
    {TypeId : Type uType}
    {AliceQuestion BobQuestion : TypeId -> Type uQuestion}
    {AliceAnswer BobAnswer : TypeId -> Type uAnswer}
    (D : TypedDecider TypeId AliceQuestion BobQuestion AliceAnswer BobAnswer)
    (leftType rightType : TypeId)
    (leftQuestion : AliceQuestion leftType)
    (rightQuestion : BobQuestion rightType)
    (leftAnswer : AliceAnswer leftType)
    (rightAnswer : BobAnswer rightType) : Bool :=
  D.decide leftType rightType leftQuestion rightQuestion leftAnswer rightAnswer

end MIPStarRE.QPBT
```
<!-- END F07-SIGNATURES -->

`orderedEdges` stores a loop `(u,u)` once and both ordered pairs for a non-loop
edge.  Therefore its cardinality is the paper denominator `2m-k`, and uniform
sampling preserves orientation weights without using irreflexive
`SimpleGraph`.  `sample_types` makes the graph marginal callable.

The sigma question carrier remains dependent, and `TypedDecider.decide` is
total for every type pair while retaining type-indexed question and answer
fibers.  No `BitVec` or raw string erases these fibers.  The paper's Turing
parsing, executable detyping, and complexity claims are assigned to K03-K04;
the finite mathematical game consumer remains G02.

### G01 Parameters

<!-- BEGIN G01-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

structure Parameters where
  q : Nat
  m : Nat
  d : Nat
  deriving DecidableEq

def Parameters.Admissible (params : Parameters) : Prop :=
  Exists fun k : Nat =>
    Odd k ∧ params.q = 2 ^ k ∧ Dvd.dvd params.m params.q

end MIPStarRE.QPBT
```
<!-- END G01-SIGNATURES -->

This is project-owned data, not an alias or coercion from
`MIPStarRE.LDT.Parameters`.  It adds no positivity, field witness, or reordered
conjunction.

## Statement integrity

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F02 | `y : {0,1}^m`, `x : F_q^m`, and data `a` indexed by Boolean points | `BooleanPoint m`, `FieldPoint k m`, concrete `GaloisField 2 k`; no basis | Indicator product, `g_a(x)`, Boolean interpolation, and linearity | Individually degree-one subtype, evaluation formula, Boolean interpolation, linear-map encoding, injectivity | exact |
| F05 | Characteristic-two finite field; basis only in the later binary conversion | Concrete `GaloisField 2 k`, derived finite instances, raw finite matrix/measurement API | X/Z matrices, product laws, projector Fourier/inversion equations, single/multi-register twisted phase | Same definitions and equations with `X*Z = psi(-trace(a*b)) • (Z*X)`; binary conversion excluded | documented mismatch (G09) |
| F06 | Finite coordinate field space; recursive complementary registers; uniform seed; chosen basis for downsizing | Concrete characteristic-two field vectors, finite coordinate registers, recursive certificate; F01 `FieldData` only for downsizing | CL functions/distributions, level raising, direct sum, downsizing, sampler distribution | Same mathematical operations and PMF pushforward; no executable complexity claim | faithful boundary |
| F07 | Finite type set, undirected graph with loops, typed CL families, type-indexed verifier data | Nonempty symmetric ordered-edge support, certified maps, sigma questions, dependent answer fibers | Graph distribution and typed sampler/decider semantics | Uniform ordered-edge PMF with exact support/cardinality and total dependent decider | faithful boundary |
| G01 | Tuple `(q,m,d)` | Project-owned natural-valued structure | Exists odd `k`, `q=2^k`, and `m | q` | Identical quantifier and conjunction order with `Dvd.dvd` | exact |

## QPBT-033 finding dispositions

1. **Resolved:** every definition/theorem named by F02, F05, F06, F07, and G01
   has an exact hashed signature block and direct import list.
2. **Resolved:** F06 and F07 are sequential contracts in the one Types lane.
3. **Resolved:** no raw `BitVec` codec appears; executable representation is
   K03-K04.  F01 remains the sole owner of `FieldData`; Types only consumes it
   for source-required downsizing.
4. **Preserved:** G09's negative trace phase and matrix order are explicit in
   both single- and multi-register theorems.
5. **Resolved:** Boolean coordinate indices and field evaluation points are
   separate types, and interpolation/injectivity are named theorem obligations.
6. **Preserved:** `TypeGraph` uses symmetric ordered support, not
   `SimpleGraph`, so loops and the `2m-k` orientation weight remain visible.
7. **Resolved:** F05 uses only the integrated raw operator/measurement slice;
   absent F03 binary-observable declarations create no dependency.
8. **Preserved:** G01 is project-owned and exact.

## Source authentication

No network was used.  These locally authenticated hashes agree with QPBT-033:

| Source | SHA-256 |
| --- | --- |
| `dependencies/low-degree-code.tex` | `e77125aa2c20f037b949f8890efcaaf370f5ca25407048a5ac142115104bdc9e` |
| `dependencies/pauli.tex` | `aba301b2e225f0ceaeff6a942a75ee6d5db73283ba25e208e2e43452818aef2f` |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `dependencies/types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` |
| `qpbt/qpbt-game-and-soundness.tex` | `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea` |

## Reviewer checklist

- Recompute every marker-delimited signature SHA-256 and compare it with
  `nodes.json`.
- Check F02 Boolean/field domains, product factors, evaluation theorem, and
  absence of `FieldData`.
- Check F05 matrix-entry orientation, negative phase, multiplication order,
  Fourier normalization, raw F03 API use, and F10 exclusion.
- Check F06 level-zero uniqueness, recursive tail certificate, complementary
  registers, direct sum/downsize types, uniform PMF, and absence of a generic
  caller proposition.
- Check F07 loop support, orientation cardinality, graph marginal, dependent
  fibers, total decider, and absence of `BitVec`/`SimpleGraph`.
- Check G01 quantifier/conjunction order and absence of stronger hypotheses.
- Verify all changed paths are in the immutable A02 manifest and no generated
  output outside that manifest changed.

## Validation and metrics

### Signature manifest

The checker recomputed these SHA-256 values over the exact text strictly
between each marker pair:

| Node | Signature SHA-256 |
| --- | --- |
| F02 | `4468d05a235d7ccaa2eb9b355da4e2687bbd2c0bb6444046ce24d276c6c8006e` |
| F05 | `2046e1a3784f6bf10a1a7c71b279bd41d5c27ed3424e20797cf7c5bba95b4aa7` |
| F06 | `4ff1a12c51563b66f5671077c74b5c951905a8be7c30cae3e122a5932ab5505b` |
| F07 | `4244dfbf6843f9641be2813b74f83046b93d41954f620a1309a9fedb0333b523` |
| G01 | `587cb393eff88db0291303da834e483e13f44eda8c2c286e2ab48721120386cb` |

Final non-self-referential file hashes before commit were:

| Owned path | SHA-256 | Candidate state |
| --- | --- | --- |
| `blueprint/check.py` | `8ac6b26c127d91106958e5a906dda095aa0c85d10710348309da29e9fe9aa9e1` | changed |
| `blueprint/tests/test_check.py` | `6a80840cf31fb911e88b2a66bb6089a9fb7dc5e91903fb49f85f9dde5041a6c4` | changed |
| `blueprint/metadata/nodes.json` | `9a42053782fbac0a61850cfa0b6eba9e03ca2d55596290f488382629f3119e61` | changed |
| `blueprint/generated/graph.json` | `a72fb60fd6ae8b4c8d2ce63595f515f441dca1f7dcc4bb338744300a7143a07f` | changed |
| `blueprint/generated/graph.dot` | `31cc92e962550342481623c9fe1f94a448e7d9660af0f265a16de6a371c08654` | unchanged |
| `blueprint/src/generated/chapter-02-entries.tex` | `c88a5377b004b8f49b1741e248e1710533481b34e1459b3af59e3f8d82ef7db7` | changed |
| `blueprint/src/generated/chapter-03-entries.tex` | `afdb38a9cc4321d5be450ddcf0881bc655d3df0d7257a48acf20491491e4807f` | changed |

The A02 report digest and candidate Git identities are supplied out of band to
avoid self-reference.

### Temporary signature probes

Seven bounded `lake env lean` attempts used private files under `/tmp` and the
already materialized local dependencies.  F02 passed in `2.3` seconds.  F05
first exposed missing `Fintype` (`4.5` seconds), then missing `DecidableEq`
(`4.4` seconds), and passed with local noncomputable instances in `4.4`
seconds.  The combined F06/F07 probe exposed parser/name errors in `2.8`
seconds and passed after correction in `2.7` seconds.  G01 passed in `2.3`
seconds.  These probes created no repository Lean source or proof debt.

### Acceptance gates

| Command | Result | Wall time |
| --- | --- | ---: |
| `python3 blueprint/check.py --write` | pass; deterministic/idempotent regeneration | `0.08s` |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | pass; 28 tests | `0.72s` (`0.656s` test time) |
| `python3 blueprint/check.py --check` | pass; 51 nodes, 12 chapters, acyclic/deterministic | `0.08s` |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass; 51 nodes, 12 chapters, acyclic/deterministic | `0.09s` |
| `python3 scripts/workflow.py validate` | pass; canonical issued-session command, state valid | `0.12s` |
| `python3 scripts/check_workflow.py --skip-tests` | pass; workflow state valid | `0.12s` |
| `git diff --check` | pass | `0.00s` |

An initial default blueprint check failed closed only because the newly authored
metadata had not yet been regenerated.  Regeneration then ran four times in
total, including the final idempotency check.  No output outside the immutable
A02 manifest changed.

### Cache and materialization

A02 did not seed, warm, build, or rematerialize.  It reused the A01 private
seed from authenticated key
`d71a99abea8f7ebf5bda5194dfef088b06f526230caf5ccbca34d62d5b4267b9`
for main `259c73a368ef7403b4e36e190c9bf940497b300f`: hit, 124,925 files,
3 symlinks, 10,097,592,794 bytes, zero builds, zero lock wait, and
`138.258072` seconds.  A01 had materialized the pinned archive exactly once
with `--replace-existing`: archive SHA-256
`656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`,
337 files / 5,970,111 bytes in `5.948803` seconds, preserving two authored
files / 5,319 bytes with aggregate SHA-256
`0578da860a522b58b69c2c16df366c7eee3abd97c425900401e4e83c992803ed`.

### A02 counters

```json
{
  "session_id": "i035-orchestrator-a02-q014-contract",
  "stage_id": "STAGE-04A",
  "issue_id": "QPBT-035",
  "role": "orchestrator",
  "backend": "codex-collaboration",
  "requested_model": "gpt-5.6-sol",
  "external_id": "/root/i035_q014_contract#continuation:a02",
  "started_at": "2026-09-01T13:23:16.122511Z",
  "evidence_cutoff": "2026-09-01T13:40:18.856162524Z",
  "agent_measured_elapsed_seconds_to_cutoff": 1022.733651524,
  "token_usage": null,
  "token_usage_unavailable_reason": "collaboration session token usage is not exposed",
  "topology": {"parent": "/root", "nested_agents": 0},
  "actions": {
    "owned_manifest_paths": 8,
    "changed_tracked_paths_before_commit": 7,
    "unchanged_owned_generated_paths": 1,
    "unowned_edits": 0,
    "lean_signature_probe_attempts": 7,
    "repository_lean_source_edits": 0,
    "blueprint_generation_attempts": 4,
    "cache_seeds": 0,
    "cache_warms": 0,
    "materializations": 0,
    "target_builds": 0,
    "full_builds": 0,
    "network_calls": 0,
    "endpoint_calls": 0,
    "github_operations": 0,
    "credential_accesses": 0,
    "nested_agents": 0
  },
  "outcome": "candidate-awaiting-independent-review"
}
```

Residual risk is bounded but real: A02 elaborated the callable declarations,
not their future implementation bodies, and an independent reviewer must still
check the immutable candidate before integration.  G09 remains the documented
paper mismatch corrected by the explicit negative phase.  The unfinished F03
`BinaryObservable` surface is deliberately outside the F05 contract, while F10
owns EPR and qudit-to-qubit conversion.  No additional paper ambiguity was
found.
