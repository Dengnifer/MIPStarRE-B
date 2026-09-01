# QPBT-013 first Lean wave closeout A01

Session: `i013-orchestrator-a01-first-wave-close`

## Result

The combined first-wave closure gates pass at exact checkpoint
`d60a71c945ebf407b4a1c8c322c38181e7d09dfa`, tree
`cbd1b48827acb90615f437ebd9d55d3705d7cc70`.

Both independently reviewed child candidates are present byte-for-byte, their
two local PRs are merged, both scoped Lean checks pass, exactly one combined
canonical full build passes all 8,992 jobs, and both blueprint checks pass.
The combined source has exactly one proof hole: the blueprint-authorized G16
`sorry` in `fieldDataOfOddExponent`. The F03 measurement-family/postprocess
slice has no proof debt.

This disposition closes only the QPBT-013 minimal first-wave coordination
gate. It is not a proof-complete F01 result and does not claim the still-future
binary-observable portion of F03, K03A, or any F04 declaration.

## Immutable integration identity

- Detached HEAD/tree:
  `d60a71c945ebf407b4a1c8c322c38181e7d09dfa` /
  `cbd1b48827acb90615f437ebd9d55d3705d7cc70`.
- HEAD's sole parent is
  `aa1f579d56b4476220d2d6ef4c69c3c06ae779e2`; the checkpoint commit changes
  workflow ledgers only and preserves both candidate source/report blobs.
- Common candidate base/tree:
  `259c73a368ef7403b4e36e190c9bf940497b300f` /
  `b3a404a012f9f120f1fa5fa692e51b92d000d615`.
- Field candidate/tree:
  `f5ed1cb3e10831b0230f7c28eeef4d94d0335b88` /
  `b3b368d5fb7cf2bb91c26890b3857cab7882e8b5`.
- Approximation candidate/tree:
  `00b74473b04a72b57c7c7b9ebdfd9ad7ef17a99f` /
  `d47252b71d1cfa5df331c77f03f9b890c29ca770`.

The guarded merge chain is exact:

| Merge | Tree | First parent | Second parent |
| --- | --- | --- | --- |
| `ff79fe3444eae7015def65039cac62ec213e8ed4` | `87c31cc240bda87c69c0653a5c79120d237b2a6c` | `152d4d12c2eca74bfdf30dd674355833a2e61d2f` | Field candidate `f5ed1cb3e10831b0230f7c28eeef4d94d0335b88` |
| `aa1f579d56b4476220d2d6ef4c69c3c06ae779e2` | `ee010f3013b09275ba098f2eefdae0c95c66b704` | `ff79fe3444eae7015def65039cac62ec213e8ed4` | Approximation candidate `00b74473b04a72b57c7c7b9ebdfd9ad7ef17a99f` |

All base-to-candidate, candidate-to-merge, merge-to-merge, and merge-to-HEAD
ancestry checks exited 0. Path-limited candidate-to-HEAD diffs were empty.
Across both integrations the only Lean source paths added relative to the
common base are:

```text
MIPStarRE/QPBT/Basic/Field.lean
MIPStarRE/QPBT/Basic/Approximation.lean
```

The four candidate blobs are preserved exactly:

| Candidate | Path | Bytes | Git blob | SHA-256 |
| --- | --- | ---: | --- | --- |
| Field | `MIPStarRE/QPBT/Basic/Field.lean` | 2,002 | `6844e84a08f473dc29620c80392538935348995d` | `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e` |
| Field | `workflow/reviews/qpbt-031-field-skeleton-a01.md` | 3,170 | `7430dfae6aa53a13cc2d0dd2df803a20d8610f98` | `584346e9f6709f1e6350ace98ba37730ba3a7654b2fedc52283cc31531526d32` |
| Approximation | `MIPStarRE/QPBT/Basic/Approximation.lean` | 3,317 | `b3eb1b1eee2860b83b71659add650b9ff3e8ed4c` | `13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a` |
| Approximation | `workflow/reviews/qpbt-032-approximation-skeleton-a01.md` | 4,827 | `a1b56a0024f8bb89d8f18db5c50985cccd6eb136` | `b69eb36ebfa77f2839ff7a5c4c84a6fed011aae2eb30140a4fcd64ea64575320` |

`LPR-020` and `LPR-021` are both recorded as merged at the exact candidate
heads and merge commits above. Their independent reviews approve with zero
findings. Review/binding report SHA-256 values are:

| Lane | Review | Binding |
| --- | --- | --- |
| QPBT-031 / LPR-020 | `bdcc1f4cd303321b5b0e03243734aedde732652fd44324fc6e418b36730f895f` | `e2b9501101ad3e8d574e7a361a1ee11664e0d4dd3d760b383a959c198edc28a7` |
| QPBT-032 / LPR-021 | `e8905f21662e89826aceec073604954b625c7b2c91a837ac399d32b0bb69ebe9` | `f1e0ecb1a557c93cbcc4afc86a2f41af4c3b9b1ea075c1a5e65cae05e38a9471` |

## Source and contract authority

The pinned paper and blueprint sources were read before judging the Lean:

- `references/2001.04383v3/sections/dependencies/finite-fields.tex`, SHA-256
  `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd`;
- `references/2001.04383v3/sections/dependencies/measurements.tex`, SHA-256
  `b3c03f8f4f1cbe979ee12e9db26227c9bb84c483c4743f1de988c4c38d80f946`;
- `blueprint/src/chapter/02-foundations.tex` and generated F01/F03 entries;
- frozen contract `workflow/reviews/qpbt-023-leaf-contract-a04.md`, SHA-256
  `45dfbb3142df500eff3260d89055c4763c543036d62fad2ff3b32c9b036b0f0f`;
- frozen F01 marker SHA-256
  `d888318028c82df942fcac9b81cc944b5f492aebf9902d4cfe32019c37331ad4`;
- frozen F03 marker SHA-256
  `8de7983b66b2cce523b45bb3b14a788ac34b0315be91644610cf455b5306b065`;
  and
- G16 gap record `docs/paper-gaps/self-dual-normal-basis.md`, SHA-256
  `5ee0cb8ea21cd8fe4b377554dc23ba1a96976107334d9512a6cd88175f77786e`.

The authenticated local archive has SHA-256
`656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`
and source commit `507e81220d95266ff3d589d125b2f87c7300a9fb`.
Its materialized `MIPStarRE/Quantum/Measurement.lean` has SHA-256
`c84a712e34425a46ae17d9f04d789ae7393ae97da3cf7ee3f93fe0e6705b9d0d`;
the complete POVM and fiber-sum postprocess definitions were inspected around
the new wrapper declarations. No network fallback was used.

## Statement integrity

| Lean declaration(s) | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| `FieldData` | Concrete `F_(2^k)/F_2` and simultaneous normal, trace-self-dual basis | `k : Nat`; concrete `GaloisField 2 k`; `Fin k` basis and generator | Frobenius-orbit basis with Kronecker trace pairing | The same orbit and pairing, with zero-based `Fin k` exponents | exact witness encoding |
| `fieldDataOfOddExponent`, `fieldData_nonempty_of_odd` | Positive odd `k`; existence within the paper's stronger uniform algorithm theorem | `k : Nat`, `Odd k`; no supplied basis, witness, bridge, algorithm, or obligation | Simultaneous basis; separately, a uniform algorithm and tables in polynomial time | Noncomputable pointwise `FieldData k` and its `Nonempty` projection; sole G16 `sorry`; no algorithmic claim | faithful boundary |
| `fieldTrace` | Extension trace `F_(2^k) -> F_2` | Concrete `GaloisField 2 k` algebra | Basis-independent linear trace | `Algebra.trace (ZMod 2) (GaloisField 2 k)` | exact on the admissible domain; harmless generalization outside it |
| coordinates and multiplication matrix declarations | Chosen-basis coordinates and `downsize(ab) = K_a downsize(b)` | The same `FieldData k`, `a`, and `b` | Coordinate equivalence and left-multiplication identity | `Basis.equivFun`, `LinearMap.toMatrix`, and the identical `Matrix.mulVec` equality | exact encoding |
| `MeasurementFamily` | Finite-outcome POVM for every question | Arbitrary question type; finite decidable outcomes and coordinates; qualified complete measurement | Question-indexed POVM family | Function into positive effects summing to identity | faithful finite-dimensional boundary |
| `ProjectiveMeasurementFamily` | Every effect is a projector | The same family | Pointwise `M_a^2 = M_a` | Identical pointwise idempotence | exact |
| `postprocess`, `postprocess_effect` | Arbitrary outcome map and fiber sum | Finite decidable source/target outcomes; qualified upstream postprocess | Relabeled POVM with `sum_(a:f(a)=b) M_a` | Delegated complete POVM and identical filtered finite sum | exact |
| empty-fiber theorem | `b` is outside the image of `f` | Explicit `b notin Set.range f` | Empty fiber has zero effect | Filtered finite sum is proved empty and equals zero | exact |

`Odd k` supplies the paper's positivity condition. The algorithm/table/runtime
claim remains K03A. QPBT-032 intentionally implements only the first five F03
measurement-family/postprocess declarations; the binary observable remains a
later declared task rather than an assumed or drifted result.

## Validation and timing

### Private cache seed

The worktree was seeded once with:

```text
python3 /home/drx/MIPStarRE-auto/scripts/hot_main_cache.py --repo-root /home/drx/MIPStarRE-auto --main-commit 259c73a368ef7403b4e36e190c9bf940497b300f seed --worktree /home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-013-first-wave-close-a01
```

Result: cache hit and private seed from key
`d71a99abea8f7ebf5bda5194dfef088b06f526230caf5ccbca34d62d5b4267b9`.
Internal elapsed was `64.962432` s; measured command wall time was `65.20` s.
The seed copied 124,925 files and 3 symlinks totaling 10,097,592,794 bytes.
Cache misses, lock waits, and builds were all zero; no main warm occurred.

### Pinned source materialization

The successful canonical command was:

```text
python3 scripts/materialize_mipstarre.py materialize --archive /tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz --replace-existing
```

It published 337 authenticated files and 105 directories totaling 5,970,111
bytes in `2.935132` s internal time (`2.99` s measured wall time), with
inventory SHA-256
`d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.
It preserved the two authored QPBT files: 5,319 bytes, preservation SHA-256
`0578da860a522b58b69c2c16df366c7eee3abd97c425900401e4e83c992803ed`.

The first invocation omitted `--replace-existing`; it failed closed in `0.05`
s because the post-merge worktree already contained tracked `MIPStarRE/QPBT`.
Inspection confirmed that the canonical replacement path copies the authored
QPBT tree into the authenticated stage before atomic publication. The single
corrected retry succeeded and all four candidate hashes were reauthenticated.

### Lean and blueprint gates

| Command | Result | Measured elapsed | Jobs |
| --- | --- | ---: | ---: |
| `lake env lean MIPStarRE/QPBT/Basic/Field.lean` | pass; only authorized G16 `sorry` warning | 3.84 s | n/a |
| `lake env lean MIPStarRE/QPBT/Basic/Approximation.lean` | pass; no warnings or debt | 4.06 s | n/a |
| `lake --packages=.lake/package-overrides.json build` | pass | 6.07 s | 8,992 |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass; 51 nodes, 12 chapters, acyclic and deterministic | 0.08 s | n/a |
| `python3 blueprint/check.py --check` | pass; 51 nodes, 12 chapters, acyclic and deterministic | 0.08 s | n/a |

Exactly one combined full build was run by this session. Both scoped checks
were sequential in the same private worktree. No other agent compiled this
checkpoint.

## Debt, imports, and hygiene

- Exact debt scan: one `sorry`, at `Field.lean:26`, and no `admit`, `axiom`,
  `constant`, or `opaque` in either source file.
- Exact forbidden-assumption scan: no bridge, residual, repair, witness,
  package, producer, generic `Hypotheses`/`Assumptions`, or `_ofObligations`.
- Field imports are exactly `Mathlib.FieldTheory.Finite.Trace` and
  `Mathlib.FieldTheory.Galois.NormalBasis`.
- Approximation imports are exactly
  `Mathlib.Analysis.Asymptotics.Defs`,
  `Mathlib.Probability.ProbabilityMassFunction.Constructions`,
  `MIPStarRE.Quantum.Measurement`, and
  `MIPStarRE.Quantum.FiniteHilbert`.
- No `MIPStarRE.LDT` import occurs. Approximation contains exactly the five
  requested declarations and no F04 or observable declaration.
- `git diff --check 259c73a..HEAD` passed. Pre-report tracked status was
  exactly `## HEAD (no branch)`.

## Child disposition

The orchestrator launched the already-issued read-only child
`i013-scout-a02-integration-identity` as collaboration task
`/root/i013_first_wave_close/i013_integration_identity`.

- Child report: `/tmp/qpbt-013-integration-identity-a02.md`.
- Child report SHA-256:
  `2e1cda47e46be941e5d9c50115a96a1e2fddf38d5ec235df72f59e3ce22e1f8c`.
- Verdict: approve, findings 0.
- Runtime-measured child evidence interval: `397.242273` s.
- Child token usage: `null`; collaboration backend does not expose per-agent
  token counters.
- Child actions: builds 0, cache operations 0, repository/Git/state/metric
  writes 0, network/endpoint/GitHub/credential actions 0, nested agents 0.

I read the complete child report, independently reproduced its SHA-256,
authenticated its worktree HEAD/tree as the assigned checkpoint, confirmed
detached tracked-clean status, and ran a clean worktree diff check. Its
identity and source-fidelity disposition is accepted. The root coordinator
must import the byte-identical child report into its canonical result-envelope
path; this orchestrator did not write canonical state.

## Metrics and action accounting

- Canonical session start: `2026-09-01T12:28:16.956995Z`.
- Pre-report evidence cut: `2026-09-01T12:37:16.745934120Z`.
- Runtime-measured elapsed through that cut: `539.788939` s.
- Token usage: `null`; reason: the collaboration backend does not expose
  per-agent token counters. No estimate was made.
- Topology: root coordinator -> this QPBT-013 orchestrator -> one read-only
  identity scout. Subagents launched: 1; maximum descendants active: 1.
- Cache operations: seeds 1, hits 1, misses 0, warms 0, lock waits 0,
  cache-owned builds 0.
- Source materialization attempts: 2; successes 1; fail-closed preflight
  failures 1; corrected retries 1.
- Lean/Lake validation attempts: 3; passes 3; failures 0. Full builds: 1.
- Blueprint checks: 2; passes 2; failures 0.
- Findings 0; fix requests 0; new formalization issues 0; protocol changes 0.
- Local validation-substrate incidents: 1 (missing `--replace-existing` on the
  first materializer command). This is the first occurrence in this session;
  no third-occurrence workflow issue or protocol change is warranted.
- Non-gate diagnostic query corrections: 1 (`.prs` was corrected to the
  structured ledger key `.pull_requests`); no acceptance result was affected.
- Source edits 0; candidate edits 0; canonical state/metric writes 0; Git
  index/ref/commit writes 0. Owned report writes: 1.
- Endpoint/model calls 0; external reviews 0; network calls 0; GitHub
  operations 0; credential reads/transmissions 0.

Disposition: QPBT-013's combined first-wave coordination gate is satisfied.
Residual work remains explicitly tracked by G16/K03A and the later F03/F04
issues; none was converted into an assumption or silently treated as complete.
