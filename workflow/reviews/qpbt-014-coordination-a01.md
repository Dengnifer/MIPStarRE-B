# QPBT-014 coordination (A01)

## Result

QPBT-014 remains open and its Types lane is still blocked. The contract and
three independent Lean leaves are complete, but QPBT-038 cannot advance until
the repaired QPBT-057 F06A candidate is committed, independently reviewed, and
integrated. QPBT-040 remains a planned singleton gate and must run only after
QPBT-058 adds F07 to the same `Types.lean` history.

This report is coordination evidence only. It does not change canonical issue,
PR, session, or metrics state.

## Child disposition

| Issue | Status | Evidence / next gate |
| --- | --- | --- |
| QPBT-035 | done | LPR-023 merged; frozen 54-node contract and exact F02/F05/F06/F07/G01 markers. |
| QPBT-036 | done | LPR-027 head `8467454fefefdbac7478a2df8f8c1e2d9c25fcf5`; independent review had no findings. |
| QPBT-037 | done | LPR-032 head `cdb83f4017cfc182eb2611be0fbc5cd3635fbf64`; independent review had no findings. |
| QPBT-039 | done | LPR-028 head `f6b19fc9fb87e0616b8367749ff971539bc1b45f`; independent review had no findings. |
| QPBT-056 | done | LPR-033 head `c1bfd95226e0c068f7d818689f56ab41088ff545`; F06 is integrated and proof-complete. |
| QPBT-057 | planned / review pending | Rebased candidate head `81d092630b24dedd810c1cec4272f709702090f0`, tree `10642869c5f94c70b5245f882ed79db2eadba4a2`, based on `038d878`; Types SHA `6fbc0982...`, report SHA `0db7dd00...`, exactly two authorized theorem-body sorries. Fresh immutable review remains required. |
| QPBT-058 | planned | Must extend the reviewed QPBT-057 file with exactly the 11 F07 names; sole serialized Types writer. |
| QPBT-038 | blocked | Requires reviewed/integrated QPBT-057, then QPBT-058, followed by the 81-name Types gate. |
| QPBT-040 | planned | Depends on QPBT-036/037/038/039; root-only combined integration/build owner. |

The rejected historical QPBT-057 head `a9abedb3d08d1b020d310075fc2865ae21397eb8`
is not usable: its merge base is `20745fe`, not the declared review base, and
its patch deletes unrelated canonical history. The fresh A06 review therefore
requested reconstruction. The repaired candidate preserves the required four
imports and 56-name surface; its writer report records scoped, target, full,
blueprint, workflow, and diff checks passing. It is not integratable until the
fresh immutable review gate closes.

## Attempt ledger inspected

| Attempt | Outcome used for coordination |
| --- | --- |
| `i038-orchestrator-a01-types` / `i038-orchestrator-a03-types` | Rejected zero-map candidate and compiler blocker retained as negative evidence; no public weakening permitted. |
| `i038-scout-a14-types-integration` | Confirmed serialized F06 -> F06A -> F07 DAG and singleton combined-build checklist; QPBT-057 not integratable before fresh review. |
| `i057-reviewer-a06-source-fidelity` | High finding: stale base and unrelated deletions; required reconstruction. |
| `i057-scout-a06-resource-selection` | Required a private cost-carrying compiler package so the selected witness can support `downsize_time`. |
| `i057-orchestrator-a02-types-rebase` | Reconstructed candidate from current base; writer checks pass, exact two Stage-4A holes; fresh review pending. |
| `i056-reviewer-a03-f06` | F06 proof-complete candidate accepted with no findings; inherited G16 debt remains outside the Types lane. |

## Required sequence

1. Authenticate QPBT-057 head `81d092630b24dedd810c1cec4272f709702090f0`,
   tree `10642869c5f94c70b5245f882ed79db2eadba4a2`, sole-parent/base, exact
   `Types.lean` plus report paths, the
   QPBT-059 marker `368008b7b4ba84ff1dafe842acdb8af7005902a0fe9a376a8f7a690c86ba6b15`,
   four-import union, 56 declarations, dual-rail codec, and exactly the
   `downsizeCompiler_exists` / `downsize_time` holes authorized by QPBT-060.
2. Obtain a fresh immutable mathematical/API review. The reviewer must check
   the private compiler selector carries a proved cost bound; unrestricted
   `Classical.choice` from the stale candidate is specifically disallowed.
3. After approval, root performs guarded integration. Only then may the sole
   QPBT-058 writer extend that same file with the 11 F07 declarations and run
   its scoped/target/full/review gates.
4. After QPBT-058 approval and integration, root runs QPBT-040 exactly once on
   a clean private integration worktree. Authenticate all candidate heads and
   blobs, verify 14 + 56 + 11 = 81 names and the four-import union, run the
   four scoped checks and four target builds, synchronize blueprint/source,
   scan debt (only the two F06A Stage-4A holes in Types, plus inherited F01 and
   Pauli blueprint debt), and perform one combined `lake build` through the
   singleton hot-main cache protocol.

QPBT-061 is a later Stage-4C proof-completion issue. It must not be pulled into
the Stage-4A API or used to broaden public assumptions while QPBT-038 is being
unblocked.

## Statement-integrity and ownership gates

The source-faithful boundaries are unchanged: F02 Boolean coordinate indices
remain distinct from field evaluation points; F05 retains the twisted trace
phase and G09 order; F06 uses one shared uniform seed and exact PMF transport;
F06A owns the generic executable six-input layer and its two declared Stage-4A
holes; F07 permits arbitrary dependent question/answer fibers without adding
pointwise finiteness; and G01 keeps the exact odd-exponent/equality/divisibility
conjunction. No child may add a public bridge, residual, repair, witness,
package, producer, generic `Hypotheses`/`Assumptions`, axiom, constant, or
untracked `sorry`.

## Topology and metrics

Topology is root coordinator -> QPBT-014 orchestrator, with the existing
serialized QPBT-057 repair lane. No nested child was launched by this session.
The coordination session performed read-only source/state/review inspection;
it did not run Lean, Lake, builds, cache/materialization, network, endpoint,
GitHub, or credential operations, and made no canonical state/metrics edits.
Token usage is `null` because the collaboration backend does not expose
per-agent usage; no estimate is substituted. Session elapsed time is likewise
not exposed. The report is the sole owned path.

## Acceptance checklist for root

- [ ] QPBT-057 repaired candidate committed from exact current base.
- [ ] Fresh immutable QPBT-057 review approves unchanged head.
- [ ] Guarded QPBT-057 integration complete; then QPBT-058 writer/review.
- [ ] QPBT-040 authenticates all four child heads and runs the singleton
      combined build with exact debt and source/declaration synchronization.
- [ ] Root updates canonical issue/session/PR ledgers only after each gate and
      closes QPBT-014 only when QPBT-040 passes.
