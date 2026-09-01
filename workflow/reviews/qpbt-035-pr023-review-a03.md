# LPR-023 independent contract review (A03)

**Decision: request_changes**

## Findings

1. **High / blocker - F07 defers detyping to nodes that do not own it.**
   `blueprint/metadata/nodes.json:385` says executable detyping is explicitly
   deferred to K03-K04, and the manifest repeats that assignment at
   `workflow/reviews/qpbt-035-q014-contract-a02.md:394`.  K04 instead freezes
   exactly three complexity claims and expressly says not to add sampler claims
   (`blueprint/metadata/nodes.json:1137` and `blueprint/metadata/nodes.json:1141`);
   neither K03 nor K04 names a detyping definition or theorem.  The pinned source
   defines detyped CL functions, samplers, deciders, and verifiers and proves the
   completeness/soundness/parameter relation
   (`references/2001.04383v3/sections/dependencies/types.tex:371`, `:395`, `:409`,
   `:435`, and `:444`).  The base F07 boundary also promised that detyping
   equivalences would be proved, not erased.  This is therefore an unsupported
   ownership claim, not a faithful boundary.  Keep the source obligations visible
   under F07, or create an exact later node with dependencies and callable names;
   complexity-only K03-K04 cannot discharge them.

2. **High / blocker - the F06 manifest omits the source direct-sum distribution
   theorem required by QPBT-033.**  The contract has constructors
   `ConditionallyLinearMap.directSum` and `CLSampler.directSum`
   (`workflow/reviews/qpbt-035-q014-contract-a02.md:254` and `:276`), but its only
   sampler equation is `CLSampler.sample_downsize` at line 285.  The source
   separately proves that the direct-sum sampler distribution is the product
   distribution (`references/2001.04383v3/sections/dependencies/conditionally-linear.tex:365`).
   QPBT-033 required direct-sum facts to have an explicit frozen name or an exact
   later-node assignment (`workflow/reviews/qpbt-033-q014-split-a01.md:222`).
   Merely naming the operation does not expose the distribution equality to
   consumers, and no later assignment is recorded.  Add a precisely typed
   `sample_directSum`/reindexing theorem to the manifest, or assign this lemma to
   a concrete later node.

3. **Medium - F07's metadata claims finite dependent fibers that its signatures
   do not provide.**  `TypedQuestion` permits an arbitrary family, is not used by
   `TypedSampler`, and has no pointwise finiteness assumptions
   (`workflow/reviews/qpbt-035-q014-contract-a02.md:337`).  `TypedSampler.sample`
   instead fixes both question fibers to the same `FieldVector k n` (line 347),
   while `TypedDecider` independently accepts arbitrary, possibly infinite,
   question and answer families (line 362).  Thus the declarations are usable
   for the paper's common finite ambient vector after specialization, but they do
   not establish the advertised general contract of "finite dependent fibers"
   or a "total dependent finite decider" at
   `blueprint/metadata/nodes.json:385` and `:387`.  Either narrow those metadata
   claims to the constant finite sampler carrier and leave consumer finiteness to
   G02, or connect the sampler/decider through explicit dependent families and
   pointwise finite assumptions.

## Statement integrity

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F02 | Boolean cube input, field evaluation point, Boolean-indexed data | Separate `BooleanPoint`/`FieldPoint` over `GaloisField 2 k`; no `FieldData` | Coordinate-indicator product, encoding, interpolation, linearity/injectivity | Same product and equations | **exact** |
| F05 | Characteristic-two finite field; selected basis only for binary conversion | Concrete field and raw finite operator/measurement API | X/Z entries, product/square laws, normalized Fourier projectors, negative-trace twisted commutation | Same order, sign, phase, normalization, and tensor equations; F10 owns conversion | **documented mismatch (G09), faithful as frozen** |
| F06 | Finite coordinate space, recursive complementary factors, uniform shared seed, basis for downsizing | Concrete field vectors, recursive certificate, `FieldData` only at downsize | CL maps/samplers, raising, direct sums including product distribution, downsizing | Constructors and downsize pushforward, but no direct-sum distribution equation | **mismatch (Finding 2)** |
| F07 | Finite type graph, typed CL families and verifier data, graph semantics, typed downsizing and detyping development | Symmetric ordered support, constant-vector sampler fibers, unrelated generic dependent decider | Typed distribution/decider semantics and source detyping obligations | Graph PMF/marginal and Bool decider; detyping has no owner; finiteness overclaimed | **mismatch (Findings 1 and 3)** |
| G01 | Tuple `(q,m,d)` | Project-owned natural-valued tuple | `exists k, Odd k and q=2^k and m divides q` | Identical quantifier and conjunction order using `Dvd.dvd` | **exact** |

F02's Boolean-versus-field domains and actual product were checked directly.
F05's row/column orientation, negative phase, multiplication order, Fourier
normalization, `pauli_sq`, G09 boundary, and F03/F10 ownership were checked and
were not findings.  F06's recursive certificate, `raiseLevel`, `directSum`,
`downsize`, shared-seed sampler, and lack of a generic caller `Prop` were also
checked.  F07's loop counting and ordered orientation correctly realize the
paper denominator, and G01's quantifier/conjunction order is exact.

## Authentication and validation

- Authenticated head: `fdbb37a10e416c8a9891cdcdbcd44470573886b0`
- Authenticated head tree: `ca47214b88b0ef77aa0a72d22539004e4979290b`
- Authenticated base: `50c4a9ce9fc9446b04c1c309951f05cc6a49766c`
- Exact seven-path immutable manifest SHA-256:
  `d001ca49a11bbe32526931274a74e55b61a8a57b2544d0a79fd298f83680889d`
  (SHA-256 of the byte-exact, path-sorted `git ls-tree HEAD -- <seven paths>`
  output, including its trailing newlines).
- The seven Git blobs and filesystem bytes were authenticated.  The candidate
  report SHA-256 is
  `987d17140ae4e1e808ed0504b874c67dc1285f70245cf71363dafe97fc1dd610`.
- Recomputed signature-marker SHA-256 values matched metadata: F02
  `4468d05a235d7ccaa2eb9b355da4e2687bbd2c0bb6444046ce24d276c6c8006e`,
  F05 `2046e1a3784f6bf10a1a7c71b279bd41d5c27ed3424e20797cf7c5bba95b4aa7`,
  F06 `4ff1a12c51563b66f5671077c74b5c951905a8be7c30cae3e122a5932ab5505b`,
  F07 `4244dfbf6843f9641be2813b74f83046b93d41954f620a1309a9fedb0333b523`,
  and G01 `587cb393eff88db0291303da834e483e13f44eda8c2c286e2ab48721120386cb`.
  These use the checker's exact extraction: text strictly between the unique
  markers, followed by `.strip()`, with the fenced-code delimiters included.
- Pinned source hashes matched the candidate report for all five cited sections.
- Passed: blueprint unit tests (28 tests), default deterministic check (51 nodes,
  12 chapters), pinned-source-root check, workflow validation, workflow checker
  with `--skip-tests`, and `git diff --check`.
- A separate temporary archive copy regenerated deterministically with no output
  difference.  The authenticated review worktree was byte-untouched.
- Four bounded exact-signature Lean probes passed: F02, F05, combined F06/F07,
  and G01.  Probe-local `sorry` placeholders supplied bodies only; no repository
  `sorry`, axiom, constant, or assumption was added.
- No full build, affected-target build, cache warm, or cache seed was run, as
  required by the dispatch.

## Residual risk

This was a signature/contract review, not an implementation proof review.  The
bounded probes establish elaboration against the materialized upstream API, not
that the future bodies satisfy the equations.  F05's documented G09 mismatch and
later F10 binary conversion remain tracked source risk.  Generated declaration
synchronization cannot be exercised until the contracted Lean declarations are
implemented.

## Session metrics

- Durable dispatch start: `2026-09-01T13:55:07.424576Z`
- Evidence cutoff: `2026-09-01T14:14:22.956843580Z`
- Elapsed at evidence cutoff: `1155.532 s`
- Topology: one reviewer, zero nested agents
- Action counters: 1 temporary regeneration; 1 unit-test run; 1 default
  blueprint check; 1 pinned-source check; 2 workflow validations; 2 workflow
  checker runs; 1 diff-hygiene check; 10 marker-hash recomputations (including
  the five-block corrective audit); 4 Lean probe
  attempts; 0 full/target builds; 0 cache operations; 0 network/endpoint/GitHub
  operations; 0 repository/Git/state/metrics edits; 1 review artifact written
- Findings: 2 high/blocking, 1 medium
- Token usage: `null` (the execution environment does not expose per-session
  token accounting)
