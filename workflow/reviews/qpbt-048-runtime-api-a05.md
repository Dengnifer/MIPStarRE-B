# QPBT-048 runtime/API scout (A05)

Session: `i048-scout-a05-runtime-api`  
Role: independent read-only runtime/API scout for A04.  
Base worktree: `/tmp/qpbt-048-runtime-api-a05`, clean detached `HEAD`
`783ec5f5b0ed876addb3cf6e02bf0fdc2426fa19` (tree
`87eda049a6e8bfac7965c0df41de23930f26f9ba`).  No repository, canonical-state,
metrics, cache, build, materialization, network, endpoint, GitHub, or credential
actions were performed.  A04's moving worktree/report was not inspected.

## Answers for A04

### 1. Global positive-index runtime bound

The paper's `N` is positive and its `O` quantifies one positive real constant
over every positive index (`top-level/preliminaries.tex:6,20-25`).  Do not use
`Asymptotics.IsBigO Filter.atTop` as the paper-labelled runtime theorem: it is
eventual and admits a different value at Lean's zero index.  Use a direct
predicate (or an equivalent theorem proved separately):

```lean
def RuntimeBigO (f g : Nat -> Nat) : Prop :=
  ∃ C : Real, 0 < C ∧ ∀ n, 0 < n →
    (f n : Real) ≤ C * (g n : Real)
```

The downsize theorem should have the shape

```lean
theorem ExecutableCLSampler.downsize_time
    (S : ExecutableCLSampler Q s ell) (hell : 1 ≤ ell) :
    RuntimeBigO S.downsize.time
      (fun n => S.time n * Nat.log 2 (Q.fieldSize n))
```

with `0 < n` in all pointwise map/distribution/dimension claims.  An
`IsBigO atTop` comparison can be auxiliary only; it cannot replace this
positive-global statement.

### 2. Exact finite valid-query aggregation

`TM2ComputableInTime.time` is indexed by serialized input length and
`TM2OutputsInTime` is only an at-most witness.  The source's `TIME_S(n)` is
ambiguous because one index has dimension, marginal, linear, and factor
queries.  Keep exact per-query execution steps and define the index time as a
finite maximum over the valid semantic query subtype.  A minimal elaborated
carrier is:

```lean
structure ValidQueryFamily where
  query : Nat → Type
  finite : ∀ n, Fintype (query n)

def validQueryTime (V : ValidQueryFamily)
    (steps : ∀ n, V.query n → Nat) (n : Nat) : Nat :=
  letI := V.finite n
  Finset.univ.sup (steps n)

theorem validQueryTime_spec (V : ValidQueryFamily)
    (steps : ∀ n, V.query n → Nat) (n : Nat) (q : V.query n) :
    steps n q ≤ validQueryTime V steps n := by
  letI := V.finite n
  exact Finset.le_sup (Finset.mem_univ q)
```

For a fixed machine/input/output family, derive the exact `steps` from the run
witness rather than storing an unconstrained upper bound:

```lean
structure ExactRun (M : SixTapeBoolMachine)
    (inputs : Q → SixTapeInput) (outputs : Q → List Bool)
    [Fintype Q] where
  bound : Q → Nat
  witness : ∀ q, M.outputsInTime (inputs q) (outputs q) (bound q)

def ExactRun.steps (r : ExactRun M inputs outputs) (q : Q) : Nat :=
  (r.witness q).toEvalsTo.steps

def ExactRun.maxSteps (r : ExactRun M inputs outputs) : Nat :=
  Finset.univ.sup (fun q => ExactRun.steps M inputs outputs r q)
```

`EvalsToInTime.toEvalsTo.steps` is the exact executed-step field; the supplied
bound is not itself the runtime.  The valid query family is nonempty because it
contains the dimension query, while malformed encodings and invalid prefixes
remain outside the source contract and must not inflate or discharge `TIME`.

### 3. Six-tape operational API and ignored tapes

The source has six logical input tapes but variable arity:

| mode | non-ignored logical tapes |
|---|---|
| dimension | `(n, dimension)`; tapes 2--5 empty |
| marginal | `(n,w,marginal,j,z)`; tape 5 empty |
| linear | `(n,w,linear,j,u,y)`; all six used |
| factor | `(n,w,factor,j,u)`; tape 5 empty |

Use `Fin 6 -> List Bool` as the logical input and an injective administrative
packing into the one designated input stack of `FinTM2`.  A probe-elaborated
wrapper is:

```lean
abbrev SixTapeInput := Fin 6 → List Bool

structure SixTapeBoolMachine where
  tm : Turing.FinTM2
  inputAlphabet : tm.Γ tm.k₀ ≃ Bool
  outputAlphabet : tm.Γ tm.k₁ ≃ Bool

def SixTapeBoolMachine.outputsInTime
    (M : SixTapeBoolMachine) (input : SixTapeInput)
    (output : List Bool) (steps : Nat) : Type :=
  Turing.TM2OutputsInTime M.tm
    ((packSixTapes input).map M.inputAlphabet.symm)
    (some (output.map M.outputAlphabet.symm)) steps
```

The query datatype should expose exactly four constructors (`dimension`,
`marginal`, `linear`, `factor`) and `inputTapes : Query -> SixTapeInput` should
put the index encoding on tape 0, the dimension token on tape 1 for the
dimension mode, and the side/mode/stage/vector fields on tapes 1--4 (plus `y`
on tape 5 for linear).  For every ignored tape, `inputTapes` should return
`[]`; correctness is quantified only over these typed layouts.  The packing
delimiter/code must be fixed and `packSixTapes_injective` proved.  A one-tape
simulation theorem with generic polynomial overhead does not establish the
paper's sharper `O(TIME_S(n) * log q(n))` compiler cost.

### 4. Data-valued CL decomposition and index subtypes

The decomposition chosen in `def:sampler` is nonunique and the F06 recursive
certificate is proposition-valued.  Never eliminate that `Prop` into executable
query data.  Carry a data-valued decomposition for each associated Alice/Bob
map (marginals, prefix-output function, factor coordinate sets, and supported
linear maps) together with proof fields realizing the F06 certificate.

Define valid dependent indices from the chosen data, for example:

```lean
structure CLPrefix (D : CLQueryDecomposition L) (j : Fin ell) where
  value : FieldVector k n
  inRange : ∃ x, value = D.priorOutput j x

structure CLFactorInput (D : CLQueryDecomposition L)
    (j : Fin ell) (u : CLPrefix D j) where
  value : FieldVector k n
  supported : ∀ i, i ∉ D.factor j u.value → value i = 0
```

The `linear` query then takes `u : CLPrefix ...` and `y : CLFactorInput ...`;
`factor` takes only the valid prefix subtype.  Stage zero is represented by
the chosen `priorOutput` zero law.  This avoids proof-to-data elimination while
keeping malformed raw strings outside the theorem.  Preserve two source-gap
notes: the linear bullet says `u ∈ V_<j` while `lem:cl-kth` requires
`u ∈ L_<j(V)`, and the paper never quantifies the domains of `u,y`; use the
type-correct range/factor subtypes and document the repair.

### 5. Canonical field-coordinate codec APIs

`FieldData.coordinates` is mathematical (`GaloisField 2 k ≃ₗ[ZMod 2]
(Fin k → ZMod 2)`) and currently does not provide a Bool/list codec,
algorithm-selected multiplication tables, or a coherence theorem with the
Shoup--Lenstra--Wang basis.  Expose a fixed coordinate order and derive the
Bool view through a canonical finite equivalence, while keeping construction
coherence as the explicit G16/K03A boundary:

```lean
noncomputable def zmod2Bool : ZMod 2 ≃ Bool :=
  Fintype.equivOfCardEq (by decide)

noncomputable def FieldData.coordinateBits {k : Nat} (D : FieldData k) :
    GaloisField 2 k ≃ (Fin k → Bool) :=
  D.coordinates.toEquiv.trans
    (Equiv.piCongrRight (fun _ => zmod2Bool))

noncomputable def FieldData.vectorBits {k n : Nat} (D : FieldData k) :
    (Fin n → GaloisField 2 k) ≃ (Fin n → Fin k → Bool) :=
  Equiv.piCongrRight (fun _ => D.coordinateBits)
```

The executable API still needs a `Computability.Encoding ... Bool` whose
`encode` is `List.ofFn` in the above `(coordinate, field-coordinate)` order,
with a length-checking decoder and `decode_encode` proof.  Add an analogous
fixed-order `Finset (Fin n)` indicator encoding.  Do not add an arbitrary
public codec/coherence premise to the paper theorem: the mathematical downsize
may consume F01's selected `FieldData`, but the executable representation must
eventually be specialized to the canonical algorithmic basis and multiplication
tables.  Until that construction is proved, leave the source theorem visible
with tracked proof debt and keep any conditional helper private/
`_ofObligations`.

## Probe evidence

All probes were bounded `lake env lean /dev/stdin` runs in the authenticated
private dependency worktree `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-031-field-a01`.
No probe wrote source or build output.

Passed checks:

- `RuntimeBigO` declaration and target product with `Nat.log 2`.
- `Turing.FinTM2`, `Turing.TM2ComputableAux`, `Turing.TM2OutputsInTime`, and
  `StateTransition.EvalsToInTime` names.
- `SixTapeBoolMachine.outputsInTime` wrapper above.
- `ValidQueryFamily`, `validQueryTime`, and `Finset.le_sup` specification.
- Exact step extraction through `(witness q).toEvalsTo.steps`.
- `Nat.log_pow` has pinned signature
  `Nat.log_pow {b} (hb : 1 < b) (x) : Nat.log b (b ^ x) = x`.
- `Computability.Encoding`, `Computability.encodingNatBool`, and
  `Computability.encodeNat`.
- `zmod2Bool`, `Equiv.piCongrRight`, `coordinateBits`, and `vectorBits`
  generic coordinate equivalences.

Two early exploratory probes failed only from scout-local mistakes (attempting
`List.join` instead of `List.flatten`, and malformed temporary finite/query
declarations); corrected probes passed.  No project defect was inferred from
those diagnostics.

## Source hashes

| artifact | SHA-256 |
|---|---|
| `AGENTS.md` | `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c` |
| `conditionally-linear.tex` (pinned dependencies split) | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `preliminaries.tex` (pinned top-level split) | `045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1` |
| `finite-fields.tex` (pinned dependencies split) | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |
| `source-pin.json` | `66a1e9db74f1454ce50909728a3b741f9da468b5d61902645557793ceb91ac9c` |
| `split-manifest.json` | `052cfaceb2e4a7b59778936ceb3daea9a33e3592e01b902cb2a9740c58999a20` |
| A02 report `/tmp/qpbt-048-source-audit-a02.md` | `64e66a978642b012aeb236461bd36d26204791da0f64de9e6e93b88e73e2ef3c` |
| A01 contract report | `bb1f714998e774f95d25327efe4285adc2e6817eb4c66e6b2dea8ba3f89198aa` |
| `blueprint/metadata/nodes.json` (F06/F06A/F07 entries) | `7998c5fe76c301e0b39244da3f05951903754a27539701517ee59412372f7338` |
| `workflow/state/issues.json` (QPBT-038 record) | `21edc6856f47738d976b3bbf49173bf64415fd3f5a53ab340846a54621513578` |
| A03 generated-sync report | `8d95d622e13479d1f1f42b0532db6657e6e5437dbb2e7bf2da65c73ca0647c59` |
| `MIPStarRE/QPBT/Basic/Field.lean` | `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e` |
| Mathlib `Computability/TuringMachine/Computable.lean` | `acb5fa046c00afd1f85570d4439653b009b7353d7ed93aa7a6fc52dae346a59b` |
| Mathlib `Analysis/Asymptotics/Defs.lean` | `813c16f6323617fd6cb589d118d19d62873e82b46fa76399155c46fed9e9da87` |
| Mathlib `Data/Nat/Log.lean` | `9800e6942155e28138ed981a06340d7333aacccfafcd1aa35147147ae57d8e3f` |
| Mathlib `Computability/Encoding.lean` | `55e6166b31f174ca9ac3f7b5bd802da06086931747bc301067b8f86a04eaba06` |
| Mathlib `Computability/StateTransition.lean` | `eceb96a26dccbd8f8abcd83874539b49b8b7e797f195a864cff85c1bbe8476b2` |

## Accounting

Elapsed wall time: approximately 23 minutes from packet release to report
write.  Token usage: `null` (backend does not expose per-agent usage).
Topology: root coordinator -> one read-only scout; nested agents: 0.
Counters: Lean stdin probes 8 (6 successful final checks, 2 corrected local
diagnostics), repository edits 0, `/tmp` report writes 1, target/full builds 0,
cache warm/seed 0, source materialization 0, network/endpoint/GitHub/credential
actions 0.
