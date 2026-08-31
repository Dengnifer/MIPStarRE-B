# QPBT-024 post-gate Lean handoff (a10)

## Verdict

**HOLD all Lean writers now.** At the inspected cutoff, no Lean implementation
issue is dependency-ready. `QPBT-003` is still `blocked`, `QPBT-024` is still
`review`, `QPBT-004` is `planned` with dependencies `QPBT-003` and `QPBT-024`,
`QPBT-023` is `blocked` on `QPBT-003`, and `QPBT-013` is `planned` with
dependencies `QPBT-004` and `QPBT-023`. A successful cache command alone does
not change those authorities.

After the QPBT-024 cache acceptance gate succeeds and the root coordinator has
inspected/imported its evidence, reconciled the already integrated source and
blueprint chain, moved every prerequisite to `done`, and run workflow validation,
the earliest safe issue-level dispatch wave is:

1. `QPBT-023`, the critical-path blueprint/signature contract; and
2. `QPBT-017`, the independent cache-protocol documentation/test lane.

That wave contains **no Lean source writer**. `QPBT-013` must not be issued in
the same wave because `QPBT-023` remains one of its dependencies. The current
DAG makes `QPBT-013` the first actual Lean issue only after `QPBT-023` is done.

For maximum safe Lean parallelism, QPBT-023 should record a root-owned issue-tree
split before QPBT-013 is issued: one child owns F01/`Field.lean`, including the
missing self-dual-normal-basis proof; a second child owns F03/F04/
`Approximation.lean`. These mathematical lanes are independent. F03 must precede
F04 within the approximation lane, and the self-dual-normal-basis theorem must
precede `fieldDataOfOddExponent` within the field lane. If the coordinator does
not approve that split, issue exactly one `QPBT-013` orchestrator/worktree and
allow only disjoint file delegation inside it; do not issue two orchestrators
for QPBT-013.

## Authority snapshot

- Inspected main SHA: `9c9b49548fabdd6b01916787d7dc17a4bca36513`.
- `LPR-014` is approved at exact base `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe`
  and exact head/current main `9c9b49548fabdd6b01916787d7dc17a4bca36513`,
  with zero findings, but its canonical `integration_sha` and `merged_at` remain
  null and QPBT-024 remains `review` pending the post-integration warm gate.
- Main physically contains the approved source/blueprint integration commits:
  LPR-001, LPR-002, and LPR-004 are ancestors, and LPR-004 is recorded merged at
  integration `65315213d047d9181804ad74d573f533c904ef4f`.
- Canonical issue statuses nevertheless still leave QPBT-010 in `review`,
  QPBT-002/QPBT-009/QPBT-003 `blocked`, QPBT-004 `planned`, and QPBT-023
  `blocked`. Those statuses must be reconciled leaf-first; physical ancestry is
  not dispatch authority.
- The canonical session ledger showed only the root coordinator and the three
  QPBT-024 read-only post-warm scouts as running. This is ledger evidence only;
  this scout did not inspect live processes, locks, runtime directories, or
  cache state.

The root must run `python3 scripts/workflow.py validate` before and after its
state changes, then use `python3 scripts/workflow.py ready` and the atomic
capacity-aware dispatcher. Do not infer readiness from the sequence below.

## Required closure sequence after the cache succeeds

All of the following are coordinator actions and conditions, not actions taken
by this scout:

1. Inspect the exact QPBT-024 warm result, READY binding, manifest, deep
   inventory, command identity, main SHA, timing, and no-retry provenance.
2. Import the terminal QPBT-024 session evidence; bind LPR-014's physical
   integration SHA/time; mark LPR-014 `merged` and QPBT-024 `done` only if all
   six acceptance gates are evidenced.
3. Reconcile QPBT-010 -> QPBT-002 -> QPBT-009 -> QPBT-003 leaf-first, using the
   already merged immutable PR and review evidence. Do not skip an open gate or
   convert physical integration into implicit approval.
4. Close QPBT-004 only when QPBT-003 and QPBT-024 are both `done` and the same
   successful authenticated warm proves its recorded Lean/Mathlib/provenance/
   empty-project cache gate. Its merged LPR-005 is necessary but was not by
   itself sufficient.
5. Validate state and compute readiness mechanically. Only then should
   QPBT-023 and QPBT-017 enter `ready` and receive orchestrators.

If any predecessor remains `review`, `blocked`, `planned`, or `in_progress`, the
dependent issue remains non-ready even if its files and proofs appear complete.

## Immediate post-gate dispatch batch

Use the inspected SHA `9c9b495...` as the base only if main has not changed and
the new worktrees are clean exact-base worktrees. If the coordinator commits or
integrates anything first, replace it with the new exact main SHA and re-run the
cache/base checks; never transplant the cache identity across SHAs.

### QPBT-023: critical-path contract orchestrator

- Stable orchestrator name: `i023-orchestrator-a01-leaf-contract`.
- Proposed worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-023-leaf-contract-a01`.
- Branch: `issue/qpbt-023-leaf-contract-a01`.
- Proposed exact owned repository paths (must be copied into the issue/session
  authority before dispatch):

```text
docs/paper-gaps/self-dual-normal-basis.md
blueprint/metadata/nodes.json
blueprint/metadata/gaps.json
blueprint/check.py
blueprint/tests/test_check.py
blueprint/generated/graph.json
blueprint/generated/graph.dot
blueprint/src/generated/chapter-02-entries.tex
blueprint/src/generated/chapter-12-entries.tex
blueprint/src/generated/gaps.tex
```

No Lean source, protocol, canonical workflow state, metrics, or runtime path is
owned. Generated paths are owned only insofar as the deterministic blueprint
generator changes them; the orchestrator must remove any listed path that is
byte-identical rather than manufacture churn. If the chosen checker schema
requires another generated path, the root must amend ownership before the file
is touched.

Acceptance gates:

- Freeze elaborated callable imports/signatures for F01, F03, and F04,
  including universes, finite/decidable instances, question/outcome domains,
  distribution, state carrier, operator adapters, and return/error types.
- Preserve direct `GaloisField 2 k`; no caller-supplied basis, carrier,
  `Hypotheses`, `Assumptions`, bridge, witness, or arbitrary existence input.
- Record the self-dual-normal-basis gap and a concrete proof/source-discharge
  issue without advertising a conditional helper as the paper result.
- Record statement-integrity rows for `FieldData`,
  `fieldDataOfOddExponent`, `fieldTrace`, measurement/projectivity/observable,
  `PureStrategy`, isometry conjugation, finite state-dependent distance, and
  `familyApprox`.
- Pass deterministic blueprint generation/check, source-root validation,
  blueprint tests, declaration synchronization, diff hygiene, workflow
  validation, and an immutable independent blueprint review.
- Before freezing a signature, elaborate a temporary probe against the exact
  pinned project/Mathlib API. Proposals in prior scouts are not elaboration
  evidence.

Nested topology, bounded by the observed four-slot aggregate ceiling:

- `i023-scout-a02-source-integrity`: read-only; paper-to-signature table and
  F01 mathematical/algorithmic split.
- `i023-scout-a03-lean-api`: read-only; exact pinned API/import/signature
  elaboration, especially `Matrix.unitaryGroup`, PMF evaluation, Euclidean
  operator action, adjoint/conjugation, and `GaloisField` trace/basis APIs.
- The orchestrator inspects both reports, then edits the owned contract paths.
- After deterministic validation and a frozen head, use fresh read-only
  `i023-reviewer-a04-blueprint-contract` and
  `i023-reviewer-a05-statement-integrity`. Reviewers may run in parallel only
  if aggregate capacity permits and QPBT-017 is not occupying the slot.

The two scouts are independent. Editing waits for both because the callable
contract must agree simultaneously with paper and Lean. Review is strictly
after validation/head freeze.

### QPBT-017: independent protocol lane

- Stable orchestrator name: `i017-orchestrator-a01-cache-protocol-sync`.
- Proposed worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-017-cache-protocol-a01`.
- Branch: `issue/qpbt-017-cache-protocol-a01`.
- Exact proposed ownership:

```text
protocols/local-development.md
protocols/CHANGELOG.md
tests/test_cache_protocol.py
```

This has zero overlap with QPBT-023. It must not edit
`scripts/hot_main_cache.py`, workflow state, metrics, or Lean. Its acceptance
is the exact recipe/identity/archive documentation, an omission-sensitive
focused regression, changelog evidence, deterministic gates, and one fresh
read-only documentation reviewer. QPBT-017 is useful parallel work but is not
on the Lean critical path. Delay integration if integrating it first would
needlessly advance main and invalidate the accepted cache base before the
QPBT-023 critical-path worktree is seeded/issued.

With root + two orchestrators, only one nested child slot remains under the
currently observed four-slot limit. The issue-level wave is still maximal;
nested scouts/reviewers must be time-sliced unless one orchestrator has already
finished. Neither issue needs a competing main warm. QPBT-017 is docs/test only;
QPBT-023 needs a private seed only if it runs Lean signature probes against the
project tree.

## Paper and API facts the contract must preserve

### F01 field lane

Primary paper anchors:

- `references/2001.04383v3/sections/dependencies/finite-fields.tex:62-83`:
  extension trace, trace-dual/self-dual basis, and normal Frobenius-orbit basis.
- Same file `:243-248`: only `F_(2^k)` with odd `k` is admissible.
- Same file `:283-307`, `lem:efficient_basis`: an algorithm constructs one
  simultaneously self-dual normal basis and multiplication tables for every
  positive odd `k`, citing Shoup, Lenstra, and Wang.

Blueprint anchor F01 is `blueprint/metadata/nodes.json` / generated chapter 02.
It fixes `MIPStarRE.QPBT.Basic.Field`, direct `GaloisField 2 k`, and the names
`FieldData`, `fieldDataOfOddExponent`, and `fieldTrace`, with no abstract carrier
or duplicated caller instances.

The authenticated upstream tree provides no QPBT file. Pinned Mathlib provides
the direct Galois-field instances, extension trace/nondegeneracy, a generic
normal basis, and trace-dual bases. Prior exhaustive pinned-source searches
found no theorem that one basis is both normal and self-dual for odd degree in
characteristic two. `normalBasis` plus `traceDual` does not prove the required
fixed-point/simultaneous property.

Therefore the contract must distinguish:

- mathematical existence/data needed by F01;
- the paper's algorithm and multiplication-table complexity, consumed later by
  K03A; and
- Lean's faithful noncomputable boundary, which may use classical choice only
  after a proved existence theorem, not instead of one.

### F03/F04 approximation lane

Primary anchors:

- `dependencies/measurements.tex:3-19,34-47`: finite POVM, projectivity,
  unitary/binary observable, and exact fiber-sum postprocessing.
- `dependencies/magic-square.tex:147-173` and
  `qpbt/qpbt-game-and-soundness.tex:383-410`: for a projective `F_2`-valued
  measurement the observable is specifically `effect 0 - effect 1`.
- `dependencies/strategies-distance.tex:20-32,213-282`: finite bipartite pure
  strategies, asymptotic state closeness, finite-distribution averaged squared
  POVM distance, and both-player strategy distance.
- `qpbt/appendix-preliminaries.tex:49-53`: the same average for general
  question-indexed operators without an outcome index.

Blueprint F03 fixes the qualified `MIPStarRE.Quantum.Measurement` hierarchy;
the authenticated implementation has PSD `effect`, exact `sum_eq_one`, and
`Measurement.postprocess` as the paper's fiber sum. The separate
`MIPStarRE.LDT.Measurement` hierarchy and density-matrix `QuantumState` are not
definitionally the planned QPBT boundary and must not leak into it silently.

The contract must require projectivity for a certified binary observable, fix
the `ZMod 2` sign order, and not return a unitary from an arbitrary POVM. It
must keep the finite numeric distance (`Real`/nonnegative explicit bound)
separate from the paper's indexed-family `O(delta)` relation; the later bridge
remains a named proof obligation rather than a generic assumption.

## First actual Lean-writing wave

QPBT-023 integration changes main, and the cache key binds the exact main SHA.
Before any new Lean worktree is seeded, run the required singleton post-
integration main warm for the new SHA and verify READY/deep inventory. Do not
reuse the `9c9b495...` cache as if it belonged to the contract-integration SHA.

### Recommended maximal split

The root coordinator should allocate the next available stable issue IDs rather
than hard-code the currently stale sequence counter, convert QPBT-013 into a
tracking parent (or otherwise make the two child completion gates explicit),
and create these two children after QPBT-023 freezes their contracts:

1. **F01 field and self-dual-normal basis**
   - Worktree:
     `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-field-foundation-a01`.
   - Exact ownership: `MIPStarRE/QPBT/Basic/Field.lean` only.
   - Dependencies: QPBT-004 and completed QPBT-023.
   - Source anchors: finite-fields `:62-83,243-248,283-307`, labels
     `sec:finite-fields`, `def:admissible-size`, `lem:efficient_basis`.
   - Acceptance: exact frozen F01 signatures; proved simultaneous basis
     existence before `fieldDataOfOddExponent`; no `sorry`/`axiom`/`constant`
     proof debt or public obligation input; scoped typecheck, debt scan,
     declaration/source check, full private-cache build, immutable mathematical
     review.
   - If the proof genuinely requires a helper module, stop and amend ownership
     before creating it; do not smuggle a new file into this lease.

2. **F03/F04 measurement and approximation foundations**
   - Worktree:
     `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-approximation-foundation-a01`.
   - Exact ownership: `MIPStarRE/QPBT/Basic/Approximation.lean` only.
   - Dependencies: QPBT-004 and completed QPBT-023; no dependency on the F01
     proof issue.
   - Source anchors: measurements `:3-19,34-47`, Magic Square `:147-173`, QPBT
     game `:383-410`, strategy distance `:20-32,213-282`, appendix preliminaries
     `:49-53`; blueprint F03/F04.
   - Acceptance: exact frozen F03 then F04 declarations, qualified Quantum
     measurement API, certified projective binary observable, normalized pure
     strategy and explicit adapters, exact finite squared-distance/bound API,
     no proof debt, scoped typecheck, debt scan, declaration/source check, full
     private-cache build, immutable mathematical/API review.

The two worktrees and owned paths are disjoint and can be dispatched in the same
capacity-aware wave after both are mechanically ready. Each receives a private
cache seed. Never share a writable `.lake/build`, and do not let the two agents
compile in one worktree.

Suggested topology per child:

- one issue orchestrator/integration owner;
- one read-only source/API scout first;
- one prover for the single owned file after the scout result is inspected;
- the orchestrator runs the registered validation ladder and freezes the head;
- one fresh read-only mathematical/API reviewer, followed by a completion audit
  if required.

Under a four-slot ceiling with the root running, dispatch both orchestrators and
at most one nested child at a time. The field and approximation orchestrators
may implement directly while the sole nested scout slot is assigned to the
higher-risk field theorem. Reviewer waves occur only after each corresponding
head is validated and frozen.

If the issue-tree split is rejected, the fallback is one
`i013-orchestrator-a01-leaf-foundations` in
`.../worktrees/qpbt-013-leaf-foundations-a01`, owning exactly the two currently
recorded files. It may delegate `Field.lean` and `Approximation.lean` to disjoint
provers, but all Lean/Lake commands in that shared worktree must be serialized.
The same F01 proof blocker remains; a conditional helper cannot satisfy the
no-proof-debt acceptance gate.

## Sequential downstream lane

Do not dispatch these in parallel merely because their files differ:

```text
F01 + F03/F04 complete
  -> close QPBT-013 tracking result
  -> QPBT-014 (Polynomial, Pauli, Types, Parameters)
  -> QPBT-015 (MagicSquare, Verifier)
  -> QPBT-016 (Extraction, Soundness, declared root-import sync)
```

QPBT-014 consumes the frozen field/measurement interfaces. QPBT-015 consumes
QPBT-014's algebra and typed-game surface. QPBT-016 consumes the game surface.
Those dependency edges require sequential writable issues. Read-only paper,
Mathlib, or API scouts can be prepared ahead of each transition, but no later
writer is ready until its predecessor is `done`.

## Validation envelopes

For QPBT-023, register exact commands rather than paraphrases, including at
least:

```text
python3 blueprint/check.py --check
python3 blueprint/check.py --check --source-root references/2001.04383v3
python3 -m unittest discover -s blueprint/tests -p 'test_*.py'
python3 scripts/workflow.py validate
git diff --check <BASE>..<HEAD>
```

Add the exact temporary Lean signature-probe command to its session/PR evidence
after the contract orchestrator chooses the probe path. The current materialized
source has `sections/READY`; source-root validation must bind that authenticated
split, not an arbitrary TeX directory.

For each Lean child, register the exact changed-file command, proof-debt scan,
blueprint/source checks, affected target command, and full build. The minimum
ladder is:

```text
lake env lean MIPStarRE/QPBT/Basic/Field.lean
lake env lean MIPStarRE/QPBT/Basic/Approximation.lean
rg -n '\bsorry\b|\badmit\b|^\s*(axiom|constant)\b' <OWNED_PATHS>
python3 blueprint/check.py --check
python3 blueprint/check.py --check --source-root references/2001.04383v3
lake build
python3 scripts/workflow.py validate
git diff --check <BASE>..<HEAD>
```

Each child registers only its own changed-file typecheck from the first two
lines. The debt scan must distinguish source comments from declarations and
must fail on any real owned proof debt. Full build runs only after scoped files
are stable, from that issue's private seeded cache. Reviews begin only after all
registered deterministic checks pass.

## Provenance inspected

Source-first inspection used the materialized pinned v3 fragments under
`references/2001.04383v3/sections/`, including finite fields, measurements,
strategies/distance, Magic Square, QPBT game/soundness, and Appendix A
preliminaries. Blueprint inspection used chapters 02/03/11/12, generated chapter
02 entries, `metadata/nodes.json`, `metadata/gaps.json`, and prior QPBT-023/013
contract scouts. Lean inspection used the authenticated MIPStarRE archive at
commit `507e81220d95266ff3d589d125b2f87c7300a9fb`, read without extraction,
especially `Quantum/Measurement.lean`, `Quantum/FiniteMatrix/Basic.lean`, and
the distinct LDT state/distribution/measurement APIs. Project pins are Lean
`v4.32.0`, Mathlib revision
`81a5d257c8e410db227a6665ed08f64fea08e997`, and the exact nine-package
`lake-manifest.json`.

## Session accounting

- Logical session: `i024-scout-a10-lean-handoff`.
- Topology: root coordinator -> this fresh read-only scout; 0 subagents; depth
  1 below root.
- Start: `2026-09-01T01:01:39.259658292+08:00`.
- End/evidence cutoff: `2026-09-01T01:15:13.673069419+08:00`.
- Exact elapsed through cutoff: `814.413411127` seconds.
- Repository edits, Git writes, tests, builds, Lean/Lake commands, network,
  source materialization, cache status/warm/seed, live runtime/cache/process/
  lock inspection, and subagent launches: 0. One initial broad repository
  directory enumeration displayed top-level runtime directory names; no runtime
  file, cache key, lock, process, or live state was opened or inspected.
- Output: this one `/tmp` report.
- Token usage: JSON `null`; availability reason: the collaboration backend does
  not expose per-agent token usage. No estimate was made.
- Report SHA-256: supplied to the coordinator out of band after finalization,
  because embedding an ordinary file's own digest would change that digest.
