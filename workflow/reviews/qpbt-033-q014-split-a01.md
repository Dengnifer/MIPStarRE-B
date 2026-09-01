# QPBT-033 parallel split preflight (A01)

## Verdict and findings

QPBT-014 should become a tracking issue, not retain one four-file writer. The
four Lean paths are mutually independent after their callable contracts are
frozen, but the current issue is not safe to dispatch directly. The smallest
sufficient plan is one contract PR, four disjoint Lean PRs, and one no-source
combined validation issue.

Findings, in blocking order:

1. **Blocker: three callable contracts are not exact enough for independent
   writers.** F02 lists three Lean names while also requiring evaluation,
   injectivity, and linearity. F05 lists four names while its statement also
   requires Fourier inversion and EPR identities. F06/F07 list six names but
   leave the recursive CL certificate, graph distribution, heterogeneous
   fibers, and sampler/decider boundary unstated. Independent writers could
   produce incompatible, individually plausible APIs. One reviewed contract
   freeze must precede all four Lean PRs.
2. **Blocker: QPBT-014 omits F06 from both its acceptance source list and its
   dependency description.** `Game/Types.lean` cannot implement F07 alone:
   F07 directly depends on F06, and both nodes deliberately own the same Lean
   module. F06 then F07 is a sequential declaration order inside one child PR;
   it is not a second writable lane.
3. **Blocker: the “raw BitVec codec” acceptance item has no F02/F05/F06/F07/G01
   declaration, source anchor, signature, or owned path.** Raw Turing-machine
   strings occur in the paper's CL/typed-sampler prose, while the blueprint
   explicitly defers efficiency to K03-K04 and places uniform finite POVM
   codecs in G02. The item must be removed from QPBT-014 or assigned to a
   separately anchored later node. It cannot be invented in `Game/Types.lean`.
   The same gate's reference to “FieldData declarations” is already discharged
   by integrated `Basic/Field.lean`; none of the four children owns that API.
4. **High: F05 is governed by paper gap G09.** The only generally valid
   cross-basis law is the trace-valued twisted phase
   `tauX(a) * tauZ(b) = psi(-trace(a*b)) • (tauZ(b) * tauX(a))`. A commutation
   specialization is admissible only after proving that this phase is one.
   Characteristic two may simplify the inverse phase, but the public theorem
   should retain the paper's sign/order and should not silently claim arbitrary
   cross-basis commutation.
5. **High: F02's phrase “one-hot indicator vector indexed by field points” is
   materially misleading.** The paper indexes coordinates by
   `y : {0,1}^m` and evaluates `ind_{m,y}` at `x : F_q^m`; the resulting vector
   is one-hot only when `x` is itself Boolean. The contract must distinguish a
   Boolean coordinate index from a field evaluation point. Its interpolation
   equation `g_a(y)=a_y`, linearity, and injectivity must be theorem obligations,
   not structure fields.
6. **High: `Mathlib.Combinatorics.SimpleGraph` is not a valid F07 carrier.** A
   paper type graph explicitly permits self-loops, whereas Mathlib's
   `SimpleGraph` is irreflexive. Store a finite symmetric ordered-edge support
   (or an equivalent loop-preserving `Sym2` representation), require it to be
   nonempty, and define the PMF on ordered endpoints. This automatically gives
   the paper denominator `2m-k` without dropping loops.
7. **High: integrated F03 is only its first callable slice.**
   `Approximation.lean` currently provides measurement families,
   projectivity, and postprocessing, but not the frozen `BinaryObservable` and
   `observableOfMeasurement` declarations. F05 can proceed only if its frozen
   surface uses the available raw operator/measurement API. If it is specified
   in terms of `BinaryObservable`, an explicit F03-completion dependency must
   be inserted before the Pauli child.
8. **Medium: G01 is exact and independent of the other three lanes.** Its
   project-owned `Parameters` structure and existential admissibility predicate
   need only import F01. It must not alias `MIPStarRE.LDT.Parameters`, add
   positivity, or accept field data from the caller.

No paper ambiguity was silently repaired. Findings 1-3, 5, and 7 are contract
gaps to resolve in QPBT-035. Finding 4 is the existing documented G09 repair.

## Immutable evidence and source authentication

Inspected base/head: `d60a71c945ebf407b4a1c8c322c38181e7d09dfa`;
tree: `cbd1b48827acb90615f437ebd9d55d3705d7cc70`. The detached worktree was
clean before this report was added.

The split sources are intentionally absent from this checkout. They were read
from the already authenticated local materialization in the QPBT-002 worktree;
no network was used. SHA-256 values were checked locally:

| Source | SHA-256 |
| --- | --- |
| `dependencies/finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |
| `dependencies/pauli.tex` | `aba301b2e225f0ceaeff6a942a75ee6d5db73283ba25e208e2e43452818aef2f` |
| `dependencies/types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` |
| `dependencies/magic-square.tex` | `7593e7f68178a71f62d306de5f9492357e7aed7f5f582952865b181dff477c6b` |
| `dependencies/low-degree-code.tex` | `e77125aa2c20f037b949f8890efcaaf370f5ca25407048a5ac142115104bdc9e` |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `qpbt/qpbt-game-and-soundness.tex` | `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea` |

Primary anchors are F02 `low-degree-code.tex:1-94`, F05 `pauli.tex:1-214`,
F06 `conditionally-linear.tex:1-715`, F07 `types.tex:1-582`, G01
`qpbt-game-and-soundness.tex:60-63`, and F08 context
`magic-square.tex:1-368`. The complete dependency closure read was F01, F02,
F03, F05, F06, F07, and G01, including the integrated `Field.lean` and
`Approximation.lean` implementations.

## Exact dependency and import graph

```text
QPBT-035 reviewed contract freeze
  +--> Polynomial.lean  : F01 -> F02
  +--> Pauli.lean      : F01 + available F03 slice -> F05/G09
  +--> Types.lean      : F01 -> F06 -> F07       (sequential in one file)
  +--> Parameters.lean : F01 -> G01

Polynomial + Pauli + Types + Parameters
  `--> QPBT-040 singleton combined-snapshot validation
```

There is no Lean import edge among the four new files. In particular,
`Parameters.lean` does not feed the other three at this stage, and F07's only
new-file prerequisite is F06 in the same `Types.lean` owner.

| File | Exact direct imports to freeze | Reused declarations |
| --- | --- | --- |
| `Basic/Polynomial.lean` | `Mathlib.RingTheory.MvPolynomial.Basic`; `MIPStarRE.QPBT.Basic.Field` | `MvPolynomial.restrictDegree`, `MvPolynomial.eval`, `GaloisField 2 k` |
| `Basic/Pauli.lean` | `Mathlib.Analysis.Fourier.FiniteAbelian.Orthogonality`; `Mathlib.Analysis.SpecialFunctions.Complex.CircleAddChar`; `MIPStarRE.QPBT.Basic.Field`; `MIPStarRE.QPBT.Basic.Approximation` | `ZMod.stdAddChar`, `AddChar.expect_eq_ite`, `fieldTrace`, `MIPStarRE.Quantum.Op`, `MIPStarRE.Quantum.Measurement` |
| `Game/Types.lean` | `Mathlib.Probability.Distributions.Uniform`; `MIPStarRE.QPBT.Basic.Field` | `PMF.uniformOfFintype`, `PMF.map`, finite function spaces; deliberately not `SimpleGraph` |
| `Game/Parameters.lean` | `MIPStarRE.QPBT.Basic.Field` | `Odd`, `Dvd.dvd`, project-owned namespace only |

`MIPStarRE.LDT.Preliminaries.polyFunc` is already a thin abbreviation of
`MvPolynomial.restrictDegree`, and its finite-field module already proves
Fourier orthogonality. They are useful precedents, but importing either would
pull the incompatible LDT parameter hierarchy into the QPBT boundary. The
lowest Mathlib APIs above avoid that dependency. No missing helper should be
reproved a third way.

## Contract manifest for QPBT-035

QPBT-035 must publish elaborated signatures and bind them by SHA-256 before a
writer starts. The following shapes are the smallest source-faithful surface;
names marked `required addition` close facts already required by the blueprint
statement but currently absent from its declaration list.

### F02 / Polynomial

```lean
abbrev BooleanPoint (m : Nat) := Fin m -> ZMod 2
abbrev FieldPoint (k m : Nat) := Fin m -> GaloisField 2 k

noncomputable abbrev IndividualDegreePolynomial (k m d : Nat) :=
  MvPolynomial.restrictDegree (Fin m) (GaloisField 2 k) d

noncomputable def indicatorVector {k m : Nat} (x : FieldPoint k m) :
    BooleanPoint m -> GaloisField 2 k

noncomputable def lowDegreeEncode (k m : Nat) :
    (BooleanPoint m -> GaloisField 2 k) ->ₗ[GaloisField 2 k]
      IndividualDegreePolynomial k m 1

@[simp] theorem lowDegreeEncode_eval_boolean ... -- required addition
theorem lowDegreeEncode_injective ...            -- required addition
```

The implementation must use the product
`prod_i (if y i = 1 then X i else 1-X i)`, prove evaluation at embedded Boolean
points, and derive injectivity from that theorem. `lowDegreeEncode` being a
linear map exposes linearity directly. It must not require `FieldData`; the
encoding uses only the concrete field, not a chosen basis.

### F05 / Pauli

```lean
inductive PauliBasis | X | Z

noncomputable def pauliX (k : Nat) (a : GaloisField 2 k) :
    MIPStarRE.Quantum.Op (GaloisField 2 k)

noncomputable def pauliZ (k : Nat) (b : GaloisField 2 k) :
    MIPStarRE.Quantum.Op (GaloisField 2 k)

noncomputable def pauliProjector (k : Nat) (W : PauliBasis) :
    MIPStarRE.Quantum.Measurement (GaloisField 2 k) (GaloisField 2 k)

theorem pauli_twistedCommutation (k : Nat)
    (a b : GaloisField 2 k) :
  pauliX k a * pauliZ k b =
    ZMod.stdAddChar (N := 2) (-(fieldTrace k (a * b))) •
      (pauliZ k b * pauliX k a)
```

The contract must additionally name and sign the single- and multi-register
observable/projector Fourier equations required by `pauli.tex:67-109`. EPR and
qudit-to-qubit identities at `pauli.tex:113-210` belong in F10 if F05 is meant
to remain core algebra; otherwise F05 must name them now and take a genuine
`FieldData k` only where self-duality is used. QPBT-035 must choose and record
that node boundary. It may not satisfy the prose through unnamed private facts.

### F06/F07 / Types

The exact recursive certificate cannot be guessed from the six current names.
QPBT-035 must freeze it using the paper's level-zero zero map and level-step
complementary register decomposition, rather than a generic
`isConditionallyLinear : Prop` supplied by callers. The public shape is:

```lean
structure ConditionallyLinearMap (k n level : Nat) where
  toFun : (Fin n -> GaloisField 2 k) -> (Fin n -> GaloisField 2 k)
  certificate : ConditionallyLinearCertificate k n level toFun

structure CLSampler (k n level : Nat) where
  alice : ConditionallyLinearMap k n level
  bob : ConditionallyLinearMap k n level

noncomputable def CLSampler.sample (S : CLSampler k n level) :
    PMF ((Fin n -> GaloisField 2 k) × (Fin n -> GaloisField 2 k))

structure TypeGraph (Type : Type*) [Fintype Type] [DecidableEq Type] where
  orderedEdges : Finset (Type × Type)
  symmetric : ∀ u v, (u, v) ∈ orderedEdges <-> (v, u) ∈ orderedEdges
  nonempty : orderedEdges.Nonempty

structure TypedSampler ... -- finite type-indexed left/right CLSampler families
structure TypedDecider ... -- total Bool predicate on dependent question/answer fibers
```

`TypeGraph.orderedEdges` includes `(u,u)` once and both orientations of a
non-loop edge. Its uniform PMF is therefore exactly the graph distribution.
`TypedSampler` questions must be dependent sums over type-indexed finite
fibers. `TypedDecider` must be total for every type pair and must not erase
heterogeneous answer fibers into raw `BitVec`. The paper's executable
Turing-machine/complexity interface remains K03-K04 as the existing blueprint
boundary says. Direct sum, downsizing, graph-PMF, and detyping facts required by
the node statement need explicit names in the frozen manifest or an explicit
later-node assignment.

### G01 / Parameters

```lean
structure Parameters where
  q : Nat
  m : Nat
  d : Nat

def Parameters.Admissible (params : Parameters) : Prop :=
  Exists fun k : Nat =>
    Odd k /\ params.q = 2 ^ k /\ Dvd.dvd params.m params.q
```

This signature is already exact. Do not add `0 < k`, `0 < m`, a field witness,
or an LDT parameter coercion.

## Proposed child issues and local PR boundaries

The IDs below start after already allocated QPBT-034. Local PR numbers are
shown as the present next-free sequence (`LPR-022` onward) but are proposals,
not reservations; root must allocate them atomically from canonical state.

### QPBT-035 — Freeze QPBT-014 callable contracts (`LPR-022`, proposed)

- Parent: QPBT-014. Dependencies: QPBT-013 and QPBT-033.
- Sole ownership: `blueprint/metadata/nodes.json`,
  `blueprint/generated/graph.json`, `blueprint/generated/graph.dot`,
  `blueprint/src/generated/chapter-02-entries.tex`,
  `blueprint/src/generated/chapter-03-entries.tex`, and
  `workflow/reviews/qpbt-035-q014-contract-a01.md`. No Lean path.
- Sources: F02/F05/F06/F07/G01 anchors and G09 listed above.
- Acceptance: resolve findings 1-3, 5, and 7; publish elaborated signatures and
  exact imports; add all statement-required names or assign them explicitly to
  later nodes; correct Boolean indicator language; retain G09; run blueprint
  generation/source/declaration checks and unit tests; obtain fresh independent
  mathematical/API review on an immutable manifest.
- Review scope: source fidelity and quantifier/domain match first; orphan
  declarations, codec ownership, F03 availability, and acyclic imports second.

### QPBT-036 — Implement F02 Polynomial (`LPR-023`, proposed)

- Parent: QPBT-014. Dependencies: QPBT-013 and QPBT-035.
- Sole paths: `MIPStarRE/QPBT/Basic/Polynomial.lean` and
  `workflow/reviews/qpbt-036-polynomial-a01.md`.
- Signatures: exact frozen F02 block from QPBT-035.
- Acceptance: Boolean/field domains remain distinct; interpolation, linearity,
  and injectivity are proved; no `sorry`, `axiom`, `constant`, or imported LDT
  parameter model; scoped check passes.
- Commands: `lake env lean MIPStarRE/QPBT/Basic/Polynomial.lean`;
  `lake build MIPStarRE.QPBT.Basic.Polynomial`; owned-scope debt/import scan;
  blueprint declaration synchronization; private full `lake build` before its
  immutable review.
- Reviewer: low-degree-code fidelity, degree subtype closure, interpolation and
  injectivity, direct Mathlib reuse.

### QPBT-037 — Implement F05 Pauli algebra (`LPR-024`, proposed)

- Parent: QPBT-014. Dependencies: QPBT-013 and QPBT-035; additionally the F03
  completion issue if QPBT-035 chooses `BinaryObservable` in a signature.
- Sole paths: `MIPStarRE/QPBT/Basic/Pauli.lean` and
  `workflow/reviews/qpbt-037-pauli-a01.md`.
- Signatures: exact frozen F05/G09 block from QPBT-035.
- Acceptance: matrix entries, projector positivity/normalization, Fourier
  equations, and twisted phase are proved; no false cross-basis commutation;
  self-dual basis appears only at source sites that use it; no proof debt.
- Commands: `lake env lean MIPStarRE/QPBT/Basic/Pauli.lean`;
  `lake build MIPStarRE.QPBT.Basic.Pauli`; G09/debt/import scan; blueprint sync;
  private full `lake build` before review.
- Reviewer: exact matrix multiplication order and phase sign, projector laws,
  Fourier normalization, G09 disposition, and F03/F10 boundary.

### QPBT-038 — Implement F06 then F07 Types (`LPR-025`, proposed)

- Parent: QPBT-014. Dependencies: QPBT-013 and QPBT-035.
- Sole paths: `MIPStarRE/QPBT/Game/Types.lean` and
  `workflow/reviews/qpbt-038-types-a01.md`.
- Signatures: exact frozen F06 then F07 blocks from QPBT-035.
- Acceptance: recursive CL semantics precede typed wrappers; sampler PMFs are
  normalized; graph support preserves loops and orientation weights;
  heterogeneous finite fibers remain dependent; no raw-string efficiency
  claim and no proof debt.
- Commands: `lake env lean MIPStarRE/QPBT/Game/Types.lean`;
  `lake build MIPStarRE.QPBT.Game.Types`; loop/codec/debt/import scan;
  blueprint sync; private full `lake build` before review.
- Reviewer: F06 recursion before F07, loop weight `2m-k`, PMF normalization,
  dependent fibers, and mathematical-versus-computational boundary.

### QPBT-039 — Implement G01 Parameters (`LPR-026`, proposed)

- Parent: QPBT-014. Dependencies: QPBT-013 and QPBT-035.
- Sole paths: `MIPStarRE/QPBT/Game/Parameters.lean` and
  `workflow/reviews/qpbt-039-parameters-a01.md`.
- Signatures: exact G01 block above.
- Acceptance: project-owned structure; exact existential quantifier,
  conjunction order, power equality, and natural divisibility; no stronger
  hypotheses, alias, coercion, or proof debt.
- Commands: `lake env lean MIPStarRE/QPBT/Game/Parameters.lean`;
  `lake build MIPStarRE.QPBT.Game.Parameters`; owned-scope scan; blueprint sync;
  private full `lake build` before review.
- Reviewer: exact statement-integrity table and absence of LDT leakage.

### QPBT-040 — Validate the combined QPBT-014 snapshot (no PR)

- Parent: QPBT-014. Dependencies: QPBT-036, QPBT-037, QPBT-038, QPBT-039.
- Sole ownership: `workflow/reviews/qpbt-040-q014-combined-a01.md`; no Lean or
  blueprint path. This is the only combined-snapshot build owner.
- Acceptance: bind the four approved immutable heads, assemble them on the
  current main in a private integration worktree, verify no conflicts or import
  cycles, then run the four scoped checks, four target builds, declaration and
  source synchronization, complete debt/forbidden-assumption scan, and exactly
  one `lake build` for that combined snapshot. Record cache key/hit/wait/build
  duration. Root alone performs guarded integrations and canonical state edits.
- Reviewer: combined import graph, candidate-blob identity, full-build result,
  declaration synchronization, and absence of cross-PR semantic drift.

After QPBT-040 passes, close QPBT-014 only as a tracking issue with no owned
paths. Implementers/orchestrators cannot approve their own PRs.

## Parallel lanes, critical path, and forecast

With four aggregate collaboration slots, root consumes one and at most three
child sessions run concurrently. After QPBT-035 is reviewed, dispatch the
three longest independent writers QPBT-036/037/038 together; queue QPBT-039 and
start it as soon as the first slot frees. Reviews may fan out only after each
candidate has an immutable head and its private validation gates pass.

| Work | Engineering wall-time forecast |
| --- | --- |
| QPBT-035 contract freeze + review | 4-8 h |
| QPBT-036 Polynomial + review | 3-8 h |
| QPBT-037 Pauli + review | 8-20 h |
| QPBT-038 Types + review | 12-30 h |
| QPBT-039 Parameters + review | 0.5-2 h |
| QPBT-040 combined gate | 1-3 h |

The critical lane is contract -> Types (or Pauli after proof retries) ->
combined gate. With immediate three-wide dispatch, forecast 17-41 active wall
hours, approximately 1-4 calendar days including review/repair and slot
turnover. Without the contract gate, apparent parallelism is likely to be lost
to incompatible rewrites and cannot be counted as a speed-up.

## Session accounting and zero-action counters

- Durable coordinator lifecycle start:
  `2026-09-01T12:31:17.320073Z`.
- Report evidence cutoff: `2026-09-01T12:55:18.257976434Z`; lifecycle window
  through that cutoff: 1,440.938 seconds. This window includes time queued
  behind the observed collaboration cap.
- Actual agent activation timestamp and activation-to-completion elapsed:
  unavailable. The collaboration spawn was delayed by backend rejection and
  the collaboration tool exposes no activation timestamp; no value is
  invented.
- Token usage: input `null`, output `null`, total `null`; availability reason:
  collaboration backend does not expose per-agent token usage.
- Topology: root coordinator -> one QPBT-033 orchestrator; nested agents 0.
- Read-only searches/file inspections: performed locally; compile attempts 0;
  cache hits 0; cache misses 0; cache waits 0; builds 0; Lean invocations 0.
- Lean edits 0; blueprint edits 0; protocol edits 0; source edits 0; Git/state
  edits 0; canonical issue/PR mutations 0; metric edits 0; generated-file edits
  0; `sorry`/axiom/constants introduced 0.
- Network 0; endpoint calls 0; GitHub operations 0; credential access 0;
  external reviews 0; nested-agent dispatches 0.

This report is the sole owned edit.
