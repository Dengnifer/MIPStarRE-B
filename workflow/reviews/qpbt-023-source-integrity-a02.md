# QPBT-023 source-integrity audit (i023-scout-a02)

## Session and immutable boundary

- Logical session ID: `i023-scout-a02-source-integrity`.
- Collaboration task path: `/root/i023_orchestrator_a01_leaf_contract/i023_scout_a02_source_integrity`.
- External collaboration/thread ID: `null` (`not exposed by the collaboration backend`).
- Detached clone: `/tmp/qpbt-023-source-integrity-a02`.
- Required/observed HEAD: `942f9438b991ece8942815db16c019b92d9cdd8e`.
- Required/observed tree: `09123f4b25c892a146aabaa77d73cf0c5f35a0c6`.
- Initial and final clone status: clean.
- UTC start: `2026-09-01T08:06:53.270250038Z`.
- UTC end: `2026-09-01T08:20:20.659762233Z`.
- Monotonic start: `/proc/uptime = 1274174.67 s`.
- Monotonic end: `/proc/uptime = 1274981.91 s`.
- `elapsed_seconds`: `807.24`.
- `timing_quality`: `monotonic /proc/uptime measurement at 0.01 s resolution; UTC timestamps from date -u with nanosecond formatting`.
- `token_usage`: `{"value":null,"availability_reason":"Per-session token usage is not exposed by the collaboration backend; not estimated."}`
- Topology: one scout under one orchestrator; `subagents = 0`.

## Verdict

**BLOCKED for immutable callable-signature freeze in its current proposed form.**

The eleven proposed declarations preserve most leaf-level mathematics, but the
contract is not yet source-complete. F01 conflates a noncomputable existence
projection with the paper's uniform deterministic algorithm and multiplication-
table complexity. F03 cites only the bracket definition for declarations whose
actual sources are elsewhere and leaves postprocessing/body semantics outside
the callable freeze. F04 replaces the paper's indexed `O(delta)` relations with
an exact one-instance inequality, omits the cited state/strategy relations and
laws, and does not freeze the local-action/tensor adapters needed to call the
distance on a bipartite state. Local conjugation also retains an unresolved
pair-versus-side-specific API choice.

These are contract and provenance blockers, not permission to add assumptions.
The mathematical existence obligation for the self-dual normal basis must stay
visible and be discharged without an `axiom`, `constant`, generic hypothesis, or
public implication input.

## Findings (ordered by severity)

### 1. Blocker: F04's numeric predicate is not the cited paper relation

The node claims normalized strategies, consistency, state-dependent
operator/family distance, and triangle/data-processing laws
(`blueprint/metadata/nodes.json:88-101`; generated mirror
`blueprint/src/generated/chapter-02-entries.tex:38-47`). Its five planned names
contain no state-family relation, strategy relation, consistency relation,
triangle law, or data-processing law (`nodes.json:96-97`).

The paper has distinct layers:

- state *families* indexed by `n in N`, with
  `delta : N -> [0,1]` and squared norm `= O(delta(n))`
  (`dependencies/strategies-distance.tex:213-224`);
- finite POVM distance
  `E_{x~mu} sum_a ||(M^x_a-N^x_a) psi||^2 <= O(delta)` for finite `X`, a
  probability distribution `mu`, and a state (`:252-265`);
- strategy distance, requiring same-space states and both player families,
  evaluated under the game distribution and on either of the two states
  (`:267-282`);
- triangle and postprocessing/data-processing facts (`:377-395`); and
- Appendix A's raw-operator, no-answer-index form
  `E_x <psi|(A^x-B^x)^dagger(A^x-B^x)|psi> <= O(delta)`
  (`qpbt/appendix-preliminaries.tex:49-53`).

The proposal instead defines one finite predicate with `delta : NNReal` and an
exact inequality (`workflow/reviews/stage-04a-materialized-contract-a55.md:255-290`).
That is a useful internal helper, but it is not definitionally the paper's
`approx_delta`: it drops the index, the `[0,1]` error domain, the asymptotic
quantifiers/universal constant, state closeness, and strategy closeness. It also
combines the POVM form (with answer summation) and Appendix raw-operator form
(without an answer index) into a strictly more general operator family.

Required disposition: either (a) freeze the exact finite value/bound under a
name that cannot be mistaken for the paper relation and add an indexed
asymptotic wrapper plus state/strategy relations and laws, or (b) explicitly
re-scope F04 and create source-anchored dependent nodes for every omitted paper
relation/law. A later theorem may absorb a universal constant into a named
numeric error, but it may not silently identify `<= delta` with `<= O(delta)`.

### 2. Blocker: F04 lacks callable local-operator and tensor adapters

The proposed state lives in `EuclideanSpace Complex (Alice x Bob)`, while each
measurement effect lives on only `Alice` or `Bob`
(`stage-04a-materialized-contract-a55.md:222-235`). The paper's consistency and
distance expressions apply `A tensor I` and `I tensor B` to the bipartite state
(`dependencies/strategies-distance.tex:138-165,226-250`), and its extraction
conclusions compare conjugated effects after explicit identity extensions
(`qpbt/qpbt-game-and-soundness.tex:533-545`).

The node promises explicit adapters among Euclidean space, `WithLp`, matrices,
endomorphisms, and operator actions (`nodes.json:100-101`), but none appears in
the planned name list. `stateDependentDistance` accepts operators already on the
same coordinate carrier and therefore cannot by itself express the paper's
cross-side formulas. The callable freeze must name or identify exact qualified
existing declarations for:

- Alice-local and Bob-local lifts (`A tensor I`, `I tensor B`) to the product
  carrier;
- the tensor/product action of the two local isometries on the bipartite state;
- rectangular linear-isometry-to-matrix conversion and its adjoint; and
- the reassociation/reindexing between `(A' x A'') x (B' x B'')` and the
  paper's junk/ideal grouping.

Private implementation coercions are not enough because F04 downstream
consumers need these operations and the blueprint expressly forbids implicit
adapter choices.

### 3. Blocker: local conjugation is mathematically fixed but callable shape is not

The source applies the two sides separately:
`tilde A^x_a = phi_A A^x_a phi_A^dagger` and
`tilde B^y_b = phi_B B^y_b phi_B^dagger`, after existential local isometries
whose targets are explicitly factored (`dependencies/magic-square.tex:109-123`;
`qpbt/qpbt-game-and-soundness.tex:533-545`). The proposed single method requires
both an Alice and Bob operator and returns a pair
(`stage-04a-materialized-contract-a55.md:249-276`). The formulas and orientation
`V A V^dagger` are correct, but requiring an unrelated opposite-side operator
to conjugate one side is not the paper's quantifier shape and is not the weakest
callable abstraction.

Resolve `conjugate`-returning-a-pair versus `conjugateAlice`/`conjugateBob`
before freeze. Whichever API is selected must retain factored target types at
soundness call sites rather than treating the entire target as an opaque
`AuxAlice`/`AuxBob`. Also preserve the tracked source discrepancy: Theorem 7.14
declares `phi_alice`/`phi_bob` but uses `phi_A`/`phi_B` in its conclusions
(`QPBT_SOURCE_MAP.md:132-138`; game fragment `:537-545`). A consistent Lean name
is a documented notation repair, not an unrecorded normalization.

### 4. Blocker: F03 provenance does not support all three planned declarations

F03 currently anchors only `dependencies/measurements.tex:35-50`, label
`def:bracket` (`nodes.json:70-83`; generated entries `:26-35`). That range gives
the fiber-sum postprocessing rule, but not the paper definitions of POVM,
projectivity, observable, or binary observable, which are at
`measurements.tex:3-19`. Conversely, the sign-specific conversion in the
proposal is not defined by `def:bracket`; it comes from two-outcome projective
measurements and the convention `E_0-E_1`
(`dependencies/magic-square.tex:147-173,256-281` and
`qpbt/qpbt-game-and-soundness.tex:383-410`).

The node also says it represents postprocessing (`nodes.json:78`), but its
planned names contain no postprocessing declaration (`:79`). If the intent is
to reuse `MIPStarRE.Quantum.Measurement.postprocess`, freeze that exact qualified
callable signature and its fiber-sum/empty-fiber behavior; otherwise add a QPBT
wrapper. Widen F03 to multiple exact source anchors. For
`observableOfMeasurement`, freeze the defining equation
`O = effect 0 - effect 1`, not merely a return subtype containing some unitary
involution. The sign and projectivity requirements themselves are source-exact.

### 5. Blocker: F01 must separate three logically different claims

The paper first defines trace, duality, and normality
(`dependencies/finite-fields.tex:62-83`). Its algorithm lemma then has the
uniform order

`exists deterministic Alg, forall odd integers k > 0, Alg(k)`

and requires `Alg(k)` to output both a self-dual normal basis and its
multiplication tables in `poly(k)` time (`:265-307`). The arithmetic lemma uses
that particular algorithm-selected basis/tables to compute addition,
multiplication, tables, inverse, trace, and projections (`:350-400`).

The proposed noncomputable constructor has only the pointwise mathematical
order `forall k : Nat, Odd k -> FieldData k`, and `FieldData` contains no
algorithm, table output, or runtime statement
(`stage-04a-materialized-contract-a55.md:139-167`). Thus:

1. simultaneous self-dual-normal-basis existence is a mathematical theorem;
2. a single deterministic algorithm and its multiplication-table complexity is
   a stronger, uniform computational theorem; and
3. direct `GaloisField 2 k`, `Basis (Fin k)`, `Algebra.trace`, coordinates, and
   matrix/operator adapters are the chosen Lean representation.

Layer 1 may define `fieldDataOfOddExponent` by classical choice once proved.
It cannot discharge layer 2. K03A must state the algorithm/table theorem and
must connect the algorithm-selected basis to the same `FieldData`/binary
representation used downstream; an unrelated classical basis plus an unrelated
efficient basis is insufficient. The current F01 metadata says `fidelity:
exact` and `gap_ids: []` (`nodes.json:34-49`), which is incompatible with
treating the noncomputable projection as the whole paper claim. Record the
self-dual-normal existence gap and the algorithmic discharge separately, with
no caller-supplied witness.

### 6. Major unresolved domains: distributions and strategy-state choice

The proposed placement of finiteness is mostly correct:

- `MeasurementFamily` may have an arbitrary question type; the measurement and
  bracket definitions only quantify over `x in X` (`measurements.tex:21-47`).
- Outcomes and finite coordinates may be `Fintype`/`DecidableEq` as a faithful
  finite application boundary. Games make both question and answer alphabets
  finite (`strategies-distance.tex:4-18`).
- `PureStrategy` must therefore require finite/decidable question, answer, and
  coordinate types, as proposed.
- A family average must require finite questions/outcomes and a normalized
  probability distribution. `PMF Question` is a faithful Lean representation of
  the single-question `mu` in `def:povm-distance`.

Two choices remain. First, a game's `mu` is joint on `X x Y`
(`strategies-distance.tex:6-16`), but strategy distance discusses Alice- and
Bob-indexed families "under mu" (`:267-280`); the Lean relation must explicitly
take marginals or state how the joint PMF is consumed. Second, the paper allows
the family comparisons on either `psi` or `psi'` (`:279-280`). A source-faithful
strategy-distance signature must make that choice/quantifier explicit rather
than silently selecting one state. Passing an explicit state to the finite leaf
helper is correct, but it does not resolve the paper relation.

### 7. Minor source indexing choice: normal-basis coordinates

The binding normal-basis definition uses the Frobenius orbit
`{alpha^(q^j)}_{j=0}^{k-1}` (`finite-fields.tex:79-83`). Later 1-based prose
writes `e_i = alpha^(2^i)` (`:313-323`), which is a cyclic reindexing because
`alpha^(2^k)=alpha`, not a different basis. `Fin k` with
`basis i = alpha^(2^(i:Nat))` follows the defining zero-based order. Record this
index convention in the signature documentation so it is not mistaken for a
silent off-by-one repair.

## Exact paper contract and quantifier order

### F01-FIELD

- General input: prime `p`, prime power `q=p^k`; `F_{q^k}` is a degree-`k`
  extension of `F_q` (`finite-fields.tex:4-18`).
- Chosen-basis data: coordinates/downsize and multiplication matrix `K_a`, with
  `downsize_q(ab)=K_a downsize_q(b)` (`:19-53`).
- Trace: `tr_{q^k->q}(a)=Tr(K_a)=sum_{j=0}^{k-1}a^(q^j)`, an `F_q`-linear,
  basis-independent map (`:62-73`).
- Self-duality: `forall i j, tr(e_i e_j)=delta_ij`; normality: one witness
  `alpha` with the whole Frobenius orbit as basis (`:75-83`).
- QPBT domain: `q=2^k`, `k` odd; odd positive input is constructed data, not a
  hypothesis supplying a basis (`:243-292`).
- Uniform algorithm order: one deterministic algorithm works for every odd
  positive `k`, outputs basis *and tables*, and runs in polynomial time
  (`:283-307`).

### F03-MEASUREMENT

- For each outcome `a in S`, a POVM has positive effects and
  `sum_a M_a=I`; projective means `forall a, M_a^2=M_a`
  (`measurements.tex:3-17`).
- An observable is unitary; binary additionally satisfies `O^2=I` (`:17-19`).
- Family/postprocess order: given `{M^x_a}_{a in A}` for every `x in X`, then
  given `f:A->B`, for every `x,b` define the fiber sum over `a` with `f(a)=b`;
  an empty fiber gives zero (`:21-47`).
- Binary conversion used by QPBT: first require an `F_2`-indexed two-outcome
  projective measurement, then define `O=E_0-E_1`; this is the fixed sign order
  (`magic-square.tex:147-173,256-281`; game fragment `:383-410`).

### F04-DISTANCE

- A game first supplies finite `X,Y,A,B`, joint distribution `mu` on `X x Y`,
  and predicate `D`; a strategy then supplies finite-dimensional local Hilbert
  spaces, one bipartite unit vector, and Alice/Bob POVM families
  (`strategies-distance.tex:4-32`).
- Finite family distance order: finite `X`, probability `mu`, normalized state
  `psi`, then two POVMs for every `x`, then expectation over `x` and sum over
  outcomes (`:252-265`).
- Asymptotic order: families/implicit `n`, error function into `[0,1]`, then a
  Big-O assertion as `n -> infinity` (`:213-238`).
- Strategy distance: game and two strategies first, then `delta in [0,1]`, then
  same-space state closeness and both local-family conditions, with an explicit
  state choice (`:267-282`).
- Extraction order: after a success hypothesis, existentially choose local
  isometries and auxiliary state; only then define every conjugated Alice/Bob
  effect and assert state/family conclusions (`qpbt-game-and-soundness.tex:533-545`).

## Statement-integrity table for every planned declaration

| Declaration | Paper assumptions and order | Proposed Lean assumptions | Paper conclusion/data | Proposed Lean conclusion/data | Verdict |
| --- | --- | --- | --- | --- | --- |
| `FieldData` | Concrete `F_{2^k}/F_2`, one normal generator, basis indexed by the Frobenius orbit | `k : Nat`, direct `GaloisField 2 k`, `Basis (Fin k) (ZMod 2)` and generator | `b_i=alpha^(2^i)` and `tr(b_i b_j)=delta_ij` | Same two equations using `Algebra.trace` | **exact** mathematical witness data |
| `fieldDataOfOddExponent` | One deterministic algorithm, then every odd integer `k>0`; output basis and multiplication tables in `poly(k)` | For every `k : Nat`, `Odd k`; noncomputably return `FieldData k` | Uniform executable basis/table construction and complexity | Pointwise mathematical basis witness only | **documented mismatch** if identified with `lem:efficient_basis`; **faithful boundary** only as an explicitly named existence projection |
| `fieldTrace` | Finite-extension trace `F_{2^k}->F_2`, linear and basis-independent | Concrete GF algebra/finite-dimensional instances; proposal accepts `k : Nat` | Extension trace | `Algebra.trace` as a `ZMod 2`-linear map | **exact** on the admissible domain; harmless definitional generalization outside it must be documented |
| `MeasurementFamily` | For every question `x`, an outcome-indexed complete POVM | Arbitrary `Question`; finite/decidable `Outcome` and coordinate carrier; `Complex` matrices | Family `x -> {M^x_a}` | Function into qualified `Quantum.Measurement` | **faithful boundary** (finite coordinate realization; question finiteness correctly deferred) |
| `ProjectiveMeasurementFamily` | For all `x,a`, each POVM effect is a projector | A `MeasurementFamily`; `forall x a`, matrix idempotence | Projective family | Same predicate; positivity/completeness inherited from measurement | **exact** |
| `observableOfMeasurement` | Given an `F_2` two-outcome projective measurement, define `E_0-E_1` | `Measurement (ZMod 2) Coord` plus pointwise projectivity | Canonical unitary involution with sign `0` minus `1` | Certified unitary involution; body intended to be that difference | **faithful boundary**, becoming source-exact only when the defining equation is frozen/tested |
| `PureStrategy` | Finite `X,Y,A,B`; finite local Hilbert spaces; unit `psi`; two POVM families | Finite/decidable question, outcome, Alice/Bob coordinate types | Tensor-product strategy tuple | Product-index Euclidean state, norm-one proof, two measurement families | **faithful boundary** via the canonical finite-coordinate tensor realization |
| `BipartiteIsometry` | Local isometries arise existentially after a test-success hypothesis; each target is factored into junk and ideal registers | Pair of finite-coordinate linear isometries into opaque whole target carriers | Two local maps with factored codomains | Paired maps to `AuxAlice`/`AuxBob` | **faithful boundary** as generic data; insufficient by itself for the factored extraction theorem |
| `BipartiteIsometry.conjugate` | After each local isometry, independently define every `phi_A A phi_A^dagger` and `phi_B B phi_B^dagger` | One paired isometry plus both operators at once | Two side-specific conjugated operator families | Pair of the same two formulas | **faithful boundary with unresolved callable shape**; freeze side-specific quantification before dispatch |
| `stateDependentDistance` | Finite integrand `||(A-B)psi||^2` inside POVM/operator-family distance; paper states use normalized states | Finite coordinate state and two same-carrier operators; helper permits any vector | Nonnegative real integrand | `Real` squared Euclidean norm using an explicit matrix-to-linear adapter | **exact** finite integrand, with a documented harmless vector-domain generalization; not the whole paper closeness relation |
| `familyApprox` | Finite `X`, distribution, state, two POVMs, answer sum, but closeness is indexed `O(delta)`; Appendix raw operators have no answer sum | Finite/decidable `Question`, `Outcome`, `Coord`; `PMF`; raw outcome-indexed operators; `delta : NNReal`; exact `<= delta` | Asymptotic POVM/operator relation and, separately, strategy relation | One exact numeric predicate | **documented mismatch** if paper-labelled; **faithful boundary** only as a renamed finite-bound helper with a separately frozen asymptotic bridge |

## Node-level source-fidelity disposition

| Node | Verdict | Required before freeze |
| --- | --- | --- |
| F01-FIELD | **conditional / not `exact` as currently described** | Keep `FieldData` and trace; label the noncomputable constructor as the existence projection; add the tracked simultaneous-basis gap; keep uniform algorithm/table/runtime and representation coherence in K03A |
| F03-MEASUREMENT | **mathematically faithful, provenance-blocked** | Add `uQuestion`; widen source anchors; freeze postprocess reuse/signature; freeze `observableOfMeasurement = effect 0 - effect 1`; resolve certified-bundle naming |
| F04-DISTANCE | **blocked / incomplete** | Freeze local lift/tensor/reindex adapters and side-specific conjugation; distinguish exact numeric value/bound from indexed Big-O; add or explicitly defer state/strategy relations, consistency, triangle, and data processing; state joint-marginal and state-choice semantics |

Overall source-fidelity verdict: **documented mismatch; do not approve QPBT-023 or dispatch QPBT-013 until the required dispositions are represented in canonical blueprint metadata and generated callable entries.**

## Authentication and checks

The materialized boundary is authenticated. `QPBT_SOURCE_MAP.md:21-44` requires
`sections/READY` to equal the inventory digest. Observed:

- `READY` = `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`;
- SHA-256 of `inventory.json` is the same value;
- inventory-recorded and observed source pin SHA-256 are both
  `66a1e9db74f1454ce50909728a3b741f9da468b5d61902645557793ceb91ac9c`;
- inventory-recorded and observed split-manifest SHA-256 are both
  `052cfaceb2e4a7b59778936ceb3daea9a33e3592e01b902cb2a9740c58999a20`;
- all six mandated fragment hashes matched `inventory.json:1`:
  `finite-fields.tex` `379d970...b9cd`, `measurements.tex` `b3c03f8...f946`,
  `strategies-distance.tex` `a3a2e3f...e5f`, `magic-square.tex`
  `7593e7f...7c6b`, `qpbt-game-and-soundness.tex` `30c7351...62ea`, and
  `appendix-preliminaries.tex` `20d608c...c284`.

Complete bounded reads were made of `AGENTS.md`, `QPBT_SOURCE_MAP.md`, READY,
inventory, every line of the six mandated TeX fragments, relevant F01/F03/F04
metadata and generated entries, `blueprint/src/chapter/02-foundations.tex`, both
required prior reviews, and the QPBT-023/QPBT-013 issue records. The initial
`wc` probe against the detached clone's ignored `sections/` path exited 1 because
the materialized artifacts are intentionally absent there; the mandated
authenticated canonical materialization was then located and verified. No
paper conclusion relies on that failed discovery probe.

Read-only command classes: `git rev-parse`, `git status`, `date`, `/proc/uptime`,
`rg`, `find`, `ls`, `wc`, `sed`, `nl`, `jq`, and `sha256sum`. No Lean/API
elaboration claim is made by this source-only audit.

## Action accounting

```json
{
  "repository_file_writes": 0,
  "canonical_workflow_state_writes": 0,
  "research_metrics_writes": 0,
  "git_writes": 0,
  "git_ref_or_worktree_writes": 0,
  "lean_invocations": 0,
  "lake_invocations": 0,
  "build_invocations": 0,
  "cache_warm_seed_or_status_invocations": 0,
  "network_accesses": 0,
  "endpoint_accesses": 0,
  "github_operations": 0,
  "credential_accesses": 0,
  "agent_spawns": 0,
  "subagents": 0,
  "compile_attempts": 0,
  "report_files_written": 1
}
```

The report SHA-256 is intentionally not self-embedded; it is communicated to
the orchestrator out of band after the final file is closed.
