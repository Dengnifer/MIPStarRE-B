# QPBT-035 direct-sum distribution API scout (A06)

Session: `i035-scout-a06-directsum-api`

## Verdict

**ACCEPT A04's `CLSampler.sample_directSum` signature unchanged.**  At changed
candidate `3f2630a7631a0164b6ef4aca1fd081ba264beeb2`, the theorem is the smallest
callable binary form of the source product-distribution statement.  Its
`PMF.bind`/`PMF.map` expression samples the two component sampler PMFs
independently, while each `CLSampler.sample` retains the source's one shared
uniform seed for its Alice/Bob pair.  The result

```lean
(Fin.append left.1 right.1, Fin.append left.2 right.2)
```

has the required order `(Alice_S ++ Alice_T, Bob_S ++ Bob_T)`.  It does not
cross Alice with Bob or reverse the component coordinates.

No extra public product PMF, split equivalence, bridge assumption, or
obligation parameter is needed.  The paper states an `m`-ary direct sum;
the frozen API is its binary generator and is therefore a faithful boundary,
not a literal restatement of the paper's arbitrary-`m` quantifier.

## Source derivation

The governing source is pinned
`dependencies/conditionally-linear.tex:132-138,315-383` (SHA-256
`f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638`).
Definition `def:cl-dist` samples one uniform `x : V` and returns
`(L x, R x)`.  Lemma `lem:cl-dist-prod` decomposes
`V = V^(1) direct-sum ... direct-sum V^(m)` and identifies that distribution
with the product of the component pair distributions.

For the binary Lean carrier, write independently uniform
`x_S : FieldVector k n1` and `x_T : FieldVector k n2`.  Then:

```text
S.sample = law (S.alice x_S, S.bob x_S)
T.sample = law (T.alice x_T, T.bob x_T)
product  = law ((S.alice x_S, S.bob x_S),
                (T.alice x_T, T.bob x_T))
append   = law (S.alice x_S ++ T.alice x_T,
                S.bob x_S   ++ T.bob x_T)
```

Uniformity of `Fin (n1 + n2) -> GaloisField 2 k` factors through the canonical
equivalence with the product of the two finite function spaces.  This is the
only probability fact hidden by the concise public equality.

There is a source defect worth recording rather than silently copying:
`conditionally-linear.tex:377` says that `x` is uniform in `V x V`, although
`L,R : V -> V`, Definition `def:cl-dist`, and lines 376 and 379-382 all require
one `x : V`.  Line 369 also switches harmlessly from superscripts `L^(i),R^(i)`
to subscripts `L_i,R_i`.  The recommended theorem follows the definition and
lemma statement; A04 does not amplify either typo into Lean.

## Recommended callable contract

Production direct imports remain exactly:

```lean
import Mathlib.Probability.Distributions.Uniform
import MIPStarRE.QPBT.Basic.Field
```

The public theorem should be:

```lean
theorem CLSampler.sample_directSum
    {k n1 n2 level1 level2 : Nat}
    (S : CLSampler k n1 level1) (T : CLSampler k n2 level2) :
    (S.directSum T).sample =
      S.sample.bind fun left =>
        T.sample.map fun right =>
          (Fin.append left.1 right.1, Fin.append left.2 right.2)
```

This is byte-for-byte the mathematical type in A04 apart from ASCII binder
names.  `PMF.bind` followed by a `T.sample` that is constant in `left` is the
independent product construction.  `PMF.map` then applies the canonical two
player reindexing.  The two `Fin.append` calls are all the Sum/Fin reindexing
that the public carrier equality needs.

No public helper is recommended.  If the implementation needs proof-local
facts, the smallest useful names and exact types are:

```lean
private noncomputable def fieldVectorSumEquiv (k n1 n2 : Nat) :
    Equiv (FieldVector k (n1 + n2))
      (Prod (FieldVector k n1) (FieldVector k n2))

private theorem uniform_fieldVector_append (k n1 n2 : Nat) :
    (PMF.uniformOfFintype (FieldVector k n1)).bind
        (fun left =>
          (PMF.uniformOfFintype (FieldVector k n2)).map
            (Fin.append left)) =
      PMF.uniformOfFintype (FieldVector k (n1 + n2))
```

`fieldVectorSumEquiv.toFun` restricts at `Fin.castAdd n2` and `Fin.natAdd n1`;
its inverse is `Fin.append`.  Existing APIs found and reused are `Fin.append`,
root-level `finSumFinEquiv`,
`Equiv.sumPiEquivProdPi`, `PMF.bind`, `PMF.map`, `PMF.bind_comm`, and
`PMF.uniformOfFintype`.  No existing `PMF.prod` or uniform-product theorem was
found in the pinned Mathlib source, so a private uniform-factorization lemma is
reasonable; adding a project-wide public abstraction is not required by this
contract.

## Statement integrity

| Item | Paper | Lean | Verdict |
| --- | --- | --- | --- |
| Seed within one component | One uniform `x_i` feeds both `L^(i)` and `R^(i)` | Each `S.sample`/`T.sample` is one pair PMF | exact |
| Independence across components | Product of component distributions | `S.sample.bind` then constant `T.sample.map` | exact |
| Coordinate carrier | `(product_i V_i) x (product_i V_i)` | two `Fin.append` maps into `FieldVector k (n1+n2)` | faithful canonical reindexing |
| Alice/Bob order | `((L_i x_i)_i, (R_i x_i)_i)` | `(append left.1 right.1, append left.2 right.2)` | exact |
| Arity | arbitrary finite `m` | binary `directSum`, iterable | faithful boundary |
| Assumptions | finite field-coordinate spaces and CL maps | concrete finite `GaloisField` vectors and certified samplers | faithful boundary |

## Candidate comparison and authentication

- Issued detached base: `fdbb37a10e416c8a9891cdcdbcd44470573886b0`;
  tree `ca47214b88b0ef77aa0a72d22539004e4979290b`; clean and detached.
- Compared candidate: `3f2630a7631a0164b6ef4aca1fd081ba264beeb2`;
  tree `4effdd7686905e59c188b70c71b04a6cb46e8b21`; parent is the issued base.
- Candidate A04 report Git blob:
  `cbd2274b0f83b32083760ccbd579f982ed290ef6`; filesystem-stream SHA-256
  `a55e7789d6a899b31e6fc8625dfb6116c9430884fb2ce83fc6e1182bb2d3225e`.
- Independently recomputed F06 A04 marker SHA-256:
  `120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461`.
- QPBT-033 report SHA-256:
  `5b6e073865225ef6a8c70a78ce3ad43e2a41d26c1d19b42534e7ef01eb03f55c`.
- A02 contract report SHA-256:
  `987d17140ae4e1e808ed0504b874c67dc1285f70245cf71363dafe97fc1dd610`.
- A03 review SHA-256:
  `a1ed48ff7a642c8811f56d1aa77caec32e3cf1608a33dd474fffb16b367e4caf`.

## Probe text and results

Three bounded signature probes used only `/dev/stdin` and the immutable,
already-authenticated local Mathlib oleans; they wrote no probe file or build
output.

1. An independent canonical formulation defined the concrete
   `fieldVectorSumEquiv`, re-associated both player outputs, and checked
   `PMF.map directSumSampleEquiv (S.directSum T).sample = pmfProduct S.sample
   T.sample`.  It passed in `2.1s`; only three probe-local `sorry` bodies were
   warnings.
2. The exact A04 theorem shown above passed in `2.0s`; only the two definition
   stubs and theorem body were probe-local `sorry` warnings.
3. The exact `uniform_fieldVector_append` helper type passed in `1.9s` with one
   probe-local `sorry` warning.

The isolated probes imported `Mathlib.FieldTheory.Finite.Trace` in place of the
project `Basic.Field` module solely to obtain `GaloisField` from the immutable
cache snapshot; this does not alter the production import recommendation.
Three earlier API-discovery invocations exited nonzero without creating output:
one unbuilt temporary project could not resolve `Mathlib`, and two deliberate
`#check` batches included nonexistent candidate names
`Equiv.finSumFinEquiv` (the actual name is root-level `finSumFinEquiv`) and
`ENNReal.natCast_mul`.  The usable API names above were then checked exactly.

No target or full build was run.

## Session accounting

- Durable dispatch start: `2026-09-01T14:35:42.109543Z`.
- Evidence cutoff: `2026-09-01T14:46:47.528471482Z`.
- Elapsed to cutoff: `665.419` seconds.
- Token usage: input `null`, output `null`, total `null`; availability reason:
  collaboration backend does not expose per-agent token usage.
- Topology: root coordinator -> one scout; nested agents `0`.
- Actions: `6` Lean invocations (`3` passing signature probes, `3` failed or
  partial API-discovery probes); `0` target builds; `0` full builds; `0` cache
  warm/seed/materialization actions; immutable cache reads only; `0`
  repository/Git/state/metrics/source/blueprint edits; `0` network/endpoint/
  GitHub/credential operations; `0` nested-agent dispatches; `1` report
  artifact written.
- Repository proof debt introduced: `0`; probe-local `sorry` bodies: `7` across
  the three passing probes.
- This report's SHA-256 is supplied out of band after final bytes are written.
