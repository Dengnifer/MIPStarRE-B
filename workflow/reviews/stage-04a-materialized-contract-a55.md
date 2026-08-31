# Stage-04A materialized leaf-contract scout (a55)

## Scope and evidence

Session `i000-scout-a55-materialized-contract` inspected canonical base
`c5a0fecc26eb18452219cf0df31ce2a9113e45f1`. The canonical worktree already
contained unrelated coordinator-owned workflow/metrics changes and two review
reports; none was modified. This session was read-only except for this required
`/tmp` report. It did not run tests, Lean, Lake, cache status/warm/seed, network,
or GitHub commands, and it did not create a worktree, Git ref, or subagent.

The newly materialized source boundary is usable: `sections/READY` is present,
and the three dependency fragments match `split-manifest.json` exactly:

| Fragment | Original lines | SHA-256 |
| --- | ---: | --- |
| `finite-fields.tex` | 1317-1728 | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |
| `measurements.tex` | 1854-1948 | `b3c03f8f4f1cbe979ee12e9db26227c9bb84c483c4743f1de988c4c38d80f946` |
| `strategies-distance.tex` | 2884-3417 | `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f` |

Elapsed wall time was approximately 12 minutes from dispatch through report
completion. Subagents: 0. Exposed token usage: `null` (the collaboration
backend does not expose per-session token accounting; not estimated).

## Exact paper contract

The source order below is binding. Prose is paraphrased; displayed symbolic
domains and equations identify the exact mathematical objects.

### F01: field, trace, and basis

`references/2001.04383v3/sections/dependencies/finite-fields.tex:14-83`
(original 1330-1399) fixes the extension and basis domains:

- `F_{q^k}` is a `k`-dimensional vector space over `F_q`;
- `downsize_q : F_{q^k} -> F_q^k` is the coordinate map for a chosen basis;
- `tr_{q^k -> q} : F_{q^k} -> F_q`, with
  `tr(a) = sum_{j=0}^{k-1} a^(q^j)`;
- self-duality is `tr(e_i e_j) = delta_{i,j}`;
- normality is a basis of the form `{alpha^(q^j)}_{j=0}^{k-1}`.

The project uses only `F_{2^k}` with odd `k`
(`finite-fields.tex:243-248`, original 1559-1564). Lemma
`lem:efficient_basis` (`:283-307`, original 1599-1623) says that, from an odd
integer `k > 0`, a deterministic polynomial-time algorithm produces a
self-dual normal basis of `F_{2^k}/F_2` and its multiplication tables. This is
constructed data, not a caller hypothesis. `:309-317` (original 1625-1633)
then uses normality plus self-duality to derive `tr(e_i)=1` and the all-ones
coordinate vector for `1`.

### F03: finite measurements and observables

`references/2001.04383v3/sections/dependencies/measurements.tex:3-19`
(original 1856-1872) fixes a POVM as `{M_a}_{a in S}`, with `M_a >= 0` and
`sum_a M_a = I`; projective means `M_a^2=M_a`. An observable is unitary, and
a binary observable additionally squares to identity.

The bracket operation at label `def:bracket` (`:34-47`, original 1887-1900)
has domains `x in X`, `a in A`, `f : A -> B`, and is the fiber sum
`M^x_[f(.)=b] = sum_{a : f(a)=b} M^x_a`.

The paper does not define a canonical observable for an arbitrary POVM.
For a two-outcome projective measurement indexed by `F_2`, it fixes the sign
order `E_0-E_1`: see `dependencies/magic-square.tex:149-173` (original
4808-4832) and the QPBT use in `qpbt-game-and-soundness.tex:383-410`
(original 5429-5456). Therefore a generic `Outcome -> phase` conversion is not
source-determined. The weakest faithful public conversion is specifically
`ZMod 2`, requires projectivity, uses effect `0` minus effect `1`, and returns
a certified unitary involution.

### F04: strategy and finite/asymptotic distance

`references/2001.04383v3/sections/dependencies/strategies-distance.tex:20-32`
(original 2903-2915), label `def:tensor-product-strategy`, has symbolic data

`(|psi>, {A^x_a}_{x in X,a in A}, {B^y_b}_{y in Y,b in B})`

where `|psi>` is a unit vector in finite-dimensional
`H_A tensor H_B`, and each indexed family is a POVM on its local space.

The source then uses two related but distinct distance layers:

- state families `psi_n, psi'_n in H`, `n in N`, are close when
  `||psi_n-psi'_n||^2 = O(delta(n))`, with `delta : N -> [0,1]`
  (`strategies-distance.tex:213-224`, original 3096-3107);
- for finite `X`, probability distribution `mu`, state `psi in H`, and POVMs
  `M^x_a,N^x_a`, the finite quantity is
  `E_{x~mu} sum_a ||(M^x_a-N^x_a) psi||^2`
  (`:252-265`, original 3135-3148), and strategy distance also compares both
  player families and same-space states (`:267-282`, original 3150-3165).

Appendix A explicitly extends the operator form to general question-indexed
operators with no answer index:
`E_{x~mu} <psi|(A^x-B^x)^dagger(A^x-B^x)|psi> <= O(delta)`
(`qpbt/appendix-preliminaries.tex:49-53`, original 13134-13138).

Consequently `O(delta)` must not be baked into a finite numeric definition.
The leaf should expose an exact nonnegative real quantity and an explicit
finite bound. A later indexed-family theorem must connect that bound to the
paper's asymptotic relation and universal constant.

## Proposed callable Lean contract

These signatures are a contract proposal, not an elaboration claim. Items
marked **fixed** follow the source and approved carrier policy. Items marked
**faithful boundary** are representation choices Lean needs but the paper does
not choose. Items marked **unresolved** require QPBT-023 review before a writer
is issued.

### Exact imports

`MIPStarRE.QPBT.Basic.Field`:

```lean
import Mathlib.FieldTheory.Finite.Trace
import Mathlib.FieldTheory.Galois.NormalBasis
```

`MIPStarRE.QPBT.Basic.Approximation`:

```lean
import MIPStarRE.Quantum.Measurement
import MIPStarRE.Quantum.FiniteHilbert
import Mathlib.LinearAlgebra.UnitaryGroup
import Mathlib.Probability.ProbabilityMassFunction.Basic
```

The Approximation module must not import/open/inherit the incompatible LDT
measurement hierarchy. `PMF` is preferred over
`MIPStarRE.LDT.Distribution`: on a finite question type it carries probability
normalization without coupling a QPBT foundation to LDT. This exact PMF choice
is a **faithful boundary** and needs immutable API review.

### F01 signatures

```lean
namespace MIPStarRE.QPBT

structure FieldData (k : Nat) where
  basis : Module.Basis (Fin k) (ZMod 2) (GaloisField 2 k)
  generator : GaloisField 2 k
  normal : forall i,
    basis i = generator ^ (2 ^ (i : Nat))
  selfDual : forall i j,
    Algebra.trace (ZMod 2) (GaloisField 2 k) (basis i * basis j) =
      if i = j then 1 else 0

noncomputable def fieldDataOfOddExponent
    (k : Nat) (hk : Odd k) : FieldData k

noncomputable def fieldTrace (k : Nat) :
    GaloisField 2 k →ₗ[ZMod 2] ZMod 2 :=
  Algebra.trace (ZMod 2) (GaloisField 2 k)

end MIPStarRE.QPBT
```

| Aspect | Contract | Status |
| --- | --- | --- |
| Universe | `k : Nat`; no carrier universe parameter | fixed |
| Carrier | direct `GaloisField 2 k` over `ZMod 2` | fixed |
| Instances | derive `Field`, `CharP`, `Algebra`, `Finite`, `FiniteDimensional`; install local noncomputable `Fintype.ofFinite` and resulting `DecidableEq` | fixed |
| Positivity | `Odd k` proves `0 < k` and `k != 0` for `GaloisField.finrank/card` | fixed |
| Basis index | `Fin k`, Frobenius order `alpha^(2^i)` | fixed by paper representation |
| Return | `FieldData k`; caller supplies only `k` and `Odd k` | fixed |
| Trace | `ZMod 2`-linear map, not additive/ring hom | fixed; corrects older scout sketches |
| Complexity | excluded from `FieldData`; later node K03A proves algorithm/table complexity | fixed separation |

The structure may be constructible for exponents beyond the paper's odd
domain; that does not weaken the public constructor, whose only advertised
input is `Odd k`. Cardinality is a derived theorem, not a redundant structure
field.

### F03 signatures

```lean
universe uQuestion uOutcome uCoord

abbrev MeasurementFamily
    (Question : Type uQuestion) (Outcome : Type uOutcome)
    (Coord : Type uCoord)
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord] :=
  Question -> MIPStarRE.Quantum.Measurement Outcome Coord

def ProjectiveMeasurementFamily
    (M : MeasurementFamily Question Outcome Coord) : Prop :=
  forall x a, (M x).effect a * (M x).effect a = (M x).effect a

noncomputable def observableOfMeasurement
    (M : MIPStarRE.Quantum.Measurement (ZMod 2) Coord)
    (hM : forall b, M.effect b * M.effect b = M.effect b) :
    { O : MIPStarRE.Quantum.Op Coord //
      O ∈ Matrix.unitaryGroup Coord Complex /\ O * O = 1 }
```

The returned operator is definitionally intended to be `M.effect 0 -
M.effect 1`. Whether to give the certified return an auxiliary public name
such as `BinaryObservable` is **unresolved**. The anonymous subtype above is
the smallest contract and prevents callers from treating an arbitrary POVM as
a paper observable.

| Aspect | Contract | Status |
| --- | --- | --- |
| Universes | `uQuestion uOutcome uCoord` | add `uQuestion`; faithful boundary |
| Question instances | none for a family alias | fixed weakest boundary; finiteness begins at games/averages |
| Outcome/coordinate instances | explicit `Fintype` and `DecidableEq` | fixed blueprint policy |
| Scalar/operator | `Complex`; `Quantum.Op Coord = Matrix Coord Coord Complex` | fixed |
| Postprocess | reuse qualified `Quantum.Measurement.postprocess` | fixed; exact fiber sum |
| Projectivity | separate pointwise predicate | fixed |
| Observable domain | projective `ZMod 2` measurement | fixed by QPBT/Magic-Square sources |
| Observable return | certified unitary involution | faithful boundary; bundle naming unresolved |
| Sign order | effect `0` minus effect `1` | fixed |

### F04 signatures

```lean
universe uQuestionA uQuestionB uOutcomeA uOutcomeB
universe uQuestion uOutcome uCoord
universe uAlice uBob uAuxAlice uAuxBob

structure PureStrategy
    (QuestionA : Type uQuestionA) (QuestionB : Type uQuestionB)
    (OutcomeA : Type uOutcomeA) (OutcomeB : Type uOutcomeB)
    (Alice : Type uAlice) (Bob : Type uBob)
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob] where
  state : EuclideanSpace Complex (Alice × Bob)
  normalized : ‖state‖ = 1
  alice : MeasurementFamily QuestionA OutcomeA Alice
  bob : MeasurementFamily QuestionB OutcomeB Bob

structure BipartiteIsometry
    (Alice : Type uAlice) (Bob : Type uBob)
    (AuxAlice : Type uAuxAlice) (AuxBob : Type uAuxBob)
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    [Fintype AuxAlice] [DecidableEq AuxAlice]
    [Fintype AuxBob] [DecidableEq AuxBob] where
  alice : EuclideanSpace Complex Alice →ₗᵢ[Complex]
    EuclideanSpace Complex AuxAlice
  bob : EuclideanSpace Complex Bob →ₗᵢ[Complex]
    EuclideanSpace Complex AuxBob

noncomputable def BipartiteIsometry.conjugate
    (V : BipartiteIsometry Alice Bob AuxAlice AuxBob)
    (A : MIPStarRE.Quantum.Op Alice)
    (B : MIPStarRE.Quantum.Op Bob) :
    MIPStarRE.Quantum.Op AuxAlice × MIPStarRE.Quantum.Op AuxBob

noncomputable def stateDependentDistance
    (psi : EuclideanSpace Complex Coord)
    (A B : MIPStarRE.Quantum.Op Coord) : Real :=
  ‖Matrix.toEuclideanLin (A - B) psi‖ ^ 2

def familyApprox
    [Fintype Question] [DecidableEq Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B : Question -> Outcome -> MIPStarRE.Quantum.Op Coord)
    (delta : NNReal) : Prop :=
  (sum x, (mu x).toReal *
    sum a, stateDependentDistance psi (A x a) (B x a)) <= (delta : Real)
```

`BipartiteIsometry.conjugate` is intended to convert each local linear
isometry explicitly to its rectangular matrix `V`, then return
`(V_A * A * V_Aᴴ, V_B * B * V_Bᴴ)`. Returning a pair is the smallest way to
retain the single planned name while making both paper sides explicit. A
review may instead approve two names, `conjugateAlice` and `conjugateBob`;
this naming choice is **unresolved**, while the two formulas are fixed.

| Aspect | Contract | Status |
| --- | --- | --- |
| Universes | add question/outcome universes plus the four carrier universes already planned | faithful boundary |
| Strategy carriers | local `EuclideanSpace Complex Alice/Bob`; bipartite state uses product index `Alice × Bob` | faithful finite-coordinate boundary |
| Strategy data | norm-one state and both finite POVM families | exact up to coordinate representation |
| Isometry targets | `AuxAlice`/`AuxBob` represent each entire target local Hilbert space | faithful boundary; downstream factorization into junk/ideal registers remains explicit |
| Operator adapter | `Matrix.toEuclideanLin`; no implicit function/`WithLp` coercion | fixed blueprint policy |
| Distribution | Mathlib `PMF Question` on a `Fintype` | faithful boundary; requires review |
| Single distance | squared Euclidean norm, `Real` | exact finite quantity |
| Family domain | raw operator families; measurement effects embed directly; singleton outcome covers no-answer operator families | faithful weakest reusable boundary |
| Error | `NNReal` explicit bound; no `Real.rpow` in leaf definitions | faithful boundary |
| Return | `stateDependentDistance : Real`; `familyApprox : Prop` | fixed proposal |
| Asymptotics | a separate later indexed-family `O(delta)` bridge | unresolved downstream obligation, intentionally not hidden here |

The paper permits evaluation on either strategy state in strategy distance.
The leaf relation therefore takes the state explicitly; a future strategy
distance theorem must quantify which normalized state is used rather than
silently selecting one.

## Exact downstream consumers

The generated blueprint gives these direct consumers:

| Leaf | Direct consumers |
| --- | --- |
| F01 | F02-CODE, F05-PAULI, F06-CL, G01-PARAMETERS, K03A-FIELD-ARITHMETIC |
| F03 | E01-ORTHO, E02-MAGIC-SQUARE, F04-DISTANCE, F05-PAULI, F08-MAGIC-GAME, F09-LDT-GAME |
| F04 | A02-PRELIMINARIES, E01-ORTHO, E02-MAGIC-SQUARE, E03-LINEARITY, E04-TENSOR-CODE, N01-NAIMARK |

The first concrete call sites that constrain the contract are: F02/F05 for
field coordinates and trace phase; F08/G02 for `F_2` binary measurements;
A02 for raw operator-family averages; N01 for isometries and enlarged states;
and S01 transitively for the separate Alice/Bob conjugations displayed in
Theorem 7.14 (`qpbt-game-and-soundness.tex:533-545`, original 5579-5591).

## Statement-integrity table

| Declaration | Paper assumptions | Lean assumptions | Paper conclusion/data | Lean conclusion/data | Verdict |
| --- | --- | --- | --- | --- | --- |
| `FieldData` | extension `F_(2^k)/F_2`; self-dual normal basis | direct `GaloisField 2 k`, `Basis (Fin k)`, Frobenius and trace equations | basis with both properties | same equations on the concrete carrier | exact |
| `fieldDataOfOddExponent` | odd integer `k>0` | `k : Nat`, `Odd k` (which entails positivity) | algorithm outputs basis/tables | noncomputable mathematical basis data only | faithful boundary; algorithmic complexity deferred to K03A |
| `fieldTrace` | `F_2`-linear extension trace | derived GF algebra/finite-dimensional instances | `F_(2^k) -> F_2` trace | `Algebra.trace` linear map | exact |
| `MeasurementFamily` | family of finite POVMs indexed by questions | arbitrary question type; finite/decidable outcome and coordinates | `x -> {M^x_a}` | function into qualified complete POVM structure | faithful boundary |
| `ProjectiveMeasurementFamily` | every effect is a projector | pointwise matrix idempotence | projective family | same predicate | exact |
| `observableOfMeasurement` | two-outcome projective `F_2` measurement | same plus explicit projectivity proof | unitary involution `E_0-E_1` | certified unitary involution with same sign | exact modulo coordinate bundle |
| `PureStrategy` | finite bipartite unit vector plus Alice/Bob POVM families | finite coordinate/question/outcome types | tensor-product strategy tuple | product-index Euclidean realization of tuple | faithful boundary |
| `BipartiteIsometry.conjugate` | local isometries and `V A V^dagger` on each side | finite Euclidean linear isometries, explicit matrix conversion | two conjugated local operators | pair of the same two formulas | faithful boundary |
| `stateDependentDistance` | `||(A-B)psi||^2` | finite Euclidean state and matrix operators | nonnegative scalar | exact real squared norm | exact |
| `familyApprox` | PMF average and outcome sum bounded by `O(delta)` | finite PMF average bounded by explicit `delta : NNReal` | asymptotic closeness relation | finite numerical bound only | faithful boundary; separate `O` bridge required |

## Self-dual-normal-basis obligation

The exact mathematical theorem needed before the no-`sorry` F01 writer can
finish is:

```lean
theorem exists_selfDualNormalBasis_of_odd
    (k : Nat) (hk : Odd k) :
    exists (alpha : GaloisField 2 k)
      (b : Module.Basis (Fin k) (ZMod 2) (GaloisField 2 k)),
      (forall i, b i = alpha ^ (2 ^ (i : Nat))) /\
      (forall i j,
        Algebra.trace (ZMod 2) (GaloisField 2 k) (b i * b j) =
          if i = j then 1 else 0)
```

Pinned Mathlib commit `81a5d257c8e410db227a6665ed08f64fea08e997`
provides:

- direct GF `Field`, `CharP`, `Algebra`, `Finite`, and
  `FiniteDimensional` instances (`FieldTheory/Finite/GaloisField.lean:65-74`),
  plus `finrank` and `card` after `k != 0` (`:80-95,131-135`);
- trace nondegeneracy and the Frobenius power-sum trace formula
  (`FieldTheory/Finite/Trace.lean:36-56`);
- a generic Galois-orbit normal basis (`FieldTheory/Galois/NormalBasis.lean:108-129`);
- the trace-dual of any basis and exact Kronecker-delta equations
  (`RingTheory/Trace/Basic.lean:547-604`).

A negative search across the pinned Mathlib tree found no self-dual normal
basis theorem, no characteristic-two odd-degree criterion, and no formalized
Wang/Lenstra/Shoup construction. `normalBasis` and `traceDual` do not imply
that one basis is simultaneously normal and fixed by trace duality.

Discharge plan, adding no assumption, axiom, or constant:

1. Add a dedicated dependency issue and module for the theorem above, separate
   from the two-file QPBT-013 writer. Record the paper's exact
   `lem:efficient_basis` citation chain in `docs/paper-gaps/` and pin any
   additional primary mathematical source before using it.
2. Reuse Mathlib's GF, trace, normal-basis, and trace-dual APIs for the ambient
   algebra. Formalize the missing characteristic-two odd-degree theorem,
   preferably via the normal-basis/group-algebra factorization underlying
   Wang's construction. The proof must produce the simultaneous witness, not
   merely separate normal and self-dual bases.
3. Once the existence theorem is proved, define
   `fieldDataOfOddExponent` by classical choice from that theorem. Its public
   parameters remain exactly `(k) (hk : Odd k)`.
4. Track polynomial-time construction and multiplication tables separately in
   K03A. Mathematical F01 may be noncomputable; K03A cannot claim the paper's
   algorithmic conclusion merely from classical choice.
5. If a skeleton temporarily needs a conditional helper, keep it internal and
   name it `..._ofObligations`; keep the source-faithful constructor visibly
   unproved. Stage 4A/QPBT-013 currently permits no such `sorry`, so the writer
   remains blocked until the dependency theorem is actually proved.

## Smallest ordered blueprint edits after QPBT-003

1. Create `docs/paper-gaps/self-dual-normal-basis.md` with the exact claim,
   missing pinned API, mathematical/algorithmic split, and discharge issue.
2. Add gap `G16` to `blueprint/metadata/gaps.json`, reciprocally link F01 and
   K03A, and mark the unresolved proof boundary without changing any public
   theorem assumption.
3. Extend the blueprint metadata/checker with one optional, validated
   `signatures` array rendered as `Callable signatures`; populate it only for
   F01, F03, and F04 with the declarations above. Prose in `encoding` alone is
   not a sufficiently frozen callable contract.
4. Amend F03's boundary to include `uQuestion`, explicitly state that the
   family alias does not require finite questions, and widen its source anchors
   to cover the POVM definition plus the `F_2` observable convention.
5. Amend F04 with the question/outcome universes, product-index state carrier,
   `PMF` representation, exact `Real`/`NNReal` return-error split, and the
   separate asymptotic bridge obligation. Resolve the conjugation pair-vs-two-
   names choice in review.
6. Update generated declaration lists/TeX/graph, add checker tests for the
   signature field, and record the integrity table above.
7. Open the dedicated self-dual proof issue as a dependency of QPBT-013 (or
   split F03/F04 into a disjoint first implementation issue); do not make the
   F03 measurement leaf wait on F01's theorem if issue ownership is split.

This order preserves QPBT-023's dependency on QPBT-003 and avoids editing an
approved blueprint range before its integration/second-commit gate.

## Blockers and independent gates

Current blockers:

1. QPBT-023 remains dependency-blocked on QPBT-003; its approved blueprint
   ranges must be integrated and the second main commit created first.
2. Pinned Mathlib cannot discharge the F01 simultaneous basis theorem.
3. The observable certified-bundle name and local-conjugation API need one
   explicit choice; the mathematics/sign order/formulas are no longer
   ambiguous.
4. The `PMF` and product-index Euclidean adapters have not been elaborated in
   the materialized project. This scout was forbidden to run Lean.
5. The paper's `O(delta)` relation is not a finite error type; a later bridge
   remains an explicit obligation.

Required independent-review gates:

- source reviewer checks every anchor and the F01 mathematical/algorithmic
  split against the materialized v3 source;
- fresh Lean API reviewer elaborates the exact signatures/imports at the
  pinned Mathlib/project revisions and checks all explicit adapters;
- statement-integrity reviewer approves each verdict above, especially the
  binary observable and finite-vs-asymptotic boundary;
- blueprint source-root, graph, deterministic generation, declaration-sync,
  unit-test, and diff-integrity checks pass;
- implementation review scans for `sorry`, `axiom`, `constant`, generic
  assumptions/bridges, LDT measurement leakage, and unreviewed public
  hypotheses;
- only after the self-dual dependency is proved may the no-`sorry` F01 portion
  of QPBT-013 be approved.

## Commands/actions

Read-only commands used were bounded `git rev-parse/status`, `rg`, `find`,
`sed`, `nl`, `jq`, `sha256sum`, and `date` over AGENTS, materialized paper
fragments/source map/manifests, blueprint metadata/generated chapters/issues,
the two required prior reports plus directly relevant earlier QPBT-023 scouts,
the authenticated materialized MIPStarRE source, and pinned Mathlib source.
No validation/build command was run by this scout. This report was created in
`/tmp` with `apply_patch`; no repository file was written.
