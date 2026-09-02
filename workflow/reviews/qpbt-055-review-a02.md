# QPBT-055 independent repair review A02

Final verdict: `approve`

## Findings

No blocking findings.

The A01 high finding is fully resolved in the canonical and generated data. G20
is absent from the gap registry and F06 linkage, while historical A01/A03
artifacts retain the rejected diagnosis only as review/session provenance. The
repaired account at `workflow/reviews/qpbt-055-level-raise-gap-a01.md:5-18`
and `blueprint/metadata/nodes.json:382-384` matches the pinned source. G21 is
still reciprocal and scoped only to the downsize prefix-index error and omitted
level-zero proof case. The independent shared-seed typo at source line 377
remains separately recorded at
`workflow/reviews/qpbt-035-directsum-api-a06.md:52-57`.

## Immutable authentication

- Manifest SHA-256: exact
  `71e8b43c2ce4f3c1f7abd185cc41e47c347a3aa736dd45a2616cc994a0c65b7f`.
- Base: exact `98c0fe23dee3ee1d657c4e5612708e875f6c405a`.
- Intermediate: exact `740e22cc052555051f3c716440de1b58b2f3f4d6`,
  sole parent equal to the base.
- Head: exact `4cc1762f85da1bd46599311b77c4647d5f3c30b4`.
- Head tree: exact `0da9b4f149b653ff5dfbcd9440016101c9dc1e7b`.
- Head sole parent: exact
  `740e22cc052555051f3c716440de1b58b2f3f4d6`.
- Ancestry: exact two commits, intermediate then head; neither commit is a
  merge.
- Canonical binary patch SHA-256 from
  `git diff --binary --full-index <base> <head>`: exact
  `e07473c86727d893b052be1b3a78acad2ac710b430bfe8f9ddbfb80e13a44a64`.
- Changed paths: exact 13/13, with no Lean path:
  `blueprint/generated/graph.json`, `blueprint/metadata/gaps.json`,
  `blueprint/metadata/nodes.json`,
  `blueprint/src/generated/chapter-02-entries.tex`,
  `blueprint/src/generated/gaps.tex`, `research/metrics/sessions.jsonl`,
  `workflow/events.jsonl`, `workflow/reviews/qpbt-038-types-a03.md`,
  `workflow/reviews/qpbt-055-level-raise-gap-a01.md`,
  `workflow/reviews/qpbt-055-review-a01.md`,
  `workflow/state/issues.json`, `workflow/state/sessions.json`, and
  `workflow/state/stages.json`.
- `git diff --check <base> <head>`: pass.

All 18 manifest entries authenticated byte-for-byte:

| Entry | Blob | SHA-256 |
| --- | --- | --- |
| `git:head:blueprint/generated/graph.json` | pass | pass |
| `git:head:blueprint/metadata/gaps.json` | pass | pass |
| `git:head:blueprint/metadata/nodes.json` | pass | pass |
| `git:head:blueprint/src/generated/chapter-02-entries.tex` | pass | pass |
| `git:head:blueprint/src/generated/gaps.tex` | pass | pass |
| `git:head:research/metrics/sessions.jsonl` | pass | pass |
| `git:head:workflow/events.jsonl` | pass | pass |
| `git:head:workflow/reviews/qpbt-038-types-a03.md` | pass | pass |
| `git:head:workflow/reviews/qpbt-055-level-raise-gap-a01.md` | pass | pass |
| `git:head:workflow/reviews/qpbt-055-review-a01.md` | pass | pass |
| `git:head:workflow/state/issues.json` | pass | pass |
| `git:head:workflow/state/sessions.json` | pass | pass |
| `git:head:workflow/state/stages.json` | pass | pass |
| `git:head:AGENTS.md` | pass | pass |
| `git:head:workflow/reviews/qpbt-035-q014-contract-a04.md` | pass | pass |
| `filesystem:.../conditionally-linear.tex` | n/a | pass |
| `filesystem:/tmp/i038-scout-a03-f06.md` | n/a | pass |
| `filesystem:/tmp/i038-scout-a03-downsize.md` | n/a | pass |

Here `head` abbreviates the authenticated immutable head above. Every Git entry
matched both its full manifest blob ID and file SHA-256; all three filesystem
entries matched their full manifest SHA-256.

## Source reasoning

The recursive definition at
`references/2001.04383v3/sections/dependencies/conditionally-linear.tex:35-57`
defines level zero as the unique zero function and a successor certificate as a
linear head plus a lower-level tail on a complementary register.

The remark at lines 124-129 does not claim to wrap an arbitrary lower-level
function with its displayed full-head/zero-tail data. It says that proving the
zero function is one-level suffices. Those displayed data do realize zero, so
they establish the zero-to-one base inclusion. For the inductive step, retain
the outer decomposition of an existing level-r certificate and promote every
level-(r-1) recursive tail using the induction hypothesis on its tail register.
This preserves the realized function and yields level r+1. Thus the paper's
terse base-case-plus-structural-promotion proof is valid.

The empty-head/full-tail wrapper also realizes the old function exactly: the
new head contributes zero and the unique recursive branch is the original
certificate on the full register. It is therefore an exact Lean implementation
alternative, not a source repair. The repaired report and F06 encoding make
that distinction explicitly.

G21 remains correct at `blueprint/metadata/gaps.json:195-202`. The original
factor family is indexed by `u in L_{<j}(V)` at source lines 158-163, while
lines 425-428 and 453-455 incorrectly select the original map with
`downsize(u)`. Pulling a target prefix back through the coordinate equivalence,
selecting the original map, and then conjugating it is type-correct. The lemma
allows `ell >= 0` at lines 411-418 but its proof starts at `ell = 1` at lines
432-438; the unique level-zero certificate supplies the omitted case.

The separate line-377 defect is unchanged and remains outside G21: Definition
`def:cl-dist` at lines 132-138 samples one `x : V`, whereas proof line 377 says
`V x V`; lines 376 and 379-382 again require one shared seed.

The F06 generated projection is exact: the head graph F06 object equals the
metadata object after removing the derived `consumers` field. G21 occurs once
in the gap registry, points to F06, and F06 has exactly `gap_ids = ["G21"]`.
The chapter entry at `blueprint/src/generated/chapter-02-entries.tex:243` and
gap table at `blueprint/src/generated/gaps.tex:24` carry the same disposition.

## Statement integrity

| Item | Paper assumptions | Frozen Lean assumptions | Paper conclusion | Frozen Lean conclusion / repair | Verdict |
| --- | --- | --- | --- | --- | --- |
| Level inclusion | Existing lower-level CL function and recursive certificate definition | Certified map on the same full register | Every level contains the preceding level | `raiseLevel` preserves the map; empty-head/full-tail may implement the same inclusion directly | `exact implementation alternative`; no paper gap |
| Mathematical downsize | Finite coordinate field space, CL certificate, selected basis | Concrete `GaloisField` vectors, certificate, and `FieldData` only at downsize | Conjugated CL map and sampler pushforward at the same level | Pull prefixes back before source-map selection and handle level zero with `.zero` | `documented mismatch G21`; faithful internal repair |
| Shared-seed distribution | One uniform `x : V` feeds `(L x, R x)` | One uniform ambient vector feeds both sampler components | Direct sum gives the product of component pair laws | Exact bind/map law after `Fin.append` reindexing | `faithful boundary`; line-377 typo separate |
| F06 public surface | Mathematical CL maps/samplers through source line 552 | Exact frozen 14-name contract and two direct imports | Level raise, direct sum, downsize, and exact PMF laws | Same hypotheses, conclusions, quantifier surface, and ownership | `faithful boundary`; unchanged |

Overall statement-integrity verdict: `faithful boundary`. No paper-labelled Lean
declaration changed, and no public assumption or proof obligation was added.

The contract blob is identical at base and head. The text strictly between the
F06 markers, stripped only of its final newline, hashes at both revisions to
`120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461`.
The 14 names, imports, boundary hypotheses, paper/Lean assumptions, and
paper/Lean conclusions are byte-identical. `MIPStarRE/QPBT/Game/Types.lean` is
absent at both revisions.

## QPBT-038 provenance and issue graph

The report-only blocker is authentic. Commit
`e22e2ee0730c5c9c6a2d3bdb4d0729f5e7de6062` has sole parent
`5e5c4e025db423e87f76b0185533cd21f5ce9ab5`, tree
`1b3d01493b74f4546f8a9b5eb068a9328281737d`, and adds only
`workflow/reviews/qpbt-038-types-a03.md`. Its report blob
`8958cc734f16557f450a7b723b73138450d579e7` and SHA-256
`99fc04e0bfe2c430de2674c9d0037c27d775867e03358152f5c1ec9def6ef5ff`
are preserved exactly in intermediate commit `740e22c...` and the reviewed
head. The report records the failed first F06A compiler gate and intentional
absence of `Types.lean` at
`workflow/reviews/qpbt-038-types-a03.md:10-33,35-71,152-153`.

The pinned Mathlib revision is
`81a5d257c8e410db227a6665ed08f64fea08e997`. Its authenticated local
`Computable.lean` has the recorded SHA-256 and lines 284-288 contain only the
`proof_wanted TM2ComputableInPolyTime.comp` command. The searched pinned
Turing-machine source exposes `FinTM2`, execution predicates, and `idComputer`,
but no elaborated composition declaration. The blocker is therefore a valid
dependency report, not an excuse to weaken the frozen F06A surface.

The issue decomposition is sound at `workflow/state/issues.json:2054-2100` and
`:2876-3007`: QPBT-056 depends on QPBT-055 and the earlier prerequisites;
QPBT-057 depends on QPBT-056; QPBT-058 depends on QPBT-057. All three are
children of blocked tracking parent QPBT-038, are `planned`, have no owner
session, and intentionally reuse `MIPStarRE/QPBT/Game/Types.lean` only in that
strict sequence. No running session at the reviewed head owns that path. The
children appear once together in Stage 04A. The split keeps the internal
compiler/resource work in QPBT-057 and leaves F06/F07 ownership with QPBT-056
and QPBT-058 respectively.

The two appended metric rows are unique and agree with archived session state
for the A03 orchestrator and A01 reviewer; the 20 appended events consistently
record the issue/session transitions and three-child split. The historical A03
F06 scout/report metric retains its now-rejected level-raise diagnosis as
immutable attempt provenance, while the A01 review metric records the rejection
and current blueprint/issues contain no G20. This does not reactivate G20.

## Review limits and accounting

Claimed candidate validation was authenticated and inspected but not rerun.
Per the immutable review constraints, no Lean, Lake, target/full build, cache
warm/seed, materialization, network, GitHub, credential, or nested-agent action
was performed. No workflow or blueprint generator was run. No repository or
Git write was performed; the only write is this required `/tmp` report.

One read-only lookup batch first checked the nonexistent root `.lake/packages`
location and produced three path-miss invocations; the already-present private
QPBT-038 worktree source was then read directly. No cache command or cache write
occurred.

- Evidence cutoff: `2026-09-03T05:37:32+08:00` before report creation.
- Review start and total elapsed seconds: `null`; the collaboration backend did
  not expose a session start/elapsed clock and no estimate was made.
- Read-only shell invocations: 82 across 20 shell batches, including the final
  report hash invocation.
- Temporary report writes: 1 (`/tmp/qpbt-055-review-a02.md`).
- Repository edits: 0; Git writes: 0.
- Lean: 0; Lake: 0; builds: 0; cache actions: 0; materializations: 0.
- Network: 0; GitHub: 0; credential operations: 0.
- Nested agents: 0.
- Findings: 0; resolved prior findings verified: 1 high.
- Token usage: `null`.
- Token availability reason: the collaboration backend does not expose
  per-agent token usage; no estimate was made.
