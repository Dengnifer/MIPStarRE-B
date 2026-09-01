# QPBT-035 contract finding repairs (A04)

Session: `i035-orchestrator-a04-q014-contract-fixes`

## Candidate verdict

This changed candidate resolves F-LPR023-001 through F-LPR023-003. F06 now
exposes the direct-sum product-distribution equality after explicit `Fin.append`
reindexing. F07 claims finiteness only for its type index, ordered edge support,
and constant `FieldVector` sampler carrier; G02 remains responsible for
pointwise finite consumer fibers. The full source detyping development is
retained under the new `F07A-DETYPING` node instead of being assigned to K03 or
K04.

## Revised F06 callable contract

<!-- BEGIN F06-A04-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

noncomputable local instance (k : Nat) : Fintype (GaloisField 2 k) :=
  Fintype.ofFinite (GaloisField 2 k)
noncomputable local instance (k : Nat) : DecidableEq (GaloisField 2 k) :=
  Classical.decEq (GaloisField 2 k)

abbrev FieldVector (k n : Nat) := Fin n -> GaloisField 2 k

noncomputable def restrictVector {k n : Nat} (register : Finset (Fin n))
    (x : FieldVector k n) : FieldVector k n

inductive ConditionallyLinearCertificate (k n : Nat) :
    Finset (Fin n) -> Nat -> (FieldVector k n -> FieldVector k n) -> Prop
  | zero (remaining : Finset (Fin n)) :
      ConditionallyLinearCertificate k n remaining 0 (fun _ => 0)
  | step {remaining : Finset (Fin n)} {level : Nat}
      {toFun : FieldVector k n -> FieldVector k n}
      (head tail : Finset (Fin n))
      (disjoint : Disjoint head tail)
      (covers : head ∪ tail = remaining)
      (headMap : FieldVector k n →ₗ[GaloisField 2 k] FieldVector k n)
      (head_supported : forall x i, i ∉ head -> headMap x i = 0)
      (head_depends : forall x, headMap (restrictVector head x) = headMap x)
      (next : LinearMap.range headMap -> FieldVector k n -> FieldVector k n)
      (next_certificate : forall pfx,
        ConditionallyLinearCertificate k n tail level (next pfx))
      (toFun_eq : forall x,
        toFun x = headMap (restrictVector head x) +
          next ⟨headMap (restrictVector head x),
            ⟨restrictVector head x, rfl⟩⟩ (restrictVector tail x)) :
      ConditionallyLinearCertificate k n remaining (level + 1) toFun

structure ConditionallyLinearMap (k n level : Nat) where
  toFun : FieldVector k n -> FieldVector k n
  certificate : ConditionallyLinearCertificate k n Finset.univ level toFun

instance {k n level : Nat} : CoeFun (ConditionallyLinearMap k n level)
    (fun _ => FieldVector k n -> FieldVector k n) :=
  ⟨ConditionallyLinearMap.toFun⟩

noncomputable def ConditionallyLinearMap.raiseLevel
    {k n level : Nat} (L : ConditionallyLinearMap k n level) (extra : Nat) :
    ConditionallyLinearMap k n (level + extra)

noncomputable def ConditionallyLinearMap.directSum
    {k n₁ n₂ level₁ level₂ : Nat}
    (L : ConditionallyLinearMap k n₁ level₁)
    (R : ConditionallyLinearMap k n₂ level₂) :
    ConditionallyLinearMap k (n₁ + n₂) (max level₁ level₂)

noncomputable def downsizeVector {k : Nat} (D : FieldData k) (n : Nat) :
    FieldVector k n ≃ₗ[ZMod 2] FieldVector 1 (n * k)

noncomputable def ConditionallyLinearMap.downsize
    {k n level : Nat} (D : FieldData k)
    (L : ConditionallyLinearMap k n level) :
    ConditionallyLinearMap 1 (n * k) level

structure CLSampler (k n level : Nat) where
  alice : ConditionallyLinearMap k n level
  bob : ConditionallyLinearMap k n level

noncomputable def CLSampler.sample {k n level : Nat}
    (S : CLSampler k n level) :
    PMF (FieldVector k n × FieldVector k n)

noncomputable def CLSampler.directSum
    {k n₁ n₂ level₁ level₂ : Nat}
    (S : CLSampler k n₁ level₁) (T : CLSampler k n₂ level₂) :
    CLSampler k (n₁ + n₂) (max level₁ level₂)

theorem CLSampler.sample_directSum
    {k n₁ n₂ level₁ level₂ : Nat}
    (S : CLSampler k n₁ level₁) (T : CLSampler k n₂ level₂) :
    (S.directSum T).sample =
      S.sample.bind fun left =>
        T.sample.map fun right =>
          (Fin.append left.1 right.1, Fin.append left.2 right.2)

noncomputable def CLSampler.downsize
    {k n level : Nat} (D : FieldData k) (S : CLSampler k n level) :
    CLSampler 1 (n * k) level

theorem CLSampler.sample_downsize
    {k n level : Nat} (D : FieldData k) (S : CLSampler k n level) :
    (S.downsize D).sample =
      PMF.map (fun pair =>
        (downsizeVector D n pair.1, downsizeVector D n pair.2)) S.sample

end MIPStarRE.QPBT
```
<!-- END F06-A04-SIGNATURES -->

The right side samples the two component PMFs independently and then reindexes
both players' component outputs into `Fin (n₁ + n₂)` via `Fin.append`. This is
the binary direct-sum instance of `conditionally-linear.tex:365-383`.

## Detyping ownership and proposed issue

`F07A-DETYPING` owns exactly `types.tex:225-579`. Its first five callables own
the graph CL sampler and rejection-simulation support required by detyping:
`TypeGraph.neighborIndicator`, `TypeGraph.vertexEncoding`,
`TypeGraph.clSampler`, `TypeGraph.simulationEvent`, and
`TypeGraph.simulatesDistribution`. The remaining five name all four detyping
definitions plus the concluding theorem:

| Source obligation | Callable owner |
| --- | --- |
| Detyped CL functions (`:371-393`) | `MIPStarRE.QPBT.detypeCL` |
| Detyped samplers (`:395-404`) | `MIPStarRE.QPBT.TypedSampler.detype` |
| Detyped deciders (`:409-433`) | `MIPStarRE.QPBT.TypedDecider.detype` |
| Detyped verifiers (`:435-442`) | `MIPStarRE.QPBT.TypedVerifier.detype` |
| Completeness, soundness, entanglement, parameter, and complexity relations (`:444-579`) | `MIPStarRE.QPBT.detypingVerifier` |

Root should allocate a follow-up issue titled `feat(QPBT/Detyping): freeze typed-verifier detyping contract`, parented under QPBT-014 and dependent on QPBT-035 plus the generic measurement/game semantics owner. Its sole future Lean path should be `MIPStarRE/QPBT/Game/Detyping.lean`. Acceptance must freeze and elaborate all ten signatures, retain the exact rejection-event probability and conditional graph distribution, retain the `16 ^ |Type|` soundness/entanglement factor and level `+ 2`, specify executable representation/cost data without a generic obligation input, and obtain an independent source-fidelity review before implementation.

## Statement integrity

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F06 | Finite coordinate spaces, recursive complementary factors, independent uniform direct-sum coordinates, selected basis for downsizing | Concrete field vectors/certificates, independent component PMFs via `bind`/`map`, `Fin.append` reindexing, `FieldData` only at downsize | CL direct sum has product distribution; downsizing is a pushforward | Exact PMF equalities for reindexed direct sum and downsizing | faithful boundary |
| F07 | Finite type set/graph, typed CL families, typed verifier data | Finite type/edge support and constant finite sampler carrier; generic dependent decider fibers have no pointwise finiteness assumptions | Typed graph distribution and sampler/decider semantics | Exact finite graph PMF and total dependent decider; G02 supplies consumer finiteness | faithful boundary |
| F07A | Finite type graph, typed sampler/decider/verifier | F07 interfaces, graph CL rejection simulation, and established measurement/game semantics; executable representation remains to be frozen | Graph simulation, four detyping definitions, and the five-part equivalence/complexity theorem | All supporting and detyping obligations explicitly named and owned; no K03/K04 delegation | faithful boundary |

## Finding dispositions

- `F-LPR023-001`: resolved by `F07A-DETYPING`; every definition and theorem in
  the source detyping range has a callable owner and exact dependencies.
- `F-LPR023-002`: resolved by the elaborated
  `CLSampler.sample_directSum` equality above.
- `F-LPR023-003`: resolved by narrowing F07 to the constant finite sampler
  carrier and assigning pointwise consumer finiteness to G02.

## Validation, authentication, and metrics

The authenticated base is commit
`fdbb37a10e416c8a9891cdcdbcd44470573886b0`, tree
`ca47214b88b0ef77aa0a72d22539004e4979290b`. The worktree was clean on the
issued branch before edits. The final commit/tree and exact eight-path Git
manifest are reported out of band because this tracked report cannot contain
the hash of the commit that contains itself.

The revised F06 marker hash, computed over the stripped text strictly between
its unique markers, is
`120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461`.

### Source authentication

No network or source materialization was used. The locally authenticated pinned
source hashes are:

| Source | SHA-256 |
| --- | --- |
| `dependencies/low-degree-code.tex` | `e77125aa2c20f037b949f8890efcaaf370f5ca25407048a5ac142115104bdc9e` |
| `dependencies/pauli.tex` | `aba301b2e225f0ceaeff6a942a75ee6d5db73283ba25e208e2e43452818aef2f` |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `dependencies/types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` |
| `qpbt/qpbt-game-and-soundness.tex` | `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea` |

### Owned manifest before commit

| Owned path | SHA-256 | Candidate state |
| --- | --- | --- |
| `blueprint/check.py` | `ea3b350def92c6a651e77e311cc15265c2367c8093458a7651921cbdab6303e4` | changed |
| `blueprint/tests/test_check.py` | `a8bebeec5daddf5c92eae74e14d9eb6a90636ce8f57fd1049eeb153989655d30` | changed |
| `blueprint/metadata/nodes.json` | `0977ed07a22c1a3730e4fa2e6b112c3166deaf402d42b1a516cac9699a38b64c` | changed |
| `blueprint/generated/graph.json` | `631a729912202ac198d4a0ecf1139e81312a2650c5d6633b5573630c3a3fd885` | changed |
| `blueprint/generated/graph.dot` | `43923f52d177a0f26709af43a696b98c88ca5fd9845796c6cacafd21acb54593` | changed |
| `blueprint/src/generated/chapter-02-entries.tex` | `f855e79306db4090878a8bf103071bd042e130959c1428fd9f6bdf06dd9af9e1` | changed |
| `blueprint/src/generated/chapter-03-entries.tex` | `afdb38a9cc4321d5be450ddcf0881bc655d3df0d7257a48acf20491491e4807f` | unchanged |

The A04 report hash is supplied out of band after its final byte is committed.

### Acceptance gates

| Command | Result | Wall time |
| --- | --- | ---: |
| `lake env lean /tmp/qpbt_f06_direct_sum_probe.lean` | pass; exact new theorem type elaborated, three probe-local `sorry` bodies only | `2.18s` |
| `python3 blueprint/check.py --write` | pass; final idempotent regeneration, 52 nodes / 12 chapters | `0.08s` |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | pass; 29 tests | `0.78s` (`0.723s` test time) |
| `python3 blueprint/check.py --check` | pass; acyclic and deterministic | `0.08s` |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass; pinned sources present | `0.09s` |
| `python3 scripts/workflow.py validate` | pass; 41 issues, 23 PRs, 384 issued sessions, 7 stages | `0.13s` |
| `python3 scripts/check_workflow.py --skip-tests` | pass | `0.12s` |
| `git diff --check` | pass | `<0.01s` |

The first default check failed closed only for three stale generated outputs
before regeneration. The first 29-test run exposed one over-broad test that
rejected explanatory text saying K03/K04 do not own detyping; the assertion was
narrowed to dependencies and all subsequent runs passed. There were three
generation attempts and the last was byte-idempotent. No generated output
outside the owned manifest changed.

### Reviewer checklist

- Authenticate the final base/head/tree and the byte-exact eight-path manifest.
- Recompute the F06 marker hash and elaborate `CLSampler.sample_directSum` with
  its `PMF.bind`/`PMF.map` product and two `Fin.append` reindexings.
- Compare the theorem with `conditionally-linear.tex:365-383`, including
  independence of the two component seeds and output coordinate order.
- Confirm F07 claims no pointwise finiteness for generic dependent question or
  answer families, and that G02 owns consumer finiteness.
- Confirm F07A owns `types.tex:225-579`, has exact prerequisites F03/F07, names
  all graph-simulation and detyping obligations, and has no K03/K04 dependency.
- Check the `16 ^ |Type|` error factor, level `+ 2`, dimension, complexity, and
  efficient-description obligations remain visible for the follow-up contract.
- Re-run unit, default, pinned-source, workflow, deterministic-generation, and
  diff-hygiene gates; verify no Lean source, canonical state, metrics, or
  research file changed.

### Session accounting

- Durable start: `2026-09-01T14:22:18.593304Z`.
- Evidence cutoff: `2026-09-01T14:33:36.741409209Z`.
- Elapsed to cutoff: `678.148105209` seconds.
- Token usage: input `null`, output `null`, total `null`; availability reason:
  collaboration backend does not expose per-agent token usage.
- Topology: root coordinator -> one QPBT-035 orchestrator; nested agents 0.
- Actions: 8 owned paths; 7 changed paths; 1 unchanged owned generated path;
  1 Lean signature probe; 0 repository Lean edits; 3 blueprint generations;
  4 unit-test attempts; 3 default checks; 2 pinned-source checks; 2 workflow
  validations; 2 workflow-checker runs; 0 target/full builds; 0 cache warm/seed,
  materialization, network, endpoint, GitHub, credential, canonical state,
  metrics, research, or Git-write actions; 0 nested agents.

Git publication occurs after the evidence cutoff. Its attempts and final
identities are reported out of band to avoid recursively amending this report.

Residual risk is bounded to the intentionally proposed follow-up: F07A freezes
source range, dependencies, and callable ownership, but its ten full Lean
signatures must be elaborated before a writer is issued. No source obligation
was replaced by a public assumption or assigned to a complexity-only node.
