# LPR-020 / QPBT-031 Independent Review A01

Session: `i031-reviewer-a01-pr020`

Role: fresh read-only local reviewer

Verdict: `approve`

## Findings

No findings. I found no false or drifted statement, undeclared assumption,
unexpected proof debt, import or namespace mismatch, or build failure in the
immutable candidate.

This approval is limited to the declared minimal-skeleton stage. The one
`sorry` at `MIPStarRE.QPBT.fieldDataOfOddExponent` is the frozen G16 exception;
it is not approval of a proof-complete F01 implementation or of the separate
K03A uniform algorithm and complexity claim.

## Source-First Review

I read the pinned paper source before the candidate:

- `references/2001.04383v3/sections/dependencies/finite-fields.tex`, SHA-256
  `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd`;
- the trace, normal-basis, and self-duality definitions at generated lines
  62-83;
- the admissible odd-extension domain and uniform algorithm statement at
  lines 243-307; and
- the algorithm-selected arithmetic contract at lines 350-410.

I then read `docs/paper-gaps/self-dual-normal-basis.md` and the frozen
`F01-SIGNATURES` marker block in
`workflow/reviews/qpbt-023-leaf-contract-a04.md`. The marker payload, with its
terminal newline removed as specified by the metadata contract, has SHA-256
`d888318028c82df942fcac9b81cc944b5f492aebf9902d4cfe32019c37331ad4`,
matching `blueprint/metadata/nodes.json`.

The candidate preserves the source/blueprint split: F01 exposes a concrete
`GaloisField 2 k` mathematical witness selected from only `k` and `Odd k`;
the uniform executable construction, compatible tables, and polynomial cost
remain K03A. `Odd k` entails positivity, so no paper domain premise was lost.

## Immutable Authority

- Base commit: `259c73a368ef7403b4e36e190c9bf940497b300f`
- Base tree: `b3a404a012f9f120f1fa5fa692e51b92d000d615`
- Head commit: `f5ed1cb3e10831b0230f7c28eeef4d94d0335b88`
- Head tree: `b3b368d5fb7cf2bb91c26890b3857cab7882e8b5`
- Relationship: the base is the head's sole direct parent; `merge-base` is the
  exact base.

The sorted manifest encoding is one UTF-8 line per path in the form
`path<TAB>mode<TAB>Git-blob<TAB>SHA-256<LF>`. Its SHA-256 is
`0913e510f0a4392c517cc0f8a546239261744ac238febbe17d706a57eca0f9de`.

| Path | Mode | Git blob | SHA-256 |
| --- | --- | --- | --- |
| `MIPStarRE/QPBT/Basic/Field.lean` | `100644` | `6844e84a08f473dc29620c80392538935348995d` | `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e` |
| `workflow/reviews/qpbt-031-field-skeleton-a01.md` | `100644` | `7430dfae6aa53a13cc2d0dd2df803a20d8610f98` | `584346e9f6709f1e6350ace98ba37730ba3a7654b2fedc52283cc31531526d32` |

The diff adds exactly those two regular files: 54 and 62 lines respectively.
There are no deletions, renames, submodules, or additional changed paths.

## Statement Integrity

| Declaration | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| `FieldData` | Concrete extension `F_(2^k)/F_2` and one chosen basis | `k : Nat`; concrete `GaloisField 2 k`, `Basis (Fin k) (ZMod 2)`, and a generator | Frobenius-orbit normality and trace Kronecker self-duality | The same equations, with zero-based `Fin k` exponent `2^i` | exact mathematical witness data |
| `fieldDataOfOddExponent` | Positive odd `k`; mathematical existence is part of the stronger uniform algorithm statement | `k : Nat`, `Odd k`; no caller-supplied field, basis, witness, algorithm, or obligation | A simultaneous self-dual normal basis; separately, one algorithm emits it and tables in polynomial time | Noncomputable pointwise `FieldData k`; sole G16 `sorry`; no algorithmic claim | faithful boundary for the existence projection |
| `fieldData_nonempty_of_odd` | Same positive odd-extension existence | Same `k` and `Odd k` | Existence of the simultaneous basis | `Nonempty (FieldData k)`, derived only from the declared selector | faithful boundary; no additional debt |
| `fieldTrace` | The basis-independent extension trace `F_(2^k) -> F_2` | Concrete finite-dimensional `GaloisField 2 k` algebra; definition is available for all `k` | Linear extension trace | `Algebra.trace (ZMod 2) (GaloisField 2 k)` | exact on the admissible domain; harmless generalization outside it |
| `FieldData.coordinates` | Downsize coordinates in the chosen basis | A concrete `FieldData k` | Vector-space coordinate bijection | `D.basis.equivFun` | exact encoding |
| `FieldData.multiplicationMatrix` | Multiplication table `K_a` in the chosen basis | `D : FieldData k`, `a : GaloisField 2 k` | Matrix for multiplication by `a` | `LinearMap.toMatrix D.basis D.basis (Algebra.lmul ... a)` | exact encoding |
| `multiplicationMatrix_mulVec_coordinates` | `downsize(ab) = K_a downsize(b)` | The same concrete `D`, `a`, and `b` | Coordinate multiplication identity | The same `Matrix.mulVec` equality | exact |

I inspected the surrounding Mathlib definitions of `Algebra.trace`,
`Algebra.lmul`, `LinearMap.toMatrix`, and
`LinearMap.toMatrix_mulVec_repr`. The proof at `Field.lean:46` uses the explicit
matrix/coordinate lemma and has the correct left-multiplication orientation.

## Proof Debt And Assumptions

The owned Lean file contains exactly one textual `sorry`, at
`MIPStarRE/QPBT/Basic/Field.lean:26`, inside the frozen
`fieldDataOfOddExponent` declaration. It contains no `axiom`, `constant`,
generic `Hypotheses` or `Assumptions`, `_ofObligations` helper, bridge,
residual, repair, producer, or caller-supplied witness premise.

An independent `#print axioms` scan showed:

- `FieldData.multiplicationMatrix_mulVec_coordinates` depends only on
  `propext`, `Classical.choice`, and `Quot.sound`, and not `sorryAx`;
- `fieldData_nonempty_of_odd` depends on `sorryAx` only transitively through
  the one declared G16 selector.

Thus the nonempty and matrix theorems add no independent proof hole.

## Validation

| Command or check | Result |
| --- | --- |
| direct-parent, ancestry, tree, path, mode, blob, and SHA-256 authentication | pass |
| byte comparison of both manifest files between review and seeded candidate worktrees | pass |
| `lake env lean MIPStarRE/QPBT/Basic/Field.lean` in the exact seeded candidate worktree | pass in 3.02 s; only the declared G16 `sorry` warning; max RSS 2,856,988 KiB |
| `lake build` in the exact private candidate worktree | pass in 6.07 s; 8,992 jobs; max RSS 946,580 KiB |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass in 0.08 s; 51 nodes, 12 chapters, acyclic, deterministic |
| `python3 blueprint/check.py --check` | pass in 0.07 s; 51 nodes, 12 chapters, acyclic, deterministic |
| `git diff --check 259c73a368ef7403b4e36e190c9bf940497b300f..f5ed1cb3e10831b0230f7c28eeef4d94d0335b88` | pass in less than 0.01 s |
| read-only `#print axioms` source scan | pass in 2.86 s |
| tracked status before and after scoped/full validation | clean |

The writer report truthfully recorded that the writer had not run a full
project build. The missing pre-review gate was completed during this A01 review
under explicit coordinator authorization, using only the issue's private,
previously seeded `.lake` tree. No main cache warm or shared writable build
output was used.

## Validation-Substrate Incident

The detached review worktree was initially provisioned without a private Lake
seed. The first required scoped command there ran for 30.0 seconds, emitted
`info: mathlib: cloning https://github.com/leanprover-community/mathlib4`, and
returned no Lean verdict before the process ended. It left only the ignored
directories `.lake/` and `.lake/packages/`; tracked status remained clean, and
no active process remained. I did not seed, continue, or reuse that partial
state.

The coordinator then explicitly authorized the successful read-only scoped
check in the already seeded writer worktree after exact HEAD/tree, cleanliness,
and byte-equality authentication. This execution incident does not change the
candidate verdict, but it should inform review-worktree provisioning metrics.

## Metrics And Actions

- Ledger start: `2026-09-01T12:09:40.598840Z`
- Last validation timestamp: `2026-09-01T12:15:28.023473Z`
- Runtime-measured review interval through last validation: `347.424633` s
- Backend: `codex-collaboration`
- Token usage: `null`
- Token availability reason: collaboration backend does not expose per-agent
  token usage
- Topology: root coordinator -> one fresh reviewer; nested subagents: `0`
- Tracked candidate/repository/Git-ref/state/metric edits: `0`
- Reviewer report files written: `1` (this `/tmp` report)
- Findings: `0`; fix requests: `0`; issues opened: `0`
- External reviewer or model launches: `0`; endpoint calls: `0`
- Dependency-network initialization attempts: `1` (the incomplete unseeded
  Lake invocation disclosed above)
- GitHub writes: `0`; credential reads/transmissions: `0`
- Main-cache warms: `0`; private full builds: `1`

## Residual Risk

G16 remains real proof debt and must be discharged by a simultaneous
self-dual-normal-basis existence proof before the proof-complete stage. K03A
must still formalize the paper's uniform deterministic basis/table algorithm,
representation coherence, and polynomial bounds. Those are declared future
obligations, not defects in this minimal-skeleton candidate.
