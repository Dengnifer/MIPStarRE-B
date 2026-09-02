# QPBT-054 executable CL contract repair (A01)

Session: `i054-orchestrator-a01-f06a-contract`
Role: sole QPBT-054 blueprint writer
Base: `639c883737e07b91156a9cbc31ec1aa65100a935`

## Verdict

The F06A executable conditionally-linear contract is now an elaborated Lean
boundary rather than prose shaped like Lean.  A sampler query is indexed by a
positive index proof, has exactly the four paper modes, and carries actual
dependent prefix-range and factor-space inputs.  The selected decomposition
records the marginal, partition, support, dependency, sum, and top-level laws
from Lemma `lem:cl-kth` as quantified data and equations; it has no naked
`Prop` fields.

The machine wrapper contains an actual `Turing.FinTM2`.  Its correctness data
is a `Turing.TM2OutputsInTime` execution, and the runtime of a query is the
execution's `toEvalsTo.steps`, not a caller-provided step function.  `time n`
is definitionally the finite supremum over every well-typed query when
`0 < n`, and zero only at Lean's out-of-paper index zero.  The six logical
tapes remain visible before an injective fixed-order packing into Mathlib's
single input stack.

Executable downsizing is internally indexed by the canonical representation
width `s n * Q.exponent n`.  The public dimension theorem identifies this with
the paper's `s n * Nat.log 2 (Q.fieldSize n)`.  This is the same quantity by
`Nat.log_pow` and avoids inserting dependent casts into every associated-map
and PMF statement.

## Source evidence

No network or source materialization was used.  The source is the authenticated
ignored tree at `/home/drx/MIPStarRE-auto/references/2001.04383v3`.

| Source | SHA-256 | Clauses used |
| --- | --- | --- |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` | `lem:cl-kth` at 150-281; sampler/query modes at 553-626; downsizing and runtime at 628-712 |
| `top-level/preliminaries.tex` | `045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1` | positive naturals and global `O` at 1-35; machine execution at 37-143 |
| `dependencies/finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` | fixed-coordinate bit representation and basis algorithm at 234-411 |

The paper modes become the following exact tape layouts.  `n`, `j`, vector,
and indicator encodings are those in the signature manifest below.

| Mode | Tape 0 | Tape 1 | Tape 2 | Tape 3 | Tape 4 | Tape 5 |
| --- | --- | --- | --- | --- | --- | --- |
| dimension | `n` | `00` | ignored | ignored | ignored | ignored |
| marginal | `n` | side | `01` | `j` | `z` | ignored |
| linear | `n` | side | `10` | `j` | valid prefix `u` | supported `y` |
| factor | `n` | side | `11` | `j` | valid prefix `u` | ignored |

Here paper stage `j` is encoded by `j.val + 1`, so Lean's `Fin ell` index has
exactly the paper range `{1, ..., ell}`.

## Paper gaps retained

- `A02-002`: the phrase "the number of steps before the sampler halts for
  index n" does not aggregate the dimension, marginal, linear, and factor
  inputs.  The faithful finite boundary takes the exact maximum over all typed
  valid queries and excludes malformed raw strings.
- `A02-004`: the linear bullet says only that `u` is in a "previous marginal
  range" and omits the domain of `y`; the factor bullet uses
  `u in L_{<j}(V)`.  `CLPrefix` uses that range and `CLFactorInput` uses the
  selected coordinate factor.  These are type repairs, not stronger paper
  assumptions.
- `A02-005/G16/K03A`: the source requires the algorithm-selected field basis
  and multiplication tables.  `fieldCodec` is a definition from F01's selected
  `FieldData`; no codec or coherence premise is exposed to a caller.  The
  construction theorem remains the tracked G16/K03A work.
- `A02-006`: the paper's runtime proof mentions factor-indicator output but
  omits parsing, prefix inversion, and machine composition costs.  The public
  `downsize_time` remains the exact source theorem and must be proved by the
  implementation; no compiler-cost assumption is added.

## Corrected signature manifest

This is a declaration-header manifest.  Concrete bodies shown below are part
of the frozen semantics.  For headers whose implementation is intentionally
omitted, the whole-block probe inserted `:= by sorry` only in `/tmp`; the
repository contains no Lean proof debt from this contract issue.

<!-- BEGIN F06A-A01-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

noncomputable section

structure AdmissibleFieldFamily where
  exponent : Nat -> Nat
  exponent_odd : forall n, 0 < n -> Odd (exponent n)

def AdmissibleFieldFamily.fieldSize
    (Q : AdmissibleFieldFamily) (n : Nat) : Nat :=
  2 ^ Q.exponent n

noncomputable def AdmissibleFieldFamily.fieldData
    (Q : AdmissibleFieldFamily) (n : Nat) (hn : 0 < n) :
    FieldData (Q.exponent n) :=
  fieldDataOfOddExponent (Q.exponent n) (Q.exponent_odd n hn)

noncomputable def AdmissibleFieldFamily.fieldCodec
    (Q : AdmissibleFieldFamily) (n dimension : Nat) (hn : 0 < n) :
    Computability.Encoding (FieldVector (Q.exponent n) dimension) Bool

def binaryFieldFamily : AdmissibleFieldFamily where
  exponent := fun _ => 1
  exponent_odd := by
    intro n hn
    exact odd_one

def RuntimeBigO (f g : Nat -> Nat) : Prop :=
  Exists fun C : Real => 0 < C ∧ forall n, 0 < n ->
    (f n : Real) <= C * (g n : Real)

abbrev SixTapeInput := Fin 6 -> List Bool

def SixTapeInput.ofLists
    (tape0 tape1 tape2 tape3 tape4 tape5 : List Bool) : SixTapeInput :=
  ![tape0, tape1, tape2, tape3, tape4, tape5]

namespace CLStage

def pred {ell : Nat} (j : Fin ell) (h : 0 < j.val) : Fin ell

def castLE {ell : Nat} (j : Fin ell) (i : Fin (j.val + 1)) : Fin ell

def last (ell : Nat) (h : 0 < ell) : Fin ell

end CLStage

inductive CLSamplerSide
  | alice
  | bob
  deriving DecidableEq, Fintype

def CLSamplerSide.bits : CLSamplerSide -> List Bool
  | .alice => [false]
  | .bob => [true]

def CLSampler.side {k n ell : Nat} (S : CLSampler k n ell) :
    CLSamplerSide -> ConditionallyLinearMap k n ell
  | .alice => S.alice
  | .bob => S.bob

abbrev CLPrefix {k n : Nat}
    (priorOutput : FieldVector k n -> FieldVector k n) :=
  {u : FieldVector k n // Exists fun x => u = priorOutput x}

abbrev CLFactorInput {k n : Nat} (factor : Finset (Fin n)) :=
  {y : FieldVector k n // forall i, i ∉ factor -> y i = 0}

structure CLQueryDecomposition
    {k n ell : Nat} (L : ConditionallyLinearMap k n ell) where
  marginal : (j : Fin ell) -> ConditionallyLinearMap k n (j.val + 1)
  priorOutput : Fin ell -> FieldVector k n -> FieldVector k n
  priorOutput_zero : forall (j : Fin ell), j.val = 0 ->
    priorOutput j = 0
  priorOutput_succ : forall (j : Fin ell) (h : 0 < j.val),
    priorOutput j = (marginal (CLStage.pred j h)).toFun
  factor : (j : Fin ell) -> CLPrefix (priorOutput j) -> Finset (Fin n)
  linear : (j : Fin ell) -> (u : CLPrefix (priorOutput j)) ->
    FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n
  factor_cover : forall (x : FieldVector k n) (i : Fin n),
    Exists fun j : Fin ell =>
      i ∈ factor j ⟨priorOutput j x, ⟨x, rfl⟩⟩
  factor_disjoint : forall (x : FieldVector k n) (j1 j2 : Fin ell),
    j1 ≠ j2 -> Disjoint
      (factor j1 ⟨priorOutput j1 x, ⟨x, rfl⟩⟩)
      (factor j2 ⟨priorOutput j2 x, ⟨x, rfl⟩⟩)
  linear_supported : forall (j : Fin ell) (u : CLPrefix (priorOutput j))
      (y : FieldVector k n) (i : Fin n),
    i ∉ factor j u -> linear j u y i = 0
  linear_depends : forall (j : Fin ell) (u : CLPrefix (priorOutput j))
      (y : FieldVector k n),
    linear j u (restrictVector (factor j u) y) = linear j u y
  marginal_sum : forall (j : Fin ell) (x : FieldVector k n),
    (marginal j).toFun x =
      ∑ i : Fin (j.val + 1),
        linear (CLStage.castLE j i)
          ⟨priorOutput (CLStage.castLE j i) x, ⟨x, rfl⟩⟩
          (restrictVector
            (factor (CLStage.castLE j i)
              ⟨priorOutput (CLStage.castLE j i) x, ⟨x, rfl⟩⟩) x)
  marginal_top : forall h : 0 < ell,
    (marginal (CLStage.last ell h)).toFun = L.toFun

inductive CLSamplerQuery
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell n : Nat) (hn : 0 < n)
    (associated : CLSampler (Q.exponent n) (s n) ell)
    (decomposition : (w : CLSamplerSide) ->
      CLQueryDecomposition (associated.side w))
  | dimension
  | marginal (w : CLSamplerSide) (j : Fin ell)
      (z : FieldVector (Q.exponent n) (s n))
  | linear (w : CLSamplerSide) (j : Fin ell)
      (u : CLPrefix ((decomposition w).priorOutput j))
      (y : CLFactorInput (k := Q.exponent n)
        ((decomposition w).factor j u))
  | factor (w : CLSamplerSide) (j : Fin ell)
      (u : CLPrefix ((decomposition w).priorOutput j))

noncomputable instance CLSamplerQuery.instFintype
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell n : Nat) (hn : 0 < n)
    (A : CLSampler (Q.exponent n) (s n) ell)
    (D : (w : CLSamplerSide) -> CLQueryDecomposition (A.side w)) :
    Fintype (CLSamplerQuery Q s ell n hn A D)

def CLSamplerQuery.index : CLSamplerQuery Q s ell n hn A D -> Nat :=
  fun _ => n

def CLSamplerQuery.tapes :
    CLSamplerQuery Q s ell n hn A D -> SixTapeInput
  | .dimension =>
      SixTapeInput.ofLists (Computability.encodeNat n) [false, false]
        [] [] [] []
  | .marginal w j z =>
      SixTapeInput.ofLists (Computability.encodeNat n) w.bits [false, true]
        (Computability.encodeNat (j.val + 1))
        ((Q.fieldCodec n (s n) hn).encode z) []
  | .linear w j u y =>
      SixTapeInput.ofLists (Computability.encodeNat n) w.bits [true, false]
        (Computability.encodeNat (j.val + 1))
        ((Q.fieldCodec n (s n) hn).encode u.1)
        ((Q.fieldCodec n (s n) hn).encode y.1)
  | .factor w j u =>
      SixTapeInput.ofLists (Computability.encodeNat n) w.bits [true, true]
        (Computability.encodeNat (j.val + 1))
        ((Q.fieldCodec n (s n) hn).encode u.1) []

def CLSamplerQuery.expectedOutput :
    CLSamplerQuery Q s ell n hn A D -> List Bool
  | .dimension => Computability.encodeNat (s n)
  | .marginal w j z =>
      (Q.fieldCodec n (s n) hn).encode ((D w).marginal j z)
  | .linear w j u y =>
      (Q.fieldCodec n (s n) hn).encode ((D w).linear j u y.1)
  | .factor w j u =>
      List.ofFn (fun i : Fin (s n) => decide (i ∈ (D w).factor j u))

def packSixTapes (input : SixTapeInput) : List Bool :=
  Computability.encodingNatBool.encode (Encodable.encode (List.ofFn input))

theorem packSixTapes_injective : Function.Injective packSixTapes

structure IndexedSixInputBitMachine where
  tm : Turing.FinTM2
  inputAlphabet : tm.Γ tm.k₀ ≃ Bool
  outputAlphabet : tm.Γ tm.k₁ ≃ Bool

def IndexedSixInputBitMachine.outputsInTime
    (M : IndexedSixInputBitMachine) (input : SixTapeInput)
    (output : List Bool) (bound : Nat) :=
  Turing.TM2OutputsInTime M.tm
    ((packSixTapes input).map M.inputAlphabet.symm)
    (some (output.map M.outputAlphabet.symm)) bound

structure IndexedSixInputBitMachine.Execution
    (M : IndexedSixInputBitMachine) (input : SixTapeInput)
    (output : List Bool) where
  bound : Nat
  runInTime : M.outputsInTime input output bound

def IndexedSixInputBitMachine.Execution.steps
    {M : IndexedSixInputBitMachine} {input : SixTapeInput}
    {output : List Bool} (execution : M.Execution input output) : Nat :=
  execution.runInTime.toEvalsTo.steps

structure ExecutableCLSampler
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell : Nat) where
  associated : forall n, CLSampler (Q.exponent n) (s n) ell
  decomposition : forall n (w : CLSamplerSide),
    CLQueryDecomposition ((associated n).side w)
  machine : IndexedSixInputBitMachine
  execution : forall n (hn : 0 < n)
      (query : CLSamplerQuery Q s ell n hn (associated n) (decomposition n)),
    machine.Execution query.tapes query.expectedOutput

def ExecutableCLSampler.correct
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n)
    (query : CLSamplerQuery Q s ell n hn (S.associated n) (S.decomposition n)) :
    Turing.TM2Outputs S.machine.tm
      ((packSixTapes query.tapes).map S.machine.inputAlphabet.symm)
      (some (query.expectedOutput.map S.machine.outputAlphabet.symm)) :=
  Turing.TM2OutputsInTime.toTM2Outputs (S.execution n hn query).runInTime

def ExecutableCLSampler.executedSteps
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n)
    (query : CLSamplerQuery Q s ell n hn (S.associated n) (S.decomposition n)) : Nat :=
  (S.execution n hn query).steps

noncomputable def ExecutableCLSampler.validQueries
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    Finset (CLSamplerQuery Q s ell n hn (S.associated n) (S.decomposition n)) :=
  Finset.univ

noncomputable def ExecutableCLSampler.time
    (S : ExecutableCLSampler Q s ell) (n : Nat) : Nat :=
  if hn : 0 < n then
    (S.validQueries n hn).sup (S.executedSteps n hn)
  else 0

theorem ExecutableCLSampler.time_eq_validQueryMax
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    S.time n = (S.validQueries n hn).sup (S.executedSteps n hn)

noncomputable def ExecutableCLSampler.sample
    (S : ExecutableCLSampler Q s ell) (n : Nat) :
    PMF (FieldVector (Q.exponent n) (s n) ×
      FieldVector (Q.exponent n) (s n)) :=
  (S.associated n).sample

def ExecutableCLSampler.dimension
    (S : ExecutableCLSampler Q s ell) (n : Nat) : Nat :=
  s n

def ExecutableCLSampler.associatedMap
    (S : ExecutableCLSampler Q s ell) (n : Nat) (w : CLSamplerSide) :
    ConditionallyLinearMap (Q.exponent n) (s n) ell :=
  (S.associated n).side w

noncomputable def ExecutableCLSampler.downsize
    (S : ExecutableCLSampler Q s ell) :
    ExecutableCLSampler binaryFieldFamily
      (fun n => s n * Q.exponent n) ell

theorem ExecutableCLSampler.downsize_dimension
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    S.downsize.dimension n = s n * Nat.log 2 (Q.fieldSize n)

theorem ExecutableCLSampler.downsize_associated
    (S : ExecutableCLSampler Q s ell) (hEll : 1 <= ell)
    (n : Nat) (hn : 0 < n) (w : CLSamplerSide) :
    S.downsize.associatedMap n w =
      ((S.associatedMap n w).downsize (Q.fieldData n hn))

theorem ExecutableCLSampler.sample_downsize
    (S : ExecutableCLSampler Q s ell) (hEll : 1 <= ell)
    (n : Nat) (hn : 0 < n) :
    S.downsize.sample n = PMF.map (fun pair =>
      (downsizeVector (Q.fieldData n hn) (s n) pair.1,
       downsizeVector (Q.fieldData n hn) (s n) pair.2)) (S.sample n)

theorem ExecutableCLSampler.downsize_time
    (S : ExecutableCLSampler Q s ell) (hEll : 1 <= ell) :
    RuntimeBigO S.downsize.time
      (fun n => S.time n * Nat.log 2 (Q.fieldSize n))

end

end MIPStarRE.QPBT
```
<!-- END F06A-A01-SIGNATURES -->

## Statement integrity

| Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| Positive `n`; admissible `q(n)`; dimension `s(n)`; one six-input machine whose four modes expose chosen Alice/Bob CL decompositions; `ell >= 1` for downsizing | `0 < n` is in the query index; `q(n)=2^(exponent n)` with odd exponent; canonical F01 codec definition; exact typed prefixes/factor inputs; quantified Lemma `cl-kth` laws; genuine `FinTM2` executions | Associated CL maps/distribution and `TIME_S(n)`; downsize has field 2, dimension `s(n) log q(n)`, downsized maps/distribution, and global `O(TIME_S(n) log q(n))` | Same four outputs and six tape layouts; exact execution-step maximum; exact F06 sample/downsize equalities; representation width proved equal to `s(n) * Nat.log 2(q(n))`; global positive-index `RuntimeBigO` | faithful boundary |

No executable-realization assumption for an arbitrary mathematical sampler is
introduced: `ExecutableCLSampler` is the source-defined machine plus its
intrinsic operational semantics.  No codec, runtime, compiler, bridge,
residual, repair, witness-package, producer, or generic obligation premise is
added to a paper theorem.

## Elaboration evidence

The final public surface was tested as one block in
`/tmp/qpbt054_f06a_probe.lean`.  The temporary file prepends the exact F01/F06
declarations, supplies `:= by sorry` only for omitted implementation bodies,
and includes a proof-complete finite-query encoding into a nested finite sum.
The dependent query encoding erases proof fields, and injectivity recovers them
with subtype extensionality and proof irrelevance.

The independent read-only API scout also passed two narrower probes:

- `/tmp/i054_probe_a01.lean`, SHA-256
  `5a25a23bc5a81e120ef0825df2cb7d7c363f072052e4150ac5e2cce63fcd4d10`;
- `/tmp/i054_dependent_probe_a01.lean`, SHA-256
  `6b07a7070b6dac2983906ecb7284d68095631911d16a2492c18009569cca8c25`.

All repository files remained untouched by the scout.  The final validation
table and immutable candidate identities are recorded below.

## Validation

| Command | Result | Wall time |
| --- | --- | --- |
| `lake env lean /tmp/qpbt054_f06a_probe.lean` from the prepared F01 dependency worktree | passed; only the temporary inserted-body `sorry` warnings and one unused-variable lint; probe SHA-256 `46ce962465b445152e6ca2a5e1508e228862992407ad8865259b91f0882c5394` | 4.63 s |
| `python3 blueprint/check.py --check` | passed: 54 nodes, 12 chapters, acyclic graph, deterministic outputs | 0.12 s |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | passed with the same counts | 0.13 s |
| `python3 -m unittest discover -s blueprint/tests -p 'test_check.py'` | passed: 33/33 tests (framework time 2.552 s) | 2.62 s |
| `python3 scripts/reference_source.py verify --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3 --runtime-root /home/drx/MIPStarRE-auto/.workflow-runtime/reference-source` | passed: 39 files, 646 labels; inventory `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`; ready marker `4d6a33759051b17428b3928d529d18e10da82e3bc09c75fbe429df324612b360` | 0.14 s |
| `python3 scripts/workflow.py validate` | passed: 55 issues, 30 PRs, 441 issued sessions, 7 stages | 0.17 s |
| `python3 scripts/check_workflow.py --root . --skip-tests` | passed | 0.16 s |
| `python3 -m py_compile blueprint/check.py blueprint/tests/test_check.py` | passed | not separately timed |
| `git diff --check` | passed | 0.04 s |

`blueprint/check.py --write` was run after the metadata edit and then rerun
idempotently.  It changed `graph.json` and `chapter-02-entries.tex`.
`graph.dot` remained byte-identical, as expected: QPBT-054 changes the F06A
declaration/contract payload but adds no dependency edge or node.  The final
owned generated/checker inputs have these SHA-256 identities:

| Path | SHA-256 | Candidate status |
| --- | --- | --- |
| `blueprint/check.py` | `32958aeb497558a7619e01d66ca204e3da90496400724939715f83a58af6053c` | changed |
| `blueprint/tests/test_check.py` | `308b707b9c77bb05b56144b37b090d416258612721e416c117ef707e8483c4eb` | changed |
| `blueprint/metadata/nodes.json` | `b0fb145e6a6c6b09e4fe10cbb7469de03300e707320903b7f9ef3abbadf20866` | changed |
| `blueprint/generated/graph.json` | `470b7cc9f250d4280725db0dd78c78f24c88f10397c6859ef1c802119139aa0c` | changed |
| `blueprint/generated/graph.dot` | `889fb76e7a18029485ca0db7738629dd2d03eb53e123236e5b5c9772f65650ee` | unchanged |
| `blueprint/src/generated/chapter-02-entries.tex` | `02376d6841300e7baf9881286c96a0ab39a644a9138c46571f0937e89883dad4` | changed |

The marker-delimited signature block hashes to
`0e376f7539828c204b37ea88ad8f7330ad699a57c216ebe4d02397c5753b5948`.
The candidate commit and all Git blob identities are returned to the root
coordinator after commit; embedding this report's own post-commit identity
inside itself would be self-referential.

Three validation incidents were resolved without broadening scope.  The first
pre-generation default check correctly rejected stale `graph.json` and
`chapter-02-entries.tex`.  The first focused checker-test attempt found three
test mutations that still targeted the superseded A04 strings; those fixtures
were updated and the full suite passed.  A reference verification invoked
without `--reference-root` from the isolated worktree correctly reported its
ignored source tree missing; the canonical-root invocation above passed and
verified the pinned identities.

## Accounting

Token usage is `null`: the collaboration backend exposes no per-session token
count.  Topology is root coordinator -> QPBT-054 orchestrator -> one bounded
read-only Turing/dependent-query API scout.  The scout made no repository
writes and its exact issued-to-finished lifecycle was 846.789771 seconds.
The session transcript records 16 isolated Lean probe invocations: 14 by the
orchestrator while closing import, dependent-index, finiteness, namespace,
packing, and output-equation errors, plus the scout's two successful bounded
API probes.  No repository target or full main snapshot was compiled, so the
hot-main singleton gate was not entered.

The measured issue-session interval from issuance at
`2026-09-02T18:14:34.929948Z` through the final validation cutoff at
`2026-09-02T18:40:04.167113Z` is 1529.237165 seconds.  One generation attempt
produced the owned outputs and one subsequent generation attempt confirmed
idempotence.  The exact writable manifest is the six changed paths in the
table above other than unchanged `graph.dot`, plus this report; no canonical
workflow state, metrics, Lean source, Git configuration, or GitHub state was
written.
