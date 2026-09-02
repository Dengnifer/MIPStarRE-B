# QPBT-054 executable exponent gap linkage (A07)

Session: `i054-orchestrator-a07-gap-linkage`  
Role: sole QPBT-054 gap-linkage writer  
Base: `3a248eac86fa8b782134a4fae88169f514a0168d`  
Issue / local PR: `QPBT-054` / `LPR-031`

## Verdict and finding disposition

`F-LPR031-A06-001` is resolved. The executable-boundary problem already
described by `F06A-EXECUTABLE-CL` is now recorded as numbered paper gap `G19`,
and the node and gap point to each other. The gap is bound to `QPBT-054`, names
the exact effect on `TIME_S(n)`, and explicitly rejects a fabricated theorem
that would turn an arbitrary admissible field-size family into executable
code.

No F06A signature, implementation-contract marker, or Lean declaration was
changed. The frozen signature SHA-256 remains
`cfe433e36d0670c344b29ab5107557842e7d4fc8358fba2713b8ff2ee107a3a1`.

## Source evidence

The authenticated source was read from
`/home/drx/MIPStarRE-auto/references/2001.04383v3`; no network or source
materialization was used.

| Source | SHA-256 | Clauses recorded by G19 |
| --- | --- | --- |
| `sections/dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` | arbitrary admissible `q(n)` at generated lines 566-568 / original 2728-2730; sampler `TIME_S(n)` at 599-600 / 2761-2762; one downsized machine using `log q(n)` and its stated runtime at 632-674,709-710 / 2794-2836,2871-2872 |
| `sections/dependencies/finite-fields.tex` | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` | admissibility is only the pointwise equation `q = 2^k` for odd `k` at generated lines 245-247 / original 1561-1563; the efficient basis algorithm receives `k` as its input at 283-307 / 1599-1623 |

These clauses permit an arbitrary admissible field-size function but require a
single downsized Turing machine to form widths depending on `log q(n)`. They do
not provide that machine with an algorithm computing the exponent from `n`.
Consequently, `G19` requires concrete intrinsic `FieldExponentProgram` data and
expands the faithful executable `TIME_S(n)` boundary to charge that execution
alongside the valid sampler queries.

## Statement integrity

| Field | Result |
| --- | --- |
| Paper assumptions | An arbitrary pointwise admissible field-size function `q(n)`, a dimension function `s(n)`, and one executable conditionally-linear sampler. |
| Lean assumptions | The existing faithful executable boundary additionally carries a concrete intrinsic `FieldExponentProgram` computing the exponent from positive `n`; it is data of the executable sampler, not a theorem or caller-supplied proof obligation. |
| Paper conclusion | One downsized sampler has dimension `s(n) log q(n)` and runtime `O(TIME_S(n) log q(n))`. |
| Lean conclusion | The same executable-downsize contract, with `TIME_S(n)` defined to charge both valid sampler-query executions and the intrinsic exponent execution needed to determine `log q(n)`. |
| Verdict | `faithful boundary`: the missing executable input is made explicit and charged; no arbitrary family-to-machine theorem is asserted, and the mathematical admissible-family statements remain unchanged. |

## Changes and regression

- Added `G19` to `blueprint/metadata/gaps.json` with reciprocal affected node
  `F06A-EXECUTABLE-CL`, issue `QPBT-054`, exact source anchors, disposition,
  and public effect.
- Added `G19` to the F06A node's `gap_ids`.
- Added one focused test that freezes reciprocal linkage, issue identity, the
  arbitrary-family/single-machine problem, the `FieldExponentProgram`
  disposition, and the `TIME_S` public effect. It also checks both broken-link
  directions are rejected by the validator.
- Regenerated only deterministic consumers. `graph.dot` remained byte-equal to
  the base (`ee3402d1e1ef89a01277223087fd68d413060cfe`).

## Validation

| Gate | Result | Observed time |
| --- | --- | --- |
| Focused G19 regression | PASS, 1/1 | unittest 0.063 s; real 0.13 s |
| Full blueprint test module | PASS, 34/34 (33 existing plus 1 new) | unittest 2.660 s; real 2.74 s |
| `blueprint/check.py --write` pass 1, pinned source | PASS, 54 nodes / 12 chapters | real 0.13 s |
| `blueprint/check.py --write` pass 2, pinned source | PASS, 54 nodes / 12 chapters | real 0.13 s |
| Byte-idempotence after both writes | PASS, all four owned generated outputs have identical hashes | immediate |
| Default `blueprint/check.py --check` | PASS, 54 nodes / 12 chapters | real 0.12 s |
| Pinned-source `blueprint/check.py --check` | PASS, 54 nodes / 12 chapters | real 0.13 s |
| `reference_source.py verify` | PASS, 39 files / 646 labels | real 0.14 s |
| `workflow.py validate` | PASS | real 0.16 s |
| `check_workflow.py --skip-tests` | PASS | real 0.16 s |
| `py_compile blueprint/tests/test_check.py` | PASS | real 0.04 s |
| `git diff --check` | PASS | real 0.01 s |

Generated-output SHA-256 values after each of the two write passes were
identical:

| Path | SHA-256 |
| --- | --- |
| `blueprint/generated/graph.json` | `8a8a944a2ac001ec02ca52a00b65ba8bf06d2ea175bbf2e95ac14e809385c574` |
| `blueprint/generated/graph.dot` | `889fb76e7a18029485ca0db7738629dd2d03eb53e123236e5b5c9772f65650ee` |
| `blueprint/src/generated/chapter-02-entries.tex` | `faeee962cfe0134056800384ae9112762e3c82797b3a786cafea69f75bf972b6` |
| `blueprint/src/generated/gaps.tex` | `e4fb2ca10890e6fab48ad6013e5eaf5540037d9aa507af72a46af0d532cb9b9a` |

One preliminary generator invocation used the sections directory instead of
the documented pin root and was rejected before writing because
`split-manifest.json` was absent there (real 0.12 s). The corrected two write
passes above succeeded and were byte-idempotent.

## Accounting

- Manual patch operations: 4 (metadata/test change, this report, the
  source-anchor refinement requested before freeze, and final report metrics).
- Generator attempts: 5 (4 passed across two idempotence pairs; 1
  path-configuration rejection before
  output generation).
- Test invocations: 4 (2 focused and 2 full), all passed.
- Lean invocations, Lake invocations, target builds, full builds, cache warms,
  cache seeds, cache materializations, and shared build-output actions: 0.
- Network calls, endpoint calls, GitHub operations, credential reads, source
  materializations, canonical state writes, canonical metrics writes, protocol
  changes, and nested agents: 0.
- New issues or gaps beyond required `G19`: 0.
- Token usage: `null`; the collaboration backend exposes no per-agent token
  count.
