# QPBT-056 / LPR-033 immutable mathematical and API review A03

- Session: `i056-reviewer-a03-f06`
- Role: fresh independent senior Lean and mathematical reviewer
- Verdict: `approve`
- Candidate: `c1bfd95226e0c068f7d818689f56ab41088ff545`
- Review interval: epoch `1788389777` through `1788389864` (`87` seconds, reviewer measured)

## Findings

None.

I found no false or drifted statement, source-fidelity defect, frozen-API
departure, edge-case failure, sampler-law error, forbidden assumption, new proof
debt, import defect, or undocumented source repair in the authenticated candidate.

## Authentication

| Object | Required identity | Independently observed | Result |
| --- | --- | --- | --- |
| Manifest | SHA-256 `3aca933b01ae463de91e103acbe98f5fdcd0e981c7e4cf19e6866fa292b0db21` | same | pass |
| Candidate base/tree | `4cc1762f85da1bd46599311b77c4647d5f3c30b4` / `0da9b4f149b653ff5dfbcd9440016101c9dc1e7b` | same | pass |
| Candidate head/tree | `c1bfd95226e0c068f7d818689f56ab41088ff545` / `27d113095e14b6063e6931f5dca6b8ee818edeca` | same | pass |
| Sole parent / commit count | base / `1` | same | pass |
| Changed paths | `MIPStarRE/QPBT/Game/Types.lean`; `workflow/reviews/qpbt-056-f06-a01.md` | exactly those two | pass |
| Binary patch | SHA-256 `5b59f3045a5835b22800f588ae7d8e38e7e73be067b6cc3f156365d6f3501464` | same | pass |
| Canonical checkpoint/tree | `6efa4b486a01568f4b01e3178f19734591a0d3f7` / `d8e303d139aaa5ce3a338619dae91a55858e1aee` | same | pass |
| Manifest Git/filesystem entries | 17 declared blob/SHA-256 identities | 17/17 exact | pass |
| Candidate Types blob/SHA-256 | `1f8ffe50e1aefa3ba5946bd1e94e61a2c28319b1` / `db09fff1f8e9bb12b2c35d97503fc58954ab2600f98162b78b1d5c73c8d24191` | same | pass |
| Frozen F06 marker | stripped SHA-256 `120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461` | same; bytes strictly between unique markers with only final newline removed | pass |

The complete candidate `Types.lean`, both pinned source ranges, `Field.lean`,
G21 and F06 metadata, QPBT-056/LPR-033/session records, writer and binder reports,
and both nonbinding audits were inspected only after authentication. The
candidate commit's ancestry, tree, two-path diff, and patch were independently
derived rather than trusted from those reports.

## Mathematical and source review

`MIPStarRE/QPBT/Game/Types.lean:30` gives the source recursion without reducing
it to global linearity. At each successor, the head map is linear on a selected
coordinate register, is supported there, and depends only on it. The family
`next` is indexed by the actual head-map range, and each prefix receives its own
recursive proof object. Consequently all later factor partitions, maps, and
branches may depend arbitrarily on the accumulated prefix, as required by
`conditionally-linear.tex:35-57`; the common `tail` at one node is exactly the
fixed complementary ambient domain on which each prefix-indexed recursive CL
function lives.

Level raising at `Types.lean:60` prepends an empty, zero head and retains the
old full-register certificate as its tail. This preserves `toFun` and is a valid
implementation of the paper's level inclusion. It also works at level zero;
it does not use the paper's defective zero-to-one witness as a wrapper for an
arbitrary function.

The same-level direct-sum induction at `Types.lean:240` combines head registers,
head linear maps, and arbitrary branches componentwise. Its `leftPrefix` and
`rightPrefix` recover genuine component range witnesses from the combined
range prefix. `ConditionallyLinearMap.directSum` at `Types.lean:381` first
raises unequal levels to their maximum and then realizes the exact appended
function. This is the faithful binary instance of the paper's finite direct
sum and generates the m-ary construction by iteration.

Downsizing at `Types.lean:398` is a linear equivalence: it applies the selected
`FieldData.coordinates` basis to every source coordinate and bijectively
flattens the resulting binary blocks. Registers expand to whole basis blocks.
The source head map is restricted to `ZMod 2` and conjugated by this equivalence.
Most importantly, `pullbackRange` at `Types.lean:522` applies the inverse
coordinate equivalence before selecting the source branch at `Types.lean:567`.
The realization proof identifies the restricted pulled-back prefix at
`Types.lean:611`. This is exactly the documented G21 inverse-prefix repair.
The induction has a separate `.zero` branch at `Types.lean:557`, repairing the
paper's omitted level-zero proof case without altering a public statement or
adding a premise.

## Frozen API

The exact frozen surface was compared declaration by declaration. The 14 names
are `FieldVector`, `restrictVector`, `ConditionallyLinearCertificate`,
`ConditionallyLinearMap`, `ConditionallyLinearMap.raiseLevel`,
`ConditionallyLinearMap.directSum`, `downsizeVector`,
`ConditionallyLinearMap.downsize`, `CLSampler`, `CLSampler.sample`,
`CLSampler.directSum`, `CLSampler.sample_directSum`, `CLSampler.downsize`, and
`CLSampler.sample_downsize`. Their hypotheses, conclusions, quantifier order,
levels, dimensions, PMF bind/map order, and namespaces match the marker. The
required `CoeFun` and two local instances also match. All implementation
helpers are private. The only direct imports are exactly
`Mathlib.Probability.Distributions.Uniform` and
`MIPStarRE.QPBT.Basic.Field`.

## Edge cases and sampler laws

- `n = 0`: `FieldVector k 0` is the singleton empty vector; restrictions,
  partitions, uniform sampling, direct sums, flattening, and PMF laws remain
  total with their ordinary definitions.
- Hypothetical `k = 0`: given `D : FieldData 0`, both coordinate products are
  empty and `downsizeVector` remains an equivalence. Expanded registers are
  empty. No impossible-case elimination or zero fallback is present. The
  source-facing field construction separately restricts actual exponents.
- `n1 = 0` or `n2 = 0`: the empty component seed is a singleton, and the append
  equivalence proves the same product law without an exceptional case.
- `level = 0`: `.zero` is the only certificate; raise, direct sum, and downsize
  preserve the zero map and sampler equalities exactly.
- `CLSampler.sample` at `Types.lean:722` maps one uniform seed to both Alice and
  Bob outputs, preserving their required correlation.
- `sample_directSum` at `Types.lean:737` uses `S.sample.bind` followed by
  `T.sample.map`: component seeds are independent, while each component still
  shares one seed between its Alice/Bob maps. Output order is exactly
  `(Alice_S ++ Alice_T, Bob_S ++ Bob_T)`.
- `sample_downsize` at `Types.lean:765` proves the exact PMF pushforward through
  the pair of coordinate equivalences. The proof's two map compositions have
  the same input seed and output ordering as the frozen statement.

No construction has a degenerate zero fallback except the mathematically
required level-zero constructor.

## Downstream usability and hygiene

The public maps coerce to functions, direct sum supports unequal levels,
downsize preserves the level, and both sampler operations expose exact PMF
equalities suitable for rewriting downstream. The concrete coordinate-register
boundary is consistent with `FieldData` and the reviewed F06 ownership graph.

A full candidate scan found zero occurrences of `sorry`, `admit`, `axiom`,
`constant`, `proof_wanted`, generic `Hypotheses`/`Assumptions`,
`_ofObligations`, or bridge/repair/witness/package/producer inputs. The known
upstream G16 debt in `Field.lean` is inherited and not consumed as a new
assumption here. G21 is documented and repaired internally. No other source
repair was found.

## Statement integrity

| Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| Finite characteristic-two coordinate spaces; recursive complementary register factors and prefix-dependent linear maps; uniform shared seed; independent direct-sum component seeds; selected binary basis for downsize | Concrete `GaloisField 2 k` vectors, recursive certificates on coordinate registers, `FieldData` only for downsize, finite instances derived locally | CL recursion and level inclusion; maximum-level direct sum and product law; conjugated downsize and sampler pushforward at the same level | The same constructions and exact PMF equalities, with binary direct sum and explicit coordinate/basis boundary; G21 repaired internally | `faithful boundary` |

## Residual risk

This review was intentionally static and did not rerun Lean or builds; the task
packet states that these exact authenticated bytes passed scoped, target, API,
and full builds. Residual risk is limited to that externally supplied build
evidence and inherited tracked G16 proof debt. Neither affects the reviewed
F06 statements or introduces candidate assumptions.

## Counters

- Findings: `0` blocker, `0` major, `0` minor; total `0`.
- Manifest entries authenticated: `17/17`.
- Candidate commits/diff paths: `1` commit, `2/2` exact paths.
- Frozen names/imports checked: `14/14` names, `2/2` imports.
- Read-only tool batches before report write: `8`.
- Read-only `exec_command` invocations before report write: `8`.
- Report writes: `1` (`/tmp/i056-review-a03.md`).
- Repository writes / Git writes: `0 / 0`.
- Lean / Lake / compile / target build / full build: `0 / 0 / 0 / 0 / 0`.
- Cache / materialization / network / endpoint / GitHub / credential actions:
  `0 / 0 / 0 / 0 / 0 / 0`.
- Nested agents: `0`; topology: one reviewer leaf
  `/root/i056_reviewer_a03_f06` under root coordinator `/root`.
- Recommended candidate changes: `0`.
- Token usage: `null`; availability reason: the collaboration backend does not
  expose per-session token counts, and no estimate is substituted.

Final report SHA-256 is returned out of band to avoid self-reference.
