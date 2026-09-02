# QPBT-038 Types implementation attempt A03

Session: `i038-orchestrator-a03-types`
External identity: `/root/i038_orchestrator_a03_types`
Role: sole writer/orchestrator
Assigned worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-038-types-a02`

## Verdict

**Blocked at the required first F06A compiler gate; no `Types.lean` candidate
was created.** The frozen `ExecutableCLSampler.downsize` declaration requires
a constructed `Turing.FinTM2`, genuine query-indexed
`TM2OutputsInTime` executions, and a proved global-positive
`RuntimeBigO` bound. The pinned proved API has no machine composition,
simulation, parser, output-loop, or resource theorem. Its only concrete
`FinTM2` program is `idComputer`; the advertised
`TM2ComputableInPolyTime.comp` is a `proof_wanted` command and does not create
an elaborated declaration. A direct probe confirmed that
`Turing.TM2ComputableInPolyTime.comp` is an unknown constant.

This is a dependency blocker, not authority to weaken the theorem. No public
compiler obligation, bridge, residual, repair, witness, package, producer,
generic assumption, `sorry`, `admit`, `axiom`, `constant`, or fabricated run
relation was introduced. The rejected zero-map/pure-zero candidate
`9070aa4d7db267fd890c9b487defa2940e9810a` was used only as negative evidence.

F06 mathematical direct sum, shared-seed sampling, mathematical downsize, and
F07 remain feasible under their immutable signatures. They were not committed
as a partial `Types.lean`: the reviewed declaration order is F06, F06A, F07,
and the issue acceptance gate requires the complete 81-name surface. Moving
F07 ahead of absent F06A or presenting only F06 as this issue's candidate would
create another misleading interface checkpoint after A01. The implementation
should resume after the compiler dependency below is proof-complete.

## Exact blocker and discharge plan

Pinned Mathlib `81a5d257c8e410db227a6665ed08f64fea08e997`
provides `FinTM2`, the primitive statement language, `TM2Outputs(InTime)`,
execution-trace transitivity, and the identity machine. It provides no proved
combinator for arbitrary finite machines. At
`Mathlib/Computability/TuringMachine/Computable.lean:284-288`, composition is
only:

```lean
proof_wanted TM2ComputableInPolyTime.comp ... :
  Nonempty (TM2ComputableInPolyTime eAlpha eGamma (g o f))
```

Even a proved theorem of that displayed type would be insufficient by itself:
it bounds a polynomial in encoded input length, while the frozen result needs
exact execution witnesses and one constant bounding every positive index by
`S.time n * Nat.log 2 (Q.fieldSize n)`.

Recommend a numbered sequential dependency for a proof-complete internal
`FinTM2` compiler/resource layer. Its acceptance must include:

1. lift arbitrary source and exponent machines into one finite stack/label/
   state space and prove step/trace simulation;
2. verify parsing of the exact `encodeNat (Encodable.encode (List.ofFn input))`
   six-tape packing and reconstruction of canonical source inputs;
3. implement the four downsize modes: dimension multiplication, marginal bit
   pass-through, linear prefix conversion, and ordered factor-bit expansion;
4. construct the binary-family exponent program and every exact
   `TM2OutputsInTime` execution used by the returned sampler; and
5. derive input/output-size domination from machine syntax and prove the
   global-positive `RuntimeBigO` result from the exact valid-query/exponent
   maximum.

The dependency must remain internal and proof-complete. Adding it as a field or
hypothesis of a paper-facing declaration would violate the repository rules
and the frozen F06A contract.

## Mathematical handoff

The F06 direct-sum scout found a complete construction route without changing
the marker. Equalize levels with empty-head/full-tail raising, combine two
same-level certificates recursively, recover component range prefixes by
restricting the combined prefix value, and define the public function by
splitting and `Fin.append`-ing both actual inputs. Define `CLSampler.sample` as
one `PMF.uniformOfFintype` seed mapped to `(S.alice x, S.bob x)`; prove the
binary direct-sum theorem using private uniform-product and equivalence lemmas.

The F06 downsize scout likewise found no signature blocker. Use
`FieldData.coordinates`, `finProdFinEquiv`, and
`GaloisField.equivZmodP 2` for the sole public coordinate equivalence. Expand a
source register to every binary coordinate in its block; restrict source head
maps to `ZMod 2`, conjugate by `downsizeVector`, and rebundle them as
`GaloisField 2 1`-linear maps through the algebra equivalence. Pull recursive
range prefixes back with `downsizeVector.symm`, and transport the one-seed PMF
through the same equivalence. The construction is total for hypothetical
`D : FieldData 0`; `Fin (n * 0)` and all expanded registers are empty, so no
zero fallback or impossible-case eliminator is needed.

F07 should then bind the uniform ordered-edge PMF to the F06 shared-seed law
selected by the edge endpoints. Its downsize theorem follows from the exact
F06 PMF pushforward. The dependent question/answer fibers remain arbitrary;
only type/edge support and the constant field-vector sampler carrier are
finite.

## Paper-gap notes

The source-first review found the following material defects. They should be
entered or linked by the canonical state owner; none was silently turned into
an assumption.

| Source | Defect | Type-correct reading |
| --- | --- | --- |
| `conditionally-linear.tex:126-129` | The level-raise remark says `V_1 = V`, `V_{>1} = {0}`, `L_1` is zero, and `L_{>1,x^{L_1}}` is also the zero map. With the recursive equation this yields zero, not the old function. | Use empty head/full tail: `V_1 = {0}`, `V_{>1} = V`, zero head, old function as tail. |
| `conditionally-linear.tex:377` | The proof samples `x` uniformly from `V x V`, contradicting `def:cl-dist` and the surrounding proof. | One uniform `x : V` feeds both `L` and `R`. |
| `conditionally-linear.tex:425-428,453-455` | The original linear map is indexed by `downsize(u)` although its source prefix index is `u`. | At target prefix `v`, conjugate the source map indexed by `downsize^-1(v)`. |
| `conditionally-linear.tex:432-438` | The lemma permits level zero but its induction begins at level one. | The omitted level-zero case is the unique zero certificate. |

The already tracked G19 gap concerns computing the arbitrary exponent from
`n`; its `FieldExponentProgram` repair is necessary but does not provide the
missing compiler or its resource theorem.

## Statement integrity

| Node | Paper assumptions | Frozen Lean assumptions | Paper conclusion | Implementable conclusion / verdict |
| --- | --- | --- | --- | --- |
| F06-CL | Finite coordinate field spaces, recursive complementary register factors, independent uniform direct-sum coordinates, selected basis for downsize | Concrete `GaloisField` vectors and recursive certificates; `FieldData` only at downsize | CL maps/distributions, level raise, direct sum/product law, conjugated downsize/pushforward | Exact mathematical construction described above; **faithful boundary, feasible, not implemented in A03** |
| F06A-EXECUTABLE-CL | Positive indices, admissible field sizes, dimension, one six-input sampler with four modes, positive level for downsize | Frozen canonical codec/tapes, dependent valid queries, actual sampler and exponent `FinTM2` executions, exact step maximum | Constructed executable downsize, field size 2, dimension `s log q`, downsized maps/PMF, global `O(TIME_S log q)` | Same target cannot be constructed from pinned proved APIs without the compiler/resource dependency; **faithful boundary, blocked** |
| F07-TYPED | Finite type graph with loops/orientations, typed CL families, selected basis | Nonempty symmetric ordered-edge finset, constant field-vector CL families, arbitrary dependent decider fibers | Typed graph/sample law, downsize pushforward, total dependent decider | Exact mathematical construction remains feasible after F06A order is restored; **faithful boundary, not implemented in A03** |

## Provenance and immutable identities

No network, endpoint, GitHub, or credential operation occurred. Sources were
read from the canonical authenticated materialization at
`/home/drx/MIPStarRE-auto/references/2001.04383v3`.

| Artifact | SHA-256 |
| --- | --- |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `dependencies/finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |
| `top-level/preliminaries.tex` | `045ef86cf9bb1ca5898f66de29f814fc869a54d357160286322c4cad7786aab1` |
| `dependencies/types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` |
| `MIPStarRE/QPBT/Basic/Field.lean` | `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e` |
| pinned `Computable.lean` | `acb5fa046c00afd1f85570d4439653b009b7353d7ed93aa7a6fc52dae346a59b` |
| pinned `StackTuringMachine.lean` | `ae6fda6914374b51b88ffd3eea75c6393ec84ac487bb36fb88b54999c43f9ea6` |
| pinned `StateTransition.lean` | `eceb96a26dccbd8f8abcd83874539b49b8b7e797f195a864cff85c1bbe8476b2` |
| frozen F06 marker | `120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461` |
| frozen F06A marker | `cfe433e36d0670c344b29ab5107557842e7d4fc8358fba2713b8ff2ee107a3a1` |
| frozen F07 marker | `99cfe240da252a94527d50c53d39a9673ee8d673cf6eba9730fb1a7e92df9d46` |

The evaluated implementation identity stayed unchanged throughout the critical
gate:

- exact base/head: `5e5c4e025db423e87f76b0185533cd21f5ce9ab5`;
- tree: `48f0d01eb63ecafded160f321ed0b5a920b08327`;
- sole parent: `66a876158cafe5022030e43dc8200002ee7bdfc4`;
- branch: `issue/qpbt-038-types-a02`;
- `MIPStarRE/QPBT/Game/Types.lean`: absent at base and intentionally absent in
  this attempt.

The report-only handoff commit identity and this report's final Git blob and
filesystem SHA-256 are returned out of band after the final bytes are committed
because embedding any of those identities in this file would be
self-referential. No other changed path is permitted or present.

## Validation and cache accounting

| Command/check | Result | Observed wall time |
| --- | --- | ---: |
| `git status --short --branch`, `git rev-parse`, merge-base checks | PASS: clean assigned branch at exact base | 0.2 s |
| required paper/blueprint/marker/API reads and hash checks | PASS: local pinned bytes and frozen manifests inspected | batched read-only calls, each 0.2-0.5 s |
| `lake env lean /dev/stdin` exact composition-name probe | Expected blocker reproduced: `Unknown constant Turing.TM2ComputableInPolyTime.comp`; `FinTM2` and `idComputableInPolyTime` resolve | 18.6 s including PTY EOF polling |
| `git diff --check` before report | PASS | <0.1 s |
| `lake env lean MIPStarRE/QPBT/Game/Types.lean` | NOT RUN: target intentionally absent after critical gate failed | n/a |
| forbidden-debt/import/tape/output/dimension/loop/codec scans | NOT RUN on target: no target was created; report and worktree scope checked instead | n/a |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | PASS: 54 nodes, 12 chapters, acyclic deterministic outputs and source synchronization | 0.5 s batched |
| `python3 scripts/check_workflow.py --root . --skip-tests` | PASS: workflow state valid | 0.5 s batched |
| `python3 scripts/workflow.py validate` | PASS: 55 issues, 32 PRs, 458 issued sessions, 7 stages | 0.5 s batched |
| affected Lean target | NOT RUN: no Lean declaration changed | n/a |
| full `lake build` | NOT RUN: scoped file never became stable; duplicate/unproductive full build was avoided | n/a |

The coordinator supplied this worktree with a private preseeded `.lake`; it was
not warmed, reseeded, or shared by this session. Observed private cache size was
`3.0G` for `.lake/build` and `6.9G` for `.lake/packages`. There was no cache
lock wait and no build duration. Cache-hit status for a seed command is
`null`, availability reason: the seed occurred before this session and no seed
receipt was exposed. The target `Field.olean` was not present in the private
cache, but no target build was attempted after the mandated stop.

## Topology, attempts, and incidents

Topology used all available bounded read-only lanes:

- orchestrator -> `i038_scout_a03_f06a` (first critical gate), report
  `/tmp/i038-scout-a03-f06a.md`, SHA-256
  `be4c5793850a17e1bc816a375056351aa9528806d2b6f0949d2c363da02af8af`;
- orchestrator -> `i038_scout_a03_f06` (second launch), report
  `/tmp/i038-scout-a03-f06.md`, SHA-256
  `da9b7b1d51ae11d9b17efc7caf2ec5adf553a9e6e2bc334e3c44f4383d5972b3`;
- after F06A finished, orchestrator -> `i038_scout_a03_downsize` (third launch,
  slot reuse), report `/tmp/i038-scout-a03-downsize.md`, SHA-256
  `8c0b1f19c39f05ae99281873d80990ad5212b4210e793676f39188c73a4e11f3`.

Nested subagent count: `3` direct children, maximum `2` concurrently active,
no grandchildren. All were read-only, ran no Lean/Lake/build/cache/network
operation, and wrote only their exact `/tmp` report. The downsize scout reports
56 shell invocations across 13 orchestration calls; the backend did not expose
equivalent counters or timestamps for the other two scouts.

Compile attempts: `1` bounded API-name probe, `0` target builds, `0` full
builds. Retries: `0` implementation retries. Incident: the first attempt to
name a child used hyphens and was rejected before launch; it was immediately
corrected to the required lowercase/underscore name. A probe file was briefly
created at canonical root due an `apply_patch` working-directory mistake and
immediately deleted before any repository commit or source work; canonical
root returned to its prior status, and the actual probe used `/dev/stdin`.
The first scoped commit attempt was rejected because sandboxed Git could not
write the linked-worktree index lock; the same exact add/commit was then
approved outside that restriction. A post-commit diff check found three
Markdown hard-break trailing spaces that the untracked-file pre-check had not
inspected; they were removed in one whitespace-only amend.

Observed evidence cutoff: `2026-09-02T21:07:57.479942938Z`. Session start,
per-agent start/end timestamps, total elapsed time, and per-session token counts
are `null`; availability reason: the collaboration runtime did not expose
them. Token accounting is therefore:

```json
{
  "input_tokens": null,
  "output_tokens": null,
  "total_tokens": null,
  "availability_reason": "collaboration runtime does not expose per-session token usage"
}
```

Protocol revision: none. Canonical `workflow/state/` and `research/metrics/`
were not edited; the root coordinator alone owns the dependency/gap/state and
metrics updates.
