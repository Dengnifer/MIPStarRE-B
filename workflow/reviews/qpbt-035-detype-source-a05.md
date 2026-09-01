# QPBT-035 detyping source audit (A05)

Session: `i035-scout-a05-detype-source`

## Findings

1. **Blocker: the candidate has no owner for the mathematical detyping
   development.**  At detached head
   `fdbb37a10e416c8a9891cdcdbcd44470573886b0`, F07 says that executable
   detyping is deferred to K03-K04
   (`blueprint/metadata/nodes.json:385`; contract
   `workflow/reviews/qpbt-035-q014-contract-a02.md:394`).  The pinned source
   does not merely state an encoding-cost fact.  It defines a graph sampler,
   detyped CL functions, a detyped sampler, a detyped decider, and a detyped
   verifier, and proves graph-event probability, conditioned graph
   distribution, completeness, soundness, an entanglement lower bound, level
   and dimension relations, running-time bounds, and description
   computability (`types.tex:225-579`, original `3791-4145`).  None of those
   names or conclusions occurs in F07, K03, or K04.

2. **Blocker: K03 and K04 cannot truthfully discharge this debt.**  K03 is
   sourced only to `qpbt-parameters.tex:73-84` and owns computation of the
   canonical tuple `(q,m,d)`.  K04 is sourced only to
   `qpbt-parameters.tex:85-127`; its statement and encoding deliberately own
   exactly three QPBT-specific complexity claims and explicitly forbid extra
   sampler claims (`blueprint/metadata/nodes.json:1075-1090,1129-1145`).
   Detyping is generic in a finite type graph and typed normal-form verifier,
   has mathematical value/entropy conclusions, and is used later by answer
   reduction, introspection, and parallel repetition.  Rewording F07's
   boundary cannot create those missing definitions or theorems.

3. **High: F07 also omits a pre-detype source obligation.**  Typed sampler
   downsizing and its correctness/parameter theorem are defined and stated at
   `types.tex:153-183` (original `3719-3749`).  The current F07 callable list
   has no `TypedSampler.downsize` or typed-downsize theorem.  This belongs in
   F07 because it is the typed analogue of the already-owned F06 downsizing
   surface and precedes normal verifiers and graph simulation.

4. **High: the full detyping theorem cannot be frozen against the candidate's
   present F07 types alone.**  The source theorem quantifies over indexed
   Turing samplers and deciders, typed and untyped normal-form verifiers and
   their games, PCC strategies, game value, Schmidt rank/entanglement
   requirement, and a machine cost model.  The candidate F07 instead exposes
   a single finite `TypedSampler`, a generic but unconnected `TypedDecider`,
   and no verifier/game/value/entropy or executable sampler interface.  A
   future contract must link the sampler question fibers to the decider and
   must freeze the generic finite-game/strategy boundary before an elaborated
   proof signature is claimed.  It must not replace any of these facts with a
   public obligation or arbitrary implication input.

5. **Medium: the paper silently needs a nonempty graph.**  The graph
   distribution divides by `2m-k`, and the proof weakens using `2m-k >= 1`.
   The candidate's `TypeGraph.nonempty` is therefore faithful Lean boundary
   data, not drift.  The graph-simulation and soundness statements must retain
   it.

## Recommendation

Use one exact later mathematical node rather than expanding the already
bounded F06/F07 `Types.lean` writer into game semantics, quantum strategies,
entropy, executable machines, and complexity.  The smallest truthful repair
is:

- keep `F07-TYPED`, narrow its source ownership to generated lines `57-195`
  (original `3623-3761`), and add the typed-downsize operation and theorem;
- add `F07A-DETYPING` for generated lines `197-579` (original `3763-4145`),
  including typed normal verifier/game data, graph rejection sampling, all
  detyping constructions, the complete theorem, and its executable clauses;
- create root-owned tracking issue `QPBT-041` so this is durable proof debt;
- remove every claim that K03-K04 owns parsing or detyping.  K03/K04 may supply
  a shared cost-model API to `F07A-DETYPING`, but they are not the owner or
  discharge target.

This split leaves QPBT-038's existing F06/F07 finite-interface implementation
bounded.  `QPBT-041` is a later issue and need not become a consumer edge of
G02 or a prerequisite of QPBT-040 merely to make the current ownership claim
truthful.  The actual paper consumers are the later answer-reduction,
introspection, and parallel-repetition developments.

## Direct assessment of A04's proposed repair

The comparison target was authenticated before reading: immutable HEAD
`3f2630a7631a0164b6ef4aca1fd081ba264beeb2`, with A04 node
`F07A-DETYPING` at `blueprint/metadata/nodes.json:390-405` and report SHA-256
`a55e7789d6a899b31e6fc8625dfb6116c9430884fb2ce83fc6e1182bb2d3225e`.

**Verdict: the proposal is directionally correct but is not yet a complete
source-faithful ownership repair.**

- **Source range `[225,579]`: conditionally faithful for graph simulation and
  detyping proper, but incomplete for the node as stated.**  It exactly spans
  `sec:graph-dist` and `sec:detype`, from the graph-distribution discussion
  through the complete proof.  However, `TypedVerifier.detype` and
  `detypingVerifier` depend on the source definitions of typed normal-form
  verifier and indexed game at `197-220`.  No A04 callable node owns those
  definitions.  Either change F07A to `[197,579]`, or extend F07 through line
  220 and add callable owners for `TypedVerifier` and its indexed game.  A04
  also leaves typed sampler downsizing `153-183` unnamed; add it to F07.
- **Prerequisites `[F03-MEASUREMENT,F07-TYPED]`: not sufficient as currently
  contracted.**  F03 owns finite POVM/postprocessing data, and F07 owns finite
  typed sampler/decider data.  Neither owns a finite game, strategy value,
  support-relative commuting/PCC predicate, Schmidt rank, or `Ent`.  The
  theorem needs F04's strategy and consistency layers plus an exact callable
  owner for game/value/PCC/Ent.  F07 transitively supplies F06 CL, so a separate
  direct F06 prerequisite is optional; the missing quantum-game semantics are
  not optional.
- **The ten names: sufficient as a compact grouping for lines `234-579`, but
  not sufficient for the complete source contract.**  The first five names
  can own neighbor encoding, vertex encoding, graph CL maps, the rejection
  event, and both conclusions of `prop:simulating-graph` only if
  `simulatesDistribution`'s future signature explicitly includes both the
  exact event probability and conditioned PMF equality.  The last five can
  own the four detyping definitions and one aggregate theorem only if
  `detypingVerifier` exposes all five enumerated paper clauses.  Missing names
  are the prerequisite constructors `TypedVerifier` and `TypedVerifier.game`,
  plus F07 typed downsizing.  `fidelity: "exact"` is also too strong while
  executable representation/cost data and these semantic prerequisites remain
  unfrozen; use `faithful-boundary` until the follow-up contract elaborates
  them.
- **Follow-up dependency on QPBT-015: not sufficient or source-faithful by
  itself.**  QPBT-015 owns only `Game/MagicSquare.lean` and
  `Game/Verifier.lean` for the concrete minimal QPBT game, with callable nodes
  F08/G02.  Its acceptance gates do not promise a generic finite-game value,
  PCC, Schmidt-rank, or entanglement-requirement API.  QPBT-015 may be an
  additional ordering dependency if its contract is explicitly expanded to
  expose that reusable source-anchored API.  Otherwise `QPBT-041` needs a
  separate prerequisite issue for that API, or must own and source it
  explicitly; merely depending on QPBT-015 does not discharge the obligation.

## Complete source-obligation inventory

All generated-line ranges below refer to the complete pinned
`references/2001.04383v3/sections/dependencies/types.tex`; original-paper
ranges add 3566.  The file has 582 lines and SHA-256
`732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c`.

### Typed layer retained by F07

| Source range | Obligation | Exact content/dependencies |
| --- | --- | --- |
| `57-63` / original `3623-3629` | Typed CL family | For finite `Type`, a family `Type -> ConditionallyLinearMap` at common ambient space and level; depends on F06 CL maps. |
| `65-82` / `3631-3648` | Graph distribution `mu_G` | Undirected multiset edges with loops; if there are `m` edges and `k` loops, each ordered adjacent pair has mass `1/(2m-k)`.  Requires nonempty edge support. |
| `84-93` / `3650-3659` | Typed CL distribution | Draw `(leftType,rightType)` from `mu_G`, then a shared-seed CL pair from the selected maps; output typed questions. |
| `95-131` / `3661-3697` | Executable typed sampler specification | Seven-input indexed Turing machine; admissible `q(n)`, dimension `s(n)`, marginal/linear/factor operations for every player, type, level, and vector; complexity `TIME_S(n)`.  The finite F07 PMF is only the mathematical projection of this source object. |
| `133-141` / `3699-3707` | Type encoding and invalid input | Types use strings of length at most `ceil(log |Type|)`; invalid type input returns zero; graph is part of the sampler because its distribution uses it. |
| `143-151` / `3709-3717` | Typed sampler distribution | `mu^G_(S,n)` is the selected typed CL distribution. |
| `153-160` / `3719-3726` | Typed sampler downsize | Add type as an input while applying ordinary sampler downsizing. |
| `162-183` / `3728-3749` | Typed-downsize theorem | Same type graph and level; field size becomes 2; dimension becomes `s(n) * log q(n)`; time is `O(TIME_S(n) * log q(n))`; CL functions are pointwise downsized.  Depends on F06 `ConditionallyLinearMap.downsize`, sampler downsize, and its correctness theorem. |
| `185-195` / `3751-3761` | Typed decider | Total seven-input indexed Turing machine on raw strings, returns one bit, with `TIME_D(n)`.  The candidate finite dependent `TypedDecider` is a boundary representation, not this executable object. |

Minimum F07 additions at the existing mathematical boundary are callable
`MIPStarRE.QPBT.TypedSampler.downsize` and
`MIPStarRE.QPBT.TypedSampler.sample_downsize`.  If executable typed samplers
remain deferred, F07's integrity verdict must say `faithful boundary`, name
the later executable owner `F07A-DETYPING`, and stop claiming K03-K04 owns it.

### Typed verifier and graph simulator assigned to F07A

| Source range | Obligation | Exact content/dependencies |
| --- | --- | --- |
| `197-203` / original `3763-3769` | Typed normal-form verifier | Pair of a `(Type,G)` typed sampler over field size 2 and a typed decider. |
| `205-220` / `3771-3786` | Indexed typed normal-form game | Question sets `Type x {0,1}^{TIME_S(n)}`, answer sets `{0,1}^{TIME_D(n)}`, question PMF `mu^G_(S,n)`, predicate computed by the typed decider, and quantum value `val*`. |
| `234-248` / `3800-3814` | Neighbor indicator and vertex encoding | `neigh_G(u) : F_2^Type`; `enc_G(u)=(e_u,neigh_G(u))`. |
| `250-305` / `3816-3871` | Two-level graph CL sampler | Ambient `V_G = V_vertexA + V_edgeA + V_vertexB + V_edgeB`, dimension `4|Type|`; each player first returns its own vertex/neighbor encoding and then retains the other player's selected edge bit, or zero when the prefix is not an encoding. |
| `312-339` / `3878-3905` | Graph-simulation proposition | Defines event `E_G`; proves `Pr(E_G)=(2m-k)/16^|Type|`; conditioned on `E_G`, recovered ordered endpoints have exactly `mu_G`; at least one player detects failure. |
| `341-357` / `3907-3923` | Graph-simulation proof | Uniform encodings occur with probability `|Type|^2/16^|Type|`; adjacency contributes `(2m-k)/|Type|^2`; their product gives the exact event probability and conditional law. |

### Detyping constructions assigned to F07A

| Source range | Obligation | Exact content/dependencies |
| --- | --- | --- |
| `359-369` / original `3925-3935` | Shared detyping context | Finite `Type`, graph `G`, graph maps on `V_G`, with `dim V_G=4|Type|`. |
| `371-393` / `3937-3959` | Detyped CL functions | For typed `ell`-level families on `V`, form `(ell+2)`-level maps on `V_G + V`.  After the graph prefix, select the unique type's CL map when the other-side edge register is nonzero and select zero otherwise; concatenate using F06 `lem:cl-concat`. |
| `395-407` / `3961-3973` | Detyped sampler | At every index `n`, apply the CL detyping construction to both typed families; result is an ordinary sampler with dimension `4|Type|+s(n)`. |
| `409-433` / `3975-3999` | Detyped decider | Parse ordinary questions as `V_G x string`; malformed encodings accept.  If the graph prefixes are the displayed Alice/Bob views for an edge, call the typed decider on recovered types and contents; otherwise accept. |
| `435-442` / `4001-4008` | Detyped verifier | Pair the detyped sampler with the graph-indexed detyped decider to obtain an ordinary normal-form verifier. |

### Main theorem and every stated relation

The one source lemma is `lem:detyping-verifiers`, statement
`types.tex:444-475` (original `4010-4041`), proof `477-579` (original
`4043-4145`).  Its obligations are conjunctive and must all stay visible:

| Clause | Exact obligation | Proof dependency/range |
| --- | --- | --- |
| Completeness | For every `n`, a value-1 PCC strategy for the typed game induces a value-1 PCC strategy for the detyped game, using the same state and typed measurements on valid views and the trivial identity measurement otherwise. | `452-453`, proof `498-538`; depends on projectivity, consistency, and support-relative commutation. |
| Soundness | If `val*(detype(V)_n) >= 1-eps`, then `val*(V_n) >= 1-16^|Type| eps`. | `454-455`, proof `540-567`; depends on the graph-event theorem. |
| Entanglement | `Ent(detype(V)_n,1-eps) >= Ent(V_n,1-16^|Type| eps)`.  The strategy restriction keeps the same state and Schmidt rank. | `456-460`, proof `568-570`; depends on the exact game/strategy/Ent definition. |
| Level | An `ell`-level typed sampler detypes to level `ell+2`. | `461-462`, proof `572-575`; depends on F06 CL concatenation. |
| Dimension | The detyped ambient dimension is exactly `4|Type|+s(n)`. | Definition `403`, proof `479-481,575`. |
| Sampler time | `TIME_detype(S)(n) = poly(|Type|, TIME_S(n))`. | `463-467`, proof `576-578`; requires an executable sampler and fixed cost model. |
| Decider time | `TIME_detype_G(D)(n) = poly(|Type|, TIME_D(n))`. | `468-469`, proof `576-578`; requires parsing/encoding costs. |
| Description construction | Descriptions of both transformed machines are computable in polynomial time from `G` and the respective source-machine description. | `470-473`, proof `576-578`. |

The proof gives the sharper strategy-level identity

```text
value(detype(V), strategy)
  = 1 - (2m-k)/16^|Type|
    + ((2m-k)/16^|Type|) * value(V, restrictedStrategy)
```

at `560-562`, then uses nonemptiness (`2m-k >= 1`) to obtain the published
`16^|Type|` loss at `563-566`.  A formal theorem may expose the sharper
identity as a helper, but the public paper-labelled theorem must retain the
five source clauses and exact error dependence.

## External dependencies

- F06 CL distribution/certificate: `conditionally-linear.tex:135-178`.
- F06 concatenation theorem `lem:cl-concat`:
  `conditionally-linear.tex:282-314`.
- Ordinary executable sampler and distribution:
  `conditionally-linear.tex:565-626`; the typed-downsize theorem also depends
  on ordinary downsizing beginning at `630` and `lem:downsize_sampler`.
- Finite game, strategy, value, PCC, and entanglement requirement:
  `strategies-distance.tex:4-51,62-81,126-190`.  The present F04 metadata owns
  only a subset of this API, so `QPBT-041` must freeze the missing reusable
  game/value/PCC/Ent surface before claiming an elaborated detyping theorem.
- Current F07 mathematical data: `TypeGraph`, its uniform ordered-edge PMF,
  CL maps/samplers, and the linked typed decider boundary after F-LPR023-003 is
  resolved.
- Executable clauses require one explicit machine/encoding/cost model.  K03
  may be reused for that model only; no K03/K04 theorem entails a detyping
  result.

## Proposed node metadata

```json
{
  "id": "F07A-DETYPING",
  "chapter": "02",
  "title": "Graph simulation and detyping of typed normal-form verifiers",
  "kind": "lemma",
  "public": false,
  "status": "not-started",
  "fidelity": "faithful-boundary",
  "source": {
    "path": "references/2001.04383v3/sections/dependencies/types.tex",
    "label": "lem:detyping-verifiers",
    "generated_lines": [197, 579],
    "original_lines": [3763, 4145]
  },
  "statement": "Define typed normal-form verifiers and games, the graph rejection sampler, detyped CL functions/samplers/deciders/verifiers, and prove exact graph-event sampling, PCC completeness, value and entanglement soundness, level/dimension relations, runtime bounds, and description computability.",
  "lean": {
    "module": "MIPStarRE.QPBT.Game.Detyping",
    "names": [
      "MIPStarRE.QPBT.TypedNormalFormVerifier",
      "MIPStarRE.QPBT.TypedNormalFormVerifier.game",
      "MIPStarRE.QPBT.TypeGraph.neighborIndicator",
      "MIPStarRE.QPBT.TypeGraph.vertexEncoding",
      "MIPStarRE.QPBT.TypeGraph.graphSampler",
      "MIPStarRE.QPBT.TypeGraph.graphEvent",
      "MIPStarRE.QPBT.TypeGraph.graphEvent_probability",
      "MIPStarRE.QPBT.TypeGraph.graphEvent_conditioned_types",
      "MIPStarRE.QPBT.TypedSampler.detype",
      "MIPStarRE.QPBT.TypedDecider.detype",
      "MIPStarRE.QPBT.TypedNormalFormVerifier.detype",
      "MIPStarRE.QPBT.detyping_complete",
      "MIPStarRE.QPBT.detyping_sound",
      "MIPStarRE.QPBT.detyping_entanglement",
      "MIPStarRE.QPBT.detyping_level",
      "MIPStarRE.QPBT.detyping_dimension",
      "MIPStarRE.QPBT.detyping_sampler_time",
      "MIPStarRE.QPBT.detyping_decider_time",
      "MIPStarRE.QPBT.detyping_descriptions_time"
    ]
  },
  "prerequisites": [
    "F04-CONSISTENCY",
    "F04-DISTANCE",
    "F06-CL",
    "F07-TYPED"
  ],
  "consumers": [
    "future answer-reduction node",
    "future introspection node",
    "future parallel-repetition node"
  ]
}
```

Callable signatures are frozen only to the level justified by the source and
current API:

```lean
def TypeGraph.neighborIndicator (G : TypeGraph TypeId) (u : TypeId) :
    TypeId -> ZMod 2

def TypeGraph.vertexEncoding (G : TypeGraph TypeId) (u : TypeId) :
    (TypeId -> ZMod 2) x (TypeId -> ZMod 2)

def TypeGraph.graphSampler (G : TypeGraph TypeId) :
    CLSampler 1 (4 * Fintype.card TypeId) 2

theorem TypeGraph.graphEvent_probability (G : TypeGraph TypeId) :
    Probability (G.graphEvent) =
      G.orderedEdges.card / 16 ^ Fintype.card TypeId

theorem TypeGraph.graphEvent_conditioned_types (G : TypeGraph TypeId) :
    conditionalTypePMF G.graphSampler G.graphEvent = G.distribution

def TypedSampler.detype (S : IndexedTypedSampler TypeId G ell s) :
    IndexedCLSampler (ell + 2) (fun n => 4 * Fintype.card TypeId + s n)

def TypedDecider.detype (G : TypeGraph TypeId) (D : IndexedTypedDecider ...) :
    IndexedDecider

def TypedNormalFormVerifier.detype
    (V : TypedNormalFormVerifier TypeId G) : NormalFormVerifier

theorem detyping_complete (V : TypedNormalFormVerifier TypeId G) (n : Nat) :
    HasValueOnePCCStrategy (V.game n) ->
      HasValueOnePCCStrategy (V.detype.game n)

theorem detyping_sound (V : TypedNormalFormVerifier TypeId G)
    (n : Nat) (eps : Real) :
    gameValue (V.detype.game n) >= 1 - eps ->
      gameValue (V.game n) >= 1 - 16 ^ Fintype.card TypeId * eps

theorem detyping_entanglement (V : TypedNormalFormVerifier TypeId G)
    (n : Nat) (eps : Real) :
    Ent (V.detype.game n) (1 - eps) >=
      Ent (V.game n) (1 - 16 ^ Fintype.card TypeId * eps)
```

`IndexedTypedSampler`, `IndexedTypedDecider`, `IndexedCLSampler`,
`IndexedDecider`, `NormalFormVerifier`, `gameValue`, `Ent`, and
`HasValueOnePCCStrategy` above are semantic placeholders, not proposed Lean
declarations to invent.  `QPBT-041` must first bind them to the weakest
project-native executable/game API.  The displayed quantifier order,
domains, constants, dimensions, and implications are the part fixed by the
paper.  No public `Hypotheses`, `Assumptions`, witness package, or
`_ofObligations` theorem may replace them.

## Proposed root-created tracking issue

```text
QPBT-041 - feat(QPBT/Game): formalize graph simulation and verifier detyping

kind: formalization
execution_category: implementation
parent_id: QPBT-014
dependency_ids: [QPBT-038 and the issue that completes the reusable finite
  game/value/PCC/Ent API represented by F04-DISTANCE/F04-CONSISTENCY]
owned path: MIPStarRE/QPBT/Game/Detyping.lean
source: types.tex:197-579 (original 3763-4145), with dependency anchors
  conditionally-linear.tex:135-178,282-314,565-626 and
  strategies-distance.tex:4-51,62-81,126-190
acceptance: implement every F07A callable name and all five clauses of
  lem:detyping-verifiers; exact graph-event probability and conditional law;
  exact level ell+2 and dimension 4|Type|+s(n); explicit executable cost model;
  no sorry/axiom/constant/public obligation inputs; scoped Lean, target build,
  declaration/source sync, debt/assumption scan, one private full build, and
  fresh immutable source-fidelity review
```

Root should allocate `QPBT-041` atomically; this scout did not reserve or edit
canonical state.  If the finite game/value/PCC/Ent API does not already have a
numbered implementation issue, root must create that dependency rather than
pretend F04's current callable list supplies it.

## Metadata diff guidance for LPR-023 A04

1. In F07, remove “executable detyping ... deferred to K03-K04” from
   `boundary_hypotheses`, change `fidelity`/integrity to acknowledge the finite
   mathematical boundary, add `F07A-DETYPING` as the exact later owner, and add
   typed-downsize callable names/signatures.
2. Restrict F07's source range to generated `57-195`, original `3623-3761`.
   This retains typed CL families, graph distribution, typed sampler,
   downsize, and decider.
3. Add `F07A-DETYPING` exactly as above, generated after F07 in chapter 02.  Its
   implementation contract should be omitted until `QPBT-041` freezes and
   elaborates the missing generic game/executable API; do not publish an
   untested signature hash now.
4. Do not add F07A to G02's prerequisites or transitive definitions: G02
   consumes typed sampling/deciding, not detyping.  Add F07A only to future
   answer-reduction, introspection, and parallel-repetition nodes when those
   nodes enter the blueprint.
5. Leave K03 and K04 statements, names, and exact three-claim K04 scope
   unchanged.  At most add F07A as a future consumer of the common cost-model
   vocabulary once that vocabulary has a callable owner.
6. Add `QPBT-041` to canonical state in a root-only transaction, but do not
   make QPBT-038 own `Detyping.lean` and do not add a second writer to
   `Types.lean`.

## Authentication, timing, and counters

- Detached candidate HEAD:
  `fdbb37a10e416c8a9891cdcdbcd44470573886b0`; worktree was read-only.
- Canonical LPR-023 base/head:
  `50c4a9ce9fc9446b04c1c309951f05cc6a49766c` /
  `fdbb37a10e416c8a9891cdcdbcd44470573886b0`; status `changes_requested`;
  F-LPR023-001 is the binding detyping finding.
- A03 report SHA-256:
  `a1ed48ff7a642c8811f56d1aa77caec32e3cf1608a33dd474fffb16b367e4caf`.
- Pinned `types.tex` SHA-256:
  `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c`.
- Durable dispatch start: `2026-09-01T14:35:41.175698Z`.
- Evidence cutoff: `2026-09-01T14:46:07.814394588Z`.
- Elapsed to cutoff: `626.638696588` seconds.
- Token usage: `null`; collaboration backend does not expose per-agent token
  usage.
- Topology: one scout, zero nested agents.
- Actions: 0 repository edits; 0 Git writes; 0 state/metrics edits; 0 Lean or
  Lake invocations; 0 builds; 0 cache actions; 0 network, endpoint, GitHub, or
  credential operations; 0 agent launches; 1 authorized immutable A04
  comparison target inspected; 1 `/tmp` report written.
- Report SHA-256: supplied out of band after the final bytes are written.
