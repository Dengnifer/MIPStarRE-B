# QPBT-059 F06A linear six-tape contract (A01)

Session: `i059-orchestrator-a02-pack-contract`
Role: sole QPBT-059 writer and orchestrator
Base commit: `c0fcfccbfa796a8a719713910f543e895d606a48`

## Verdict

This report supersedes only the F06A signature marker in
`workflow/reviews/qpbt-054-f06a-repair-a04.md`; that historical report remains
unchanged. The 56 public declaration names, their signatures and quantifier
order, the four-import union, every accepted semantic clause, and the G19
field-exponent boundary are preserved. The sole public-definition change is
the body of `packSixTapes`, together with the unchanged injectivity contract
that its implementation must prove.

The new body is the paper's explicit linear, self-delimiting tuple encoding:
within each tape `false` is encoded as `01`, `true` as `10`, and `00`
terminates the tape. `List.ofFn` fixes the order of all six tapes. Consequently
the packed length is exactly twice the sum of the six logical tape lengths
plus six terminators:

```text
2 * ((sum i, (input i).length) + 6)
```

## Source evidence and correction finding

The controlling source is the authenticated pinned tree at
`/home/drx/MIPStarRE-auto/references/2001.04383v3`. In
`top-level/preliminaries.tex:105-111`, the paper requires an unambiguous tuple
encoding computable in `O(k + |x_1| + ... + |x_k|)` and gives exactly the
dual-rail encoding frozen here.

The prior Cantor-based body was not merely missing an implementation lemma.
For all-false lists its inner codes obey `c_0 = 0`, `c_1 = 1`, and
`c_(m+1) = 1 + c_m^2` for `m >= 1`, so its output bit length grows
exponentially in logical tape length. That contradicts the paper's explicit
linear encoding convention. This finding does **not** assert that the old
abstract `ExecutableCLSampler.downsize_time` proposition is false; it
establishes that the old representation did not realize the paper's linear
input-length convention.

G19 remains unchanged and orthogonal: it concerns computing the odd field
exponent from `n` and charging that computation to `TIME_S`, not tuple
serialization.

## Superseding signature manifest

Concrete bodies below are frozen semantics. Headers without bodies freeze
signatures for the existing proof-complete implementation task; this report
introduces no Lean proof debt or new public obligation.

<!-- BEGIN F06A-QPBT059-SIGNATURES -->
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
  (List.ofFn input).flatMap fun tape =>
    tape.flatMap (fun bit =>
      match bit with
      | false => [false, true]
      | true => [true, false]) ++ [false, false]

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
<!-- END F06A-QPBT059-SIGNATURES -->

## Statement integrity

| Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| Positive `n`; admissible `q(n)`; dimension `s(n)`; one six-input sampler with the four source modes; `ell >= 1` for downsizing; the paper's linear self-delimiting tuple encoding convention | The same accepted F06A boundary data, including canonical F01 codec, dependent valid domains, genuine sampler executions, intrinsic finite exponent program, canonical blank normalization, and the explicit six-tape dual-rail codec | Associated CL maps/distribution and `TIME_S(n)`; downsize has field 2, dimension `s(n) log q(n)`, downsized maps/distribution, and global `O(TIME_S(n) log q(n))`; tuple encoding has linear length | The same accepted conclusions and G19 exponent boundary; `packSixTapes` has exact length `2 * (sum tape lengths + 6)`, is self-delimiting by `00`, and remains injective | faithful boundary |

No public parser, length theorem, hypothesis, obligation, or additional
declaration is introduced. The implementation may use private decoder,
length, parser-correctness, and linear trace lemmas.

## Validation and accounting

The superseding marker SHA-256 is
`368008b7b4ba84ff1dafe842acdb8af7005902a0fe9a376a8f7a690c86ba6b15`.
Replacing only its new `packSixTapes` body with the historical Cantor body
reproduces the old marker SHA-256
`cfe433e36d0670c344b29ab5107557842e7d4fc8358fba2713b8ff2ee107a3a1`,
which proves the remainder of the marker is byte-identical. The metadata still
lists exactly 56 public names and exactly four imports. The dependency,
consumer, transitive-definition, target, and topological-order projection is
unchanged.

| Command | Result | Wall time |
| --- | --- | --- |
| `python3 -m py_compile blueprint/check.py blueprint/tests/test_check.py` | pass | `0.05s` |
| `python3 -m unittest discover -s blueprint/tests -p 'test_check.py'` | pass, 34 tests | `2.77s` final run |
| first `python3 blueprint/check.py --write` | pass, 54 nodes and 12 chapters | `0.13s` |
| second `python3 blueprint/check.py --write` | pass; complete generated-output SHA-256 manifest byte-identical to the first run | `0.13s` |
| `python3 blueprint/check.py --check` | pass, deterministic declaration synchronization | `0.13s` |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass, pinned-source synchronization | `0.13s` |
| `python3 scripts/workflow.py validate` | pass, 60 issues, 34 PRs, 480 issued sessions, 7 stages | `0.18s` |
| `python3 scripts/check_workflow.py --root . --skip-tests` | pass | `0.20s` |
| `git diff --check` | pass | `<0.01s` |

Final non-report file identities before commit are:

| Path | SHA-256 | Git blob |
| --- | --- | --- |
| `blueprint/check.py` | `4281a603c94652fdacb94a45816c381ce7e08c37ffc1393fce3d18ef376330fb` | `61667a45e3da00c884e6d4c7dcc889c86ebf0c0b` |
| `blueprint/tests/test_check.py` | `a4e8db927723e143ab356409495a265c173c4af67f41d785374ed84ba924b9ae` | `8ce384f2297a0299536964beb80199914a3e664a` |
| `blueprint/metadata/nodes.json` | `07b7f404aea1a48605bc8a4bd3fb938e6ca818953be81e9fc7492eed11fa051d` | `ec2c5985a760b14d1c449cc18c73dbd54404362d` |
| `blueprint/generated/graph.json` | `9bc7a513aa76e48b8d4cb0623cc8868a471142fe03960a68d407a0cafd9b1893` | `2e0b177dabf3c3f87346ac84ea67e745aeb0d688` |
| `blueprint/src/generated/chapter-02-entries.tex` | `236cf118b457a2c37d6dd82b7720be803beef30aa73ef9ed1b91529304ed41ee` | `211631d510f00cc06fd51ea5a8a3643fcb5874d9` |

The report's own final hash and Git blob, plus the commit/tree/parent identity,
are returned out of band after commit to avoid self-reference.

This session performed zero Lean, Lake, build, hot-main cache, network,
endpoint, GitHub, credential, canonical workflow-state, or research-metrics
actions and spawned zero child agents. Token usage is `null`: the
collaboration backend exposes no per-session token count.

The first staged diff-hygiene check caught two Markdown trailing spaces in
this new report. They were removed before commit; the final staged check
passed.
