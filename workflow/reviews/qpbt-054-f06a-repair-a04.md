# QPBT-054 executable CL contract repair (A04)

Session: `i054-orchestrator-a04-f06a-repair`
Role: sole QPBT-054 repair writer
Rejected parent: `83062f78cc52ecf0edf0e725c00850fb458721b5`

## Verdict

The revised F06A contract resolves both findings from the immutable A03 review.
It does not construct a finite exponent machine from an arbitrary function.
Instead, `ExecutableCLSampler` contains a concrete `FieldExponentProgram Q`,
whose genuine `TM2OutputsInTime` execution computes `Q.exponent n` from each
positive index.  The sampler's exact `time` is the maximum of the public-query
execution maximum and this field-program execution, so the computation needed
by executable downsizing is charged to the source time in `downsize_time`.

The four paper query modes remain exactly four.  Their input map is now named
`CLSamplerQuery.canonicalTapes`: every unused tape is normalized to `[]`.  This
typed boundary deliberately does not claim that the packed machine returns the
same output for arbitrary payloads on unused raw tapes.

## Source evidence and paper gaps

No network source discovery or source materialization was used.  The source is
the authenticated tree at
`/home/drx/MIPStarRE-auto/references/2001.04383v3`.

| Source | SHA-256 | Clauses used |
| --- | --- | --- |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` | admissible functions and sampler machine at 553-601; unused tapes at 603-612; downsizing and runtime at 628-712 |
| `dependencies/finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` | representations at 234-281; basis algorithm given `k` at 283-307; arithmetic and machine convention at 350-411 |

Paper-gap note `A03-001`: the paper permits an arbitrary admissible field-size
function, but its downsize machine must multiply by `log q(n)`.  The cited field
algorithm takes the odd exponent `k` as input and does not compute it from `n`.
The Lean executable boundary therefore requires intrinsic exponent code and
charges it to `TIME_S`; no theorem produces that code from an arbitrary
`AdmissibleFieldFamily`.  The downsize implementation must compose the concrete
sampler and exponent machines.

Boundary note `A03-002`: the paper says unused raw tapes are ignored.  This
contract instead normalizes well-typed invocations to canonical blank tapes.
Arbitrary-unused-payload invariance is neither assumed nor concluded.

## Corrected signature manifest

Concrete bodies below are frozen semantics.  Headers whose implementation is
omitted were given `:= by sorry` only in the temporary whole-block elaboration
probe; this blueprint repair adds no repository Lean proof debt.

<!-- BEGIN F06A-A04-SIGNATURES -->
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
  Exists fun C : Real => 0 < C /\ forall n, 0 < n ->
    (f n : Real) <= C * (g n : Real)

abbrev SixTapeInput := Fin 6 -> List Bool

def SixTapeInput.ofLists
    (tape0 tape1 tape2 tape3 tape4 tape5 : List Bool) : SixTapeInput :=
  ![tape0, tape1, tape2, tape3, tape4, tape5]

def fieldExponentInput (n : Nat) : SixTapeInput :=
  SixTapeInput.ofLists (Computability.encodeNat n) [] [] [] [] []

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

def CLSamplerQuery.canonicalTapes :
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

structure FieldExponentProgram (Q : AdmissibleFieldFamily) where
  machine : IndexedSixInputBitMachine
  execution : forall n, 0 < n ->
    machine.Execution (fieldExponentInput n)
      (Computability.encodeNat (Q.exponent n))

def FieldExponentProgram.correct
    (P : FieldExponentProgram Q) (n : Nat) (hn : 0 < n) :
    Turing.TM2Outputs P.machine.tm
      ((packSixTapes (fieldExponentInput n)).map
        P.machine.inputAlphabet.symm)
      (some ((Computability.encodeNat (Q.exponent n)).map
        P.machine.outputAlphabet.symm)) :=
  Turing.TM2OutputsInTime.toTM2Outputs (P.execution n hn).runInTime

def FieldExponentProgram.steps
    (P : FieldExponentProgram Q) (n : Nat) (hn : 0 < n) : Nat :=
  (P.execution n hn).steps

structure ExecutableCLSampler
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell : Nat) where
  associated : forall n, CLSampler (Q.exponent n) (s n) ell
  decomposition : forall n (w : CLSamplerSide),
    CLQueryDecomposition ((associated n).side w)
  machine : IndexedSixInputBitMachine
  execution : forall n (hn : 0 < n)
      (query : CLSamplerQuery Q s ell n hn (associated n) (decomposition n)),
    machine.Execution query.canonicalTapes query.expectedOutput
  fieldProgram : FieldExponentProgram Q

def ExecutableCLSampler.correct
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n)
    (query : CLSamplerQuery Q s ell n hn (S.associated n) (S.decomposition n)) :
    Turing.TM2Outputs S.machine.tm
      ((packSixTapes query.canonicalTapes).map S.machine.inputAlphabet.symm)
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

noncomputable def ExecutableCLSampler.queryTime
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) : Nat :=
  (S.validQueries n hn).sup (S.executedSteps n hn)

theorem ExecutableCLSampler.queryTime_eq_validQueryMax
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    S.queryTime n hn =
      (S.validQueries n hn).sup (S.executedSteps n hn)

noncomputable def ExecutableCLSampler.time
    (S : ExecutableCLSampler Q s ell) (n : Nat) : Nat :=
  if hn : 0 < n then
    Nat.max (S.queryTime n hn) (S.fieldProgram.steps n hn)
  else 0

theorem ExecutableCLSampler.time_eq_max
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    S.time n = Nat.max (S.queryTime n hn) (S.fieldProgram.steps n hn)

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
<!-- END F06A-A04-SIGNATURES -->

## Statement integrity

| Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| Positive `n`; admissible `q(n)`; dimension `s(n)`; one six-input sampler exposing the four source modes; `ell >= 1` for downsizing | The same mathematical family and modes, canonical F01 codec, dependent valid domains, genuine sampler executions, plus an intrinsic finite exponent program; canonical blank normalization rather than arbitrary-payload invariance | Associated CL maps/distribution and `TIME_S(n)`; downsize has field 2, dimension `s(n) log q(n)`, downsized maps/distribution, and global `O(TIME_S(n) log q(n))` | The same mathematical and downsize conclusions; `TIME_S` is the exact maximum of source-query and exponent-program steps, so required exponent computation is charged; no raw unused-payload invariance theorem | faithful boundary |

The extra exponent program is a documented executable boundary forced by the
paper's missing computability premise.  It is data of an executable sampler,
not a generic implication, bridge, obligation, or theorem that every
mathematical field family has executable code.

## Elaboration and validation

The final public surface was tested as one namespace in
`/tmp/qpbt054_f06a_repair_a04_probe.lean`, SHA-256
`148129f6b00addba74c7778fb8f35591127c33667e39d24ab9d95b82759eb9b3`.
The temporary file contains the exact revised types plus the surrounding
F01/F06 declarations and implementation-only finite-query encoder.  Its
`sorry` bodies stand only for declarations whose implementation is outside
this contract repair; no temporary file is a repository artifact.

| Command | Result | Wall time |
| --- | --- | --- |
| `lake env lean /tmp/qpbt054_f06a_repair_a04_probe.lean` from prepared worktree `qpbt-036-polynomial-a01` | passed; only probe-local `sorry` warnings and one unused-variable lint in a placeholder theorem | 4.72 s |
| `python3 blueprint/check.py --write` | passed: 54 nodes, 12 chapters, acyclic graph; generated consumers updated | 0.12 s |
| `python3 blueprint/check.py --check` | passed with the same counts and deterministic outputs | 0.12 s |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | passed with authenticated pinned sources | 0.13 s |
| `python3 -m unittest discover -s blueprint/tests -p 'test_check.py'` | passed: 33/33, including constructibility/runtime and canonical-blank regressions | 2.73 s |
| `python3 scripts/reference_source.py verify --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3 --runtime-root /home/drx/MIPStarRE-auto/.workflow-runtime/reference-source` | passed: 39 files, 646 labels; inventory `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`; ready marker `4d6a33759051b17428b3928d529d18e10da82e3bc09c75fbe429df324612b360` | 0.13 s |
| `python3 scripts/workflow.py validate` | passed: 55 issues, 30 PRs, 441 issued sessions, 7 stages | 0.17 s |
| `python3 scripts/check_workflow.py --root . --skip-tests` | passed | 0.16 s |
| `python3 -m py_compile blueprint/check.py blueprint/tests/test_check.py` | passed | 0.05 s |
| `git diff --check` | passed | under 0.1 s |

The generated graph topology did not change, so `graph.dot` remains
byte-identical to the rejected parent.  Final owned non-report hashes before
commit are:

| Path | SHA-256 | Candidate status |
| --- | --- | --- |
| `blueprint/check.py` | `47f76c91effbb1e21b8b9d466e22cbcdd0be74ef249b03e241b604bac9bdf57b` | changed |
| `blueprint/tests/test_check.py` | `d5be2938487f2c2fc7641d99a780ff934393a347bda225a4a61919d31a56dc0f` | changed |
| `blueprint/metadata/nodes.json` | `b5cda5640de1cdbbbde45be9fa5029815c37324be7b0f686f4072fd15baf8cd7` | changed |
| `blueprint/generated/graph.json` | `253c01a9256c86d195ee3ce10877140d8bad095caa9f4a180e60e61d7e62de05` | changed |
| `blueprint/generated/graph.dot` | `889fb76e7a18029485ca0db7738629dd2d03eb53e123236e5b5c9772f65650ee` | unchanged |
| `blueprint/src/generated/chapter-02-entries.tex` | `c4bfd44479839d1cb6f64959f0947e3d63d2b75a0885da7d225e23c36bc9f1e7` | changed |

The marker-delimited signature hashes to
`cfe433e36d0670c344b29ab5107557842e7d4fc8358fba2713b8ff2ee107a3a1`.
The report's own final hash and Git blob are returned after commit rather than
embedded self-referentially.

## Accounting

One bounded read-only nested agent, `i054-prover-a05-runtime-boundary`, checked
the paper/runtime boundary.  It made zero edits, builds, network, GitHub, or
credential operations and spawned zero children.  Its token usage is `null`
because the collaboration backend exposes no per-agent count; the root
coordinator owns its exact issued/finished lifecycle timestamps.

The orchestrator ran three successful whole-block Lean probes while refining
the exponent-program binder and final signature.  One exploratory `lake env
lean --help` command was mistakenly run in the unseeded repair worktree; Lake
attempted to clone Mathlib, but DNS resolution failed before any transfer or
compilation.  All actual probes then used the already prepared private
dependency worktree.  Blueprint generation ran six times while the contract,
manifest hash, and declaration order were refined; the final deterministic
check is idempotent.  No repository target or full snapshot was compiled, so
the singleton hot-main build gate was not entered.  This session spawned
exactly one nested agent.  Its own token usage is likewise `null` because the
collaboration backend exposes no per-session token count.
