# QPBT-039 admissible parameters implementation (A01)

Session: `i039-orchestrator-a01-parameters`

External identity: `/root/i039_orchestrator_a01_parameters`

## Findings

1. **Process incident, coordinator action required:** before detecting the
   assigned issue worktree, this session created an untracked duplicate at
   `/home/drx/MIPStarRE-auto/MIPStarRE/QPBT/Game/Parameters.lean`.  The root
   coordinator instructed this session not to delete or overwrite either copy.
   All candidate edits, builds, and the commit below were subsequently made
   only in
   `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-039-parameters-a01`.
   The candidate commit contains no canonical workflow or metrics paths.
2. **Non-blocking inherited proof debt:** target builds replay
   `MIPStarRE/QPBT/Basic/Field.lean:24` and report its existing tracked `sorry`
   for G16.  The owned G01 file contains no `sorry`, `axiom`, `constant`, or
   public obligation input, and `Parameters.Admissible` does not expose or
   consume a field witness.
3. **Candidate findings:** none.  The declaration surface, import, quantifier
   order, conjunction order, and natural divisibility relation match the
   authenticated G01 contract exactly.

Verdict: `ready_for_review`.  The candidate is source-faithful and all final
candidate gates pass.  The root coordinator must reconcile the untracked
canonical-root duplicate before integration.

## Candidate authentication

| Field | Value |
| --- | --- |
| Candidate commit | `f6b19fc9fb87e0616b8367749ff971539bc1b45f` |
| Candidate tree | `19df34c6a5687eff9bf64611c8880e45b3ea4339` |
| Parent / immutable base | `874dc07433936e26d62c42cdd779dde42386f99d` |
| Commit count from base | `1` |
| Changed path | `MIPStarRE/QPBT/Game/Parameters.lean` |
| Git blob | `f9d65fc4a468997f93b95cb380d780bce46aed25` |
| File SHA-256 | `2f749aca171739bf57d4a7945fbdbdc55bdaf83418a4cabe1a6582520b3ec2e5` |
| One-path manifest SHA-256 | `4a26a5faf9611c9e689ef03e253f5a4fbfe164d92ac86288eed3aac2422df539` |

The one-path manifest hash is SHA-256 of the exact UTF-8 output of
`git diff-tree --no-commit-id --name-only -r f6b19fc9fb87e0616b8367749ff971539bc1b45f`,
namely `MIPStarRE/QPBT/Game/Parameters.lean` followed by one LF.

The worktree was clean immediately after candidate commit creation and before
this required immutable report was written.  This report is intentionally not
part of the one-path candidate commit.

## Source and contract

- Pinned paper: `references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex:60-63`,
  label `def:admissible`.
- Blueprint node: `blueprint/metadata/nodes.json#G01-PARAMETERS`.
- Exact signature contract:
  `workflow/reviews/qpbt-035-q014-contract-a02.md`, markers
  `BEGIN G01-SIGNATURES` / `END G01-SIGNATURES`, SHA-256
  `587cb393eff88db0291303da834e483e13f44eda8c2c286e2ab48721120386cb`.
- Release packet referenced a nonexistent intermediate
  `sections/dependencies/qpbt/` path and named the A07 report.  The authenticated
  metadata identifies the extant paper path above and the A02 marker file; A07
  preserves that G01 contract unchanged.
- Reused API: `Odd`, natural exponentiation `2 ^ k`, and
  `Dvd.dvd params.m params.q`.

No material paper ambiguity or paper gap was found.  The paper defines an
admissible tuple `(q,m,d)` by admissible field size and `m | q`; the pinned
field-size definition expands this to an odd natural exponent and exact power
of two.  The parameter `d` is intentionally not constrained by this definition.

## Statement integrity

| Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| A tuple `(q,m,d)` | One project-owned `Parameters` value with natural fields `q`, `m`, and `d` | Admissible iff `q=2^k` for an odd `k` and `m | q` | `Exists fun k : Nat => Odd k ∧ params.q = 2 ^ k ∧ Dvd.dvd params.m params.q` | exact |

The implementation adds no positivity premise, field witness, LDT alias or
coercion, bridge, residual, repair, witness package, generic assumptions, or
arbitrary implication input.

## Validation

Final successful gates:

| Command | Result | Measured wall time |
| --- | --- | --- |
| `lake env lean MIPStarRE/QPBT/Game/Parameters.lean` | pass, no output | `2.09s` |
| `lake build MIPStarRE.QPBT.Game.Parameters` | pass, 2,358 jobs; only inherited G16 warning | `3.21s` |
| `python3 blueprint/check.py --check` | pass, 54 nodes / 12 chapters / acyclic / deterministic | `0.09s` |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass, same 54-node result | `0.10s` |
| `python3 scripts/workflow.py validate` | pass: 53 issues, 26 PRs, 2 planned sessions, 424 issued sessions, 7 stages | `0.14s` |
| owned-file debt scan | pass: no `sorry`, `axiom`, `constant`, generic assumptions, or `_ofObligations` | below timer resolution |
| exact import scan | pass: sole import is `MIPStarRE.QPBT.Basic.Field` | below timer resolution |
| SHA-bound commit count/path and `git diff --check BASE..HEAD` | pass: one commit, one owned path, clean diff | below timer resolution |
| private `lake build` | pass, 8,992 jobs | `5.95s` |

Blueprint declaration/source synchronization was checked in both normal and
explicit pinned-source modes.  This issue changes no generated declaration
list because G01's planned declaration names were already present in metadata.

## Cache and build protocol

- Canonical cache recipe: `qpbt-hot-main`, version `7`.
- Exact cache key:
  `2c33c7b065555411d1f8d56fb339daf69ee76fa3981b8cd31432c7e9012b75a9`.
- Exact main commit: `874dc07433936e26d62c42cdd779dde42386f99d`.
- Warm result: cache miss; this session was elected owner; no lock wait;
  `builds=1`; total `804.435210s`; foundation materialization `4.241668s`;
  package materialization `18.782291s`; package verification `18.620205s`;
  dependency cache `44.386822s`; build `690.977058s`.
- Mathlib source identity: commit
  `81a5d257c8e410db227a6665ed08f64fea08e997`, tree
  `5ea66b811b8461daae82f14d356fed2a287d7c40`, authenticated local source
  mode.
- Foundation archive provenance: codeload URL pinned in
  `references/mipstarre-upstream.json`, 1,989,153 bytes, SHA-256
  `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.
- Private seed: cache hit; no lock wait; `75.002550s`; 124,925 files and
  10,097,592,570 bytes copied via byte-copy fallback; no writable build output
  was shared.
- Private foundation materialization before full-build retry: pass,
  `3.82s`, authenticated inventory
  `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.

## Incidents and retries

1. Initial `hot_main_cache.py warm` exited `2` in `0.063s` because neither
   `MATHLIB_SOURCE` nor `MATHLIB_ARCHIVE` was set.
2. The second warm attempt used authenticated Mathlib source but exited `2`
   after `1.25s`: local Git clone hit `EXDEV`, correctly retried `--no-local`,
   then foundation materialization reported unset `MIPSTARRE_ARCHIVE`.
3. A canonical-root scoped Lean attempt started an unintended dependency clone
   and was interrupted.  Its exact elapsed time was not emitted; it is not
   counted as a validation gate.
4. The first private seed command exited `2` in `0.061s` because repo-root
   inference treated the issue worktree as main.  Supplying canonical
   `--repo-root` produced the successful private seed above.
5. The first private scoped check exited `1` in `1.66s` because the base cache
   did not include `Basic/Field.olean`.  Building the declared prerequisite
   succeeded in `4.89s`; the scoped rerun succeeded in `2.64s`.
6. The first affected target build passed in `3.31s` but emitted a docstring
   style warning.  The docstring was corrected; final scoped and target gates
   are recorded above.
7. One explicit-source blueprint preflight used the issue worktree's absent
   reference path and exited `1` in `0.09s`.  The corrected canonical pinned
   source-root command passed in `0.10s`.
8. The first private full build exited `1` in `0.49s` because seeding copies
   `.lake` but not materialized untracked foundation sources.  After exact
   private materialization, the single retry passed in `5.95s`.

No failure class occurred three times.  No workflow issue or protocol change
was opened by this session.

## Metrics and topology

- Nested topology: `/root` -> `/root/i039_orchestrator_a01_parameters`.
- Subagents dispatched: `0`.
- Compile attempts: 3 scoped checks after private seed (1 prerequisite miss,
  2 passes), 1 prerequisite target build, 2 affected target builds, and 2
  private full-build attempts (1 materialization preflight failure, 1 pass).
- Token usage: `null`; reason: the agent interface does not expose token usage.
- End-to-end session elapsed: `null`; reason: the agent interface exposes
  command wall times but not an authoritative session wall-clock metric.
- Protocol revision: repository `AGENTS.md` plus hot-cache recipe version `7`.

No canonical file under `workflow/state/` or `research/metrics/` was edited by
this session.
