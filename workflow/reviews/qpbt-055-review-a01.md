# QPBT-055 independent source-fidelity review A01

Final verdict: `request_changes`

## Findings

### High: G20 incorrectly classifies the paper's level-raising argument as defective

`blueprint/metadata/gaps.json:194-202`,
`workflow/reviews/qpbt-055-level-raise-gap-a01.md:5-17,55-61`, and
`workflow/state/issues.json:2855-2858` read the data at
`conditionally-linear.tex:126-129` as though the paper claimed those data
directly wrap an arbitrary lower-level function. It does not. Lines 124-129
say that it suffices to show that the unique zero-level function is also a
one-level function, and the displayed full-head/zero-tail data correctly do
exactly that.

The sufficiency follows from the recursive definition at lines 35-57. Write
`C_r(W)` for the `r`-level functions on a register space `W`. The displayed
construction proves `C_0(W) subset C_1(W)`. If
`C_(r-1)(W) subset C_r(W)` for every register space, retain the outer head,
head map, and decomposition of a function in `C_r(V)`, and promote each
recursive tail from `C_(r-1)(V_tail)` to `C_r(V_tail)`. The same outer equation
then witnesses membership in `C_(r+1)(V)`. Equivalently, replace every terminal
zero certificate by the displayed one-level zero certificate. The realized
function is unchanged.

The proposed empty-head/full-tail construction is also a valid direct wrapper:
its head contributes zero and its full-tail branch is the old function. It is
an implementation choice, however, not a source repair. Calling G20 an
`incorrect-construction` paper gap and propagating it to F06 and the generated
outputs is therefore source-false.

Disposition required: remove G20 as a paper defect, or reframe it only as an
explicit Lean implementation strategy while recording that the paper's terse
argument is a valid base case plus structural induction. Update the QPBT-055
acceptance gate, F06 `gap_ids`/encoding, generated graph/chapter/gap table, and
the candidate review's statement-integrity row accordingly. G21 can remain.

No other blocking finding was found.

## Substantive dispositions

- **G20: rejected.** The displayed recipe realizes zero, but zero is exactly
  the function the paper says it is realizing. The recursive definition makes
  that base inclusion sufficient for all level inclusions.
- **Empty-head/full-tail wrapper: mathematically accepted.** It preserves the
  old function pointwise and raises the certificate level by one, but it is not
  evidence of an error in the paper.
- **G21 prefix defect: accepted.** At lines 425-428 and 453-455 the source
  writes an original family member `L_{j,downsize(u)}` even though that family
  is indexed by original prefixes `u in L_{<j}(V)` (lines 158-163). For a target
  prefix `v`, selecting `u = downsize^{-1}(v)` and conjugating `L_{j,u}` is the
  type-correct repair; when `v = downsize(u)`, this is equivalently the simple
  correction from `L_{j,downsize(u)}` to `L_{j,u}`.
- **G21 omitted case: accepted.** The lemma quantifies `ell >= 0` at lines
  411-418, while its proof starts at `ell = 1` at lines 432-438. At level zero,
  the source definition permits only the zero function, conjugation preserves
  zero, and the existing Lean zero certificate discharges the case.
- **Proof/API boundary: accepted apart from G20's label.** The candidate changes
  no Lean file. Base and head have the same 14 F06 names, imports, hypotheses,
  conclusions, ownership, sampler semantics, and marker bytes. The stripped
  F06 marker hashes to
  `120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461`
  at both revisions.
- **Separate seed typo: preserved.** `conditionally-linear.tex:377` says the
  common seed lies in `V x V`, whereas Definition `def:cl-dist` and the
  surrounding proof require one seed in `V`. The unchanged
  `workflow/reviews/qpbt-035-directsum-api-a06.md` retains that separate finding;
  G20/G21 do not merge or rewrite it.
- **Reciprocity/generated output: mechanically consistent but substantively
  tainted by G20.** G20/G21 have reciprocal `affected_nodes`/F06 `gap_ids`;
  the F06 graph object equals the metadata object after deleting derived
  `consumers`; the graph canonical source hash recomputes to
  `eab1f9746d2c11693596bd6039e36d770662549610754985bdb1b219c98cf4a8`;
  chapter 02 and the generated gap table reproduce the metadata. These exact
  derivatives must be regenerated after correcting G20.
- **Session and metric provenance: accepted.** Exactly three metric rows were
  appended for the F06A, F06, and downsize scouts; IDs are unique. Their report
  hashes and line counts recompute as 279, 342, and 381, and their base SHA,
  external IDs, archived state, timestamps, rounded elapsed values, null token
  fields, zero-action counters, and outcomes agree with canonical session
  state. The 20 appended events consistently finish/archive the two existing
  scouts, issue/run/finish/archive the replacement downsize scout, add/activate
  QPBT-055, and update Stage 04A. `subagents_issued` increases by one because
  only the downsize scout is newly issued in this candidate.

## Statement integrity

| Item | Paper statement/proof | Candidate disposition | Verdict |
| --- | --- | --- | --- |
| Level inclusion | The one-level zero witness is the base case; recursive promotion establishes every subsequent inclusion | Treats the base witness as a failed direct wrapper and records G20 | `mismatch` |
| Empty-head/full-tail | Not the displayed paper construction | Valid proof-local direct wrapper with the same realized function | `exact implementation alternative`, not a paper repair |
| Downsize prefix | Source RHS selects an original map using a downsized prefix | Pull target prefix back, then select and conjugate the original map | `documented mismatch G21`, faithful repair |
| Downsize `ell = 0` | Allowed by the lemma, omitted by its proof | Use the unique zero certificate | `documented mismatch G21`, faithful repair |
| Frozen F06 surface | Mathematical CL maps/samplers with basis-mediated downsize | Same names, imports, assumptions, conclusions, seed law, and ownership | `faithful boundary`, unchanged |

Overall statement-integrity verdict: `mismatch`; the candidate cannot be
approved while G20 is represented as a paper defect.

## Immutable authentication

- Manifest SHA-256: exact
  `0934f2af269c42a7625dd553854d6dbd2a5d792ca3b56af828c4a955c86c4064`.
- Base: exact commit `ead85cbb7ad4a51147686d732e7c04824ce074d4`.
- Head: exact commit `98c0fe23dee3ee1d657c4e5612708e875f6c405a`.
- Sole parent: exact
  `ead85cbb7ad4a51147686d732e7c04824ce074d4`.
- Head tree: exact `b50307ad35a469c3694931bba336b6978e3f6865`.
- Binary patch SHA-256: exact
  `d44eaf0e6c0907f795b39bdcd4bf289c670f3d3d77e2541cd6b4f76ac968920e`.
- Changed paths: exact 11/11, in manifest order:
  `blueprint/generated/graph.json`, `blueprint/metadata/gaps.json`,
  `blueprint/metadata/nodes.json`,
  `blueprint/src/generated/chapter-02-entries.tex`,
  `blueprint/src/generated/gaps.tex`, `research/metrics/sessions.jsonl`,
  `workflow/events.jsonl`,
  `workflow/reviews/qpbt-055-level-raise-gap-a01.md`,
  `workflow/state/issues.json`, `workflow/state/sessions.json`, and
  `workflow/state/stages.json`.
- `git diff --check`: pass.

All 16 manifest entries authenticated:

| Entry | Blob | SHA-256 |
| --- | --- | --- |
| `git:...:blueprint/generated/graph.json` | pass | pass |
| `git:...:blueprint/metadata/gaps.json` | pass | pass |
| `git:...:blueprint/metadata/nodes.json` | pass | pass |
| `git:...:blueprint/src/generated/chapter-02-entries.tex` | pass | pass |
| `git:...:blueprint/src/generated/gaps.tex` | pass | pass |
| `git:...:research/metrics/sessions.jsonl` | pass | pass |
| `git:...:workflow/events.jsonl` | pass | pass |
| `git:...:workflow/reviews/qpbt-055-level-raise-gap-a01.md` | pass | pass |
| `git:...:workflow/state/issues.json` | pass | pass |
| `git:...:workflow/state/sessions.json` | pass | pass |
| `git:...:workflow/state/stages.json` | pass | pass |
| `git:...:AGENTS.md` | pass | pass |
| `git:...:workflow/reviews/qpbt-035-q014-contract-a04.md` | pass | pass |
| `filesystem:.../conditionally-linear.tex` | n/a | pass |
| `filesystem:/tmp/i038-scout-a03-f06.md` | n/a | pass |
| `filesystem:/tmp/i038-scout-a03-downsize.md` | n/a | pass |

Here each abbreviated Git locator has the authenticated head
`98c0fe23dee3ee1d657c4e5612708e875f6c405a`; every actual blob ID and content
digest equals the corresponding full value in the immutable manifest.

## Residual risk and review limits

The source's downsize definition states odd extension degree while the lemma's
hypothesis presentation does not repeat it. The paper globally restricts its
field use to odd binary extensions, and the frozen Lean boundary receives the
selected basis explicitly as `D : FieldData k`; this is an existing faithful
boundary presentation issue, not a new candidate blocker.

Per the review constraint, no Lean, Lake, build, cache, materialization,
network, GitHub, credential, or nested-agent action was performed. Claimed
validation executions were inspected as candidate provenance but not rerun.
No repository file was changed.

## Review accounting

- First observed timestamp: `2026-09-03T05:11:29+08:00`.
- Evidence cutoff: `2026-09-03T05:16:34+08:00`.
- Read-only shell invocations: 47 across 15 orchestration calls.
- Temporary report writes: 1 (`/tmp/qpbt-055-review-a01.md`).
- Repository edits: 0; Git writes: 0.
- Lean/Lake/build/cache/materialization/network/GitHub/credential actions: 0.
- Nested agents: 0.
- Token usage: `null`.
- Token availability reason: the collaboration backend does not expose
  per-agent token usage; no estimate was made.
