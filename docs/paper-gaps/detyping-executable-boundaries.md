# Detyping executable boundaries

Tracking: `G24`, `G25`, `G26`, and `QPBT-080`.

## Authenticated source boundary

The primary source is arXiv:2001.04383v3
`dependencies/types.tex:197-579` (original lines 3763-4145), especially
`lem:detyping-verifiers`. The executable typed-sampler and typed-decider
definitions are at `types.tex:95-195` (`def:typed-sampler`, original lines
3661-3761). The polynomial convention is at
`top-level/preliminaries.tex:19-32` (original lines 916-929), canonical machine
descriptions and universal simulation are at lines 77-137
(`thm:universal-tm`, original lines 974-1034), and the high-level machine-cost
conventions are at lines 171-200 (original lines 1068-1097). The raw decider
domain and game widths are at `top-level/nonlocal-games.tex:612-678`
(`def:decider`, original lines 3489-3555).

## G24: missing width transport

The typed game takes source question and answer widths from the source sampler
and decider times. The detyped game independently uses the target times, while
the paper's target predicate forwards the received source-content and answer
strings unchanged and its completeness and soundness proof reuses the same
outcome labels. The source supplies no width equality, embedding, projection,
padding convention, retraction, or measurement coarsening.

The internal Lean construction must prove source-to-target width domination;
define fixed-prefix projections and zero-extension sections for both question
content and answers; prove their retractions, including zero and equal widths;
separate the fixed graph prefix, the exact source-content prefix, and ignored
canonical padding; and prove exact parsing and failure behavior. Completeness
lifts source measurements by zero extension. Soundness postprocesses target
measurements by prefix projection. The projectivity, consistency, support
commutation, and PCC laws used by those transformations remain proof
obligations.

No transport premise is exposed to a caller, and the paper's completeness,
soundness, entanglement, error-factor, level, and dimension conclusions are
unchanged. Because prefix-based execution replaces literal full-string
forwarding, F07A is a documented mismatch until an operational locality
theorem proves the two behaviors equivalent.

## G25: omitted description compiler

The paper assumes reasonable canonical finite Turing-machine descriptions,
interpretation `[alpha]_k`, efficient tuple encoding and universal simulation,
then claims polynomial-time computation of the detyped sampler and decider
descriptions. It does not give a finite program grammar, decoder, interpreter,
detyping compiler, or semantic compiler-correctness proof.

The F07A boundary therefore instantiates a code-native finite program syntax,
canonical typed encoders and decoders, and an interpreter into the operational
machine model. Sampler and decider tags are distinct. Separate
graph-plus-sampler and graph-plus-decider compiler functions produce the exact
programs used by `detype`; semantic interpretation theorems identify their
outputs with those operational machines. Actual polynomial-time
compiler-machine witnesses establish both description bounds. Arbitrary bit
list pairing is not a compiler, and compiler correctness is not a public
hypothesis. The target sampler reuses the existing F06A
`ExecutableCLSampler` rather than duplicating it in F07A.

## G26: undefined raw-input maximum

The source assumes only that a decider halts on each raw input, but defines
`TIME_D(n)` as its maximum over every tuple whose first component is `n`. The
other string components have unbounded length. Pointwise termination therefore
does not establish a finite uniform maximum.

The executable boundary uses a total operational decider with an intrinsic
uniform per-index bound over all raw inputs. Every step count is derived from
an actual execution. If the API exposes a literal maximum, it also proves an
attaining execution. Restricting the definition to finite game-valid queries
would change the raw source domain and is not allowed; neither is accepting an
unconstrained claimed counter. This is well-formedness data of the executable
object, not a new premise of the detyping theorem.

## Runtime and codec decisions

Each use of the paper's polynomial notation has its own outermost universal
constant. The sampler theorem has `C_s > 0` before every type set, graph,
verifier, source index, and positive numerical argument, and its bound is

```text
TIME_detype(S)(n) <= C_s * (|TypeId| * TIME_S(n)) ^ C_s.
```

The decider theorem separately has `C_d > 0` in the same outermost position
and uses

```text
TIME_detype(D)(n) <= C_d * (|TypeId| * TIME_D(n)) ^ C_d.
```

The witnesses may differ because the convention allows the universal constant
to vary between uses. Positivity applies to the displayed arguments
`|TypeId|` and `TIME(n)`. It does not infer or silently add `0 < n`: the source
quantifies every `n in N`, and the meaning of source index zero in the Lean
natural-number convention remains explicitly unresolved.

Fixed-prefix graph/content/padding parsing and self-delimiting
variable-tuple/program encoding are separate codecs. Each receives its own
roundtrip and malformed-input laws. They are not collapsed into a false shared
codec contract.

## Statement integrity

| Field | Frozen contract |
|---|---|
| Paper assumptions | A finite nonempty type graph; one typed CL sampler machine with the four seven-input query modes and invalid-type zero behavior; one total typed decider; fixed-index typed and detyped games; machine runtimes and canonical descriptions; finite-game/PCC/value/Schmidt-rank semantics. |
| Lean assumptions | F07 mathematical typed interfaces, F04A game semantics, and the existing F06A executable sampler; an F07A-local interpreted finite-program boundary; bounded raw type codes; intrinsically uniformly index-bounded total deciders; explicit fixed-word question/answer transport; no caller-supplied compiler, runtime, transport, bridge, or obligation. |
| Paper conclusion | Exact graph event and conditioning law; detyped sampler, decider, and verifier; PCC completeness; value and entanglement soundness with factor `16^|Type|`; level `ell+2`; dimension `4|Type|+s(n)`; universal sampler/decider polynomial runtime bounds; polynomial-time computation of the actual target descriptions. |
| Lean conclusion | The same mathematical constructions and theorem conclusions over execution-derived times and interpreted compiled descriptions, with explicit prefix/zero-extension transport for source content and answers, target sampler reuse of F06A, and no public repair assumption. |
| Verdict | `documented mismatch`, solely because explicit prefix transport replaces the source's literal full-string forwarding until operational locality equivalence is proved. G25 and G26 are faithful executable boundary data once discharged. |

No paper-labelled theorem may accept a caller-supplied transport, compiler,
runtime, bridge, residual, repair, witness, package, producer, generic
assumption, or arbitrary implication input. The 20 canonical F07A callable
names and the direct prerequisites `F04A-GAME-SEMANTICS` and `F07-TYPED` remain
unchanged.
