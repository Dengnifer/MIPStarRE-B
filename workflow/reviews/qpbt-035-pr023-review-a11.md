# LPR-023 immutable resolution review (A11)

Canonical session: `i035-reviewer-a11-pr023-resolution`

Formal verdict: **request_changes**

## Findings

1. **High / blocker - F06 still sends its executable sampler source debt to
   nodes that are checker-frozen not to own it (`F-LPR023-004`).**
   `blueprint/metadata/nodes.json:352` labels F06 `exact` over the full pinned
   range `conditionally-linear.tex:1-715`, but its Lean conclusion explicitly
   omits the executable layer and its integrity verdict is `faithful boundary`
   at `blueprint/metadata/nodes.json:376`. More importantly,
   `blueprint/metadata/nodes.json:374` assigns raw Turing samplers, executable
   sampler interfaces, and efficiency to K03-K04. Those nodes are sourced only
   to canonical-parameter computation and the three QPBT-specific complexity
   clauses (`blueprint/metadata/nodes.json:1115-1130,1169-1184`); K04 expressly
   forbids adding sampler claims at line 1181, and the new checker freezes both
   ranges and sole callable names at `blueprint/check.py:151-159,550-560`.
   The pinned F06 source nevertheless defines the ordinary executable sampler,
   its indexed distribution, executable downsizing, dimension, runtime, and CL
   correspondence at `references/2001.04383v3/sections/dependencies/conditionally-linear.tex:565-712`.
   Thus the declared discharge target cannot discharge the cited source.
   Narrow F06 to an honest mathematical `faithful-boundary` and assign the
   executable clauses to an exact later source/callable/issue contract, or
   expose them under F06. K03/K04 must retain their current exact ownership.

2. **Medium / blocker - F-LPR023-003 survives in the F07 statement and evades
   the new fail-closed check.** `blueprint/metadata/nodes.json:387` still calls
   both objects "finite typed samplers and deciders." The frozen
   `TypedDecider` has arbitrary dependent question and answer families and no
   pointwise `Fintype` assumptions, exactly as the corrected boundary at line
   407 acknowledges. The checker concatenates the statement, encoding, and
   boundary but rejects only the literal phrases `finite dependent fibers` or
   `finite decider` (`blueprint/check.py:543-547`), so the canonical wording
   passes. The unit test checks only the boundary and integrity conclusion
   (`blueprint/tests/test_check.py:318-323`) and misses the statement. Replace
   the statement with the actual contract: a sampler over the constant finite
   `FieldVector` carrier and a total dependent decider with no pointwise
   finiteness claim. Freeze that wording or an equivalent structural invariant
   in the checker and add a mutation that fails on the current phrase.

3. **Low - A07 cites a nonexistent stable session name (`F-LPR023-005`).**
   `workflow/reviews/qpbt-035-q014-contract-a07.md:156` names
   `i035-scout-a08-game-semantics`; the authenticated report and canonical
   session are `i035-scout-a08-game-semantics-api`. Correct this provenance
   identifier with the substantive repair so the immutable attempt chain is
   exact.

## Prior finding dispositions

| Finding | A11 disposition | Confirmation ID | Evidence |
| --- | --- | --- | --- |
| `F-LPR023-001` | resolved on c35 | `C-LPR023-A11-001` | `F07A-DETYPING` owns exact `types.tex:197-579`, exactly 20 names, and direct prerequisites `[F04A-GAME-SEMANTICS,F07-TYPED]`. Canonical QPBT-041/042/043 now bind the three sole implementation paths and exact dependency chain. |
| `F-LPR023-002` | resolved on c35 | `C-LPR023-A11-002` | `CLSampler.sample_directSum` is present; marker SHA-256 `120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461` recomputed; source order/independence and the exact theorem type were independently checked. |
| `F-LPR023-003` | **open** | `C-LPR023-A11-003` | The boundary and canonical QPBT-038 issue are narrowed, but the immutable node statement still overclaims a finite decider and the checker accepts it. |

The current canonical issue state at the evidence cutoff contains QPBT-041
under QPBT-005/STAGE-04A, while QPBT-042/QPBT-043 remain flat under the root
tracker QPBT-000 and are assigned to STAGE-04B. Their exact dependencies are
`[QPBT-032,QPBT-045] -> QPBT-041`,
`[QPBT-035,QPBT-041] -> QPBT-042`, and
`[QPBT-038,QPBT-042] -> QPBT-043`; their sole declaration paths are
respectively `Basic/Approximation.lean`, `Game/Semantics.lean`, and
`Game/Detyping.lean`. QPBT-046 and QPBT-047 separately own the proof-complete
discharge of any individually tracked skeleton `sorry` from QPBT-041 and
QPBT-043. QPBT-038's canonical acceptance text was also corrected to assign
pointwise consumer finiteness only to G02 and to cite `types.tex:57-195`.
Canonical workflow validation passed with 48 issues, 23 local PRs, 391 issued
sessions, and 7 stages. This mutable-state evidence is bound by the state
hashes below; it does not repair the immutable c35 statement.

## Statement integrity

| Node | Paper assumptions | Lean/blueprint assumptions | Paper conclusion | Lean/blueprint conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F04A | Four finite alphabets, question distribution/predicate, normalized finite tensor strategies; common local space for PCC | Explicit finite decidable carriers, PMF, reviewed `PureStrategy` and exact consistency APIs, canonical `Fin` dimensions | Fixed and supremal values; projective/symmetric/support-commuting/consistent/PCC/SPCC predicates; Schmidt rank and Ent | Same semantic layer through 18 names; no moved `PureStrategy`; implementation signatures remain for QPBT-042 | **faithful boundary, accepted** |
| F06 | Finite CL spaces and shared seeds, direct-sum independence, basis downsize, plus executable sampler/downsize/runtime layer | Certified finite field vectors, pair PMFs, `Fin.append`, `FieldData` only at downsize; no executable interface | Mathematical CL equations and executable sampler/downsize/cost clauses | Mathematical equations including exact binary product PMF and downsize pushforward; executable owner incorrectly assigned | **documented mismatch, blocker F-LPR023-004** |
| F07 | Finite type graph, executable indexed typed sampler/decider, typed downsize and cost | Nonempty symmetric ordered support, constant finite sampler carrier, arbitrary dependent decider fibers | Typed graph/sample law, typed downsize relations, total typed decider | Correct callable signatures and PMF pushforward, but statement still calls the decider finite | **documented mismatch, F-LPR023-003 open** |
| F07A | Nonempty finite graph, typed verifier/game, finite game/PCC/Ent semantics, explicit machine model | F04A and F07 plus a future explicit machine/cost representation | Exact graph event law; four detyping constructions; completeness; `16^|Type|` value/Ent loss; level, dimension, and costs | All clauses have distinct ownership among exactly 20 names; implementation signature intentionally deferred to QPBT-043 | **faithful boundary, accepted as ownership contract** |
| K03/K04 | Canonical tuple computation; exact three QPBT complexity clauses | Their pinned source ranges and one callable each | Those same concrete complexity facts | Byte-equivalent metadata at base/head; no detyping or generic sampler callable | **unchanged and accepted** |

No paper-labelled Lean declaration changes in this PR. The ten changed paths
are blueprint metadata/checker/generated artifacts and attempt reports. No
repository `sorry`, `axiom`, `constant`, generic assumptions object, or public
obligation input was introduced.

## Authentication

- Formal base commit/tree:
  `50c4a9ce9fc9446b04c1c309951f05cc6a49766c` /
  `a0248f602cc2648742a8d2636c7af15ccd9a039a`.
- Reviewed head/tree:
  `c35fcd36bea96705851655852eabc78ca9db9b3f` /
  `86d8ca78d3e4bb5fe89d57f25c2bea539d4c8100`.
- Head parent: `3f2630a7631a0164b6ef4aca1fd081ba264beeb2`.
- Detached review worktree and candidate issue worktree were clean before and
  after checks.
- Exact ten-path path-sorted `git ls-tree` manifest SHA-256:
  `1a5831dad7f443ef9ea01906caf178805e41acce8687d3c27750e1cc8390d19c`.
  The ten paths are `blueprint/check.py`, both generated graph files,
  `blueprint/metadata/nodes.json`, both generated chapter entry files,
  `blueprint/tests/test_check.py`, and A02/A04/A07 reports.
- The full formal diff has exactly those ten paths; the final A07 increment
  relative to its direct parent has seven paths. Both diff checks passed.

### Authenticated reports

| Report | SHA-256 |
| --- | --- |
| A02 contract | `987d17140ae4e1e808ed0504b874c67dc1285f70245cf71363dafe97fc1dd610` |
| A03 formal review | `a1ed48ff7a642c8811f56d1aa77caec32e3cf1608a33dd474fffb16b367e4caf` |
| A04 repair | `a55e7789d6a899b31e6fc8625dfb6116c9430884fb2ce83fc6e1182bb2d3225e` |
| A05 source audit | `de9c4c87820f76c8162f7d2f06bbcd0a66a6ed14cc8d57ed2c6d1414bccd81fb` |
| A06 direct-sum audit | `2bd9b52a679ba2bc155a28ea6b6f352375f0d5a1ee2f3db065739eba45ab24e6` |
| A07 source repair | `f98f21f7a9f355ca2f2af4e8ef20a3390f995430d045427b79b1c1a7ed93e1e8` |
| A08 game API audit | `f37ab823449c85b078330f3912b4ec8eedfc67b8c9ffedb1d1b261434ccc4b27` |
| A09 issue graph audit | `b00b9a986624270d307beabd00e93cea759f14a6f3cadce231350ffe15551e83` |

### Authenticated source and signatures

| Object | SHA-256 |
| --- | --- |
| `low-degree-code.tex` | `e77125aa2c20f037b949f8890efcaaf370f5ca25407048a5ac142115104bdc9e` |
| `pauli.tex` | `aba301b2e225f0ceaeff6a942a75ee6d5db73283ba25e208e2e43452818aef2f` |
| `conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` |
| `strategies-distance.tex` | `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f` |
| `qpbt-game-and-soundness.tex` | `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea` |
| F04A signature marker | `2bc405a88ddbfc0d82b10c431a7de2c9d2ce0ca415e1ce25fed2fabdda7da870` |
| F06 signature marker | `120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461` |
| F07 signature marker | `99cfe240da252a94527d50c53d39a9673ee8d673cf6eba9730fb1a7e92df9d46` |
| Authenticated A08 full-body probe | `ab22cecd1ced868fef8b1bbe4daf81c1604f60e3fe6cd1fd003a91edac16c5e7` |

The F04A anchors are exactly `4-51`, `62-81`, and `126-190`; its sole
prerequisite is F04-CONSISTENCY, it has 18 names, and it does not own or relist
`PureStrategy`. F07 is exactly `57-195` and its 11 names include the exact
elaborated `TypedSampler.downsize` and `sample_downsize`. F07A is exactly
`197-579`, has the two direct prerequisites above, and has 20 names covering
typed verifier/game, graph simulation/event probability/conditioned law, all
four transformations, and each published theorem clause. K03 and K04 are
byte-equivalent as JSON objects between base and head; their canonical JSON
SHA-256 values are respectively
`7f5dedfc8db656d61e932509e7ea35adbe536b717df6388b2661555756d2a3d8`
and `11339806e65d7719df32faa659c5288f5bb9a5ce7aae823637ae9efe41b53755`.

Canonical state hashes at inspection cutoff were: issues
`cc9846c0abdffca9b4c97ad8bb8e07a9dc3a91c12bd277f7439bbffe808e09c1`,
stages `a9a2ae33d82ca34b169c4efb87eaa8231406ed956ee2e9bc7453af78709b30aa`,
and PRs `94aeac27b68cc37db50bef3b91df20b19d31dced698b17b14ae07ba378631672`.

## Validation

| Gate | Result | Wall time |
| --- | --- | ---: |
| Blueprint unit suite | pass, 29/29 | `0.90s` |
| Default deterministic check | pass, 53 nodes / 12 chapters | `0.08s` |
| Pinned-source check | pass, 53 nodes / 12 chapters | `0.09s` |
| Detached workflow validation | pass, 41 issues / 21 PRs / 376 issued sessions / 7 stages | `0.12s` |
| Detached workflow checker | pass | `0.14s` |
| Formal-base diff hygiene | pass | `0.01s` |
| Authenticated F04A full-body Lean probe | pass, no proof placeholders | `5.65s` |
| Exact F06 theorem-type Lean probe | pass, 3 probe-local `sorry` bodies | `2.66s` |
| Stdin-only exact F07 surface/downsize probe | pass, 6 probe-local `sorry` bodies | `2.72s` |
| Current canonical workflow validation after final issue allocation/correction | pass, 48 issues / 23 PRs / 391 issued sessions / 7 stages | `0.13s` |

All Python commands used `-B`; no `__pycache__` or candidate byte was created.
The Lean probes read the already seeded, private, exact-c35 cache and emitted no
olean/build artifact. No target build, full build, cache warm/seed/publication,
source materialization, regeneration write, network, endpoint, GitHub, or
credential operation was performed.

## Residual risk

This is a blueprint contract review, not a proof review. Passing probes show
that the revised types elaborate at the pinned toolchain; they do not prove
future bodies or representation-invariance facts. F04A and F07A intentionally
defer implementation bodies and the concrete executable cost model to tracked
issues. The locally materialized ignored paper sections were authenticated by
their READY/inventory boundary and source hashes but are not part of the Git
manifest. F05/G09 and the later F10 binary conversion remain previously tracked
risks and were not reopened by this resolution review.

## Integration checklist

1. Do not integrate head c35 and do not resolve F-LPR023-003 yet.
2. Correct F07's statement, harden the checker against equivalent finite-decider
   wording, add the missing mutation test, and regenerate all deterministic
   graph/chapter outputs.
3. Repair F06's fidelity/ownership contract. Keep K03/K04 exact; bind the
   ordinary executable sampler/downsize source to a truthful later owner and
   issue gate if it remains outside QPBT-038.
4. Correct the A08 stable session identifier in A07.
5. Commit the owned repair as a new immutable head, update LPR-023 checks and
   finding records, rerun the same gates, and request a fresh resolution review
   only after the head SHA changes.

## Session accounting

- Durable dispatch start: `2026-09-01T15:43:28.815310Z`.
- Evidence cutoff: `2026-09-01T16:01:49.116080474Z`.
- Runtime-measured elapsed to cutoff: `1100.300770` seconds.
- Token usage: input `null`, output `null`, total `null`; availability reason:
  the collaboration backend does not expose per-session token counts.
- Topology: root coordinator -> one fresh reviewer; nested agents 0.
- Actions: 1 unit suite, 1 default check, 1 pinned-source check, 4 workflow
  validations, 1 workflow-checker run, 3 diff-hygiene checks, 3 passing Lean
  probes, 0 target/full builds, 0 cache operations, 0 materializations, 0
  regeneration writes, 0 repository/Git/state/metrics edits, 0 Git writes, 0
  network/endpoint/GitHub/credential operations, 0 nested dispatches, and 1
  temporary review report.
- Findings: 1 high blocker, 1 medium blocker retaining an old finding, and 1
  low provenance defect. Prior findings independently confirmed fixed: 2/3.
- This report's SHA-256 is returned out of band; embedding it in the file would
  be self-referential.
