# QPBT-048 / LPR-023 source-fidelity repair (A04)

Session: `i048-orchestrator-a04-source-fidelity-repair`

## Verdict

The A01 executable conditionally-linear contract was source-audited against
the pinned preliminaries, conditionally-linear, and finite-fields slices.  This
repair closes the contract drift identified by A02 without implementing Lean:
positive-index guards are explicit, `RuntimeBigO` is global over positive
indices, `TIME_S(n)` is the exact finite maximum over valid queries, and the
six logical input tapes and ignored-tape behavior remain operationally visible.
Chosen CL decompositions and valid `u`/`y` domains are data-valued.  The field
codec is the canonical F01-selected representation; no caller-supplied
coherence or compiler obligation is admitted.  The sampler law is the exact
F06 PMF and downsizing uses its exact pushforward.

The source has two documented defects that remain visible at this boundary:
the linear-query bullet leaves the domains of `u` and `y` implicit and the
downsizing proof writes `L_{j,downsize(u)}` where the original family requires
`L_{j,u}`.  They are recorded in the boundary text as paper-gap notes
`A02-004/A02-006`; no silent strengthening is made.  The source's global
complexity claim remains a proof obligation for the `types` lane, including
parsing, valid-prefix inversion, simulation, and ordered factor-block output.

## Pinned evidence

The authenticated source tree is the existing ignored mirror at
`/home/drx/MIPStarRE-auto/references/2001.04383v3`; no source was fetched or
materialized.  Relevant pinned files and SHA-256 values are:

| File | SHA-256 |
| --- | --- |
| `top-level/preliminaries.tex` | `045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1` |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `dependencies/finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |

The contract source anchors are the exact labels `lem:cl-kth`,
`lem:cl-downsize`, `def:sampler`, `def:sampler-sample`,
`def:downsize_sampler`, `lem:downsize_sampler`, `sec:prelim`, `sec:tms`,
`thm:universal-tm`, `sec:ff-representations`, `lem:efficient_basis`,
`lem:efficient_arithmetic`, and `rmk:tm_fields`, with split/original line
coordinates frozen in `blueprint/check.py` and `blueprint/metadata/nodes.json`.

## A02 finding disposition

| Finding | Disposition |
| --- | --- |
| A02-001, eventual `IsBigO` is not paper `O` | Resolved in contract: `RuntimeBigO` quantifies `C > 0` and every `0 < n`; no `Asymptotics.IsBigO` import or theorem remains. |
| A02-002, underspecified `TIME_S(n)` | Resolved in contract: `time_eq_validQueryMax` is an exact finite maximum over the dependent valid-query subtype. |
| A02-003, one-tape serialization erases six tapes | Resolved in contract: `SixTapeInput`, an operational indexed six-input machine, exact run witnesses, and explicit ignored tapes are required; packing is administrative and injective only. |
| A02-004, decomposition and `u`/`y` domains | Resolved in contract: `CLQueryDecomposition` is data-valued and the query constructors use dependent previous-marginal and factor-space domains; the source omissions are labeled. |
| A02-005, arbitrary field codec | Resolved in contract: `fieldCodec` is canonical and source-coherent through F01; no public codec/coherence premise is accepted. G16/K03A remains the tracked construction obligation. |
| A02-006, unproved compiler overhead | Resolved as an explicit proof obligation: `downsize_time` is a proved global-positive compiler-cost theorem and must account for parsing, inversion, simulation, copying, and ordered factor blocks. |
| A02-007, positivity/level/multiplication order | Resolved in contract: every pointwise claim has `0 < n`, downsizing has `1 <= level`, and dimension remains `s n * Nat.log 2 (Q.fieldSize n)` in the source order. |
| A02-008, sampler law | Resolved in contract: `sample` is the associated F06 law and `sample_downsize` is an exact `PMF.map` equality from one shared seed. |

## Statement integrity

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F06A | Positive `n`, admissible `q(n)`, dimension `s(n)`, one six-input sampler, chosen CL data, and `ell >= 1` for downsizing | Guarded odd exponent family, canonical F01 codec, explicit six-tape machine and ignored tapes, data-valued decomposition with dependent valid domains, exact finite valid-query maximum | Associated maps/distribution and downsized field-2 sampler of dimension `s(n) log q(n)` with global `O(TIME_S(n) log q(n))` | Same clauses with exact `RuntimeBigO`, pointwise map equalities, and PMF pushforward; codec construction and compiler proof remain tracked obligations rather than inputs | faithful boundary |

## A04 signature manifest

The following is a declaration-only manifest.  It is not Lean source and uses
no proof debt.  The implementation lane must elaborate these declarations in
`MIPStarRE/QPBT/Game/Types.lean` and prove every theorem before completion.

<!-- BEGIN F06A-A04-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

structure AdmissibleFieldFamily where
  exponent : Nat -> Nat
  exponent_odd : forall n, 0 < n -> Odd (exponent n)

def AdmissibleFieldFamily.fieldSize
    (Q : AdmissibleFieldFamily) (n : Nat) : Nat :=
  2 ^ Q.exponent n

noncomputable def AdmissibleFieldFamily.fieldData
    (Q : AdmissibleFieldFamily) (n : Nat) (hn : 0 < n) : FieldData (Q.exponent n)

noncomputable def AdmissibleFieldFamily.fieldCodec
    (Q : AdmissibleFieldFamily) (n dimension : Nat) (hn : 0 < n) :
    Computability.Encoding (FieldVector (Q.exponent n) dimension) Bool

def binaryFieldFamily : AdmissibleFieldFamily

def RuntimeBigO (f g : Nat -> Nat) : Prop :=
  Exists fun C : Real => 0 < C /\ forall n, 0 < n -> (f n : Real) <= C * (g n : Real)

abbrev SixTapeInput := Fin 6 -> List Bool

structure CLQueryDecomposition
    {k n ell : Nat} (L : ConditionallyLinearMap k n ell) where
  marginal : (j : Fin ell) -> ConditionallyLinearMap k n (j.val + 1)
  priorOutput : Fin ell -> FieldVector k n -> FieldVector k n
  factor : Fin ell -> FieldVector k n -> Finset (Fin n)
  linear : Fin ell -> FieldVector k n ->
    FieldVector k n ->L[GaloisField 2 k] FieldVector k n
  priorOutput_zero : forall (j : Fin ell), j.val = 0 -> priorOutput j = 0
  priorOutput_succ : forall (j : Fin ell) (h : 0 < j.val),
    priorOutput j = marginal (CLStage.pred j h)
  factor_disjoint : Prop
  factor_cover : Prop
  linear_supported : Prop
  linear_depends : Prop
  marginal_sum : Prop
  marginal_top : forall h : 0 < ell, (marginal (CLStage.last ell h)).toFun = L.toFun

inductive CLSamplerSide | alice | bob deriving DecidableEq

def CLSampler.side {k n ell : Nat} (S : CLSampler k n ell) :
    CLSamplerSide -> ConditionallyLinearMap k n ell

namespace CLStage
def pred {ell : Nat} (j : Fin ell) (h : 0 < j.val) : Fin ell
def castLE {ell : Nat} (j : Fin ell) (i : Fin (j.val + 1)) : Fin ell
def last (ell : Nat) (h : 0 < ell) : Fin ell
end CLStage

inductive CLSamplerQuery
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell n : Nat)
    (associated : CLSampler (Q.exponent n) (s n) ell)
    (decomposition : (w : CLSamplerSide) ->
      CLQueryDecomposition (associated.side w))
  | dimension
  | marginal (w : CLSamplerSide) (j : Fin ell)
      (z : FieldVector (Q.exponent n) (s n))
  | linear (w : CLSamplerSide) (j : Fin ell)
      (u : {u : FieldVector (Q.exponent n) (s n) // u in previous marginal range})
      (y : {y : FieldVector (Q.exponent n) (s n) // y in factor space for u})
  | factor (w : CLSamplerSide) (j : Fin ell)
      (u : {u : FieldVector (Q.exponent n) (s n) // u in previous marginal range})

def CLSamplerQuery.index : CLSamplerQuery Q s ell n A D -> Nat
def CLSamplerQuery.tapes : CLSamplerQuery Q s ell n A D -> SixTapeInput
def CLSamplerQuery.expectedOutput : CLSamplerQuery Q s ell n A D -> List Bool
def packSixTapes (input : SixTapeInput) : List Bool
theorem packSixTapes_injective : Function.Injective packSixTapes

structure IndexedSixInputBitMachine where
  output : SixTapeInput -> List Bool
  steps : SixTapeInput -> Nat
  run : SixTapeInput -> List Bool -> Nat -> Prop
  run_in_time : forall input, run input (output input) (steps input)

structure ExecutableCLSampler
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell : Nat) where
  associated : forall n, CLSampler (Q.exponent n) (s n) ell
  decomposition : forall n (w : CLSamplerSide),
    CLQueryDecomposition ((associated n).side w)
  machine : IndexedSixInputBitMachine
  correct : forall n (hn : 0 < n)
    (query : CLSamplerQuery Q s ell n (associated n) (decomposition n)),
    machine.output query.tapes = query.expectedOutput
  time : Nat -> Nat
  time_eq_validQueryMax : forall n, 0 < n ->
    time n = Finset.sup (validQueryFinset n) (fun query => machine.steps query.tapes)

noncomputable def ExecutableCLSampler.sample
    (S : ExecutableCLSampler Q s ell) (n : Nat) :
    PMF (FieldVector (Q.exponent n) (s n) × FieldVector (Q.exponent n) (s n))
def ExecutableCLSampler.dimension
    (S : ExecutableCLSampler Q s ell) (n : Nat) : Nat
def ExecutableCLSampler.associatedMap
    (S : ExecutableCLSampler Q s ell) (n : Nat) (w : CLSamplerSide) :
    ConditionallyLinearMap (Q.exponent n) (s n) ell
noncomputable def ExecutableCLSampler.downsize
    (S : ExecutableCLSampler Q s ell) :
    ExecutableCLSampler binaryFieldFamily (fun n => s n * Q.exponent n) ell
theorem ExecutableCLSampler.downsize_dimension
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    S.downsize.dimension n = s n * Nat.log 2 (Q.fieldSize n)
theorem ExecutableCLSampler.downsize_associated
    (S : ExecutableCLSampler Q s ell) (hEll : 1 <= ell)
    (n : Nat) (hn : 0 < n) :
    S.downsize.associated n = (S.associated n).downsize (Q.fieldData n hn)
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

end MIPStarRE.QPBT
```
<!-- END F06A-A04-SIGNATURES -->

## Validation and accounting

| Gate | Result | Elapsed |
| --- | --- | ---: |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | 32/32 passed | 1.53 s |
| `python3 blueprint/check.py --check` | 54 nodes; passed | 0.30 s |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | 54 nodes; passed | 0.30 s |
| `python3 scripts/reference_source.py verify --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | 39 files, 646 labels; passed | 0.12 s |
| `python3 scripts/workflow.py validate` | valid; 41 issues, 21 PRs, 376 sessions, 7 stages | 0.13 s |
| `python3 scripts/check_workflow.py --root . --skip-tests` | valid | 0.37 s |
| `python3 -m py_compile blueprint/check.py blueprint/tests/test_check.py` | passed | 0.04 s |
| `git diff --check` | passed | 0.02 s |
| `python3 blueprint/check.py --write` twice | passed; byte-identical | 0.4 s total |
| `python3 scripts/check_workflow.py --root .` | 336/336 passed | 174.11 s |

A bounded `timeout 30s lake env lean /tmp/qpbt048_probe.lean` was attempted as
an API probe.  The isolated worktree had no materialized Mathlib packages, so
Lake began a network clone; the probe was terminated at 30 s before any Lean
build.  The partial ignored `.lake` directory was removed immediately.  No
Lean source, target build, cache publication, package materialization,
endpoint, GitHub, credential, canonical state, or metrics action is part of
this metadata repair.

Topology is one orchestrator with zero nested agents. Token usage is `null`
because the collaboration backend exposes no per-agent token telemetry. The
final immutable commit SHA/tree, parent, ordered path manifest, and report
digest are returned in the terminal handoff after all gates pass.
