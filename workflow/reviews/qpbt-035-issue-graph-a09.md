# QPBT-035 follow-on issue graph scout (A09)

Canonical session: `i035-scout-a09-followon-issue-graph`

## Decision

Use three single-file implementation issues, but do not retain A08's flat
`QPBT-000` parenting. Keep every issue outside QPBT-014 so its accepted
QPBT-035-through-QPBT-040 closure remains unchanged. Parent QPBT-041 under the
minimal-skeleton tracker QPBT-005, and parent QPBT-042 and QPBT-043 under the
complete-declaration issue QPBT-006. This is the smallest hierarchy that maps
the work to the milestone it completes.

The implementation dependency chain remains A08's substantive chain:

```text
QPBT-032 -> QPBT-041
QPBT-041 -> QPBT-042
QPBT-035 -> QPBT-042
QPBT-038 -> QPBT-043
QPBT-042 -> QPBT-043
```

More precisely, QPBT-035 is a direct dependency only of QPBT-042. QPBT-043
inherits it through both QPBT-038 and QPBT-042; a third direct edge would be
redundant. QPBT-041 does not depend on QPBT-035 because its four F04 contracts
were already reviewed and integrated by QPBT-023 and are unchanged by
candidate `c35fcd36bea96705851655852eabc78ca9db9b3f`.

## Proposed records

### QPBT-041

```yaml
title: "feat(QPBT/Basic): complete finite strategy and consistency semantics"
kind: formalization
execution_category: implementation
status: ready
parent_id: QPBT-005
dependency_ids: [QPBT-032]
stage_id: STAGE-04A
owned_paths:
  - MIPStarRE/QPBT/Basic/Approximation.lean
source_refs:
  - blueprint/metadata/nodes.json#F04-DISTANCE
  - blueprint/metadata/nodes.json#F04-ASYMPTOTIC
  - blueprint/metadata/nodes.json#F04-CONSISTENCY
  - blueprint/metadata/nodes.json#F04-DISTANCE-LAWS
  - workflow/reviews/qpbt-023-leaf-contract-a04.md
```

Acceptance must preserve the integrated F03 declarations and implement every
remaining reviewed F04 callable in the same sole file, without reopening the
signatures or adding `sorry`, `axiom`, `constant`, an obligation input, or a
generic bridge assumption. Require scoped Lean, target and one private full
build, declaration/source synchronization, debt/assumption scans, and a fresh
immutable review.

Reason for Stage 04A: candidate metadata's required soundness spine contains
F04-DISTANCE, F04-ASYMPTOTIC, F04-CONSISTENCY, and F04-DISTANCE-LAWS, and
S01's transitive definitions contain the first three. The current file is the
completed F03-only QPBT-032 slice. Because QPBT-032 is done and no active issue
owns this path, QPBT-041 is dependency-ready and can run in parallel with the
QPBT-035 review.

### QPBT-042

```yaml
title: "feat(QPBT/Game): implement finite game and strategy semantics"
kind: formalization
execution_category: implementation
status: planned
parent_id: QPBT-006
dependency_ids: [QPBT-035, QPBT-041]
stage_id: STAGE-04B
owned_paths:
  - MIPStarRE/QPBT/Game/Semantics.lean
source_refs:
  - blueprint/metadata/nodes.json#F04A-GAME-SEMANTICS
  - references/2001.04383v3/sections/dependencies/strategies-distance.tex:4-51,62-81,126-190
  - workflow/reviews/qpbt-035-game-semantics-api-a08.md
```

Acceptance must implement all 18 F04A callables, import the QPBT-041
`PureStrategy` and exact consistency APIs rather than duplicating them, and
preserve support-relative commutation, PCC/SPCC, matrix-rank Schmidt rank,
real `sSup`, and `WithTop Nat` `sInf`. Apply the same no-proof-debt and full
validation/review gates as QPBT-041.

QPBT-035 must be explicit here. Candidate c35 introduces the F04A node and
callable ownership; without this edge, QPBT-042 becomes mechanically ready as
soon as QPBT-041 finishes even if LPR-023 is still unreviewed or unintegrated.
Timing is not a dependency protocol.

Reason for Stage 04B: F04A is absent from every candidate required target
spine and its only direct consumer is F07A. It is part of the complete
declaration skeleton, not the minimal theorem-type closure.

### QPBT-043

```yaml
title: "feat(QPBT/Game): formalize graph simulation and verifier detyping"
kind: formalization
execution_category: implementation
status: planned
parent_id: QPBT-006
dependency_ids: [QPBT-038, QPBT-042]
stage_id: STAGE-04B
owned_paths:
  - MIPStarRE/QPBT/Game/Detyping.lean
source_refs:
  - blueprint/metadata/nodes.json#F07A-DETYPING
  - references/2001.04383v3/sections/dependencies/types.tex:197-579
  - workflow/reviews/qpbt-035-detype-source-a05.md
  - workflow/reviews/qpbt-035-game-semantics-api-a08.md
```

Acceptance must implement all 20 candidate F07A callables: typed verifier/game
formation, graph simulation and both event conclusions, all detyping
constructions, completeness, the exact `16^|Type|` soundness/entanglement
loss, level `ell+2`, dimension `4|Type|+s(n)`, and each runtime/description
clause in an explicit faithful executable model. No public obligation may
replace any theorem clause. Require the standard scoped, target, singleton
private full-build, synchronization, debt, and fresh source-fidelity review
gates.

QPBT-038 supplies F06/F07 and QPBT-042 supplies F04A, including its transitive
F04 foundation. No direct QPBT-035, QPBT-041, F03, F04, or F06 issue edge is
needed. F07A is also absent from the minimal target spines, so Stage 04B is the
correct unique stage mapping.

## Departure from A08

A08's dependency substance is retained, with one fail-closed addition:
QPBT-042 explicitly depends on QPBT-035. Its flat-root parenting is not
retained. A08's stated reason was to keep QPBT-014 closable after its accepted
QPBT-035-through-QPBT-040 wave; parenting QPBT-041 under sibling QPBT-005 and
QPBT-042/043 under QPBT-006 satisfies that same constraint.

This hierarchy is stronger because QPBT-005 is a `tracking` issue whose
acceptance requires every definition used transitively by the minimal theorem
type. The workflow validator only enforces child completion for issues whose
kind is `tracking`; making QPBT-041 its direct child prevents the minimal
milestone from closing while F04 is absent. QPBT-006's title and acceptance
own every blueprint declaration, so F04A and F07A belong beneath it. Root
should amend QPBT-006's acceptance text to name QPBT-042/043 before eventual
closure; because QPBT-006 currently has kind `formalization`, that closure
check remains procedural rather than validator-enforced.

## Risks and scheduling notes

1. Do not dispatch QPBT-042 from candidate metadata alone. LPR-023/QPBT-035
   must be reviewed, integrated, and done first.
2. QPBT-041 reuses a path previously owned by completed QPBT-032. Sequential
   reuse is valid, but preserving F03 behavior and authenticated bytes is an
   explicit review gate.
3. An issue may map to exactly one stage. Add QPBT-041 only to STAGE-04A and
   QPBT-042/043 only to STAGE-04B; update each stage's issued-session metrics
   only when an actual session dispatch occurs.
4. Stage 04B may overlap Stage 04A after the exact dependencies complete. That
   is safe and improves throughput because the three writable paths are
   disjoint. It does not justify bypassing QPBT-035 or QPBT-041.
5. Candidate F04A/F07A metadata has no implementation-contract block, so the
   issue acceptance and immutable A08/A05 manifests are the binding API/source
   gates until an independently reviewed elaborated contract exists.

## Authentication and metrics

- Main inspected: `b4f73876cc491025275c5a05bb6ca2e41aaf09ee`, tree
  `26775cf61ac23bab84d41e459b9fb9c86f634592`.
- Candidate inspected: `c35fcd36bea96705851655852eabc78ca9db9b3f`, tree
  `86d8ca78d3e4bb5fe89d57f25c2bea539d4c8100`, parent
  `3f2630a7631a0164b6ef4aca1fd081ba264beeb2`.
- State SHA-256 values at inspection: issues
  `ddda9a3042b3f5a28f693dc3fcabb32474ac024b2c66f913ab929de2f26236b3`,
  stages `fe77637d8a518c1173ede411ee7dcd4da9ce0242b3bddbce9ef7727375e5b231`,
  PRs `94aeac27b68cc37db50bef3b91df20b19d31dced698b17b14ae07ba378631672`.
- A08 report SHA-256:
  `f37ab823449c85b078330f3912b4ec8eedfc67b8c9ffedb1d1b261434ccc4b27`.
- A07 report SHA-256:
  `f98f21f7a9f355ca2f2af4e8ef20a3390f995430d045427b79b1c1a7ed93e1e8`.
- Agent-measured elapsed to report-finalization cutoff: `448.458070032`
  seconds.
- Token usage: `null`; availability reason: the collaboration backend does
  not expose per-session token counts.
- Subagents dispatched: 0. Repository files written: 0. Temporary reports
  written: 1. Lean commands: 0. Build commands: 0. Cache commands: 0. Network
  operations: 0. Git/GitHub writes: 0.
- Follow-up authentication note: the root coordinator requested replacement
  of the full main SHA, then withdrew that request before canonical acceptance
  after the local object check confirmed the original full SHA above. The
  follow-up changed only the dependency diagram and this note. Incremental
  elapsed to correction cutoff: `46.436025320` seconds; additional subagents,
  repository writes, Lean/build/cache/network commands, and Git/GitHub writes:
  all 0; temporary report edits: 1.
- The immutable report SHA-256 is returned out-of-band to the root coordinator;
  embedding a file's own digest in the bytes being hashed is self-referential.
