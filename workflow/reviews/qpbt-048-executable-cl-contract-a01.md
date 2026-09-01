# QPBT-048 executable conditionally-linear contract (A01)

Session: `i048-orchestrator-a01-executable-cl-contract`

## Scope and source decision

This change addresses `F-LPR023-004` by assigning the generic executable
conditionally-linear layer to one new node, `F06A-EXECUTABLE-CL`.  The node is
limited to `conditionally-linear.tex:553-712` and the four labels
`def:sampler`, `def:sampler-sample`, `def:downsize_sampler`, and
`lem:downsize_sampler`.  F06 retains its existing mathematical callables.
F07A, K03, and K04 own none of these generic machine clauses.

The source calls the sampler a six-input Turing machine, but its four query
modes use at most six input tapes: dimension uses tapes 1-2; marginal uses
tapes 1-5; linear uses all six; factor uses tapes 1-5.  The Lean boundary
therefore exposes `Fin 6 -> List Bool`, rather than incorrectly claiming that
there are six query modes.  `packSixTapes` is an injective administrative
encoding into the designated input stack of Mathlib's operational
`Turing.FinTM2`; it does not erase the six-tape query boundary.

The paper explicitly notes that a CL map's marginal/factor decomposition need
not be unique.  `CLIntrospection` records the selected decomposition intrinsic
to a sampler and freezes the marginal CL certificate, prefix recurrence,
pairwise-disjoint factor cover, supported linear maps, marginal sum, and final
map equation.  It is sampler data required by `def:sampler`, not a generic
assumption or an obligation package.

## Signature manifest

The following declarations were elaborated together against Lean 4.32 and the
pinned Mathlib API in a bounded `/tmp` probe.  Probe-local `sorry` bodies were
used only to test these declaration types; no Lean source was changed.

<!-- BEGIN F06A-A01-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

structure AdmissibleFieldSizeFunction where
  exponent : Nat -> Nat
  exponent_odd : forall n, Odd (exponent n)

def AdmissibleFieldSizeFunction.fieldSize
    (q : AdmissibleFieldSizeFunction) (n : Nat) : Nat

noncomputable def AdmissibleFieldSizeFunction.fieldData
    (q : AdmissibleFieldSizeFunction) (n : Nat) : FieldData (q.exponent n)

noncomputable def AdmissibleFieldSizeFunction.vectorEncoding
    (q : AdmissibleFieldSizeFunction) (index dimension : Nat) :
    Computability.Encoding (FieldVector (q.exponent index) dimension) Bool

noncomputable def registerEncoding (dimension : Nat) :
    Computability.Encoding (Finset (Fin dimension)) Bool

def binaryFieldSizeFunction : AdmissibleFieldSizeFunction

inductive CLSamplerSide
  | alice
  | bob
  deriving DecidableEq

def CLSampler.side {k n level : Nat} (S : CLSampler k n level) :
    CLSamplerSide -> ConditionallyLinearMap k n level

namespace CLStage

def pred {level : Nat} (j : Fin level) (h : 0 < j.val) : Fin level

def castLE {level : Nat} (j : Fin level) (i : Fin (j.val + 1)) : Fin level

def last (level : Nat) (h : 0 < level) : Fin level

end CLStage

structure CLIntrospection {k n level : Nat}
    (L : ConditionallyLinearMap k n level) where
  marginal : (j : Fin level) -> ConditionallyLinearMap k n (j.val + 1)
  priorOutput : Fin level -> FieldVector k n -> FieldVector k n
  factor : Fin level -> FieldVector k n -> Finset (Fin n)
  linear : Fin level -> FieldVector k n ->
    FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n
  priorOutput_zero : forall (j : Fin level), j.val = 0 -> priorOutput j = 0
  priorOutput_succ : forall (j : Fin level) (h : 0 < j.val),
    priorOutput j = marginal (CLStage.pred j h)
  factor_disjoint : forall (x : FieldVector k n) (i j : Fin level),
    i ≠ j -> Disjoint (factor i (priorOutput i x)) (factor j (priorOutput j x))
  factor_cover : forall x : FieldVector k n,
    Finset.univ.biUnion (fun j : Fin level => factor j (priorOutput j x)) = Finset.univ
  linear_supported : forall (j : Fin level) (u x : FieldVector k n) (i : Fin n),
    i ∉ factor j u -> linear j u x i = 0
  linear_depends : forall (j : Fin level) (u x : FieldVector k n),
    linear j u (restrictVector (factor j u) x) = linear j u x
  marginal_sum : forall (j : Fin level) (x : FieldVector k n),
    marginal j x =
      ∑ i : Fin (j.val + 1),
        linear (CLStage.castLE j i) (priorOutput (CLStage.castLE j i) x)
          (restrictVector
            (factor (CLStage.castLE j i) (priorOutput (CLStage.castLE j i) x)) x)
  marginal_top : forall h : 0 < level,
    (marginal (CLStage.last level h)).toFun = L.toFun

inductive CLSamplerQuery
    (q : AdmissibleFieldSizeFunction) (dimension : Nat -> Nat) (level : Nat)
  | dimension (index : Nat)
  | marginal (index : Nat) (side : CLSamplerSide) (stage : Fin level)
      (input : FieldVector (q.exponent index) (dimension index))
  | linear (index : Nat) (side : CLSamplerSide) (stage : Fin level)
      (prior input : FieldVector (q.exponent index) (dimension index))
  | factor (index : Nat) (side : CLSamplerSide) (stage : Fin level)
      (prior : FieldVector (q.exponent index) (dimension index))

def CLSamplerQuery.index
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat} :
    CLSamplerQuery q dimension level -> Nat

noncomputable def CLSamplerQuery.inputTapes
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (query : CLSamplerQuery q dimension level) : Fin 6 -> List Bool

def packSixTapes (input : Fin 6 -> List Bool) : List Bool

theorem packSixTapes_injective : Function.Injective packSixTapes

structure SixTapeBoolTuringMachine where
  machine : Turing.FinTM2
  inputAlphabet : machine.Γ machine.k₀ ≃ Bool
  outputAlphabet : machine.Γ machine.k₁ ≃ Bool

def SixTapeBoolTuringMachine.OutputsInTime
    (M : SixTapeBoolTuringMachine) (input : Fin 6 -> List Bool)
    (output : List Bool) (steps : Nat) : Type

structure CLSamplerSemantics
    (q : AdmissibleFieldSizeFunction) (dimension : Nat -> Nat) (level : Nat) where
  associated : forall index,
    CLSampler (q.exponent index) (dimension index) level
  introspection : forall index side,
    CLIntrospection ((associated index).side side)

def CLSamplerSemantics.dimensionQuery
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (_ : CLSamplerSemantics q dimension level) (index : Nat) : Nat

noncomputable def CLSamplerSemantics.marginalQuery
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : CLSamplerSemantics q dimension level) (index : Nat)
    (side : CLSamplerSide) (stage : Fin level)
    (input : FieldVector (q.exponent index) (dimension index)) :
    FieldVector (q.exponent index) (dimension index)

noncomputable def CLSamplerSemantics.linearQuery
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : CLSamplerSemantics q dimension level) (index : Nat)
    (side : CLSamplerSide) (stage : Fin level)
    (prior input : FieldVector (q.exponent index) (dimension index)) :
    FieldVector (q.exponent index) (dimension index)

noncomputable def CLSamplerSemantics.factorQuery
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : CLSamplerSemantics q dimension level) (index : Nat)
    (side : CLSamplerSide) (stage : Fin level)
    (prior : FieldVector (q.exponent index) (dimension index)) :
    Finset (Fin (dimension index))

noncomputable def CLSamplerSemantics.answerBits
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : CLSamplerSemantics q dimension level)
    (query : CLSamplerQuery q dimension level) : List Bool

structure ExecutableCLSampler
    (q : AdmissibleFieldSizeFunction) (dimension : Nat -> Nat) (level : Nat) where
  semantics : CLSamplerSemantics q dimension level
  machine : SixTapeBoolTuringMachine
  stepCount : Nat -> Nat
  computes : forall query : CLSamplerQuery q dimension level,
    machine.OutputsInTime query.inputTapes (semantics.answerBits query)
      (stepCount query.index)

def ExecutableCLSampler.associatedSampler
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : ExecutableCLSampler q dimension level) (index : Nat) :
    CLSampler (q.exponent index) (dimension index) level

def ExecutableCLSampler.dimension
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (_ : ExecutableCLSampler q dimension level) (index : Nat) : Nat

def ExecutableCLSampler.associatedMap
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : ExecutableCLSampler q dimension level) (index : Nat)
    (side : CLSamplerSide) :
    ConditionallyLinearMap (q.exponent index) (dimension index) level

noncomputable def ExecutableCLSampler.distribution
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : ExecutableCLSampler q dimension level) (index : Nat) :
    PMF (FieldVector (q.exponent index) (dimension index) ×
      FieldVector (q.exponent index) (dimension index))

noncomputable def ExecutableCLSampler.downsize
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : ExecutableCLSampler q dimension level) (hlevel : 0 < level) :
    ExecutableCLSampler binaryFieldSizeFunction
      (fun index => dimension index * q.exponent index) level

theorem ExecutableCLSampler.downsize_dimension
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : ExecutableCLSampler q dimension level) (hlevel : 0 < level) (index : Nat) :
    (S.downsize hlevel).dimension index =
      S.dimension index * Nat.log 2 (q.fieldSize index)

theorem ExecutableCLSampler.downsize_associated
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : ExecutableCLSampler q dimension level) (hlevel : 0 < level) (index : Nat) :
    (S.downsize hlevel).associatedSampler index =
      (S.associatedSampler index).downsize (q.fieldData index)

theorem ExecutableCLSampler.downsize_distribution
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : ExecutableCLSampler q dimension level) (hlevel : 0 < level) (index : Nat) :
    (S.downsize hlevel).distribution index =
      PMF.map (fun pair =>
        (downsizeVector (q.fieldData index) (dimension index) pair.1,
          downsizeVector (q.fieldData index) (dimension index) pair.2))
        (S.distribution index)

theorem ExecutableCLSampler.downsize_time
    {q : AdmissibleFieldSizeFunction} {dimension : Nat -> Nat} {level : Nat}
    (S : ExecutableCLSampler q dimension level) (hlevel : 0 < level) :
    Asymptotics.IsBigO Filter.atTop
      (fun index => ((S.downsize hlevel).stepCount index : Real))
      (fun index =>
        (S.stepCount index : Real) * (Nat.log 2 (q.fieldSize index) : Real))

end MIPStarRE.QPBT
```
<!-- END F06A-A01-SIGNATURES -->

The implementation must encode the six tapes exactly as follows.  Tape 0 is
the binary natural encoding of `n`.  A dimension query puts the dimension tag
on tape 1 and leaves tapes 2-5 empty.  The other modes put side on tape 1,
mode on tape 2, the paper index `j = stage.val + 1` on tape 3, and the encoded
vector/prefix on tape 4; only the linear query uses tape 5 for `y`.  Field
vectors are encoded in coordinate order using the F01 selected basis, and a
factor space is its length-`s(n)` coordinate indicator.  Packing encodes every
bit by a two-bit code and separates all six tapes with a reserved two-bit
delimiter; `packSixTapes_injective` prevents boundary aliasing.

## Statement integrity

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F06 | Finite field-coordinate spaces, recursive CL maps, independent finite sampling, and basis downsizing | Existing certified mathematical maps, PMFs, and F01 `FieldData` | Mathematical CL operations and distribution laws | The same mathematical layer, without machine clauses | faithful boundary |
| F06A | An admissible indexed field size, positive level for downsizing, a six-input Turing sampler, selected nonunique marginal/factor data satisfying Lemma `cl-kth`, and the paper bit representation | Odd exponent family `q(n)=2^k`, F01-selected coordinate encoding, exact four typed query modes packed injectively into Mathlib `FinTM2`, explicit introspection laws, and an indexed operational step bound | Associated CL maps/distribution and all dimension/marginal/linear/factor outputs; executable downsize has field size 2, dimension `s(n) log q(n)`, downsized maps/distribution, and runtime `O(TIME_S(n) log q(n))` | The same clauses with `Nat.log 2 (q.fieldSize n)` and `Asymptotics.IsBigO Filter.atTop`; no existence or complexity theorem for constructing arbitrary samplers is added | faithful boundary |
| F07 | Finite type graph and typed sampler/decider data over the generic sampler machine | Existing unrestricted dependent fibers plus F06A as the generic executable base | Typed mathematical and executable interfaces | Existing mathematical interface; its typed machine debt remains at F07A/QPBT-043 and does not absorb F06A | faithful boundary |
| F07A | Typed verifier, graph simulation, detyping, and typed/detyping cost clauses | F04A, F07, and its own `types.tex:197-579` executable layer; F06A is only transitive | Typed/detyping clauses | Same 20 callable owners, with no generic sampler ownership | faithful boundary |

The semantic field encoding uses the existing noncomputable F01 selector.  It
does not claim the uniform basis-construction theorem from `finite-fields.tex`;
K03A must later prove that its executable basis/table algorithm is coherent
with this representation before any uniform construction-cost theorem is
closed.  This is an explicit discharge boundary, not a caller-supplied premise.

## Root recommendations for QPBT-038

Root should make these exact canonical QPBT-038 changes after integrating the
generated-sync commit:

1. Add `QPBT-048` to `dependency_ids`; keep `QPBT-013` and `QPBT-035`.
2. Add source refs to this report, `nodes.json#F06A-EXECUTABLE-CL`, and the
   exact pinned slices `conditionally-linear.tex:1-552`, `:553-626`,
   `:628-660`, and `:662-712`; replace the overbroad `:1-715` ref.
3. Replace “F06-then-F07 contract” with the exact implementation order
   `F06-CL`, `F06A-EXECUTABLE-CL`, then `F07-TYPED`, all in the existing sole
   owned file `MIPStarRE/QPBT/Game/Types.lean`.
4. Require the five direct F06A imports frozen above and all 38 signature
   names, including the exact four query constructors over `Fin 6`, injective
   packing, `Turing.FinTM2`, `TM2OutputsInTime`, associated maps/distribution,
   indexed step count, the downsize constructor, and its four
   dimension/map/distribution/runtime theorems.
5. Narrow the raw-string prohibition: unbound raw efficiency claims remain
   forbidden, while the reviewed operational F06A interface and exact
   `Asymptotics.IsBigO Filter.atTop` downsize theorem are required.  K03A still
   owns efficient basis/table construction and representation coherence.
6. Retain zero proof-complete `sorry`, `axiom`, `constant`, and caller-supplied
   obligations.  If the downsized-machine proof cannot be discharged in the
   lane, split that theorem into a dependency issue instead of weakening its
   source-faithful statement.
7. Extend validation with exact input-tape layout and output-encoding tests,
   `Nat.log 2 (q.fieldSize n)` dimension checks, blueprint declaration sync,
   the existing scoped/target/private-full-build gates, and an immutable
   independent review only after the generated sync is integrated.

## Validation and accounting

The authenticated clean base was
`77172fd30105531f668acc0338caae028901d24d`, tree
`4c158849f44522dc92c8229aeb223d96ece4cf0b`, with parent
`c35fcd36bea96705851655852eabc78ca9db9b3f`.  The branch is
`issue/qpbt-048-executable-cl-contract-a01`.  Final commit/tree/report and
path-manifest hashes are returned in the terminal result envelope because the
report cannot contain its own immutable identity.

Pinned source authentication was read-only.  `reference_source.py verify`
authenticated 39 files and 646 labels with inventory SHA-256
`04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`
and ready SHA-256
`4d6a33759051b17428b3928d529d18e10da82e3bc09c75fbe429df324612b360`.

| Pinned file | SHA-256 |
| --- | --- |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `dependencies/finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |
| `dependencies/types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` |
| `split-manifest.json` | `052cfaceb2e4a7b59778936ceb3daea9a33e3592e01b902cb2a9740c58999a20` |
| `source-pin.json` | `66a1e9db74f1454ce50909728a3b741f9da468b5d61902645557793ceb91ac9c` |

The stripped signature block above is 8,946 bytes and has SHA-256
`027de2c872cf086fb93456381ac5325aba2676b6be82428151c978e40fa2672d`.
It freezes 38 callable names.  A bounded disposable `/tmp` probe elaborated
the declarations against Lean 4.32 and the pinned Mathlib APIs.  There were
four probe attempts: three failed refinements and one pass.  The failed
classes were (1) reserved-token/parser and output-relation-sort errors, (2)
linear-map/dependent-equality/binary-family definitional-equality errors, and
(3) a missing `noncomputable` annotation.  Failed-attempt durations were not
instrumented.  The passing attempt took `2.927947562s`; its only warnings were
probe-local `sorry` declarations and an unused proof argument.

| Command | Result | Instrumented elapsed |
| --- | --- | ---: |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | 31/31 passed | 1.44 s |
| `python3 blueprint/check.py --check` | 54 nodes, 12 chapters, acyclic and deterministic | 0.09 s |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | exact pinned-source gate passed | 0.10 s |
| `python3 scripts/reference_source.py verify --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | 39 files and 646 labels authenticated | 0.13 s |
| `python3 scripts/workflow.py validate` | valid; 41 issues, 21 local PRs, 376 issued sessions, 7 stages | 0.13 s |
| `python3 scripts/check_workflow.py --root .` | 336/336 passed | 182.36 s |
| two `python3 blueprint/check.py --write` calls | passed; byte-idempotent | 0.09 s each |
| `python3 -m py_compile blueprint/check.py blueprint/tests/test_check.py` | passed | not separately instrumented |
| `git diff --check` | passed | not separately instrumented |

The two generation writes had identical tracked-diff SHA-256
`e2889a9d98f3a26e00d31559dfd2433268d64f3e80d1f619a1eab6219a399756`.
The owned deterministic outputs are:

| Generated output | SHA-256 |
| --- | --- |
| `blueprint/generated/graph.dot` | `410feb4650b1000d7d56a869aa57614fbeb458f08b5ecc25e626afc9f9faa804` |
| `blueprint/generated/graph.json` | `2840647a130395f07184a1c37d90405be9eafc0840887e91c19ba13acfbfff98` |
| `blueprint/src/generated/chapter-02-entries.tex` | `e9ff7c9c9937e217df5c5f847efc1bdc3e1738154c58039d3769093015dc88a7` |
| `blueprint/src/generated/chapter-03-entries.tex` | `34ac8533534fca99fbe3e088c434c3b989b9e79b5c75ddd4de6a928d689c2cd0` |

## Generated-sync handoff

Adding F06A as F07's definition prerequisite necessarily propagates F06A into
the exact definition-ancestor closure rendered for later chapters.  These nine
generated files are outside A01's canonical ownership.  Root directed A01 to
leave them intact but uncommitted for a separate generated-sync session:

| Pending generated output | SHA-256 |
| --- | --- |
| `blueprint/src/generated/chapter-04-entries.tex` | `eb2503f1827797a488dd20eaeff9dba9321a05867154ba80ef90391b71b61968` |
| `blueprint/src/generated/chapter-05-entries.tex` | `8151543adb04e3f75a8967a00341099f294dd13ca6ba63993c0e37f780456927` |
| `blueprint/src/generated/chapter-06-entries.tex` | `6c7dd5931ca69f434f73572dd4b57e9d1e1c82449bd0f27b9ad5c76ec2e9be7e` |
| `blueprint/src/generated/chapter-07-entries.tex` | `61c92602bbc4b83d37e88932a6de7c4f2fad2a472cf9a06082e3ceaae0be4ee9` |
| `blueprint/src/generated/chapter-08-entries.tex` | `d7bad77e605e3c4e84ebfc0ebb5b98e2413b456eb4a2053c19c24f5534d0172a` |
| `blueprint/src/generated/chapter-09-entries.tex` | `41180579da3f033c36699db181b9948aa7f8a674cff9e7fdb3bcc550cf439db3` |
| `blueprint/src/generated/chapter-10-entries.tex` | `7c87078a1c56ceb9e933d9e6986f28772c1dcd47764a93f3e8d155fa0af7ba5f` |
| `blueprint/src/generated/chapter-11-entries.tex` | `e804b1a457f14f12c890ea9e19e97fdae511a0b2d165826f9366c56668176d3d` |
| `blueprint/src/generated/chapter-12-entries.tex` | `b4c662db45be37c5f1ad2599e4270696e8854d36aa1f1d3a68d8dcf5a5f083f7` |

The full dirty generated set passed all gates and was byte-idempotent.  The
A01 commit alone is intentionally a partial generated-output commit and will
report chapter 04-12 as stale until the separate sync commit is integrated.
LPR-023 must not enter immutable review before that sync is present.

Topology was one writable orchestrator with zero children; no collaboration
slot was available for the optional bounded read-only child.  Subagents:
0 dispatched, 0 completed, 0 nested.  New blueprint nodes: 1.  New callable
names: 38.  New focused test methods: 1.  Adversarial mutation cases: 13.
Generation attempts: 2 successful, 0 idempotence mismatches.  Lean signature
probe attempts: 4 total, 3 failed refinements, 1 passed.  Target builds: 0.
Full builds: 0.  Cache actions: 0.  Materializations: 0.  Network, endpoint,
GitHub, and credential operations: 0.  One expected pre-generation checker
attempt reported the new stale outputs plus two constant mismatches; both
constants were corrected before the passing gates.

Orchestrator token usage is `null` for input, output, and total.  Availability
reason: the collaboration backend does not expose per-agent token usage.
Canonical start was `2026-09-01T16:49:25.843827Z`; exact terminal end and
elapsed time are returned in the terminal result envelope.
