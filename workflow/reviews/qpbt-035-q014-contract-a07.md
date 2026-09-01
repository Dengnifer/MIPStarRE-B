# QPBT-035 source-contract repair (A07)

Session: `i035-orchestrator-a07-source-contract-repair`

## Revised F07 callable contract

<!-- BEGIN F07-A07-SIGNATURES -->
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

noncomputable def TypedSampler.downsize
    {TypeId : Type uType} [Fintype TypeId] [DecidableEq TypeId]
    {k n level : Nat} (D : FieldData k)
    (S : TypedSampler TypeId k n level) :
    TypedSampler TypeId 1 (n * k) level where
  graph := S.graph
  alice t := (S.alice t).downsize D
  bob t := (S.bob t).downsize D

theorem TypedSampler.sample_downsize
    {TypeId : Type uType} [Fintype TypeId] [DecidableEq TypeId]
    {k n level : Nat} (D : FieldData k)
    (S : TypedSampler TypeId k n level) :
    (S.downsize D).sample =
      PMF.map (fun questions =>
        (⟨questions.1.1, downsizeVector D n questions.1.2⟩,
          ⟨questions.2.1, downsizeVector D n questions.2.2⟩)) S.sample

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
<!-- END F07-A07-SIGNATURES -->

The two new callables retain the graph and level, downsize both players'
typed CL maps pointwise, and state the exact PMF pushforward on the dependent
question pairs.  They claim neither the paper's indexed Turing-machine
representation nor its runtime equation; those executable clauses remain
visible in the later detyping contract.

## Candidate verdict

The source-contract repair now has three explicit layers without changing the
A06-approved F06 API or reopening the accepted F04 ownership:

1. `F04A-GAME-SEMANTICS` owns the generic finite game, strategy, value,
   projective/symmetric/support-commuting/consistent/PCC/SPCC, Schmidt-rank,
   and entanglement-requirement vocabulary from
   `strategies-distance.tex:4-51,62-81,126-190`.
2. `F07-TYPED` owns exactly `types.tex:57-195`, including the finite
   mathematical projection of typed downsizing and its exact PMF pushforward.
3. `F07A-DETYPING` owns typed normal-form verifiers/games and every graph
   simulation and detyping obligation in `types.tex:197-579`.

Both new nodes remain `faithful-boundary`: neither publishes an implementation
contract before its future issue elaborates the generic game and executable
machine/cost layers.  No public assumption, placeholder declaration, generic
obligation input, or K03/K04 detyping ownership was added.

## Generic game-semantics ownership

The exact callable surface is:

```text
MIPStarRE.QPBT.FiniteGame
MIPStarRE.QPBT.FiniteGameStrategy
MIPStarRE.QPBT.strategyValue
MIPStarRE.QPBT.StrategyWinsWithProbability
MIPStarRE.QPBT.FiniteDimensionalGameStrategy
MIPStarRE.QPBT.FiniteDimensionalGameStrategy.value
MIPStarRE.QPBT.gameValue
MIPStarRE.QPBT.ProjectiveStrategy
MIPStarRE.QPBT.SymmetricGame
MIPStarRE.QPBT.SymmetricStrategy
MIPStarRE.QPBT.SupportCommutingStrategy
MIPStarRE.QPBT.ConsistentStrategy
MIPStarRE.QPBT.PCCStrategy
MIPStarRE.QPBT.SPCCStrategy
MIPStarRE.QPBT.schmidtRank
MIPStarRE.QPBT.FiniteDimensionalGameStrategy.schmidtRank
MIPStarRE.QPBT.entanglementRequirement
MIPStarRE.QPBT.HasValueOnePCCStrategy
```

Its sole prerequisite is `F04-CONSISTENCY`.  `FiniteGameStrategy` is planned
as a one-field wrapper around the already-reviewed `PureStrategy`; it reuses
that structure's normalized state and two POVM families.  The finite-dimensional
wrapper introduces explicit local coordinate types only where a supremum,
Schmidt rank, or entanglement minimum ranges over dimensions.  The accepted
F04-DISTANCE ownership and Basic-to-Game layering remain unchanged.

Supplemental scout `i035-scout-a08-game-semantics` elaborated this no-move
shape in a bounded probe in `4.92s`.  Its earlier relocation experiment was
withdrawn because moving `PureStrategy` would reopen the reviewed F04 contract;
none of that experiment is present in this candidate.

## Complete detyping ownership

`F07A-DETYPING` has exact prerequisites
`[F04A-GAME-SEMANTICS, F07-TYPED]`.  F07 supplies F06 transitively, and F04A
supplies the reviewed finite measurement/strategy layer transitively.  K03 and
K04 remain unchanged and are checker-frozen to their own pinned source ranges
and callable names.

| Source range | Callable ownership |
| --- | --- |
| `types.tex:197-220` | `TypedNormalFormVerifier`, `.game` |
| `:234-305` | `TypeGraph.neighborIndicator`, `.vertexEncoding`, `.graphSampler` |
| `:312-357` | `.graphEvent`, `.graphEvent_probability`, `.graphEvent_conditioned_types` |
| `:371-393` | `detypeCL` |
| `:395-442` | `TypedSampler.detype`, `TypedDecider.detype`, `TypedNormalFormVerifier.detype` |
| `:444-579` | separate completeness, soundness, entanglement, level, dimension, sampler-time, decider-time, and description-time theorem names |

The graph remains nonempty.  The graph-event API retains both the exact event
probability `|orderedEdges| / 16^|Type|` and the conditioned type-distribution
equality.  The public paper obligations retain value-one PCC completeness,
the exact `16^|Type|` soundness and entanglement loss, level `ell+2`, dimension
`4|Type|+s(n)`, both runtime bounds, and description computability.

## Scout and finding dispositions

| Finding | Disposition | Evidence |
| --- | --- | --- |
| A05-1 missing mathematical detyping owner | resolved | F07A now spans `197-579`, names typed verifier/game, graph simulation, all four detyping constructions, and every theorem clause. |
| A05-2 false K03/K04 discharge | resolved | F07/F07A make no ownership assignment to those nodes; checker constants freeze K03 to `73-84` and K04 to `85-127` with their original sole callables. |
| A05-3 missing typed downsizing | resolved | the hashed F07 block adds exact elaborated `TypedSampler.downsize` and `sample_downsize`. |
| A05-4 missing reusable game semantics | resolved | F04A freezes the exact source anchors, dependency, and 18 callable names without adding an unelaborated implementation contract. |
| A05-5 nonempty graph boundary | preserved | `TypeGraph.nonempty` remains unchanged and is named in F07A's boundary. |
| A06 direct-sum API | accepted unchanged | the F06 signature-marker SHA-256 remains `120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461`. |
| F-LPR023-001 | resolved | exact later semantics/detyping nodes and proposed tracked issues are recorded below. |
| F-LPR023-002 | resolved | A06 independently accepted `CLSampler.sample_directSum` byte-for-byte. |
| F-LPR023-003 | preserved resolved | F07 still claims finiteness only for the type/edge support and constant sampler carrier; G02 owns pointwise consumer finiteness. |

## Statement integrity

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F06 | Finite coordinate spaces, recursive complementary factors, independent direct-sum seeds, basis only for downsize | Existing concrete field vectors/certificates, bind/map product, `Fin.append`, `FieldData` only at downsize | Direct-sum product distribution and downsizing pushforward | A06-accepted binary product PMF and downsizing equality, unchanged | faithful boundary |
| F04A | Finite questions/answers, PMF and predicate, finite-dimensional normalized strategies/POVMs; equal local spaces where required | Reviewed `PureStrategy`, measurement/projectivity/consistency interfaces, explicit finite coordinate types | Strategy/game value, projective/symmetric/support-commuting/consistent/PCC/SPCC, Schmidt rank, Ent | Exact callable ownership of the same semantic layer; implementation signatures deferred until elaborated | faithful boundary |
| F07 | Finite type graph, executable typed CL sampler/decider, selected basis for downsize | Nonempty ordered support, finite field-vector sampler projection, `FieldData`, arbitrary dependent decider fibers | Typed graph/sample semantics, pointwise downsize plus dimension/runtime, typed decider | Graph/sample semantics and exact downsize PMF; executable representation/runtime remains visible later debt | faithful boundary |
| F07A | Nonempty finite type graph, typed verifier/game, PCC/value/Ent semantics, executable machine model | F07 plus F04A, graph-event layer, future explicit machine/cost representation | Graph simulation; detyping; completeness; `16^|Type|` value/Ent loss; level/dimension/runtime/description clauses | Every clause has a distinct callable owner; no implication input replaces proof content | faithful boundary |

## Proposed root-created issues

`QPBT-041 - feat(QPBT/Basic): complete finite strategy and consistency semantics`

- Parent: `QPBT-000`.
- Dependency: `QPBT-032`.
- Sole path: `MIPStarRE/QPBT/Basic/Approximation.lean`.
- Source: the already-reviewed F04-DISTANCE, F04-ASYMPTOTIC,
  F04-CONSISTENCY, and F04-DISTANCE-LAWS anchors and signature manifests.
- Acceptance: extend the current F03-only file with every remaining reviewed
  F04 declaration and proof, without changing F03 or reopening `PureStrategy`
  ownership; no `sorry`/`axiom`/`constant`/public obligation input; scoped
  check, target and one private full build, declaration/source sync, debt scan,
  and fresh immutable review.

`QPBT-042 - feat(QPBT/Game): implement finite-game semantics`

- Parent: `QPBT-000`.
- Dependency: `QPBT-041`.
- Sole path: `MIPStarRE/QPBT/Game/Semantics.lean`.
- Source: `strategies-distance.tex:4-51,62-81,126-190`.
- Acceptance: elaborate and implement all 18 F04A names through the weakest
  project-native finite quantum APIs while wrapping the QPBT-041
  `PureStrategy`; preserve support-relative commutation, PCC/SPCC, Schmidt
  rank, and `WithTop Nat` entanglement semantics; no
  `sorry`/`axiom`/`constant`/public obligation input; scoped check, target and
  one private full build, declaration/source sync, debt scan, and fresh
  immutable source-fidelity review.

`QPBT-043 - feat(QPBT/Game): formalize graph simulation and verifier detyping`

- Parent: `QPBT-000`.
- Dependencies: `QPBT-038` and `QPBT-042`.
- Sole path: `MIPStarRE/QPBT/Game/Detyping.lean`.
- Source: `types.tex:197-579`, with dependency anchors
  `conditionally-linear.tex:135-178,282-314,565-626` and
  `strategies-distance.tex:4-51,62-81,126-190`.
- Acceptance: freeze and elaborate all F07A callables; retain the exact graph
  event probability and conditioned PMF, value-one PCC completeness,
  `16^|Type|` value/Ent loss, level `ell+2`, dimension `4|Type|+s(n)`, and all
  executable cost/description clauses in one explicit model; no
  `sorry`/`axiom`/`constant`/public obligation input; scoped check, target and
  one private full build, declaration/source sync, debt scan, and fresh
  immutable source-fidelity review.

Root must allocate all three records atomically in canonical state.  Making
the F04 implementation dependency explicit prevents QPBT-042 from becoming
spuriously ready, while flat parenting preserves QPBT-014's accepted
QPBT-035-through-QPBT-040 closure.  This session did not edit issues, PRs,
sessions, stages, research, or metrics.

## Authentication

- Immutable base commit/tree:
  `3f2630a7631a0164b6ef4aca1fd081ba264beeb2` /
  `4effdd7686905e59c188b70c71b04a6cb46e8b21`.
- A05 report SHA-256:
  `de9c4c87820f76c8162f7d2f06bbcd0a66a6ed14cc8d57ed2c6d1414bccd81fb`.
- A06 report SHA-256:
  `2bd9b52a679ba2bc155a28ea6b6f352375f0d5a1ee2f3db065739eba45ab24e6`.
- Supplemental A08 report SHA-256:
  `f37ab823449c85b078330f3912b4ec8eedfc67b8c9ffedb1d1b261434ccc4b27`.
- Supplemental A08 F04A signature-marker SHA-256:
  `2bc405a88ddbfc0d82b10c431a7de2c9d2ce0ca415e1ce25fed2fabdda7da870`.
- F07 A07 signature-marker SHA-256:
  `99cfe240da252a94527d50c53d39a9673ee8d673cf6eba9730fb1a7e92df9d46`.
- Pinned `types.tex` SHA-256:
  `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c`.
- Pinned `strategies-distance.tex` SHA-256:
  `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f`.
- Pinned `conditionally-linear.tex` SHA-256:
  `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638`.
- Final commit/tree, exact eight-path manifest, and this report's final
  filesystem SHA-256 are supplied out of band after their bytes are fixed.

## Validation

| Command | Result | Final wall time |
| --- | --- | ---: |
| bounded `lake env lean /dev/stdin` F07 downsize probe, first attempt | failed closed on dependent-pair association; no file/build output | `2.47s` |
| bounded `lake env lean /dev/stdin` F07 downsize probe, corrected exact signatures | pass; four probe-local `sorry` bodies only | `2.31s` |
| A08 no-move/full game-semantics probes | pass `3/3`; read-only sibling evidence | `20.42s`, `4.92s`, `4.90s` |
| `python3 blueprint/check.py --write` | pass; byte-idempotent, `53` nodes / `12` chapters | `0.09s` |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | pass, `29/29` | `0.89s` |
| `python3 blueprint/check.py --check` | pass | `0.08s` |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass | `0.09s` |
| `python3 scripts/workflow.py validate` | pass; `41` issues, `21` PRs, `376` issued sessions, `7` stages in immutable branch state | `0.13s` |
| `python3 scripts/check_workflow.py --skip-tests` | pass | `0.12s` |
| `git diff --check` | pass | `<0.01s` |

The first two default blueprint checks failed only because generation had not
yet run.  The first pinned-source check then caught that
`sec:typed-samplers` lay two lines before the mandated F07 range; the source
label was narrowed to the in-range `def:typed-sampler` without changing
`57-195`.  Every subsequent default, source-root, and idempotence gate passed.
No target/full build or cache warm/seed/materialization action was authorized
or performed.

## Session accounting

- Durable start: `2026-09-01T14:54:38.218033Z`.
- Evidence cutoff: `2026-09-01T15:19:29.789875784Z`.
- Elapsed to cutoff: `1491.571842784` seconds.
- Token usage: input `null`, output `null`, total `null`; availability reason:
  collaboration backend does not expose per-agent token usage.
- Topology: root coordinator -> one A07 orchestrator; nested agents `0`.
  A08 was a root-owned parallel scout and is cited as independent evidence,
  not counted as an A07 child.
- Actions: `2` bounded A07 Lean probes (`1` failed, `1` passed), `0` target
  builds, `0` full builds, `0` cache actions, `5` blueprint unit-test runs,
  `5` deterministic generation runs, `6` default checks, `5` pinned-source
  checks, `3` workflow validations, `3` workflow-checker runs, and `6` diff
  hygiene checks.
- Candidate effects: `7` changed owned paths plus `1` owned unchanged chapter
  output; `0` edits outside ownership; `0` canonical state/PR/issue/session/
  stage/research/metrics edits; `0` network/endpoint/GitHub/credential actions;
  `0` nested-agent launches.
- Proof debt: `0` repository `sorry`/`axiom`/`constant` additions.  Across the
  two temporary A07 probes, `7` probe-local `sorry` declarations were reported.
- Git writes at cutoff: `0`; the required single owned-path commit is made only
  after this report's bytes are fixed and is supplied out of band.

## Reviewer checklist

- Authenticate base/head/tree and the exact eight-path manifest before review.
- Recompute the A05, A06, A08, pinned-source, F06 marker, and F07 marker hashes.
- Confirm F06's `sample_directSum` signature is unchanged byte-for-byte.
- Confirm F07 owns exactly `57-195`, adds both downsizing callables, and makes
  no executable runtime claim.
- Confirm F04A owns exactly the three strategies-distance ranges, depends only
  on F04-CONSISTENCY, lists exactly 18 names, and does not relist PureStrategy.
- Confirm F07A owns exactly `197-579`, depends only on F04A and F07, keeps
  graph nonemptiness, and names every graph/detyping theorem clause.
- Confirm K03/K04 metadata and ownership remain unchanged.
- Confirm QPBT-041 -> QPBT-042 -> QPBT-043 is flat under QPBT-000, with the
  additional QPBT-038 -> QPBT-043 dependency.
- Re-run all validation commands and inspect statement integrity before any
  no-byte-change adoption or formal LPR-023 approval.
