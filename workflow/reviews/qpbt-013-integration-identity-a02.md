# QPBT-013 First-Wave Integration Identity Audit A02

Session: `i013-scout-a02-integration-identity`

Role: fresh read-only child scout

Verdict: `approve`

## Findings

No findings. The exact combined checkpoint preserves both independently
reviewed candidates and satisfies the identity, ownership, statement-fidelity,
and proof-debt parts of the QPBT-013 first-wave closure gate.

This verdict is limited to the minimal first-wave leaf skeleton. The tracked
G16 hole at `MIPStarRE/QPBT/Basic/Field.lean:26` remains real proof debt, and
the binary-observable portion of the broader frozen F03 contract is not part of
QPBT-032/LPR-021. Neither omission may be represented as proof-complete F01 or
complete F03 implementation.

## Immutable Authority

- Audited HEAD: `d60a71c945ebf407b4a1c8c322c38181e7d09dfa`.
- Audited tree: `cbd1b48827acb90615f437ebd9d55d3705d7cc70`.
- HEAD's sole parent: `aa1f579d56b4476220d2d6ef4c69c3c06ae779e2`;
  tree `ee010f3013b09275ba098f2eefdae0c95c66b704`.
- Worktree remained detached and tracked-clean through the pre-write evidence
  cut.

The integration ancestry is exact:

| Merge | Tree | First parent | Second parent |
| --- | --- | --- | --- |
| `ff79fe3444eae7015def65039cac62ec213e8ed4` | `87c31cc240bda87c69c0653a5c79120d237b2a6c` | `152d4d12c2eca74bfdf30dd674355833a2e61d2f` | Field candidate `f5ed1cb3e10831b0230f7c28eeef4d94d0335b88` |
| `aa1f579d56b4476220d2d6ef4c69c3c06ae779e2` | `ee010f3013b09275ba098f2eefdae0c95c66b704` | `ff79fe3444eae7015def65039cac62ec213e8ed4` | Approximation candidate `00b74473b04a72b57c7c7b9ebdfd9ad7ef17a99f` |

All four `merge-base --is-ancestor` checks passed: each candidate is an
ancestor of its merge, the Field merge is an ancestor of the Approximation
merge, and the Approximation merge is an ancestor of audited HEAD. Each
candidate has the exact common base
`259c73a368ef7403b4e36e190c9bf940497b300f` as its sole parent.

## Candidate Blob Preservation

The four candidate blobs are byte-identical at audited HEAD:

| Candidate | Path | Mode | Git blob | SHA-256 |
| --- | --- | --- | --- | --- |
| Field | `MIPStarRE/QPBT/Basic/Field.lean` | `100644` | `6844e84a08f473dc29620c80392538935348995d` | `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e` |
| Field | `workflow/reviews/qpbt-031-field-skeleton-a01.md` | `100644` | `7430dfae6aa53a13cc2d0dd2df803a20d8610f98` | `584346e9f6709f1e6350ace98ba37730ba3a7654b2fedc52283cc31531526d32` |
| Approximation | `MIPStarRE/QPBT/Basic/Approximation.lean` | `100644` | `b3eb1b1eee2860b83b71659add650b9ff3e8ed4c` | `13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a` |
| Approximation | `workflow/reviews/qpbt-032-approximation-skeleton-a01.md` | `100644` | `a1b56a0024f8bb89d8f18db5c50985cccd6eb136` | `b69eb36ebfa77f2839ff7a5c4c84a6fed011aae2eb30140a4fcd64ea64575320` |

Path-limited diffs from each candidate to audited HEAD were empty. First-parent
merge diffs add the corresponding Lean file and writer report, with no rename,
deletion, submodule, or extra candidate path. Across both merges there are
exactly two Lean source paths:

```text
MIPStarRE/QPBT/Basic/Field.lean
MIPStarRE/QPBT/Basic/Approximation.lean
```

The later checkpoint commit changes only `workflow/events.jsonl`,
`workflow/state/issues.json`, and `workflow/state/prs.json`; it changes no Lean
source or candidate report blob. All relevant candidate and merge diff checks
passed.

## Source And Contract Authentication

I read the pinned paper sources before judging the integrated Lean:

- `finite-fields.tex`, SHA-256
  `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd`,
  especially lines 19-41, 62-83, 243-307, and 350-410;
- `measurements.tex`, SHA-256
  `b3c03f8f4f1cbe979ee12e9db26227c9bb84c483c4743f1de988c4c38d80f946`,
  especially lines 3-19 and 34-47; and
- the authenticated upstream `MIPStarRE.Quantum.Measurement` source read
  directly from archive SHA-256
  `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.
  The source file SHA-256 is
  `c84a712e34425a46ae17d9f04d789ae7393ae97da3cf7ee3f93fe0e6705b9d0d`.

The frozen contract report SHA-256 is
`45dfbb3142df500eff3260d89055c4763c543036d62fad2ff3b32c9b036b0f0f`.
I independently reproduced its stripped marker-block hashes:

| Marker | SHA-256 | Blueprint value |
| --- | --- | --- |
| `F01-SIGNATURES` | `d888318028c82df942fcac9b81cc944b5f492aebf9902d4cfe32019c37331ad4` | exact match |
| `F03-SIGNATURES` | `8de7983b66b2cce523b45bb3b14a788ac34b0315be91644610cf455b5306b065` | exact match |

The candidate, independent-review, and adoption/binding reports were all read
as untrusted evidence and authenticated at these SHA-256 values:

| Lane | Candidate report | Review report | Binding report |
| --- | --- | --- | --- |
| QPBT-031/LPR-020 | `584346e9f6709f1e6350ace98ba37730ba3a7654b2fedc52283cc31531526d32` | `bdcc1f4cd303321b5b0e03243734aedde732652fd44324fc6e418b36730f895f` | `e2b9501101ad3e8d574e7a361a1ee11664e0d4dd3d760b383a959c198edc28a7` |
| QPBT-032/LPR-021 | `b69eb36ebfa77f2839ff7a5c4c84a6fed011aae2eb30140a4fcd64ea64575320` | `e8905f21662e89826aceec073604954b625c7b2c91a837ac399d32b0bb69ebe9` | `f1e0ecb1a557c93cbcc4afc86a2f41af4c3b9b1ea075c1a5e65cae05e38a9471` |

Both PR records are merged, bind the exact candidate heads above, identify
fresh independent approving reviewers with zero findings, and record guarded
integration. Both child issues are done. QPBT-013 itself remains open pending
the coordinator's combined build and closure evidence; this report does not
substitute for that separate build gate.

## Statement Integrity

| Lean declaration(s) | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| `FieldData` (`Field.lean:15-21`) | The concrete extension `F_(2^k)/F_2` and a simultaneous normal, trace-self-dual basis | `k : Nat`; concrete `GaloisField 2 k`; `Fin k` basis and one generator | Frobenius-orbit basis with trace pairing equal to the Kronecker delta | The same orbit and trace equations with the paper's zero-based exponents | exact witness encoding |
| `fieldDataOfOddExponent`, `fieldData_nonempty_of_odd` (`Field.lean:24-30`) | Positive odd `k`; existence is contained in the paper's stronger uniform algorithm theorem | `k : Nat`, `Odd k`; no caller-provided basis, witness, algorithm, bridge, or obligation | A simultaneous self-dual normal basis; separately, one algorithm also emits compatible tables in polynomial time | Noncomputable pointwise `FieldData k` selection and its `Nonempty` projection; the selector is the sole declared G16 `sorry`; no algorithmic claim | faithful boundary |
| `fieldTrace` (`Field.lean:32-34`) | Extension trace `F_(2^k) -> F_2` | Concrete `GaloisField 2 k` algebra | Basis-independent linear trace | `Algebra.trace (ZMod 2) (GaloisField 2 k)` | exact on the admissible domain; harmless totalization outside it |
| coordinates and multiplication matrix (`Field.lean:36-52`) | Coordinates in the chosen basis and `downsize(ab) = K_a downsize(b)` | The same `FieldData k`, `a`, and `b` | Coordinate equivalence and left-multiplication table identity | `Basis.equivFun`, `LinearMap.toMatrix`, and the same `Matrix.mulVec` equality | exact encoding |
| `MeasurementFamily` (`Approximation.lean:25-30`) | A finite-outcome POVM for each question | Arbitrary question type; finite decidable outcome and coordinate types; qualified finite-dimensional complete `Quantum.Measurement` | A POVM family indexed by questions | A function into effects that are positive and sum to identity | faithful finite-dimensional boundary |
| `ProjectiveMeasurementFamily` (`Approximation.lean:33-39`) | Each effect of each measurement is a projector | The same family | Pointwise `M_a^2 = M_a` | The identical pointwise idempotence equation | exact |
| `postprocess`, `postprocess_effect` (`Approximation.lean:44-64`) | Arbitrary outcome map and sum over its fibers | Finite decidable source/target outcomes; qualified upstream postprocess | Relabeled POVM with effect `sum_(a:f(a)=b) M_a` | Delegated complete POVM and the identical filtered finite sum | exact |
| empty-fiber theorem (`Approximation.lean:66-82`) | `b` outside the image of `f` | Explicit `b notin Set.range f` | The empty fiber has zero effect | The filtered sum is proved empty and equals zero | exact |

`Odd k` supplies the paper's positivity requirement. The F01 selection does not
claim the paper's uniform deterministic algorithm, multiplication-table output,
or polynomial cost; those remain K03A. QPBT-032 intentionally stops after the
five finite measurement-family/postprocess declarations, so the observable
portion of F03 remains future work rather than a drifted theorem.

## Debt, Imports, And Scope

- `Field.lean` imports exactly `Mathlib.FieldTheory.Finite.Trace` and
  `Mathlib.FieldTheory.Galois.NormalBasis`.
- `Approximation.lean` imports exactly the four frozen modules:
  `Mathlib.Analysis.Asymptotics.Defs`,
  `Mathlib.Probability.ProbabilityMassFunction.Constructions`,
  `MIPStarRE.Quantum.Measurement`, and
  `MIPStarRE.Quantum.FiniteHilbert`.
- The combined owned source contains exactly one `sorry`, at the authorized G16
  selector. It contains no `admit`, `axiom`, `constant`, `opaque`, generic
  `Hypotheses`/`Assumptions`, `_ofObligations` helper, bridge, residual, repair,
  producer, caller-supplied witness premise, or `MIPStarRE.LDT` import.
- The Approximation source contains no proof debt. No F04 or observable
  declaration was smuggled into its declared first-wave scope.

## Timing, Topology, And Actions

- Canonical session start: `2026-09-01T12:28:17.292153Z`.
- Pre-write evidence cut: `2026-09-01T12:34:54.534425573Z`.
- Runtime-measured elapsed through that cut: `397.242273` seconds.
- Timing quality: runtime-measured; coordinator lifecycle timing remains
  authoritative for archival.
- Token usage: `null`; reason: the collaboration backend does not expose
  per-agent token counters, so no estimate was made.
- Topology: root coordinator -> QPBT-013 orchestrator -> this read-only scout.
  Nested agents launched by this scout: `0`.
- Findings: `0`; fix requests: `0`; new issues: `0`; protocol changes: `0`.
- Lean checks/builds: `0`; cache warms/seeds/lock waits: `0`.
- Repository, Git ref/index, canonical state, and metric writes: `0`.
  Report writes: `1` (this `/tmp` file only).
- Endpoint/model calls: `0`; network calls: `0`; GitHub operations: `0`;
  credential reads/transmissions: `0`.
- Source-path retries: `1`. The ignored split-paper files were absent from the
  detached worktree, so the same pinned files were read from the primary local
  workspace. No network or mutable fallback was used and no incident or
  protocol change is warranted.

Disposition: approve the exact identity and statement-fidelity portion of
QPBT-013 first-wave closure. Residual risk is confined to the explicitly
declared future work: G16, K03A, the remaining F03 observable boundary, and all
later F04 declarations.
