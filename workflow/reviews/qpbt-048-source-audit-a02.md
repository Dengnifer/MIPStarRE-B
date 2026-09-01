# QPBT-048 executable CL sampler source/API audit (A02)

Canonical session: `i048-scout-a02-executable-cl-source`

Formal outcome: **source/API constraints established; do not accept a contract
that omits or weakens Findings A02-001 through A02-006.** This was an
independent source audit, not a review of A01's moving candidate. I did not read
A01's worktree or report.

## Findings

### A02-001 - Critical: the paper's `O` is global over positive indices, not
Mathlib's eventual `IsBigO`

`top-level/preliminaries.tex:6,20-25` defines `N` as the positive integers, all
logs as base 2, and `f = O(g)` as one positive real constant bounding every
positive `n`. `Mathlib.Analysis.Asymptotics.Defs` instead defines `IsBigO` by an
eventual filter predicate. Consequently

```lean
Asymptotics.IsBigO Filter.atTop
  (fun n => (downTime n : Real))
  (fun n => (sourceTime n * Nat.log 2 (fieldSize n) : Nat))
```

is not the source statement: it may discard finitely many positive indices and
silently includes a different convention at Lean's `n = 0`. The exact project
predicate should be callable directly:

```lean
def RuntimeBigO (f g : Nat -> Nat) : Prop :=
  Exists fun C : Real =>
    And (0 < C) (forall n, 0 < n ->
      (f n : Real) <= C * (g n : Real))
```

The final probe elaborated this predicate and the exact target
`RuntimeBigO downTime (fun n => sourceTime n * Nat.log 2 (fieldSize n))`.
An optional equivalence to an at-top theorem may be added later, but cannot
replace the paper-labelled theorem.

### A02-002 - Critical: `TIME_S(n)` is underspecified by the paper and does not
match Mathlib's length-indexed time wrapper

`top-level/preliminaries.tex:48-75` defines an exact step count separately for
each tuple of input strings, with infinity on nonhalting input. In contrast,
`def:sampler` at `conditionally-linear.tex:594-600` calls `TIME_S(n)` "the
number of steps before S halts for index n" even though index `n` has many
dimension, marginal, linear, and factor queries of different lengths. It does
not say maximum, worst case, query-specific value, or a promised upper bound.

This is a paper gap. The smallest faithful boundary is:

1. retain exact `timeAt : SixTapeInput -> WithTop Nat` (or a proved halting
   `Nat` time on the valid-query subtype);
2. define `time n` explicitly as the least uniform upper bound / maximum over
   all semantically valid queries at positive index `n`; and
3. state correctness and halting on those valid queries only.

For fixed `n`, the semantic query family is finite, so this maximum is
available once its `Fintype` instance is exposed. Invalid encodings are outside
the paper contract and must not be used to inflate or discharge `TIME_S(n)`.

Mathlib's `TM2ComputableInTime.time` is a function of serialized input length,
and its `outputsFun` proves an at-most bound. It is not the paper's index time.
`TM2OutputsInTime` / `StateTransition.EvalsToInTime` can implement the run
certificate, but QPBT needs the separate index/query wrapper and a minimality or
actual-step theorem. A free `time : Nat -> Nat` field with only an upper-bound
proof is insufficient for the wording "the number of steps."

### A02-003 - High: six-input semantics cannot be silently replaced by a
one-tape serialization while preserving the claimed runtime

The paper sampler has six input tapes. Its arities are exactly:

| Query | Non-ignored tapes |
| --- | --- |
| dimension | `(n, dimension)`; tapes 3 through 6 ignored |
| marginal | `(n, w, marginal, j, z)`; tape 6 ignored |
| linear | `(n, w, linear, j, u, y)` |
| factor | `(n, w, factor, j, u)`; tape 6 ignored |

`rmk:sampler-inputs` (`conditionally-linear.tex:602-613`) confirms this
variable-arity convention. `top-level/preliminaries.tex:96-122` supplies a
canonical dual-rail tuple encoding, but the cited universal one-tape simulation
has only polynomial overhead. That fact alone cannot prove the sharper
`O(TIME_S(n) * log q(n))` downsize bound.

Freeze an explicit six-tape input type (`Fin 6 -> List Bool`), ignored-tape
semantics, tag/integer/vector codecs, and a machine operational model. A
`Turing.TM2ComputableAux Bool Bool` backend is admissible only with a theorem
showing that the chosen compilation and downsize compiler preserve the exact
cost relation required here. Otherwise retain a thin six-tape semantics for
this node. Do not cite the paper's generic polynomial simulation theorem as
the missing linear-logarithmic overhead proof.

### A02-004 - High: executable queries require an explicit chosen CL
decomposition; the source contains a prefix inconsistency and omits `y`'s
domain

For every positive `n`, `def:sampler` first existentially chooses two CL maps
and their marginal/factor/linear-map data. `lem:cl-kth`
(`conditionally-linear.tex:150-178`) indexes a factor and linear map by
`u in L_<j(V)`, and the paper states at `:275-280` that such decompositions need
not be unique. The existing F06 plan stores the recursive certificate in
`Prop`. Lean cannot generally eliminate that proof into executable query data.

The executable sampler must therefore carry a data-valued
`CLQueryDecomposition` for each associated map, together with proofs that its
marginals, factors, and linear maps realize the F06
`ConditionallyLinearCertificate`. It must not pretend to extract these choices
from the proposition, and it must not move them into an arbitrary public
"obligation" argument to the paper theorem.

There are two source defects to preserve as explicit paper-gap notes:

- The linear-query bullet (`conditionally-linear.tex:586-589`) says that `u`
  is interpreted as an element of `V_<j`; the factor bullet and
  `lem:cl-kth` require `u in L_<j(V)`. The latter is the type-correct
  mathematical interface. This repair must be documented, not silent.
- The quantifier prefix of `def:sampler` names `w`, `j`, and `z`, but the
  linear bullet introduces `u,y` without quantifying their domains. From
  `lem:cl-kth`, a valid `u` is in the previous-marginal range and valid `y`
  lies in the corresponding factor subspace. Use dependent subtypes for both;
  behavior on raw invalid strings remains unspecified.

A second apparent typo occurs in `lem:cl-downsize`
(`conditionally-linear.tex:394-430`): its displayed original-side map is
indexed by `downsize(u)` where the original family is indexed by `u`. The
type-correct conjugate uses `L_{j,u}`. Record that correction when connecting
the sampler theorem to F06.

### A02-005 - High: the executable bit codec is not supplied by the current
`FieldData` API

`finite-fields.tex:234-263` defines admissible sizes as `2^k` for odd `k` and
defines the bit representation by coordinates in a specified basis.
`finite-fields.tex:283-307,350-411` further fixes the basis used by machines to
the deterministic Shoup-Lenstra-Wang construction and claims polynomial-time
basis/table generation and arithmetic.

`MIPStarRE/QPBT/Basic/Field.lean` currently exposes a mathematical
`FieldData k`, noncomputable `fieldDataOfOddExponent`, `coordinates`, and a
multiplication matrix. It does not expose:

- a `Bool`/`ZMod 2` bit-string codec with fixed coordinate order;
- the algorithm-selected basis and multiplication tables; or
- a coherence theorem between that algorithmic representation and
  `FieldData.coordinates`.

The mathematical downsize map can use F01's selected `FieldData`; the
paper-labelled executable representation must ultimately be specialized to a
canonically constructed codec coherent with the source algorithm. An arbitrary
codec/coherence premise on the downsize theorem would hide G16/K03A proof debt
and is forbidden. Until that construction is discharged, keep the faithful
source theorem visible with tracked proof debt and, if useful, give only an
internal conditional helper a name ending `_ofObligations`.

### A02-006 - High: the downsize machine and its runtime proof need more than
the paper's last sentence

`def:downsize_sampler` (`conditionally-linear.tex:631-660`) prescribes:

- dimension: original dimension multiplied by `log q`;
- marginal: forward the identical bit string;
- linear: invert `u' = downsize(u)` on a valid prefix, then forward;
- factor: expand each original indicator bit to an ordered block of exactly
  `log q` equal bits.

`lem:downsize_sampler` (`:667-680`) assumes `ell >= 1`, returns a binary-field
`ell`-level sampler of dimension `s(n) * log q(n)`, identifies both associated
maps pointwise for every positive `n`, and asserts the global runtime bound.
Its proof (`:682-712`) only says that factor output takes `O(log q)` longer.
It does not bound parsing, tuple construction, prefix conversion, simulation,
or output copying in the selected operational model. This is a proof gap, not
permission to add a runtime premise.

The compiler theorem must prove those costs and exploit the source fact that a
field vector's binary representation is byte-for-byte the representation of
its downsize. Prefix inversion is valid only on the encoded range. The factor
proof must freeze block order. The original factor output already costs at
least its written length; that lower-bound fact, if used to absorb output cost,
must be proved in the chosen machine semantics.

### A02-007 - Medium: preserve positivity, level, exponent, and multiplication
order exactly

- Paper `n` ranges over positive integers. Lean `Nat` APIs need `0 < n` guards
  or a positive-index subtype; an arbitrary value at zero is boundary data.
- The downsize lemma, unlike the general CL downsize definition, explicitly
  assumes `1 <= ell`. Do not prove a paper-labelled `ell = 0` strengthening.
- `q(n) = 2 ^ k(n)` with `Odd (k n)`; downsize field size is `2 = 2^1`.
- All logarithms are base 2. `Nat.log 2 (2 ^ k) = k` is exactly
  `Nat.log_pow (by decide) k` in the pinned Mathlib.
- Preserve the source expression as `s n * Nat.log 2 (q n)`, not a silently
  reordered or asymptotic-only dimension.

### A02-008 - Medium: expose the sampler distribution and its exact
pushforward, not only the associated maps

`def:sampler-sample` (`conditionally-linear.tex:617-626`) defines the sampler
law as `mu_(L^Alice,n,L^Bob,n)`, using one shared uniform seed.
`lem:downsize-cl-dist` (`conditionally-linear.tex:533-550`) and the associated
map clause of `lem:downsize_sampler` imply the exact pairwise pushforward under
the coordinate downsize map. This should reuse F06's
`CLSampler.sample_downsize`; it is an equality of PMFs, not an asymptotic or
independent-product claim.

## Exact paper contract

The source quantifier order is:

1. Fix `q : N -> N`, `s : N -> N`, level `ell`, and one six-input machine
   `S`; assume every positive-index `q(n)` is admissible.
2. For every positive `n`, set `q = q(n)`, `s = s(n)` and choose
   `L^(Alice,n), L^(Bob,n) : F_q^s -> F_q^s` plus level-`ell`
   marginal/factor/linear decomposition data satisfying `lem:cl-kth`.
3. For both players, every level `j` in `{1,...,ell}`, and every valid semantic
   argument, the four machine query modes return the specified binary
   representation. The machine is allowed to ignore unused tapes.
4. Define the sampler distribution from the two associated maps and one common
   uniform `x`.
5. Given such an `S`, construct `downsize(S)`. If `1 <= ell`, prove it is an
   `ell`-level binary sampler, prove dimension `s(n) log_2 q(n)`, identify both
   associated maps at every positive `n`, and prove the global-positive-index
   runtime bound.

The paper does not define machine behavior on malformed encodings, invalid
levels/prefixes/factor vectors, or index zero. Query tags, natural-number bit
encoding, tape orientation, vector coordinate order, and ignored-tape contents
are also not fixed beyond the general binary-string and dual-rail discussion.
Those choices are faithful Lean boundary data and must be documented in the
new node.

## Recommended callable surface

The new node should depend on `F01-FIELD` and `F06-CL`, live in
`MIPStarRE/QPBT/Game/Types.lean`, and remain in QPBT-038's writer lane. It
should not make F07A, K03, or K04 an owner. F07 may consume it when an
executable typed sampler is actually introduced; F07A then consumes that typed
layer transitively. K03/K04 retain their disjoint source ranges.

The exact public concepts and theorem shapes should be:

```lean
structure AdmissibleFieldFamily where
  exponent : Nat -> Nat
  exponent_odd : forall n, 0 < n -> Odd (exponent n)

def AdmissibleFieldFamily.fieldSize
    (Q : AdmissibleFieldFamily) (n : Nat) : Nat :=
  2 ^ Q.exponent n

abbrev SixTapeInput := Fin 6 -> List Bool

-- Data-valued, chosen decomposition associated to one F06 CL map.
structure CLQueryDecomposition
    {k n ell : Nat} (L : ConditionallyLinearMap k n ell) where
  -- marginal, prefix-range-indexed factor, and factor-space linear maps
  -- plus their exact lem:cl-kth realization proofs

inductive CLSamplerQuery
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell n : Nat)
    (associated : CLSampler (Q.exponent n) (s n) ell)
    (decomposition : /* Alice/Bob chosen decompositions */) where
  | dimension
  | marginal (w : Fin 2) (j : Fin ell)
      (z : FieldVector (Q.exponent n) (s n))
  | linear (w : Fin 2) (j : Fin ell)
      (u : /* subtype of the previous-marginal range */)
      (y : /* subtype of the j,u factor space */)
  | factor (w : Fin 2) (j : Fin ell)
      (u : /* subtype of the previous-marginal range */)

def CLSamplerQuery.tapes : CLSamplerQuery Q s ell n A D -> SixTapeInput
def CLSamplerQuery.expectedOutput : CLSamplerQuery Q s ell n A D -> List Bool

structure IndexedSixInputBitMachine where
  -- actual operational machine, output, exact per-input steps, and run theorem

structure ExecutableCLSampler
    (Q : AdmissibleFieldFamily) (s : Nat -> Nat) (ell : Nat) where
  associated : forall n, CLSampler (Q.exponent n) (s n) ell
  decomposition : forall n, /* chosen data for both associated maps */
  machine : IndexedSixInputBitMachine
  correct : forall n (hn : 0 < n)
    (query : CLSamplerQuery Q s ell n (associated n) (decomposition n)),
    machine.output (query.tapes) = query.expectedOutput
  time : Nat -> Nat
  time_eq_validQueryMax : forall n, 0 < n -> /* exact finite maximum */

noncomputable def ExecutableCLSampler.sample
    (S : ExecutableCLSampler Q s ell) (n : Nat) :=
  (S.associated n).sample

def ExecutableCLSampler.downsize
    (S : ExecutableCLSampler Q s ell) :
    ExecutableCLSampler binaryFieldFamily
      (fun n => s n * Q.exponent n) ell

theorem ExecutableCLSampler.downsize_dimension
    (S : ExecutableCLSampler Q s ell) (n : Nat) (hn : 0 < n) :
    (S.downsize).dimension n = s n * Nat.log 2 (Q.fieldSize n)

theorem ExecutableCLSampler.downsize_associated
    (S : ExecutableCLSampler Q s ell) (hEll : 1 <= ell)
    (n : Nat) (hn : 0 < n) :
    (S.downsize).associated n =
      (S.associated n).downsize (/* canonical F01 field data at n */)

theorem ExecutableCLSampler.sample_downsize
    (S : ExecutableCLSampler Q s ell) (hEll : 1 <= ell)
    (n : Nat) (hn : 0 < n) :
    (S.downsize).sample n =
      PMF.map (fun pair =>
        (downsizeVector (/* canonical data */) (s n) pair.1,
         downsizeVector (/* canonical data */) (s n) pair.2))
        (S.sample n)

theorem ExecutableCLSampler.downsize_time
    (S : ExecutableCLSampler Q s ell) (hEll : 1 <= ell) :
    RuntimeBigO S.downsize.time
      (fun n => S.time n * Nat.log 2 (Q.fieldSize n))
```

The comment placeholders are dependent fields whose mathematical types must be
the F06 decomposition types, not proposition-valued or arbitrary implication
inputs. The paper-labelled theorem should consume the canonically constructed
field representation, not accept a caller's codec correctness premise.

Recommended exact direct imports for the node:

```lean
import Mathlib.Computability.TuringMachine.Computable
import Mathlib.Data.Nat.Log
import Mathlib.Probability.Distributions.Uniform
import MIPStarRE.QPBT.Basic.Field
```

`Mathlib.Analysis.Asymptotics.Defs` is optional only for a separately proved
comparison theorem; it is not needed by the exact `RuntimeBigO` definition.
Import `Computable`, not a deprecated Turing-machine umbrella. Use the
nondeprecated `StateTransition.EvalsToInTime` name in new declarations.

## Statement-integrity checklist

| Clause | Paper assumptions | Faithful Lean boundary | Required Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| admissible family | positive `n`; `q(n)=2^k`, odd `k` | Nat extension plus `0<n` guard; exponent function and oddness | exact field size | exact, modulo documented zero extension |
| sampler | one six-input machine; per-index associated Alice/Bob CL maps and decompositions | explicit codecs, valid dependent query subtype, chosen data-valued decompositions, operational machine | all four binary outputs and exact valid-query time | faithful boundary; A02-002/003/004 must be explicit |
| sampler distribution | associated Alice/Bob maps, common uniform seed | F06 finite PMF | `CLSampler.sample` | exact |
| executable downsize | admissible source sampler | canonical source-coherent field codec, prefix-range inverse, block-order codec | constructed binary machine with four prescribed behaviors | faithful boundary; codec/compiler proof debt remains |
| downsize dimension/level/maps | `1<=ell`, every positive `n` | F06 `CLSampler.downsize`, base-2 exponent identity | field 2, same level, `s*log q`, both maps downsized | exact once A02-005 is discharged |
| downsize distribution | preceding associated-map equality | F06 `sample_downsize` | exact pair pushforward | exact |
| downsize runtime | same machine model and exact index time | global-positive `RuntimeBigO`; proved compiler costs | `TIME_down = O(TIME_S * log q)` | documented paper/API gap until A02-001/002/003/006 are proved |

Acceptance checklist:

- [ ] `n` is positive in every paper-labelled pointwise claim.
- [ ] `1 <= ell` is present on `lem:downsize_sampler`'s Lean theorem.
- [ ] All four query constructors have exact six-tape encodings and ignored
      tapes.
- [ ] `u` and `y` use valid dependent subtypes; malformed inputs are not
      silently totalized into the theorem.
- [ ] Associated decomposition data is explicit and proved to realize F06; no
      elimination from `Prop` is assumed.
- [ ] The finite-field bit codec has fixed coordinate order and source-basis
      coherence; no arbitrary public coherence premise discharges it.
- [ ] `TIME_S(n)` has an explicit aggregation definition based on exact
      per-query steps.
- [ ] Runtime uses global positive-index `RuntimeBigO`, not only `atTop`.
- [ ] Dimension is exactly `s n * Nat.log 2 (Q.fieldSize n)`.
- [ ] Both associated maps and the exact sampler PMF pushforward are callable.
- [ ] The factor indicator is expanded into ordered constant blocks of length
      `log q`.
- [ ] F07A/K03/K04 remain excluded as owners of this generic source range.

## Source authentication

Authenticated detached Git identity:

- commit: `77172fd30105531f668acc0338caae028901d24d`
- tree: `4c158849f44522dc92c8229aeb223d96ece4cf0b`
- detached worktree: `/tmp/qpbt-048-source-audit-a02`
- status before report: clean

Pinned labels and split locations:

| Label | Split line | Original line |
| --- | ---: | ---: |
| `def:sampler` | 573 | 2735 |
| `def:sampler-sample` | 617 | 2779 |
| `def:downsize_sampler` | 631 | 2793 |
| `lem:downsize_sampler` | 667 | 2829 |
| `def:admissible-size` | finite-fields 239 | 1561 |
| `rmk:tm_fields` | finite-fields 404 | 1720 |

SHA-256 evidence:

| Artifact | SHA-256 |
| --- | --- |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `dependencies/finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |
| `dependencies/types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` |
| `top-level/preliminaries.tex` | `045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1` |
| `sections/inventory.json` | `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4` |
| `sections/READY` | `4d6a33759051b17428b3928d529d18e10da82e3bc09c75fbe429df324612b360` |
| `sections/labels.json` | `4da8ef3d95525e4c88ccafda3ff088aed5edd1b3ded97357024342d54f857cc7` |
| `source-pin.json` | `66a1e9db74f1454ce50909728a3b741f9da468b5d61902645557793ceb91ac9c` |
| `split-manifest.json` | `052cfaceb2e4a7b59778936ceb3daea9a33e3592e01b902cb2a9740c58999a20` |
| base `blueprint/metadata/nodes.json` | `48e249d63d7e22c3c51af4a81b27cd23d96c195c7e2a737315aa5f88d4ce03f7` |
| base `MIPStarRE/QPBT/Basic/Field.lean` | `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e` |
| `lake-manifest.json` | `d20abbe9525a311d501feb89299492717e27c88f441ac77191d9394b49e47fa9` |
| `lean-toolchain` | `2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e` |
| A11 review | `ea250f6c921716e21ba758e47cbf0bc7e96a89582b05df4ecbc897cbdcf25687` |
| A12 repair report | `df93700d6879e8c67649b5b25b641fe2a498c963eb2d7e77f504f024b8bb53b0` |
| mutable issues cutoff | `3d9507940c3658c30a6ee84e781ad646dfa55a016f2755a0c6d5814d83627334` |
| mutable PRs cutoff | `e2bfdd37537925e4a625abd2bcd136e50d2e37e8d5a18e8dc1b45c7d6b877eae` |

The pinned Mathlib revision is
`81a5d257c8e410db227a6665ed08f64fea08e997`. Relevant module hashes:

| Mathlib module | SHA-256 |
| --- | --- |
| `Computability/TuringMachine/Computable.lean` | `acb5fa046c00afd1f85570d4439653b009b7353d7ed93aa7a6fc52dae346a59b` |
| `Analysis/Asymptotics/Defs.lean` | `813c16f6323617fd6cb589d118d19d62873e82b46fa76399155c46fed9e9da87` |
| `Data/Nat/Log.lean` | `9800e6942155e28138ed981a06340d7333aacccfafcd1aa35147147ae57d8e3f` |

A11's `F-LPR023-004` correctly found that F06's executable source debt was
assigned to K03/K04 despite their disjoint anchors. A12 corrected the false
ownership but intentionally left this generic layer unowned. QPBT-048 is the
right dedicated issue. The base blueprint evidence confirms F06/F07/F07A are
faithful mathematical/typed boundaries and K03/K04 own only their exact
parameter/game complexity clauses.

## Lean probes

All probes were bounded `lake env lean /dev/stdin` signature/API checks against
the pinned dependency installation. They wrote no source or build artifact in
the audit worktree.

| Attempt | Result | Evidence |
| ---: | --- | --- |
| 1 | expected probe failure | All requested Turing/asymptotic/log APIs checked; only the deliberately queried nonexistent `Nat.log_self` failed. |
| 2 | candidate-shape failure | Exposed two local probe mistakes: ASCII `->l` was not the Lean linear-map arrow, and one identity PMF map used incompatible field/dimension parameters. No project defect. |
| 3 | pass | Corrected candidate structures for admissible family, chosen query decomposition, six-tape query encoding, `TM2ComputableAux` wrapper, executable sampler/downsize, dimension, associated maps, distribution pushforward, and an at-top comparison all elaborated. Ten probe-local `sorry` bodies; no persisted file. |
| 4 | pass | Exact global-positive `RuntimeBigO` and target product with `Nat.log 2` elaborated. One probe-local `sorry`; no persisted file. |

Confirmed APIs include `Turing.FinTM2`, `Turing.TM2ComputableAux`,
`Turing.TM2OutputsInTime`, `StateTransition.EvalsToInTime`,
`Asymptotics.IsBigO`, `Filter.atTop`, `Nat.log`, and `Nat.log_pow`. Mathlib's
`TM2OutputsInTime` is at-most time, and `TM2ComputableInTime` indexes its time
function by encoded input length; neither fact resolves A02-002.

Probe counters: 4 attempts, 2 passes, 2 diagnostic failures, 0 persisted probe
files, 11 `sorry` bodies in successful probes, 0 target builds, and 0 full
builds.

## Metrics and counters

- Durable start: `2026-09-01T17:14:23.268697Z`.
- Evidence cutoff: `2026-09-01T17:39:07.785515824Z`.
- Elapsed to cutoff: `1484.516818762` seconds.
- Topology: root coordinator -> one depth-1 read-only scout; 0 nested agents.
- Findings: 8 total (1 critical asymptotic-semantics blocker, 1 critical
  time-domain blocker, 4 high executable/source blockers, 2 medium integrity
  constraints).
- Primary paper files inspected: 4; exact blueprint nodes inspected: 5
  (`F06`, `F07`, `F07A`, `K03`, `K04`); project Lean modules inspected: 1;
  Mathlib API modules inspected: 3; prior immutable reports inspected: 2;
  canonical issue records inspected: 1; local PR records inspected: 1.
- Lean signature probes: 4; scoped target builds: 0; full builds: 0; hot-cache
  warms/seeds: 0; source materializations: 0.
- Repository/canonical edits: 0; Git writes: 0; `/tmp` report writes: 1;
  network: 0; endpoint: 0; GitHub: 0; credentials: 0; nested agents: 0.
- A01 moving worktree/report reads: 0.

Token usage:

```json
{
  "input": null,
  "output": null,
  "total": null,
  "availability_reason": "Collaboration backend does not expose per-agent token usage"
}
```

No network source lookup was performed. The finite-field representation audit
used the authenticated pinned paper split and its cited algorithm claims; it
does not independently certify the external Shoup, Lenstra, or Wang papers.
