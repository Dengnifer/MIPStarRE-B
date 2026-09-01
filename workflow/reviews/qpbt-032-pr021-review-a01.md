# LPR-021 / QPBT-032 Independent Review A01

## Findings

No findings.

## Verdict

**Approve** `LPR-021` at exact head
`00b74473b04a72b57c7c7b9ebdfd9ad7ef17a99f` and tree
`d47252b71d1cfa5df331c77f03f9b890c29ca770`.

The candidate faithfully implements the QPBT-032 finite measurement-family and
postprocessing slice, type-checks without proof debt, and stays inside its
two-path immutable manifest. The broader frozen F03 contract also specifies the
binary-observable boundary; QPBT-032 and LPR-021 expressly exclude that boundary,
so this approval must not be used to mark the complete F03 blueprint node as
implemented.

## Immutable authority and manifest

- Issue: `QPBT-032`; local PR: `LPR-021`; review session:
  `i032-reviewer-a01-pr021`.
- Base commit: `259c73a368ef7403b4e36e190c9bf940497b300f`;
  base tree: `b3a404a012f9f120f1fa5fa692e51b92d000d615`.
- Candidate commit: `00b74473b04a72b57c7c7b9ebdfd9ad7ef17a99f`;
  candidate tree: `d47252b71d1cfa5df331c77f03f9b890c29ca770`.
- `git cat-file` shows that the candidate's sole parent is the exact base;
  `git merge-base --is-ancestor` passed.
- Both the detached review worktree and the validation worktree authenticated
  the exact candidate HEAD/tree, were tracked-clean after validation, and held
  byte-identical copies of both changed files.

| Mode | Git blob | Bytes | SHA-256 | Path |
| --- | --- | ---: | --- | --- |
| `100644` | `b3eb1b1eee2860b83b71659add650b9ff3e8ed4c` | 3317 | `13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a` | `MIPStarRE/QPBT/Basic/Approximation.lean` |
| `100644` | `a1b56a0024f8bb89d8f18db5c50985cccd6eb136` | 4827 | `b69eb36ebfa77f2839ff7a5c4c84a6fed011aae2eb30140a4fcd64ea64575320` | `workflow/reviews/qpbt-032-approximation-skeleton-a01.md` |

The manifest digest is
`d7f178ca37c7d82a834beba487a3313daf425e66fe449b46c0f145075fe11843`,
computed as SHA-256 of the two sorted newline-terminated
`<sha256><two spaces><path>` records shown above. `git diff --name-status` and
`git diff-tree` both returned exactly these two added paths.

Source authority read before candidate review:

- `references/2001.04383v3/sections/dependencies/measurements.tex`, especially
  `def:bracket` at generated lines 31-47; whole-file SHA-256
  `b3c03f8f4f1cbe979ee12e9db26227c9bb84c483c4743f1de988c4c38d80f946`.
- `workflow/reviews/qpbt-023-leaf-contract-a04.md#F03-SIGNATURES`;
  frozen marker-block SHA-256
  `8de7983b66b2cce523b45bb3b14a788ac34b0315be91644610cf455b5306b065`
  and whole-file SHA-256
  `45dfbb3142df500eff3260d89055c4763c543036d62fad2ff3b32c9b036b0f0f`.

## Statement-integrity review

| Declaration | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| `MeasurementFamily` | A family of finite-outcome POVMs indexed by questions | Arbitrary `Question`; finite decidable `Outcome` and finite decidable matrix coordinate type; qualified complete `Quantum.Measurement` | A POVM for every question | A function into the existing complete finite POVM structure | faithful boundary |
| `ProjectiveMeasurementFamily` | Every effect is a projector | The same family; pointwise effect idempotence | The family is projective | `forall x a`, `(M x).effect a * (M x).effect a = (M x).effect a` | exact |
| `MeasurementFamily.postprocess` | Arbitrary map `f : A -> B` | Finite decidable source/target outcomes and the existing qualified POVM family | Relabel outcomes by summing each fiber | Definitionally delegates each question to `Quantum.Measurement.postprocess` | exact |
| `postprocess_effect` | `M^x_[f(.)=b] = sum_(a:f(a)=b) M^x_a` | The same `M`, `f`, `x`, and `b` | Exact outcome-fiber sum | Exact `Finset.univ.filter (fun a => f a = b)` sum | exact |
| `postprocess_effect_eq_zero_of_not_mem_range` | If `b` is not in the image of `f`, the effect is zero | Explicit `b \notin Set.range f` | Empty fiber has value zero | The filtered finite sum is proved empty and rewritten to zero | exact |

The existing `MIPStarRE.Quantum.Measurement` structure supplies positivity and
sum-to-identity, and its qualified `postprocess` implementation uses the same
fiber sum while proving completeness. The wrapper therefore preserves POVM
semantics rather than merely introducing an unconstrained operator family.
Projectivity is stated separately, matching the paper's pointwise projector
condition. No quantifier, outcome domain, sign, constant, or error dependence is
present to drift in this slice.

## API, scope, and debt audit

- Imports are exactly the four frozen imports:
  `Mathlib.Analysis.Asymptotics.Defs`,
  `Mathlib.Probability.ProbabilityMassFunction.Constructions`,
  `MIPStarRE.Quantum.Measurement`, and
  `MIPStarRE.Quantum.FiniteHilbert`.
- Namespace, universes, family alias, projectivity predicate, postprocess
  definition, and both effect theorems match the frozen signatures.
- The question type is intentionally unrestricted. Finiteness occurs only for
  outcomes and the finite coordinate carrier at this boundary.
- The candidate adds no F04 declarations and no observable declarations, as
  required by the issue/PR scope.
- The owned Lean file contains no `sorry`, `admit`, `axiom`, `constant`,
  `opaque`, obligation helper, caller-supplied bridge, or `MIPStarRE.LDT`
  import. Its only declarations are the five requested public names.
- Surrounding definitions inspected:
  `MIPStarRE.Quantum.Submeasurement`, `Measurement`,
  `Submeasurement.postprocess`, `Measurement.postprocess`, and
  `Measurement.postprocess_effect`.

## Deterministic validation

The detached review worktree did not contain the ignored, materialized upstream
Lean sources or a private `.lake` tree. With coordinator authorization, Lean
validation therefore ran in the existing private seeded worktree
`/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-032-approx-a01`
after authenticating its exact candidate HEAD/tree, tracked cleanliness, and
byte equality with the detached review worktree. No cache warm, seed, shared
main build, or main-snapshot compilation was run by this reviewer.

| Command | Result | Elapsed |
| --- | --- | ---: |
| `lake env lean MIPStarRE/QPBT/Basic/Approximation.lean` | pass | 4.80 s |
| `lake build MIPStarRE.QPBT.Basic.Approximation` | pass, 8659 jobs | 6.07 s |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass, 51 nodes / 12 chapters / acyclic / deterministic | 0.08 s |
| `python3 blueprint/check.py --check` | pass, 51 nodes / 12 chapters / acyclic / deterministic | 0.07 s |
| `git diff --check 259c73a368ef7403b4e36e190c9bf940497b300f..00b74473b04a72b57c7c7b9ebdfd9ad7ef17a99f` | pass | 0.00 s |

The candidate's implementation report additionally records a prior private
full `lake build` pass (8992 jobs, 6.02 s). This reviewer independently reran
the scoped and affected-target gates above; guarded integration remains
responsible for current-main validation.

## Metrics and topology

- Session start: `2026-09-01T12:09:40.923779Z`.
- Final evidence time: `2026-09-01T12:13:08.330291352Z`.
- Runtime-measured elapsed through final evidence collection: `207.407` seconds.
- Token usage: `null`; reason: the collaboration backend does not expose
  per-agent token counters. No estimate was made.
- Topology: root coordinator -> one fresh read-only reviewer. Nested agents: 0.
- Compile/build attempts: 2; passes: 2; failures: 0. Cache warms: 0; cache
  seeds: 0; cache lock waits: 0.
- Findings: 0; fix agents: 0; retries: 0; new issues: 0; protocol changes: 0.
- Repository/Git/state/metric edits: 0. Report files written: 1, this file only.
- Endpoint calls: 0; network calls: 0; GitHub operations: 0; credential reads or
  transmissions: 0; external reviews: 0.

Residual risk is limited to downstream use and integration: the observable
portion of F03 and every F04 declaration remain future work, while current-main
integration validation has not yet occurred in this read-only review.
