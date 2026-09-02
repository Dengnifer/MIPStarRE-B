# QPBT-032 F04 Contract Correction A01

## Verdict and supersession

This report corrects two source-fidelity defects in the frozen F04 contract
before the affected Lean laws are implemented. It supersedes only the
`F04-CONSISTENCY-SIGNATURES` and `F04-DISTANCE-LAWS-SIGNATURES` blocks in
`workflow/reviews/qpbt-023-leaf-contract-a04.md`. The historical report remains
unchanged.

- GitHub issue: `#32`, `fix(blueprint/F04): restore source-faithful consistency laws`.
- Session: `i032-orchestrator-a01-f04-contract-correction`.
- Exact base commit: `4a6683795a71712d6a5c52b7539c2f532fd39f71`.
- Exact base tree: `66b39bdec8764c71aad5544a3ca8581ced44dbfb`.
- Authored scope: `blueprint/metadata/nodes.json`,
  `blueprint/metadata/gaps.json`,
  `docs/paper-gaps/f04-consistency-laws.md`, and this report.
- Lean files are not changed and no proof is claimed.

## Authenticated source evidence

| Input | Identity | SHA-256 |
| --- | --- | --- |
| arXiv source archive | `arXiv:2001.04383v3` | `d645cd51dd26cae59195e61aeeb5c886a254ef4adf15da7e5657ad90c7ec2174` |
| Primary TeX | `references/2001.04383v3/source/compression_arXiv_v3.tex` | `38b3e662bb85bb902fcd056436fe9ecbe9e68d1990a074d0c0c12b39d5972ea9` |
| Distance split | `references/2001.04383v3/sections/dependencies/strategies-distance.tex` | `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f` |
| Source pin | `references/2001.04383v3/source-pin.json` | `66a1e9db74f1454ce50909728a3b741f9da468b5d61902645557793ceb91ac9c` |
| Split manifest | `references/2001.04383v3/split-manifest.json` | `052cfaceb2e4a7b59778936ceb3daea9a33e3592e01b902cb2a9740c58999a20` |
| Upstream Lean archive | commit `507e81220d95266ff3d589d125b2f87c7300a9fb` | `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc` |
| Upstream materialized tree | 337-file inventory | `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db` |
| Upstream data processing | `MIPStarRE/LDT/Preliminaries/ComparisonCore.lean` | `f148d77e457645b12139b638ba783a13f0e45943f231a4cc4dd348972f4cab9b` |
| Upstream consistency triangle | `MIPStarRE/LDT/Preliminaries/Triangles/SimEq.lean` | `6ed102b06eb3ab080b816fc8592a4418deb6f71911517c7669bc08fa85346a48` |
| Superseded signature report | `workflow/reviews/qpbt-023-leaf-contract-a04.md` | `45dfbb3142df500eff3260d89055c4763c543036d62fad2ff3b32c9b036b0f0f` |

The task packet's abbreviated `sections/strategies-distance.tex` path is not a
materialized manifest path. The authenticated split is
`sections/dependencies/strategies-distance.tex`; its requested lines 391-395
are Fact 4.26.

Primary TeX line 311 expands `\abc[delta]` to the opposite-tensor-factor
`\simeq_delta` relation. Fact 4.26 at original lines 3274-3278 therefore
preserves cross-player POVM consistency under common postprocessing, not
same-space measurement-family distance. Proposition 4.29 at original lines
3266-3271 is stated for a quantum state and keeps premise order `AB/epsilon`,
`CB/delta`, `CD/gamma` before its
`epsilon + 2 * sqrt (delta + gamma)` conclusion.

The upstream guides independently confirm both readings:
`simeqDataProcessing_heterogeneous` is at `ComparisonCore.lean:464-475`, and
`simeqTriangleInequality_heterogeneous` is at `Triangles/SimEq.lean:125-145`.
The latter explicitly takes normalized `psi` before the four measurement
families. Its finite-distribution mass condition is supplied by the QPBT PMF.

## Corrected F04 consistency signatures

<!-- BEGIN F04-CONSISTENCY-CORRECTED-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uQuestion uOutcome uCoord uAlice uBob

def MeasurementConsistentOn
    {Outcome : Type uOutcome} {Coord : Type uCoord}
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (psi : EuclideanSpace Complex (Coord × Coord))
    (M : MIPStarRE.Quantum.Measurement Outcome Coord) : Prop :=
  ∀ a,
    operatorAction (aliceLocal (Bob := Coord) (M.effect a)) psi =
      operatorAction (bobLocal (Alice := Coord) (M.effect a)) psi

noncomputable def povmConsistencyValue
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MeasurementFamily Question Outcome Alice)
    (B : MeasurementFamily Question Outcome Bob) : Real :=
  ∑ x, (mu x).toReal *
    ∑ a, ∑ b ∈ (Finset.univ.erase a),
      Complex.re (inner Complex psi
        (operatorAction
          (aliceLocal (Bob := Bob) ((A x).effect a) *
            bobLocal (Alice := Alice) ((B x).effect b)) psi))

def POVMConsistencyBoundedBy
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : PMF Question)
    (psi : EuclideanSpace Complex (Alice × Bob))
    (A : MeasurementFamily Question Outcome Alice)
    (B : MeasurementFamily Question Outcome Bob)
    (delta : NNReal) : Prop :=
  povmConsistencyValue mu psi A B ≤ (delta : Real)

def POVMConsistencyBigO
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex (Alice × Bob))
    (A : Nat -> MeasurementFamily Question Outcome Alice)
    (B : Nat -> MeasurementFamily Question Outcome Bob)
    (delta : ErrorProfile) : Prop :=
  IsBigOAtTop
    (fun n => povmConsistencyValue (mu n) (psi n) (A n) (B n))
    (fun n => (delta n : Real))

def POVMConsistencyBigOTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex (Alice × Bob))
    (hpsi : ∀ n, ‖psi n‖ = 1)
    (A C : Nat -> MeasurementFamily Question Outcome Alice)
    (B D : Nat -> MeasurementFamily Question Outcome Bob)
    (epsilon delta gamma : ErrorProfile) : Prop :=
  POVMConsistencyBigO mu psi A B epsilon ->
  POVMConsistencyBigO mu psi C B delta ->
  POVMConsistencyBigO mu psi C D gamma ->
  IsBigOAtTop
    (fun n => povmConsistencyValue (mu n) (psi n) (A n) (D n))
    (fun n => (epsilon n : Real) +
      2 * Real.sqrt ((delta n : Real) + (gamma n : Real)))

theorem povmConsistencyBigO_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex (Alice × Bob))
    (hpsi : ∀ n, ‖psi n‖ = 1)
    (A C : Nat -> MeasurementFamily Question Outcome Alice)
    (B D : Nat -> MeasurementFamily Question Outcome Bob)
    (epsilon delta gamma : ErrorProfile) :
    POVMConsistencyBigOTriangleLaw
      mu psi hpsi A C B D epsilon delta gamma

end MIPStarRE.QPBT
```
<!-- END F04-CONSISTENCY-CORRECTED-SIGNATURES -->

`hpsi` is deliberately positioned after `psi`, before `A C` and `B D`, in
both the Law and theorem. No premise, profile order, or square-root scale is
changed.

`MeasurementConsistentOn` remains a reusable generalization over arbitrary
qualified POVMs. Paper Definition 3.2 assumes that `M` is projective, so every
paper-labelled use must separately supply projectivity. The general predicate
must not itself be cited as the complete paper definition without that premise.

## Corrected F04 distance-law signatures

<!-- BEGIN F04-DISTANCE-LAWS-CORRECTED-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uQuestion uOutcome uOutcome' uCoord uAlice uBob

def FiniteMeasurementTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B C : MeasurementFamily Question Outcome Coord)
    (delta epsilon : NNReal) : Prop :=
  MeasurementFamilyDistanceBoundedBy mu psi A B delta ->
  MeasurementFamilyDistanceBoundedBy mu psi B C epsilon ->
  MeasurementFamilyDistanceBoundedBy mu psi A C
    (2 * (delta + epsilon))

def MeasurementFamiliesBigOTriangleLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex Coord)
    (A B C : Nat -> MeasurementFamily Question Outcome Coord)
    (delta epsilon : ErrorProfile) : Prop :=
  MeasurementFamiliesBigO mu psi A B delta ->
  MeasurementFamiliesBigO mu psi B C epsilon ->
  IsBigOAtTop
    (fun n => measurementFamilyDistanceValue (mu n) (psi n) (A n) (C n))
    (fun n => (delta n : Real) + (epsilon n : Real))

def POVMConsistencyBigOPostprocessLaw
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex (Alice × Bob))
    (A : Nat -> MeasurementFamily Question Outcome Alice)
    (B : Nat -> MeasurementFamily Question Outcome Bob)
    (f : Outcome -> Outcome') (delta : ErrorProfile) : Prop :=
  POVMConsistencyBigO mu psi A B delta ->
  POVMConsistencyBigO mu psi
    (fun n => MeasurementFamily.postprocess (A n) f)
    (fun n => MeasurementFamily.postprocess (B n) f) delta

theorem finiteMeasurement_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : PMF Question) (psi : EuclideanSpace Complex Coord)
    (A B C : MeasurementFamily Question Outcome Coord)
    (delta epsilon : NNReal) :
    FiniteMeasurementTriangleLaw mu psi A B C delta epsilon

theorem measurementFamiliesBigO_triangle
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Coord : Type uCoord}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex Coord)
    (A B C : Nat -> MeasurementFamily Question Outcome Coord)
    (delta epsilon : ErrorProfile) :
    MeasurementFamiliesBigOTriangleLaw mu psi A B C delta epsilon

theorem povmConsistencyBigO_postprocess
    {Question : Type uQuestion} {Outcome : Type uOutcome}
    {Outcome' : Type uOutcome'}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Outcome'] [DecidableEq Outcome']
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (mu : Nat -> PMF Question)
    (psi : Nat -> EuclideanSpace Complex (Alice × Bob))
    (A : Nat -> MeasurementFamily Question Outcome Alice)
    (B : Nat -> MeasurementFamily Question Outcome Bob)
    (f : Outcome -> Outcome') (delta : ErrorProfile) :
    POVMConsistencyBigOPostprocessLaw mu psi A B f delta

end MIPStarRE.QPBT
```
<!-- END F04-DISTANCE-LAWS-CORRECTED-SIGNATURES -->

The superseded `MeasurementFamiliesPostprocessLaw` and
`measurementFamiliesBigO_postprocess` are not retained. No current consumer
requires a same-space distance-postprocessing auxiliary, and retaining one in
this paper-labelled block would obscure the corrected source contract.

## Statement integrity

| Declaration | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| `MeasurementConsistentOn` | A projective measurement `M` on a bipartite state with equal local actions | A qualified finite POVM and explicit same coordinate type; projectivity is separate | Exact consistency of projective `M` | Reusable action equality, with paper call sites required to add projectivity | faithful boundary |
| `POVMConsistencyBigOTriangleLaw` / `povmConsistencyBigO_triangle` | Normalized bipartite state; `AB` at `epsilon`, `CB` at `delta`, `CD` at `gamma` | Indexed PMF/state/families over explicit finite Alice/Bob carriers; `hpsi : forall n, norm (psi n) = 1` immediately after `psi` | `AD` consistency at `epsilon + 2*sqrt(delta+gamma)` | The same premise order and exact real-valued scale under explicit normalization | faithful boundary |
| `FiniteMeasurementTriangleLaw` / `finiteMeasurement_triangle` | Consecutive state-dependent-distance bounds | Explicit finite PMF, state, common coordinate space, and NNReal bounds | Triangle bound up to a universal constant | Exact squared-norm bound with factor `2` | exact |
| `MeasurementFamiliesBigOTriangleLaw` / `measurementFamiliesBigO_triangle` | Consecutive indexed distance relations | The same data with `[0,1]` input profiles and real-valued derived scale | `O(delta + epsilon)` distance | The same atTop Big-O implication, absorbing the finite factor | exact |
| `POVMConsistencyBigOPostprocessLaw` / `povmConsistencyBigO_postprocess` | Heterogeneous Alice/Bob POVMs, bipartite state, cross-player consistency, shared outcome map | Distinct finite Alice/Bob coordinate types, indexed PMF/state/families, `POVMConsistencyBigO`, and one explicit `f` on both sides | Common postprocessing preserves consistency at the same error | The same heterogeneous implication before and after `MeasurementFamily.postprocess` | exact |

The current `StrategyStateChoice` API is also intentionally described more
precisely in metadata. `StrategyFamiliesBigO ... choice` is a choice-indexed
helper; the paper's "either state" strategy-distance clause existentially
chooses a shared branch. The source does not explicitly settle separate
Alice/Bob choices, so this report records the singular shared-choice reading
without adding a new declaration in this correction.

## Dependency and gap disposition

`F04-DISTANCE-LAWS` now directly depends on `F04-CONSISTENCY`, because its
Fact 4.26 declarations consume `POVMConsistencyBigO`. Its transitive definition
list is updated accordingly. Gap `G17` reciprocally links
`F04-CONSISTENCY` and `F04-DISTANCE-LAWS` and points to
`docs/paper-gaps/f04-consistency-laws.md` for the full disposition.

This is a corrected plan, not a public assumption or a completed theorem. The
Law definitions remain statement contracts whose named theorems must later be
proved without added obligations.

## Materialization and validation record

The ignored source artifacts were materialized only to read and validate the
contract. They remain unstaged and are not part of the candidate.

| Command | Result | Duration |
| --- | --- | ---: |
| `python3 scripts/reference_source.py materialize` | published and verified 39 files / 646 labels; archive and member hashes matched | 2.28 s |
| `curl .../507e81220d95266ff3d589d125b2f87c7300a9fb` | downloaded exact 1,989,153-byte archive; SHA-256 matched | transport completed; wrapper duration unavailable |
| `python3 scripts/materialize_mipstarre.py materialize --archive ... --replace-existing` | published and verified 337 files; source commit and inventory matched | 3.64 s |

There were three harmless preflight failures. The first paper materialization
attempt was blocked by sandboxed networking in 0.22 s and the approved retry
succeeded. The first upstream `curl` attempt was blocked by DNS in 0.00 s and
the approved retry produced the exact pinned archive. The first upstream
materializer call omitted `--replace-existing`; it preserved the authored QPBT
subtree and exited in 0.05 s. The reviewed `--replace-existing` path then copied
that subtree into the authenticated upstream tree and verified it. No ignored
artifact was staged.

### Authored validation

| Command | Result | Duration |
| --- | --- | ---: |
| `python3 -m unittest blueprint.tests.test_check` | pass, 32 tests | 1.83 s |
| `python3 scripts/reference_source.py verify` | pass, 39 files / 646 labels, inventory `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4` | 0.15 s |
| `python3 scripts/materialize_mipstarre.py verify` | pass, 337 files, pinned inventory | 0.10 s |
| `python3 scripts/workflow.py validate` | pass, 53 issues / 28 local PRs / 433 issued sessions / 7 stages | 0.18 s |
| `python3 blueprint/check.py --check --source-root references/2001.04383v3` | expected authored-only failure: exactly four stale generated outputs; no source or metadata error | 0.13 s |
| `python3 blueprint/check.py --check` | expected authored-only failure: the same exact four stale generated outputs | 0.12 s |
| temporary-copy `python3 blueprint/check.py --write` | pass, 54 nodes / 12 chapters / acyclic graph | 0.12 s |
| temporary-copy `python3 blueprint/check.py --check` | pass immediately after generation; generator idempotence verified | 0.12 s |
| `git diff --check` | pass | 0.03 s |

Root intentionally serialized generated output into a later, separately owned
writer. The exact stale/required output set, determined both by the canonical
checker and a recursive comparison against the clean temporary generation, is:

| Deferred generated path | Expected SHA-256 |
| --- | --- |
| `blueprint/generated/graph.json` | `6b86fb25e0fcb23cf15814c4a4380d434b10ed148a35224fa47bd3a05644b85d` |
| `blueprint/generated/graph.dot` | `889fb76e7a18029485ca0db7738629dd2d03eb53e123236e5b5c9772f65650ee` |
| `blueprint/src/generated/chapter-02-entries.tex` | `2b52bd683838160862c8b386ebdb5418f5ece4d982aa08ba5a7276b6baea4d43` |
| `blueprint/src/generated/gaps.tex` | `6b6ee16a4cb3d7fdb8805cf2636c4690fe6efc5065b7d4c876aea441dbeda3e6` |

Every other generated output, including chapter entries 01 and 03 through 12,
is byte-identical to the current worktree. This authored commit therefore does
not claim a passing canonical `--check`; the four-path refresh is its explicit
serial dependency.

### Scout and session metrics

- Actual read-only scout identity:
  `/root/i032_orchestrator_a01_f04_contract_correction/i032_scout_a01_f04_sources`.
  This child was not preconfirmed by root and is recorded as an ungoverned
  actual attempt, not retroactively described as a clean governed lease.
- Scout checks: exact base HEAD; authenticated paper macro, Facts 4.26/4.28 and
  Proposition 4.29; upstream heterogeneous data-processing and triangle APIs;
  F04 metadata/signature pointers; final `git status --short` empty.
- Scout writes, builds, generators, network calls, and nested agents: zero.
- Scout elapsed time: unavailable; the collaboration result exposes no elapsed
  counter. Scout token usage: unavailable; no per-agent token counter is
  exposed. No estimates were made.
- Topology: root coordinator -> this orchestrator -> one read-only scout. No
  further child sessions were launched.
- This orchestrator's token usage and total session elapsed time are likewise
  unavailable from the collaboration backend. No estimates were made.
- Lean compiles/builds, hot-cache warms/seeds/lock waits, workflow state edits,
  research metric edits, protocol edits, GitHub writes, and generated-path
  writes in the owned worktree: zero.

The one remaining source ambiguity is whether the paper's "either state"
strategy-distance clause permits different choices for the two players. The
singular phrasing favors one shared existential choice; this report documents
that reading but does not alter the choice-indexed helper API. The broader
`MeasurementConsistentOn` domain is not ambiguous: the paper requires
projectivity, while the Lean predicate is deliberately reusable and must be
paired with projectivity at paper-labelled call sites.
