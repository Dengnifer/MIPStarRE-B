# QPBT-036 / LPR-027 independent review A02

## Verdict and findings

**Verdict: approve.**

No blocking, high, medium, or low findings.  The candidate preserves the
Boolean-coordinate/field-evaluation distinction, implements the paper's
indicator product, exposes the encoding as a linear map, and proves the
evaluation, Boolean interpolation, and injectivity obligations without new
assumptions or proof debt.

## Mathematical and source-fidelity audit

The paper anchor was read first at
`references/2001.04383v3/sections/dependencies/low-degree-code.tex:1-94`
(SHA-256
`e77125aa2c20f037b949f8890efcaaf370f5ca25407048a5ac142115104bdc9e`).
The F02 finding and frozen contracts were then checked in
`workflow/reviews/qpbt-033-q014-split-a01.md:41-47,134-158`, F02-CODE in
`blueprint/metadata/nodes.json`, and the bound F02 signature block in
`workflow/reviews/qpbt-035-q014-contract-a02.md:45-94`.  The blueprint checker
authenticated the signature block at
`4468d05a235d7ccaa2eb9b355da4e2687bbd2c0bb6444046ce24d276c6c8006e`.

The implementation has the required domain separation at
`MIPStarRE/QPBT/Basic/Polynomial.lean:8` and `:10`.  The polynomial at `:24`
is exactly the finite product of `X i` when the Boolean coordinate is one and
`1 - X i` otherwise.  Its subtype proof at `:31-56` bounds every variable
count by one using `degrees_prod_le`, `degrees_sub_le`, and the count of the
sum of singleton multisets.  This also covers `m = 0` because all claims remain
quantified over `Fin 0` and the empty product is one.

The Boolean evaluation proof at `:75-106` exhausts the two values of `ZMod 2`
and evaluates at the canonical algebra-map embedding.  The linear map at
`:62-73` is the finite indicator sum.  The arbitrary-field-point evaluation at
`:108-113`, Boolean interpolation at `:115-121`, and injectivity derived from
interpolation at `:123-129` have the paper's quantifier order and domains.

| Integrity item | Paper | Lean candidate | Verdict |
| --- | --- | --- | --- |
| Assumptions/domains | `m`, Boolean coordinate `y`, field point `x`, and field-valued data `a` | `k m : Nat`, `BooleanPoint m`, `FieldPoint k m = Fin m -> GaloisField 2 k`, and Boolean-indexed data; no `FieldData` | exact in the frozen F01 concrete-field boundary |
| Indicator | Product of `x_i` or `1-x_i` according to Boolean `y_i` | The same `MvPolynomial` product, proved individually degree at most one | exact |
| Evaluation/linearity | `g_a(x) = sum_y a_y ind_{m,y}(x)` and linearity | Same equation for arbitrary `FieldPoint`; `lowDegreeEncode` is a `LinearMap` | exact |
| Boolean evaluation | `g_a(y) = a_y` | Same after `booleanPointToField`; indicator is Kronecker on Boolean points | exact |
| Injectivity | Consequence of Boolean interpolation | Proved directly by evaluating equal encodings at every Boolean point | exact |

No downstream Lean consumer exists at this head.  The direct imports are
exactly `Mathlib.RingTheory.MvPolynomial.Basic` and
`MIPStarRE.QPBT.Basic.Field`; there is no LDT parameter import, `FieldData`
argument, generic assumptions package, or obligation helper.  The imported
`Field.lean` retains the separately tracked G16 `sorry`, but `#print axioms`
for all five definitions and all four proof theorems reported only
`propext`, `Classical.choice`, and `Quot.sound`, never `sorryAx`.

## Immutable candidate authentication

- Formal base and sole parent:
  `358cd108db045d13f4e0095a2948dd4037be2b54`.
- Candidate head:
  `8467454fefefdbac7478a2df8f8c1e2d9c25fcf5`.
- Candidate tree:
  `50fec3a3a7611f63aacff2f15568812e123ca29d`.
- Base tree: `49177ed572a18951d9bcccfcc079bd2ed1728609`.
- Exact diff: one added path,
  `MIPStarRE/QPBT/Basic/Polynomial.lean`, mode `100644`, blob
  `6bf62ea13a192aa08065512275b2bbaa180963e6`, 4,812 bytes.
- File SHA-256:
  `cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c`.
- Manifest SHA-256 over the newline-terminated record
  `MIPStarRE/QPBT/Basic/Polynomial.lean cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c`:
  `0e7fd38a46b63c7ee660fa14fb828e19331233b0c983a687b1a38d0a2ceb3725`.
- Untrusted writer report independently hashed to the packet value
  `2bc560658677218f5c4f040246a145b75d4a0a231d9338bedf1c4d4354eb604b`.
- Detached review worktree was clean before and after review; `git diff
  --check` passed.

## Validation evidence

All commands below were read-only.  Fast authentication/check commands each
completed in less than 0.01 seconds unless otherwise stated.

| Command (working directory where material) | Result | Observed duration |
| --- | --- | --- |
| `git rev-parse HEAD 'HEAD^{tree}' HEAD^` in `/tmp/qpbt-036-review-a02` | exact head/tree/parent above | `<0.01s` |
| `git diff --name-status 358cd108db045d13f4e0095a2948dd4037be2b54 8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` | only the authenticated added path | `<0.01s` |
| `sha256sum MIPStarRE/QPBT/Basic/Polynomial.lean` | exact packet file hash | `<0.01s` |
| `perl -MDigest::SHA=sha256_hex -e 'print sha256_hex("MIPStarRE/QPBT/Basic/Polynomial.lean cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c\\n"), "\\n"'` | exact packet manifest hash | `<0.01s` |
| `git diff --check 358cd108db045d13f4e0095a2948dd4037be2b54 8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` | passed | `<0.01s` |
| `lake env lean /tmp/qpbt-036-review-a02/MIPStarRE/QPBT/Basic/Polynomial.lean` from the exact-candidate private validation environment | passed; five non-failing redundant-`simp` linter warnings | `3.21s` |
| `lake env lean --stdin` with the module import and `#check` for all twelve F02 declarations | all elaborated signatures match the frozen manifest | `<2.8s` interactive wall |
| `lake env lean --stdin` with `#print axioms` for all candidate definitions/theorems | only standard Lean axioms; no `sorryAx` | two runs, each `<2.8s` interactive wall |
| `rg -n --pcre2 '\\b(sorry|admit|axiom|constant)\\b|FieldData|Hypotheses|Assumptions|_ofObligations' MIPStarRE/QPBT/Basic/Polynomial.lean` | expected exit 1, no matches | `<0.01s` |
| `python3 -B blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | `OK: 54 nodes, 12 chapters, acyclic graph, deterministic outputs` | `<0.01s` command time |
| `python3 -B scripts/reference_source.py --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3 verify` | verified 39 files and 646 labels; inventory `04548808...124f4` | `<0.01s` command time |
| `git status --short --branch` | detached and clean | `<0.01s` |

The review worktree intentionally has no `.lake` tree.  The formal-base hot
cache key `7bf4eb520a01b2c3ff49444d797e5ddd458b1136c9a3a78a9e27cfa34dc53d12`
was present and its `READY` content matched the manifest SHA-256
`bda16f9f737e88cad4c839914783eb446af5bc3be07152193861b504b81bbba3`,
but it was not seeded because the immutable packet permits writing only this
report.  The scoped Lean command read the existing implementer-private
environment while compiling the byte-identical review-worktree source; both
copies hashed to the candidate file hash.  No `lake`, `lean`, warm, or seed
process was active afterward.  No canonical warm/publish/seed was attempted,
and lock wait was not applicable.

Target and full `lake build` were not rerun: doing so would require seeding or
writing a `.lake/build` in the review worktree, contrary to the read-only
packet.  The writer report's target/full-build claims remain untrusted evidence;
the independent scoped kernel check, explicit declaration/axiom audit, and
blueprint/source checks are the reviewer-observed gates.

## Residual risk and metrics

Residual risk is limited to integration: no downstream module consumes this
new module at the candidate head, and this read-only review did not repeat the
target or aggregate build.  The five linter warnings are redundant tactic
arguments only and do not affect elaboration, source fidelity, or API shape.

- Reviewer: `/root/i036_reviewer_a02_polynomial`; topology
  `root -> i036_reviewer_a02_polynomial`; nested agents: `0`.
- Compile attempts: scoped source typecheck `1`; read-only Lean declaration/
  axiom audit sessions `3`; target builds `0`; full builds `0`.
- Findings: `0`; retries: `0`; incidents: `0`; protocol changes: `0`.
- Cache operations: warm `0`, seed `0`, publish `0`; network/GitHub/credential
  operations: `0`.
- Exposed token usage: `null` (collaboration backend does not expose per-agent
  token usage; no estimate made).
- Session elapsed: `null` (the reviewer dispatch timestamp is not exposed in
  this session; individual command durations are recorded above; no estimate
  made).
- Protocol revision evidence: `/home/drx/MIPStarRE-auto/AGENTS.md` SHA-256
  `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c`.
- Repository/worktree/Git/state/cache/source edits: `0`; the sole write is this
  out-of-tree report.  Its SHA-256 is supplied out of band.
