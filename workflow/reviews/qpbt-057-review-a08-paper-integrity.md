# QPBT-057 paper-integrity review (A08)

Session: `i057-reviewer-a08-paper-integrity`  
External collaboration ID: `/root/i057_reviewer_a08_paper_integrity`  
Review worktree: `/tmp/qpbt-057-review-a07`  
Base: `9eb476a41595fc70060ed9bb2ea91a50c793ede3`  
Head: `a67031de5a3804360e113dd4a881e94376fc435f`  
Tree: `71acb8bd5ea77959a03a1124c2fce018457b9605`

## Findings

None.

## Verdict

**APPROVE.** The source-facing declarations preserve the pinned paper's
hypotheses, conclusions, quantifier order, positive-index domain, constants,
normalizations, and runtime dependence, subject only to the documented G19
executable boundary. The exact two Stage-4A proof holes are honest and visible;
no theorem content has been displaced into a public obligation or arbitrary
caller-supplied witness.

## Statement-integrity comparison

Rows group generated structure projections and constructors with their parent
public declaration; every explicit source-facing public declaration introduced
in `MIPStarRE/QPBT/Game/Types.lean:799-1618` is named below.

| Lean declaration(s) | Paper assumptions and conclusion | Lean hypotheses, conclusion, and order | Constants / normalization / dependence | Verdict |
| --- | --- | --- | --- | --- |
| `AdmissibleFieldFamily`, `fieldSize`, `fieldData`, `fieldCodec`, `binaryFieldFamily` | `q(n)=2^k` for odd `k`, with the selected self-dual normal basis and binary coordinate representation (`finite-fields.tex:243-291`) | `n` then `0<n`; `exponent_odd` supplies oddness; field size is definitionally `2^exponent`; the F01 data/codec are selected at positive indices | Base 2, fixed coordinate order, exact width `dimension * exponent`; no error term | faithful boundary |
| `RuntimeBigO` | A positive real constant `C` works for every positive integer index (`preliminaries.tex:19-25`) | `Exists C : Real, 0<C /\ forall n, 0<n -> f(n)<=C*g(n)` in that order | Global, not eventual, big-O; exact paper normalization | exact |
| `SixTapeInput`, `SixTapeInput.ofLists`, `packSixTapes`, `packSixTapes_injective` | Ordered tuple encoding maps `0 -> 01`, `1 -> 10`, and ends each component with `00` (`preliminaries.tex:105-111`) | Six fixed ordered tapes are serialized and injectivity is proved with a private left inverse | Exact packed length is consequently `2 * (sum tape lengths + 6)`; linear encoding, no hidden Cantor growth | exact |
| `fieldExponentInput`, `FieldExponentProgram`, `FieldExponentProgram.correct`, `FieldExponentProgram.steps` | The paper requires `log q(n)` operationally but omits how it is computed (G19; `conditionally-linear.tex:632-674`) | An intrinsic program computes the exponent from each positive `n`; correctness forgets only the bound and `steps` records the actual transition count | Computation is charged in source time; no arbitrary admissible-family-to-machine theorem is asserted | faithful boundary |
| `CLStage.pred`, `CLStage.castLE`, `CLStage.last` | Stages range over `1,...,ell` (`conditionally-linear.tex:156-174`) | Zero-based `Fin ell` indices are transported explicitly; wire values use `j.val+1` | Pure indexing boundary; no changed constant or quantifier | faithful boundary |
| `CLSamplerSide`, `CLSamplerSide.bits`, `CLSampler.side` | Two maps `L^{Alice,n}` and `L^{Bob,n}` (`conditionally-linear.tex:576-582`) | A two-element side type selects exactly one associated map | One-bit side tags are an encoding choice; semantic side domain is exact | faithful boundary |
| `CLPrefix`, `CLFactorInput` | Prefixes lie in `L_{<j}(V)` and linear inputs lie in the selected factor space (`conditionally-linear.tex:588-594`) | Prefix is a range subtype; factor input is a support subtype, after `j` and its prefix | Invalid fibers are unrepresentable; this strengthens typing without strengthening theorem assumptions | faithful boundary |
| `CLQueryDecomposition` | Lemma `cl-kth` supplies marginals, prefix-indexed factor spaces/maps, direct-sum coverage/disjointness, support dependence, the marginal sum, and top marginal (`conditionally-linear.tex:150-178`) | Data are quantified by stage, then valid prefix; laws hold pointwise in the same dependency order | Register subspaces are coordinate finsets; direct sum is represented by cover plus pairwise disjointness; no error term | faithful boundary |
| `CLSamplerQuery`, `CLSamplerQuery.instFintype`, `CLSamplerQuery.index` | Exactly four query modes at a fixed positive index (`conditionally-linear.tex:572-600`) | Dependent constructors admit only valid stages, prefixes, and factor inputs; all valid queries form a finite type | `n` is fixed before the dependent query; no extraneous query or witness premise | faithful boundary |
| `CLSamplerQuery.canonicalTapes`, `CLSamplerQuery.expectedOutput` | Dimension, marginal, linear, and factor modes have the outputs in Definition `sampler`; unused tapes are ignored (`conditionally-linear.tex:584-610`) | Canonical encodings use blank unused tapes; stage is one-based on the wire; outputs are dimension, marginal vector, linear vector, or ordered indicator | Mode tags are boundary data; field-vector and factor outputs have exact fixed widths | faithful boundary |
| `IndexedSixInputBitMachine`, `outputsInTime`, `Execution`, `Execution.steps` | A six-input TM has a genuine halting computation and a step count (`preliminaries.tex:46-75,96-143`) | The six logical tapes cross the FinTM2 boundary through the proved-injective packer; an execution carries a certified bound and exposes its actual evaluation steps | Standard single-machine simulation boundary; no correctness premise detached from an execution | faithful boundary |
| `ExecutableCLSampler`, `correct`, `executedSteps`, `validQueries`, `queryTime`, `queryTime_eq_validQueryMax`, `time`, `time_eq_max` | A sampler supplies two CL maps and all four computations; `TIME_S(n)` bounds its computations (`conditionally-linear.tex:572-600`) | Associated maps/decompositions precede one uniform machine; execution is quantified `n`, positivity, then typed query. Time is the maximum over all valid queries and the intrinsic exponent execution | G19 charges exponent computation in addition to query computation; `max` preserves both costs. Exact equalities, no asymptotic error | faithful boundary |
| `ExecutableCLSampler.sample`, `dimension`, `associatedMap` | Distribution is `(L^A(x),L^B(x))` for one shared uniform `x`; dimension is `s(n)` (`conditionally-linear.tex:132-138,616-625`) | The sample delegates to the associated mathematical sampler; accessors expose exactly `s n` and the chosen side map | PMF is normalized by the existing uniform distribution; the two outputs share one seed | exact |
| `ExecutableCLSampler.downsize` | Definition `downsize_sampler` constructs one binary sampler (`conditionally-linear.tex:628-660`) | From `S`, a private existence theorem supplies one machine, all query executions, and the binary exponent program; associated data are fixed before the selector | `Classical.choice` selects from the private theorem and adds no public premise; operational construction remains the declared Stage-4A debt | faithful boundary |
| `ExecutableCLSampler.downsize_dimension` | Binary field, dimension `s(n) log q(n)` (`conditionally-linear.tex:666-675`) | For `S`, then `n`, then `0<n`, equality to `s n * Nat.log 2 (fieldSize n)` | Base-2 logarithm; `log_2(2^k)=k`; multiplication order is immaterial | exact |
| `ExecutableCLSampler.downsize_associated` | Downsized maps are coordinate conjugates for every positive `n` and both sides (`conditionally-linear.tex:676-679`) | `S`, `ell>=1`, `n`, positivity, then side; equality to mathematical `downsize` using the selected field data | The original prefix is recovered through the coordinate equivalence before selecting its map, repairing the paper's G21 index typo without changing content | exact |
| `ExecutableCLSampler.sample_downsize` | Downsized distribution is the pushforward of the original pair (`conditionally-linear.tex:533-550,676-679`) | `S`, `ell>=1`, `n`, positivity; exact PMF equality under the pair of coordinate maps | One shared uniform seed is preserved by bijection; no independence substitution or normalization loss | exact |
| `ExecutableCLSampler.downsize_time` | `TIME_downsize(S)(n) = O(TIME_S(n) log q(n))` (`conditionally-linear.tex:666-675,708-710`) | `S`, then `ell>=1`; global-positive `RuntimeBigO` with RHS `S.time n * Nat.log 2 (fieldSize n)` | Exact base-2 factor and global quantification; this is the sole runtime proof hole; no error parameter exists | exact statement, tracked proof debt |

## Focused semantic audit

- Dual rail: `Types.lean:1083-1161` implements and decodes six ordered,
  independently terminated tapes. `00` cannot occur inside either `01` or `10`,
  so tape boundaries are unambiguous and the inverse proof establishes
  injectivity.
- Typed fibers: `Types.lean:944-1080` restricts prefixes to the prior marginal's
  image and linear inputs to the selected register. The downsize construction at
  `Types.lean:1389-1504` pulls a binary prefix back before indexing the original
  factor/map, expands each source coordinate to its contiguous basis block, and
  preserves cover, disjointness, support, marginal sums, and the top map.
- Packing/coordinate order: both `fieldVectorBitsEquiv` and `expandRegister` use
  `finProdFinEquiv`, so the field codec, factor indicator expansion, and
  `s(n) * exponent(n)` dimension use the same outer-coordinate/inner-basis order.
- Sampler pushforward: `Types.lean:718-728,1545-1552,1601-1611` applies Alice and
  Bob to the same uniform seed and transports that pair through one bijective
  coordinate map. It does not replace the shared seed by independent samples.
- Resource selection: `Types.lean:1239-1268` takes the maximum over the complete
  finite typed-query family and the intrinsic exponent execution. The downsize
  selector at `Types.lean:1571-1582` chooses only the private compiler witness;
  it does not accept a bridge, producer, package, or arbitrary implication from
  callers.

## Proof-debt audit

- `MIPStarRE/QPBT/Game/Types.lean:1568`: the private
  `ExecutableCLSampler.downsizeCompiler_exists` body is `sorry`. Its proposition
  is exactly the operational debt: one machine, executions for every positive
  index and every valid downsized query, plus the constant binary exponent
  program. It has no runtime conclusion and no public premise.
- `MIPStarRE/QPBT/Game/Types.lean:1618`: the public
  `ExecutableCLSampler.downsize_time` body is `sorry`. Its statement is the
  source runtime conclusion with the G19-charged source time.
- The complete candidate file contains no other `sorry`, no `admit`, no declared
  `axiom` or `constant`, and no `_ofObligations`, generic `Hypotheses` or
  `Assumptions`, bridge, residual, repair, producer, or witness-package API.
- The public `decomposition`, `execution`, and `fieldProgram` fields are not
  displaced theorem proofs: the first two are the chosen semantic/operational
  data in Definition `sampler`, and the last is the documented G19 executable
  boundary. The only classical selector is downstream of the explicit private
  compiler theorem and hides no additional assumption.

## Authentication and checks

- Manifest `/home/drx/MIPStarRE-auto/.workflow-runtime/manifests/i057-reviewer-a08-paper-integrity.json` authenticated at SHA-256 `6bb9e448bff47c835e0f3d047bfb441035612c08e732d297c91aad44c8de3474`.
- Worktree was clean and detached at the exact head. Base tree
  `bb64aa48a0d6deb12995d449778064a296a1a9b8`, head parent
  `f51b636169dc0b008f8de9b877086c518d7ac945`, head tree, and all manifest
  revisions matched.
- Plain/binary diff SHA-256 matched
  `d13454544557b44a38e7c2b3cb2c992dd5551cab3e14aa274269772ae36bfa2f`;
  changed paths were exactly `MIPStarRE/QPBT/Game/Types.lean` and
  `workflow/reviews/qpbt-057-f06a-a02.md`.
- All twelve manifest-listed file hashes matched. Pinned paper sources were read
  before candidate theorem text. Only manifest-listed evidence was read.
- Review interval: `2026-09-03T20:40:57.644152717+08:00` through
  `2026-09-03T20:45:17.920479084+08:00`; elapsed `260.276326367s`.
- Token usage: `null` (`the collaboration backend exposes no per-session token count`).
- Findings: 0. Fix actions: 0. New issues: 0. Retries/incidents: 0.
- Nested agents: 0. Compile/test/Lean/Lake/build/cache attempts: 0.
- Repository/Git/state/metrics/protocol/candidate writes: 0. Network/endpoint/
  GitHub/credential actions: 0. The sole write is this authorized `/tmp` report.

## Residual risk

This is an approval of the declared Stage-4A minimal skeleton, not a claim of
proof completeness. The compiler/execution construction and global runtime
bound remain exactly the two visible `sorry` bodies above and must be discharged
under QPBT-061 without changing the reviewed public signatures. No compilation
was run by this reviewer, as required by the immutable reviewer packet; the
authenticated candidate report records the coordinator's prior deterministic
validation, which was treated as untrusted supporting evidence rather than
reperformed proof.
