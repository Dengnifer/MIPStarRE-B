# QPBT-035 follow-on issue graph retry review (A10)

Canonical session: `i035-reviewer-a10-followon-issue-graph`

## Findings

1. **High - the proposed QPBT-006 parenting is not fail-closed under the
   current validator.** A09 moves QPBT-042 and QPBT-043 under QPBT-006 and calls
   that hierarchy stronger, while also acknowledging that closure remains only
   procedural (`/tmp/qpbt-035-issue-graph-a09.md:7-12,140-148`). Canonical
   QPBT-006 is `kind: formalization`, not `tracking`
   (`workflow/state/issues.json:326-343`). The validator requires completed
   direct children only when the parent kind is exactly `tracking`
   (`scripts/workflow.py:941-952`). Therefore QPBT-006 can currently be marked
   done while either proposed child is unfinished. Preferred repair: change
   QPBT-006 into the tracking milestone its title and acceptance already
   describe, add an explicit all-direct-children-done gate, and then parent
   QPBT-042/QPBT-043 beneath it. If that state change is not accepted, retain
   flat QPBT-000 parenting for QPBT-042/QPBT-043; QPBT-000 is tracking and is
   the only proposed parent that mechanically prevents premature final
   closure. Merely amending QPBT-006 prose is insufficient.

2. **Medium - the proposed acceptance scope crosses the declared skeleton and
   proof stages and lengthens the QPBT-042 critical path.** A09 places
   QPBT-041 in Stage 04A but requires the proof-complete
   F04-DISTANCE-LAWS surface (`/tmp/qpbt-035-issue-graph-a09.md:41-60`), even
   though F04A depends only on F04-CONSISTENCY and S01's transitive-definition
   closure contains the three F04 definition nodes, not F04-DISTANCE-LAWS
   (`.workflow-runtime/worktrees/qpbt-035-q014-contract-a01/blueprint/metadata/nodes.json:258-305,1025-1042`). It also assigns all F07A theorem clauses to
   QPBT-043 in Stage 04B under an undifferentiated proof-debt gate
   (`/tmp/qpbt-035-issue-graph-a09.md:99-125`). The canonical stage protocol
   says the minimal skeleton need not expose intermediate theorem statements,
   the complete skeleton may use tracked `sorry`, and proof completion belongs
   to the proof stage (`protocols/formalization.md:53-65`). Keep QPBT-041's
   dependency-critical Stage-04A acceptance on the F04 definition chain needed
   by F04A; do not make proof of F04-DISTANCE-LAWS a prerequisite for
   QPBT-042. Add the law declarations in a later sequential same-file
   Stage-04B issue and discharge them in Stage 04C, or explicitly document a
   deliberate proof-ahead exception if the proof is retained in QPBT-041.
   Likewise, QPBT-043 should require all source-faithful definitions and
   theorem *statements* to type-check, allow only their individually tracked
   skeleton `sorry` bodies, and leave their proofs to a QPBT-007 child. It must
   continue to forbid axioms, constants, generic obligations, and hidden
   assumptions.

## Verdict

**Changes requested** for the A09 graph as written. The dependency edges and
single-file ownership are correct; the parent choice is approved only with the
QPBT-006 tracking conversion, and the issue acceptance must respect the three
Lean implementation stages.

The smallest milestone-aligned graph is:

| Issue | Parent | Direct dependencies | Unique stage | Sole owned path |
| --- | --- | --- | --- | --- |
| QPBT-041 | QPBT-005 | QPBT-032 | STAGE-04A | `MIPStarRE/QPBT/Basic/Approximation.lean` |
| QPBT-042 | QPBT-006, after converting QPBT-006 to tracking | QPBT-035, QPBT-041 | STAGE-04B | `MIPStarRE/QPBT/Game/Semantics.lean` |
| QPBT-043 | QPBT-006, after converting QPBT-006 to tracking | QPBT-038, QPBT-042 | STAGE-04B | `MIPStarRE/QPBT/Game/Detyping.lean` |

If QPBT-006 remains a formalization issue, replace the last two parents with
QPBT-000. Do not parent any of the three beneath QPBT-014: its accepted child
wave is exactly QPBT-035 through QPBT-040, and neither F04A nor F07A is in the
minimal theorem-type closure.

QPBT-041's Stage-04A unit should expose the accepted F04-DISTANCE,
F04-ASYMPTOTIC, and F04-CONSISTENCY definitions needed by F04A. A later
same-file issue may add F04-DISTANCE-LAWS statements during Stage 04B and a
later QPBT-007 proof child may discharge them during Stage 04C. Sequential
reuse of that sole path is compatible with the ownership protocol and lets
QPBT-042 start as soon as its actual prerequisite is integrated.

## QPBT-035 edge audit

| Issue | QPBT-035 edge | Decision |
| --- | --- | --- |
| QPBT-041 | absent | Correct. QPBT-032 is done, the four accepted F04 metadata objects are byte-semantically unchanged between base and candidate, and `Approximation.lean` is unchanged. Adding QPBT-035 would be a false serialization edge. |
| QPBT-042 | direct | Required. F04A and its callable ownership are absent at main and introduced only by candidate c35; without this edge the issue becomes ready before LPR-023 is accepted and integrated. |
| QPBT-043 | absent | Correct and required for a transitive reduction. QPBT-038 directly depends on QPBT-035, and QPBT-042 must directly depend on QPBT-035. A third edge adds no readiness guarantee. |

No other direct QPBT-035 edge is required. QPBT-043 also does not need direct
QPBT-041, F03, F04, or F06 issue edges: QPBT-042 supplies the F04/F04A chain,
and QPBT-038 supplies F06/F07.

## Readiness and parallelism

QPBT-041 is dependency-ready now. Canonical QPBT-032 is done, the current
`Approximation.lean` bytes are the integrated QPBT-032 slice, and at the
inspection cutoff no active writable non-coordinator session owned that path.
QPBT-035 owns only blueprint/checker/generated paths, so its read-only review
can overlap a QPBT-041 worktree without writable overlap. STAGE-04A is active
with maximum concurrency four. QPBT-041 should branch from authenticated main
and use the singleton hot-main cache protocol when it later compiles.

QPBT-042 is not ready until both QPBT-035 and QPBT-041 are done. QPBT-043 is not
ready until QPBT-038 and QPBT-042 are done. Before either Stage-04B writer is
actually dispatched, root must transition STAGE-04B from planned to active and
assign nonzero capacity; adding planned issue membership does not itself start
the stage.

## Independent source and blueprint checks

- The exact canonical projection of F04-DISTANCE, F04-ASYMPTOTIC,
  F04-CONSISTENCY, and F04-DISTANCE-LAWS has SHA-256
  `420187eeee16812a9b0b46f88cf2ccda416d8081ed5088039eae8da183ee31da`
  in both main and candidate. `MIPStarRE/QPBT/Basic/Approximation.lean` is also
  identical in both snapshots at SHA-256
  `13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a`.
  This independently rules out a QPBT-035 dependency for QPBT-041.
- Candidate F04A has exactly one blueprint prerequisite,
  F04-CONSISTENCY. The pinned game source defines the finite game/value layer
  at `strategies-distance.tex:4-51`, projective/symmetric predicates at
  `:62-81`, and support commuting/consistency/PCC/SPCC/Schmidt-rank/Ent at
  `:126-190`.
- Candidate F07A has exactly two blueprint prerequisites,
  F04A-GAME-SEMANTICS and F07-TYPED. The pinned source defines typed
  verifier/game data at `types.tex:197-220`, graph simulation at `:234-357`,
  detyping constructions at `:359-442`, and the theorem statement/proof at
  `:444-579`. This supports exactly QPBT-038 plus QPBT-042 as its direct issue
  dependencies.
- F04A and F07A are absent from every candidate required target spine and from
  S01's transitive definitions; they therefore belong to the complete
  declaration skeleton, not Stage 04A. F04-DISTANCE-LAWS is in the soundness
  proof spine but is not a transitive definition of S01 or F04A.

## Authentication and validation

- Main reference and loose object independently authenticated as
  `b4f73876cc491025275c5a05bb6ca2e41aaf09ee`, tree
  `26775cf61ac23bab84d41e459b9fb9c86f634592`, parent
  `612037fb6527d93eed387fbe616ff3217798acae`.
- Candidate worktree reference and loose object independently authenticated as
  `c35fcd36bea96705851655852eabc78ca9db9b3f`, tree
  `86d8ca78d3e4bb5fe89d57f25c2bea539d4c8100`, parent
  `3f2630a7631a0164b6ef4aca1fd081ba264beeb2`.
- Main/candidate `nodes.json` SHA-256 values:
  `2a284ff65180a5ffd360ecb6eeab72cf8654041c347df82c2d88000a2060c328`
  and `102d365e28f59c6565b5b65b246c2cf546c3299a4f66086c841a746cc2cd1a90`.
  Their exact tree blobs are respectively
  `e869d2d10ac074c24712c409a5a6c8b492c0a486` and
  `2f1fce7a4c2a56910fac7b4aa6a3ba8c63125d25`; filesystem bytes matched both
  objects. Main and candidate `Approximation.lean` both matched exact blob
  `b3eb1b1eee2860b83b71659add650b9ff3e8ed4c`.
- Pinned source SHA-256 values: strategies-distance
  `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f`;
  types `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c`.
- Untrusted input report SHA-256 values: A09
  `b00b9a986624270d307beabd00e93cea759f14a6f3cadce231350ffe15551e83`;
  A05 `de9c4c87820f76c8162f7d2f06bbcd0a66a6ed14cc8d57ed2c6d1414bccd81fb`;
  A07 `f98f21f7a9f355ca2f2af4e8ef20a3390f995430d045427b79b1c1a7ed93e1e8`;
  A08 `f37ab823449c85b078330f3912b4ec8eedfc67b8c9ffedb1d1b261434ccc4b27`.
- Workflow/semantics authority SHA-256 values: `scripts/workflow.py`
  `04e0d92a5f52949322a4c5089269cc9f223b0e32f3ca36c3b6b6651ded0b02ab`;
  `protocols/formalization.md`
  `fc2efd891f7dcc3b43ed82f0235d7abbec97d74af35d44f61fa35f9e58639079`.
- Canonical state SHA-256 values at the evidence cutoff: issues
  `d966786a3e90ab32386c0543b5ced9020e72a290e908fa35644a381e27de9219`;
  stages `4c251612eb442c08a4882ea67f16df462a7fb4f2fcbb1f74ad2b15d82cb8f988`;
  PRs `94aeac27b68cc37db50bef3b91df20b19d31dced698b17b14ae07ba378631672`;
  sessions `7896a6e2cdf6639a048824ea3a37b84a5e9c42c1d2464f88dc242297815e70cd`.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate` passed at
  the inspected state with 42 issues, 23 local PRs, 391 issued sessions, and
  seven stages. No proposed state mutation was performed.

## Metrics

- Agent-measured elapsed from review timing baseline through the final evidence
  cutoff: `809.103522019` seconds.
- Token usage: `null`; availability reason: the collaboration backend does not
  expose per-session token counts.
- Topology: root coordinator -> one fresh read-only retry reviewer; zero nested
  agents and zero subagents dispatched.
- Findings: 2 (one high, one medium). Reviews: 1. Workflow validations: 1.
  Raw loose-object commit authentications: 2; exact tree-path blob/filesystem
  authentications: 4. Lean commands: 0. Build
  commands: 0. Cache commands: 0. Network/endpoint operations: 0. Git command
  invocations: 0. GitHub operations: 0. Repository/Git/state/metrics writes: 0.
  Temporary reports written: 1. No credentials were read or transmitted.
- The report SHA-256 is returned out of band; embedding it in the report would
  be self-referential.
