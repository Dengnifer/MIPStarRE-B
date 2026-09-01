# QPBT-023 Lean API scout a03

## Verdict

**Conditional API-ready; the current F01/F03/F04 metadata is not ready to
freeze unchanged.** All requested carrier, adapter, finite-value, indexed
relation, consistency, and law *statement* signatures have clean elaborations
against the pinned project and Mathlib. The canonical `ZMod 2` observable was
also proved, not merely typed, with value exactly `effect 0 - effect 1`.

One mathematical boundary remains unresolved: neither the authenticated
MIPStarRE source nor pinned Mathlib provides the theorem that an odd-degree
`GaloisField 2 k` has one basis that is simultaneously normal in the paper's
Frobenius order and self-dual for `Algebra.trace`. Mathlib supplies a normal
basis and separately the trace-dual of a basis, but no result identifying one
basis with its trace dual while retaining normality. The paper's stronger
uniform deterministic algorithm, multiplication-table output, and polynomial
runtime are a separate K03A obligation and cannot be discharged by a
noncomputable existence projection.

F04 should be **re-scoped**, not merely have more planned names appended to its
current leaf. Keep a finite foundation node for strategies, local/tensor
adapters, numeric values, and exact bounds. Add named dependent nodes for
indexed asymptotics/strategy distance, consistency, and distance laws. The
current `familyApprox` name and `delta : NNReal` predicate must not be presented
as the paper's indexed `O(delta)` relation.

## Session boundary

| Field | Value |
| --- | --- |
| Logical session | `i023-scout-a03-lean-api` |
| Parent | `/root/i023_orchestrator_a01_leaf_contract` |
| Topology | parent orchestrator -> one read-only scout; nested agents 0 |
| Worktree | `/tmp/qpbt-023-lean-api-a03` |
| Required HEAD | `942f9438b991ece8942815db16c019b92d9cdd8e` |
| Required tree | `09123f4b25c892a146aabaa77d73cf0c5f35a0c6` |
| UTC start | `2026-09-01T08:32:40.817315175Z` |
| UTC end evidence | `2026-09-01T09:08:12.373210683Z` |
| Monotonic start | `/proc/uptime = 1275722.16` s |
| Monotonic end | `/proc/uptime = 1277853.97` s |
| Monotonic elapsed | `2131.81` s (35 min 31.81 s) |
| Timing quality | UTC from `date -u` at nanosecond display precision; elapsed from the same host's monotonic `/proc/uptime`, reported to 0.01 s; command wall times are tool-reported |
| Token usage | `null` |
| Token reason | Token accounting is not exposed to this collaboration subagent; no estimate was made |

Initial and final `git status --short --untracked-files=all` were empty.
Initial and final HEAD/tree matched the required values. Final `git diff
--quiet` exited 0. The authorized MIPStarRE materialization is ignored by Git;
there were no tracked repository changes, Git writes, ref changes, canonical
state changes, or metrics changes.

## Instructions and seed evidence

- `AGENTS.md` was read completely before action: 139 lines, SHA-256
  `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c`.
- Coordinator-provided canonical private `.lake` seed evidence: READY key
  `4a5d9cf4d7de3d89c9bf7805d59f5c1739b39fd56d66b19b2454941da8873807`;
  root cache hit 1, builds 0, elapsed `227.927544` s, inventory 124925 files /
  10097592794 bytes.
- This scout ran no cache command: warm 0, seed 0, status 0, other cache
  commands 0.
- Lean toolchain: `leanprover/lean4:v4.32.0`.
- Pinned Mathlib HEAD: `81a5d257c8e410db227a6665ed08f64fea08e997`.

## Source authentication

The parent authorized the exact canonical A02 read and exact authenticated
source fragments. Every check below passed before its source was used.

- Canonical A02 report:
  `/home/drx/MIPStarRE-auto/workflow/reviews/qpbt-023-source-integrity-a02.md`,
  observed SHA-256
  `a52001d4589465b7ffe72e852f1d818d411a8ddbb442b34e5bc0568b7a36d747`,
  exactly the required digest; all 351 lines read.
- `sections/inventory.json` SHA-256:
  `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`.
  `sections/READY` contained exactly that digest; equality test passed.
- `dependencies/finite-fields.tex`:
  `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd`.
- `dependencies/measurements.tex`:
  `b3c03f8f4f1cbe979ee12e9db26227c9bb84c483c4743f1de988c4c38d80f946`.
- `dependencies/strategies-distance.tex`:
  `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f`.
- `dependencies/magic-square.tex`:
  `7593e7f68178a71f62d306de5f9492357e7aed7f5f582952865b181dff477c6b`.
- `qpbt/qpbt-game-and-soundness.tex`:
  `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea`.
- `qpbt/appendix-preliminaries.tex`:
  `20d608c4a71df57bb8b96bf4006f136a3298521e613d4904092a802eed09c284`.
- All six observed fragment digests exactly matched `inventory.json` and A02.
- `QPBT_SOURCE_MAP.md` SHA-256:
  `31b8c51501e433ac0a02592ee35ead3a80234e9e911d0145d490cf715cd14214`.
- Source pin SHA-256:
  `66a1e9db74f1454ce50909728a3b741f9da468b5d61902645557793ceb91ac9c`.
- Split manifest SHA-256:
  `052cfaceb2e4a7b59778936ceb3daea9a33e3592e01b902cb2a9740c58999a20`.
- `workflow/reviews/stage-04a-materialized-contract-a55.md` SHA-256:
  `d2d7708a383d4882ef5b72af6f911e2be7261b9b1ac939cf90c1973afb268c57`;
  read completely.

Relevant authenticated paper anchors read:

| Contract | Anchors |
| --- | --- |
| F01 | `finite-fields.tex:1-100,235-412`, especially trace/duality/normality `:62-83`, odd-QPBT domain `:243-248`, uniform algorithm/table/runtime `:265-307`, arithmetic tied to the selected basis `:350-400` |
| F03 | `measurements.tex:3-19,21-47`; `magic-square.tex:147-173,256-281`; `qpbt-game-and-soundness.tex:383-410` |
| F04 | `strategies-distance.tex:4-32,138-165,213-282,365-395`; `qpbt-game-and-soundness.tex:533-545`; `appendix-preliminaries.tex:49-53` |

The paper-source facts used here are: postprocess is a fiber sum with an empty
fiber equal to zero; the QPBT binary sign convention is outcome 0 minus outcome
1; local actions are `A tensor I` and `I tensor B`; conjugation is independently
`V_A A V_A^dagger` and `V_B B V_B^dagger`; finite numeric distance and indexed
Big-O relations are distinct; strategy-family comparisons use the game
distribution and explicitly allow either state; exact consistency is local
operator-action equality; approximate consistency is the off-diagonal outcome
probability; and the paper separately states POVM triangle, consistency
triangle, and postprocess data processing.

The tracked paper notation discrepancy is preserved: Theorem 7.14 declares
`phi_alice`/`phi_bob` but writes `phi_A`/`phi_B` in its conclusion. Consistent
Lean names are a documented notation repair, not a silent source rewrite.

## Authorized local materialization

The authenticated upstream MIPStarRE sources were initially absent from the
detached tree. No alternate worktree or network source was used. After explicit
parent authorization:

1. Archive `/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz`
   was verified as a regular 1,989,153-byte local file with SHA-256
   `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.
2. Exact command:
   `python3 scripts/materialize_mipstarre.py materialize --archive /tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz`.
   Exit 0; tool wall 3.42972844 s; command-reported elapsed 3.439119 s.
3. Exact command: `python3 scripts/materialize_mipstarre.py verify`.
   Exit 0; tool wall 0.031115858 s.
4. Both commands reported source commit
   `507e81220d95266ff3d589d125b2f87c7300a9fb`, inventory digest
   `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`,
   337 files, 105 directories, 5,970,111 bytes, and authored QPBT files 0.

## Pinned API evidence and exact imports

| Area | Weakest elaborated import(s) | Exact pinned API / disposition |
| --- | --- | --- |
| GF trace and basis | `Mathlib.FieldTheory.Finite.Trace`; `Mathlib.FieldTheory.Galois.NormalBasis` | Direct GF instances, `Algebra.trace`, `GaloisField.finrank/card`, `IsGalois.normalBasis`, and `Basis.traceDual` elaborate. No simultaneous self-dual-normal theorem was found. |
| F03 family/postprocess/observable | `MIPStarRE.Quantum.Measurement` | This single import suffices at the pin for `Quantum.Measurement`, qualified `postprocess`, matrix order, unitary group, and the certified binary observable proof. |
| Finite PMF values | `Mathlib.Probability.ProbabilityMassFunction.Basic` | `PMF Question` is callable as `mu x : ENNReal`; real weights are `(mu x).toReal`; finite expectations elaborate as `Finset.univ` sums. |
| PMF marginals | `Mathlib.Probability.ProbabilityMassFunction.Constructions` | `PMF.map` at line 45 supplies `mu.map Prod.fst` and `mu.map Prod.snd`. |
| Euclidean/operator/isometry adapters | `MIPStarRE.Quantum.Measurement`; `MIPStarRE.Quantum.FiniteHilbert` | `Quantum.Op`, `Matrix.toEuclideanLin`, adjoints, Kronecker products, rectangular matrices, product-state action, and the certified tensor isometry elaborate. |
| Indexed asymptotics | `Mathlib.Analysis.Asymptotics.Defs` | `Asymptotics.IsBigO Filter.atTop value scale` elaborates without the guessed nonexistent `Asymptotics` umbrella import. |

Exact materialized declarations inspected include
`MIPStarRE.Quantum.Measurement` (`Measurement.lean:45`), qualified
`MIPStarRE.Quantum.Measurement.postprocess` (`:127`) and
`postprocess_effect` (`:136`), `MIPStarRE.Quantum.Op`
(`FiniteMatrix/Basic.lean:79`), and the explicit matrix/Euclidean lemmas in
`FiniteHilbert.lean:55-117`. The existing LDT `opTensor`, `leftTensor`, and
`rightTensor` are direct `Matrix.kronecker` helpers, but importing the LDT
hierarchy would couple a QPBT foundation to an incompatible downstream
measurement layer. The recommended QPBT adapters are therefore local thin
definitions over `Matrix.kronecker`.

Pinned Mathlib declarations inspected include
`FiniteField.algebraMap_trace_eq_sum_pow` (`Finite/Trace.lean:49`),
`GaloisField.finrank` (`Finite/GaloisField.lean:81`), `GaloisField.card`
(`:131`), `IsGalois.normalBasis` (`Galois/NormalBasis.lean:121`),
`Matrix.reindexAlgEquiv` (`LinearAlgebra/Matrix/Reindex.lean:211`),
`LinearIsometryEquiv.piLpCongrLeft` (`Analysis/Normed/Lp/PiLp.lean:865`),
and `PMF.map` (`ProbabilityMassFunction/Constructions.lean:45`).

## F01 exact callable contract

Recommended public data and adapters, all elaborated in the final union probe:

```lean
structure FieldData (k : Nat) where
  basis : Module.Basis (Fin k) (ZMod 2) (GaloisField 2 k)
  generator : GaloisField 2 k
  normal : forall i, basis i = generator ^ (2 ^ (i : Nat))
  selfDual : forall i j,
    Algebra.trace (ZMod 2) (GaloisField 2 k) (basis i * basis j) =
      if i = j then 1 else 0

noncomputable def fieldTrace (k : Nat) :
    GaloisField 2 k →ₗ[ZMod 2] ZMod 2 :=
  Algebra.trace (ZMod 2) (GaloisField 2 k)

-- Exact theorem boundary; no caller-supplied witness may enter the API.
theorem fieldData_nonempty_of_odd
    (k : Nat) (hk : Odd k) : Nonempty (FieldData k)

noncomputable def fieldDataOfOddExponent
    (k : Nat) (hk : Odd k) : FieldData k
```

The probe used `FieldDataOfOddExponentSignature := forall k, Odd k ->
FieldData k` and a proposition `SelfDualNormalBasisObligation k` only to
elaborate the unresolved theorem boundary. It did **not** inhabit that type,
add an axiom, or move the obligation into a caller argument. In an implementation
stage, the source-faithful theorem remains visible with tracked proof debt until
the dependency is discharged; the constructor is then classical choice from
that theorem.

Recommended coordinate/table adapters, with their compatibility theorem fully
proved in the probe:

```lean
noncomputable def FieldData.coordinates (D : FieldData k) :
    GaloisField 2 k ≃ₗ[ZMod 2] (Fin k -> ZMod 2) := D.basis.equivFun

noncomputable def FieldData.multiplicationMatrix
    (D : FieldData k) (a : GaloisField 2 k) :
    Matrix (Fin k) (Fin k) (ZMod 2) :=
  LinearMap.toMatrix D.basis D.basis
    (Algebra.lmul (ZMod 2) (GaloisField 2 k) a)

theorem FieldData.multiplicationMatrix_mulVec_coordinates
    (D : FieldData k) (a b : GaloisField 2 k) :
    Matrix.mulVec (D.multiplicationMatrix a) (D.coordinates b) =
      D.coordinates (a * b)
```

Directly available instances/APIs:

- `Field (GaloisField 2 k)`, characteristic 2, the `ZMod 2` algebra,
  `Finite`, `FiniteDimensional`, `Algebra.IsSeparable`, and `IsGalois` synthesize.
- Install `Fintype.ofFinite` and resulting `DecidableEq` locally under
  `noncomputable`/`classical` when enumeration is required; do not add redundant
  public instance assumptions to `FieldData`.
- `Odd k` yields `hk.pos.ne'`; therefore
  `GaloisField.finrank 2 hk.pos.ne'` and
  `GaloisField.card 2 k hk.pos.ne'` elaborate.
- `IsGalois.normalBasis` is indexed by Galois automorphisms, not `Fin k`.
  `normalBasis.traceDual` is a trace-dual basis with the same automorphism index,
  but the pin has no theorem that it is the same normal basis.

Unresolved mathematics is exactly: obtain one generator and `Fin k` basis in
zero-based Frobenius order `alpha^(2^i)` and prove its trace Gram matrix is the
identity. This includes the required reindex/order bridge. The later paper's
one-based prose is a cyclic reindexing; public documentation must state that
the binding definition's zero-based order is used.

F01 metadata disposition: replace `fidelity: exact`/no gaps with a tracked
simultaneous-basis gap. Keep `FieldData`, `fieldTrace`, coordinates, and matrix
adapters in F01. Treat `fieldDataOfOddExponent` only as the noncomputable
existence projection. Keep the single deterministic algorithm, selected-basis
coherence, multiplication-table output, and polynomial runtime in K03A.

## F03 exact callable contract

Recommended names and signatures, all cleanly elaborated:

```lean
abbrev MeasurementFamily
    (Question : Type uQuestion) (Outcome : Type uOutcome)
    (Coord : Type uCoord)
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord] :=
  Question -> MIPStarRE.Quantum.Measurement Outcome Coord

def ProjectiveMeasurementFamily (M : MeasurementFamily Question Outcome Coord) : Prop :=
  forall x a, (M x).effect a * (M x).effect a = (M x).effect a

noncomputable def MeasurementFamily.postprocess
    (M : MeasurementFamily Question Outcome Coord)
    (f : Outcome -> Outcome') : MeasurementFamily Question Outcome' Coord :=
  fun x => MIPStarRE.Quantum.Measurement.postprocess (M x) f

abbrev BinaryObservable (Coord : Type uCoord) :=
  { O : MIPStarRE.Quantum.Op Coord //
      O ∈ Matrix.unitaryGroup Coord Complex /\ O * O = 1 }

noncomputable def observableOfMeasurement
    (M : MIPStarRE.Quantum.Measurement (ZMod 2) Coord)
    (hM : forall b, M.effect b * M.effect b = M.effect b) :
    BinaryObservable Coord

@[simp] theorem observableOfMeasurement_val (M) (hM) :
    (observableOfMeasurement M hM : MIPStarRE.Quantum.Op Coord) =
      M.effect 0 - M.effect 1
```

The exact pinned qualified declaration reused by the family wrapper is:

```lean
MIPStarRE.Quantum.Measurement.postprocess
  (M : Quantum.Measurement alpha d) (f : alpha -> beta) :
  Quantum.Measurement beta d
```

Its pinned `postprocess_effect` theorem gives the `Finset.univ.filter` fiber
sum. The probe also proved
`MeasurementFamily.postprocess_effect_eq_zero_of_not_mem_range`.

The observable proof itself elaborated without placeholders. From completeness
on `ZMod 2`, it derives `P + Q = 1`; projectivity derives both orthogonality
orders; positivity supplies Hermiticity; and it proves the difference is a
unitary involution. Thus both certification and the concrete sign equation are
resolved API, not remaining obligations.

F03 metadata disposition: add the missing `uQuestion`; widen source anchors to
`measurements.tex:3-19,21-47` plus the exact magic-square/game sign anchors;
add the qualified/wrapper postprocess and fiber behavior to planned names; add
`BinaryObservable` (or freeze the anonymous subtype) and
`observableOfMeasurement_val`. The current bracket-only provenance is
insufficient.

## F04 finite foundation and adapters

All declarations in this subsection elaborated together in the final union
probe.

### Side-specific rectangular conjugation

```lean
noncomputable def isometryMatrix
    (V : EuclideanSpace Complex Source →ₗᵢ[Complex]
      EuclideanSpace Complex Target) :
    Matrix Target Source Complex :=
  Matrix.toEuclideanLin.symm V.toLinearMap

noncomputable def conjugateByIsometry (V) (A : Quantum.Op Source) :
    Quantum.Op Target := isometryMatrix V * A * (isometryMatrix V)ᴴ

noncomputable def BipartiteIsometry.conjugateAlice (V) (A : Quantum.Op Alice) :
    Quantum.Op AuxAlice := conjugateByIsometry V.alice A

noncomputable def BipartiteIsometry.conjugateBob (V) (B : Quantum.Op Bob) :
    Quantum.Op AuxBob := conjugateByIsometry V.bob B
```

Use the two side-specific methods. Do not require an unrelated Bob operator to
conjugate Alice or vice versa. Soundness call sites must instantiate
`AuxAlice`/`AuxBob` by their explicit junk/ideal product types.

### Local lifts, tensor isometry, and reindexing

```lean
def aliceLocal (A : Quantum.Op Alice) : Quantum.Op (Alice × Bob) :=
  Matrix.kronecker A 1

def bobLocal (B : Quantum.Op Bob) : Quantum.Op (Alice × Bob) :=
  Matrix.kronecker 1 B

noncomputable def BipartiteIsometry.tensorMatrix (V) :
    Matrix (AuxAlice × AuxBob) (Alice × Bob) Complex :=
  Matrix.kronecker (isometryMatrix V.alice) (isometryMatrix V.bob)

noncomputable def BipartiteIsometry.tensorIsometry (V) :
    EuclideanSpace Complex (Alice × Bob) →ₗᵢ[Complex]
      EuclideanSpace Complex (AuxAlice × AuxBob)

noncomputable def BipartiteIsometry.mapState (V) (psi) :=
  V.tensorIsometry psi

def localProductToJunkIdeal :
  ((AliceJunk × AliceIdeal) × (BobJunk × BobIdeal)) ≃
    ((AliceJunk × BobJunk) × (AliceIdeal × BobIdeal))

noncomputable def reindexState (e : Source ≃ Target) :
    EuclideanSpace Complex Source ≃ₗᵢ[Complex]
      EuclideanSpace Complex Target :=
  LinearIsometryEquiv.piLpCongrLeft 2 Complex Complex e

def reindexOperator (e : Source ≃ Target) :
    Quantum.Op Source ≃ₐ[Complex] Quantum.Op Target :=
  Matrix.reindexAlgEquiv Complex Complex e
```

The scout proved `isometryMatrix V` has `V^dagger V = I`, proved the Kronecker
matrix has the same identity using `conjTranspose_kronecker` and
`mul_kronecker_mul`, and constructed `tensorIsometry` by
`LinearMap.isometryOfInner`. Therefore the tensor state map is now certified as
an isometry rather than only being a raw matrix action.

### Finite numeric values and bounds

Recommended separate names:

```lean
noncomputable def operatorAction (A : Quantum.Op Coord) (psi) :=
  Matrix.toEuclideanLin A psi

noncomputable def stateDependentDistance (psi) (A B : Quantum.Op Coord) : Real :=
  ||operatorAction (A - B) psi|| ^ 2

noncomputable def operatorFamilyDistanceValue
    (mu : PMF Question) (psi) (A B : Question -> Quantum.Op Coord) : Real :=
  ∑ x, (mu x).toReal * stateDependentDistance psi (A x) (B x)

noncomputable def measurementFamilyDistanceValue
    (mu : PMF Question) (psi)
    (A B : MeasurementFamily Question Outcome Coord) : Real :=
  ∑ x, (mu x).toReal *
    ∑ a, stateDependentDistance psi ((A x).effect a) ((B x).effect a)

def OperatorFamilyDistanceBoundedBy ... (delta : NNReal) : Prop :=
  operatorFamilyDistanceValue ... <= (delta : Real)

def MeasurementFamilyDistanceBoundedBy ... (delta : NNReal) : Prop :=
  measurementFamilyDistanceValue ... <= (delta : Real)
```

The raw-operator value and the POVM answer-summed value remain separate. These
finite exact helpers may accept any vector; a normalized state comes from
`PureStrategy` or an explicit hypothesis at paper-labelled call sites.

## F04 indexed relations, consistency, and laws

### Indexed state/operator/measurement/strategy relations

The following choices elaborated cleanly:

```lean
abbrev ErrorProfile := Nat -> Set.Icc (0 : Real) 1

def IsBigOAtTop (value scale : Nat -> Real) : Prop :=
  Asymptotics.IsBigO Filter.atTop value scale
```

`StateFamiliesBigO`, `OperatorFamiliesBigO`, and
`MeasurementFamiliesBigO` use the appropriate finite value at each `n` and
scale `fun n => (delta n : Real)`. `StrategyFamiliesBigO` combines state
closeness with Alice and Bob outcome-family distance. It explicitly uses
`aliceQuestionMarginal mu := mu.map Prod.fst`, `bobQuestionMarginal mu :=
mu.map Prod.snd`, local lifts to the bipartite carrier, and a
`StrategyStateChoice.first | second` argument. This resolves A02's joint-PMF
and `psi` versus `psi'` ambiguity at the callable boundary.

The strategy wrapper is a directly elaborated relation definition; no theorem
about it was claimed.

### Exact and approximate consistency

These definitions elaborated cleanly in `/tmp/i023_probe09.lean`:

```lean
def MeasurementConsistentOn
    (psi : EuclideanSpace Complex (Coord × Coord))
    (M : Quantum.Measurement Outcome Coord) : Prop :=
  forall a,
    operatorAction (aliceLocal (Bob := Coord) (M.effect a)) psi =
    operatorAction (bobLocal (Alice := Coord) (M.effect a)) psi

noncomputable def povmConsistencyValue
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MeasurementFamily Question Outcome Alice)
    (B : MeasurementFamily Question Outcome Bob) : Real :=
  ∑ x, (mu x).toReal *
    ∑ a, ∑ b ∈ Finset.univ.erase a,
      Complex.re (inner Complex psi
        (operatorAction (aliceLocal ((A x).effect a) *
          bobLocal ((B x).effect b)) psi))
```

`POVMConsistencyBoundedBy` is the corresponding finite `<= delta` helper.
`POVMConsistencyBigO` evaluates this quantity on `Nat`-indexed PMFs, states,
and measurement families against an `ErrorProfile`. The finite helper is not
itself the paper's `simeq_delta`; the indexed wrapper is the paper-facing
relation.

### Law contracts and proof disposition

Four exact *statement contracts* elaborated as `Prop` definitions. No proof of
any law is claimed, and no `sorry`, `axiom`, `constant`, or `opaque` was used.

| Contract | Exact callable semantics | Elaboration/proof status | Recommended owner |
| --- | --- | --- | --- |
| `FiniteMeasurementTriangleLaw` | exact bounds `A-B <= delta`, `B-C <= epsilon` imply `A-C <= 2 * (delta + epsilon)`; factor 2 is explicit for squared norms | statement elaborated; proof unresolved | finite helper lemma in `F04-DISTANCE-LAWS` |
| `MeasurementFamiliesBigOTriangleLaw` | Big-O `A~B` at `delta` and `B~C` at `epsilon` imply `A~C` at pointwise `delta + epsilon`; Big-O absorbs the finite factor | statement elaborated; proof unresolved | `F04-DISTANCE-LAWS` |
| `MeasurementFamiliesPostprocessLaw` | `MeasurementFamiliesBigO A B delta` implies the same relation after the same explicit `MeasurementFamily.postprocess ... f` on both families | statement elaborated; proof unresolved | `F04-DISTANCE-LAWS`, dependent on F03 |
| `POVMConsistencyBigOTriangleLaw` | premises `A simeq_epsilon B`, `C simeq_delta B`, `C simeq_gamma D`; conclusion scale `epsilon + 2 * sqrt(delta + gamma)` | statement elaborated; proof unresolved | `F04-CONSISTENCY` |

Using a general `Nat -> Real` scale in law conclusions is necessary because
pointwise sums and `epsilon + 2*sqrt(delta+gamma)` need not remain in `[0,1]`,
even though each input error profile does. This keeps the source error domain
and the derived Big-O scales distinct instead of inserting an unmentioned
clamp.

Recommended F04 split:

| Node | Owns | Dependencies |
| --- | --- | --- |
| Re-scoped `F04-DISTANCE` (finite foundation) | `PureStrategy`, local lifts, rectangular/side conjugation, certified tensor isometry, grouping/reindexing, action, finite values, exact bounds | F03 for measurement carrier |
| New `F04-ASYMPTOTIC` | `ErrorProfile`, Big-O base, state/operator/measurement/strategy indexed relations, PMF marginals, explicit state choice | finite F04 |
| New `F04-CONSISTENCY` | exact `MeasurementConsistentOn`, finite consistency value/bound, indexed consistency, Proposition 4.29 contract/proof | F03, finite F04, F04-ASYMPTOTIC |
| New `F04-DISTANCE-LAWS` | finite triangle helper, indexed Fact 4.28, postprocess Fact 4.26 | F03, finite F04, F04-ASYMPTOTIC |

If the node is not split, F04 must expand its sources, planned names, and
issue/dependency graph to include every declaration above. Merely leaving the
promises in prose is not an acceptable freeze. Re-scoping is recommended
because these are separate paper definitions and proof obligations with
different dependency boundaries.

## A02 finding dispositions

| A02 finding | Disposition |
| --- | --- |
| 1. F04 numeric predicate is not the cited relation | **Resolved at API level by separation, canonical metadata still blocked.** Use `...DistanceValue` and `...BoundedBy` for finite numbers; use `ErrorProfile` plus indexed Big-O definitions for paper relations. Remove/rename `familyApprox`. Re-scope F04 and add F04-ASYMPTOTIC. |
| 2. F04 lacks local/tensor adapters | **Resolved by elaborated API.** Freeze `aliceLocal`, `bobLocal`, `isometryMatrix`, adjoint identity, `tensorMatrix`, certified `tensorIsometry`, `mapState`, grouping equivalence, and state/operator reindexing. |
| 3. Paired conjugation has wrong callable shape | **Resolved by elaborated API.** Replace paired `.conjugate` with independent `.conjugateAlice`/`.conjugateBob`; retain `V A V^dagger`; instantiate factored target carriers downstream; retain the paper-name discrepancy note. |
| 4. F03 provenance/names incomplete | **Canonical metadata change required.** Add question universe, widened anchors, qualified/wrapper postprocess and empty-fiber behavior, `BinaryObservable`, and the exact value theorem. Observable certification is fully proved in probe. |
| 5. F01 conflates existence, algorithm, representation | **Mathematical blocker remains and metadata must change.** Track simultaneous-basis existence in F01, keep uniform algorithm/tables/runtime/coherence in K03A, and use direct GF/trace/coordinate APIs as the representation layer. No caller witness. |
| 6. PMF and strategy-state semantics unresolved | **Resolved at API level.** Use Mathlib `PMF`; consume joint game PMF through named marginals; require finite types only at averages/games; expose `.first | .second` state choice in the strategy relation. |
| 7. Normal-basis indexing | **Resolved as documentation policy.** Use `Fin k` zero-based Frobenius order from the binding definition and document the cyclic relationship to later one-based prose. |

## Probe log

All Lean commands were run from `/tmp/qpbt-023-lean-api-a03` against the seeded
private `.lake`. Temporary files were written only under `/tmp` with
`apply_patch`. No `lake build` was run. Durations are tool-reported wall times;
the first 15 were retained at the displayed 0.01 s precision.

| # | Exact command | Wall | Exit | Result |
| --- | --- | ---: | ---: | --- |
| 1 | `lake env lean /tmp/i023_probe01.lean` | 5.40 s | 1 | Guessed nonexistent import `Mathlib.Analysis.Asymptotics.Asymptotics`; corrected to `.Defs`. |
| 2 | `lake env lean /tmp/i023_probe01.lean` | 7.40 s | 1 | Import fixed; guessed nonexistent `PMF.coeFn`; exact PMF call syntax then used. |
| 3 | `lake env lean /tmp/i023_probe02.lean` | 7.57 s | 0 | Certified projective `ZMod 2` observable and exact `effect 0 - effect 1` value theorem passed. |
| 4 | `lake env lean /tmp/i023_probe03.lean` | 4.84 s | 1 | `omega` did not consume `Odd k`; `traceDual` required local classical decidable equality. |
| 5 | `lake env lean /tmp/i023_probe03.lean` | 4.27 s | 0 | GF instances, finrank/card, trace, normal basis, trace dual, and unresolved boundary type passed. |
| 6 | `lake env lean /tmp/i023_probe04.lean` | 8.51 s | 0 | Rectangular conjugation, local lifts, Kronecker state map, grouping, and initial reindex adapters passed. |
| 7 | `lake env lean /tmp/i023_probe05.lean` | 7.90 s | 1 | Projection precedence and Bob-local inference errors in strategy wrapper. |
| 8 | `lake env lean /tmp/i023_probe05.lean` | 7.27 s | 1 | Bob inference fixed; one remaining projection-parenthesization error. |
| 9 | `lake env lean /tmp/i023_probe05.lean` | 4.62 s | 0 | Finite PMF values/bounds and state/operator/measurement/strategy Big-O wrappers passed. |
| 10 | `lake env lean /tmp/i023_probe06.lean` | 7.47 s | 1 | Empty-fiber proof used a `simp` step that made no progress. |
| 11 | `lake env lean /tmp/i023_probe06.lean` | 7.48 s | 1 | Empty-fiber Set.range witness had equality orientation reversed. |
| 12 | `lake env lean /tmp/i023_probe06.lean` | 7.36 s | 0 | Qualified family postprocess, fiber theorem, empty-fiber zero, and finite PMF sum passed. |
| 13 | `lake env lean /tmp/i023_probe07.lean` | 4.40 s | 1 | Parser rejected an over-typed Unicode `mulVec` notation. |
| 14 | `lake env lean /tmp/i023_probe07.lean` | 4.74 s | 0 | Coordinates, multiplication matrix, and coordinate-action theorem passed. |
| 15 | `lake env lean /tmp/i023_probe04.lean` | 6.97 s | 0 | Stronger `Matrix.reindexAlgEquiv` operator adapter passed. |
| 16 | `lake env lean /tmp/i023_all_signatures.lean` | 11.769535456 s | 0 | Initial union of F01/F03/F04 signatures passed. |
| 17 | `lake env lean /tmp/i023_probe08.lean` | 10.591045406 s | 1 | Tensor-isometry proof needed an explicit `toEuclideanLin` equality and unfolding of `Matrix.kronecker`. |
| 18 | `lake env lean /tmp/i023_probe08.lean` | 11.288499003 s | 0 | Individual and Kronecker adjoint identities plus certified tensor linear isometry passed. |
| 19 | `lake env lean /tmp/i023_probe09.lean` | 8.001309462 s | 1 | Typed inner-product notation produced a parser error in the consistency value. |
| 20 | `lake env lean /tmp/i023_probe09.lean` | 7.477109166 s | 0 | Exact/approximate consistency and all four law statement contracts passed using `inner Complex`. |
| 21 | `lake env lean /tmp/i023_all_signatures.lean` | 12.502608422 s | 0 | Final union, now including projectivity, side conjugation, certified tensor isometry, grouping/reindex, finite values/bounds, and indexed strategy relation, passed. |

Totals: Lean compile attempts 21; passes 12; expected scouting failures 9;
aggregate displayed/tool wall approximately 157.83 s. Every failure was an API,
parser, or proof-script correction in a temporary probe. None is a remaining
build failure. The only unresolved mathematics is explicitly separated above.

Final temporary probe inventory: 10 Lean files, 1,589 lines, 60,790 bytes.
`rg -n '\bsorry\b|\baxiom\b|\bconstant\b|\bopaque\b'` over all ten files
returned exit 1 with no matches. Thus placeholder matches are 0.

## Action accounting

```json
{
  "repository_file_writes": 0,
  "tracked_repository_edits": 0,
  "canonical_workflow_state_writes": 0,
  "research_metrics_writes": 0,
  "git_writes": 0,
  "git_ref_or_worktree_writes": 0,
  "destructive_git_commands": 0,
  "authorized_ignored_materialization_commands": 2,
  "authorized_materialized_files": 337,
  "temporary_lean_files_written": 10,
  "lean_invocations": 21,
  "lean_passes": 12,
  "lean_failures": 9,
  "lake_env_lean_invocations": 21,
  "lake_build_invocations": 0,
  "full_build_invocations": 0,
  "affected_target_builds": 0,
  "cache_commands": 0,
  "cache_warm_invocations": 0,
  "cache_seed_invocations": 0,
  "cache_status_invocations": 0,
  "network_accesses": 0,
  "endpoint_accesses": 0,
  "github_operations": 0,
  "credential_accesses": 0,
  "agent_spawns": 0,
  "nested_agents": 0,
  "placeholder_matches": 0,
  "report_files_written": 1,
  "token_usage": null,
  "token_usage_reason": "not exposed to this collaboration subagent"
}
```

Prohibited-action counters are all zero: cache warm/seed/status, full build,
network/endpoint access, GitHub operation, credential access, destructive Git,
tracked repository write, canonical state write, metrics write, and nested
agent spawn.

## Final identity and report integrity

- Final HEAD: `942f9438b991ece8942815db16c019b92d9cdd8e`.
- Final tree: `09123f4b25c892a146aabaa77d73cf0c5f35a0c6`.
- Final tracked status: clean; `git status --short --untracked-files=all`
  produced no output and `git diff --quiet` exited 0.
- Full builds: 0. Cache warms: 0. Cache seeds/status probes: 0.
- The report SHA-256 is intentionally not self-embedded. It is computed after
  this file is closed and communicated to the orchestrator out of band.
