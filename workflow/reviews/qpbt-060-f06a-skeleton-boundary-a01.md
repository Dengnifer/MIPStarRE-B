# QPBT-060 F06A Stage-4A skeleton boundary (A01)

Session: `i060-orchestrator-a01-skeleton-boundary`
Role: sole QPBT-060 writer and orchestrator
Base commit: `838907973f585a3dcb2290178568c47697e4e90d`

## Candidate verdict

The blueprint now records exactly four Stage-4A theorem-body holes:
`fieldDataOfOddExponent`, private F06A `downsizeCompiler_exists`, public F06A
`downsize_time`, and `pauliSoundness`. The F06A implementation contract permits
exactly its two holes. `ExecutableCLSampler.downsize` remains a definition that
must be constructed from the private existence theorem, while
`downsize_dimension`, `downsize_associated`, and `sample_downsize` remain
proof-required at Stage 4A. Proof completion remains an unconditional zero-hole
gate.

The private helper is absent from the frozen 56-name public API. The QPBT-059
marker SHA-256 remains
`368008b7b4ba84ff1dafe842acdb8af7005902a0fe9a376a8f7a690c86ba6b15`;
the exact four-import union, dual-rail packing contract, source anchors,
prerequisites, transitive definitions, target spines, and topological projection
are unchanged.

This is an implementation candidate, not an approval. A fresh read-only reviewer
must inspect the committed diff before QPBT-060 can be approved.

## Source and gap disposition

The controlling paper ranges are
`conditionally-linear.tex:553-712` and `preliminaries.tex:96-143` in the pinned
arXiv:2001.04383v3 source. The former specifies the four sampler queries,
downsized machine, associated maps, dimension, and runtime claim. The latter
requires the linear dual-rail tuple encoding and charges encoding, simulation,
and output writing to total runtime.

The new paper-gap note records `G19` without expanding the public theorem
surface. An arbitrary admissible exponent family is not thereby made
executable. The faithful boundary requires an intrinsic `FieldExponentProgram`
and charges its execution in `TIME_S`; QPBT-061 must prove both the operational
compiler existence theorem and the paper-labelled runtime theorem at Stage 4C.

## Statement integrity

| Declaration | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| `ExecutableCLSampler.downsize_time` | Positive indices, an admissible field-size family, an ell-level six-input sampler, and `ell >= 1` | The frozen faithful F06A boundary: positive-index odd exponent family, canonical field codec, dual-rail six-tape encoding, genuine sampler and exponent executions, and `1 <= ell`; no public obligation premise | The downsized sampler runs in `O(TIME_S(n) log q(n))` | The unchanged global-positive `RuntimeBigO S.downsize.time (fun n => S.time n * Nat.log 2 (Q.fieldSize n))` | faithful boundary |
| private `ExecutableCLSampler.downsizeCompiler_exists` | No separately labelled paper theorem; operational content is implicit in `def:downsize_sampler` and its proof | Internal construction obligations only; no caller-supplied bridge, package, producer, or arbitrary implication | A concrete downsized machine implements the four source query cases | A private existence witness from which the public `downsize` definition is selected | faithful boundary implementation debt |

No paper-labelled signature changed in this patch.

## Fail-closed checks

The checker rejects a missing, substituted, or extra F06A hole; a hole in
`downsize`, `downsize_dimension`, `downsize_associated`, or `sample_downsize`;
and any attempt to add `downsizeCompiler_exists` to the public name list. The
existing exact-contract comparisons continue to reject public-name, import,
signature-marker, semantic-contract, source-anchor, and topology drift.

## Validation and accounting

| Command | Result | Wall time |
| --- | --- | --- |
| `python3 -m py_compile blueprint/check.py blueprint/tests/test_check.py` | pass | `0.06s` |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | pass, 36 tests | `3.10s` final run |
| first `python3 blueprint/check.py --write` | pass, 54 nodes and 12 chapters | `0.13s` |
| second `python3 blueprint/check.py --write` | pass; 16-file generated-output SHA-256 manifests byte-identical | `0.13s` |
| `python3 blueprint/check.py --check` | pass | `0.13s` |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass | `0.14s` |
| `python3 scripts/workflow.py validate` | pass, 62 issues, 34 PRs, 489 issued sessions, 7 stages | `0.19s` |
| exact structured contract/topology/marker scan | pass | `0.07s` |
| `git diff --check` | pass | `0.02s` |

The generated `graph.json` SHA-256 is
`b0a60fd71853ccaaf0ae4e8634a65e2619991e9fb8ce9d02aaeb955aa21c747c`;
the generated chapter-02 entry SHA-256 is
`b626aa2db2612c97c20f60b90841cfed9addecba116de341d562289bd0d71971`.
The complete QPBT-059 report SHA-256 remains
`ae8b065fca3786c301b2468ac49debcb0f39279d9987028a89678eea5658b290`;
the historical QPBT-054 report remains
`22db8cee76ff159412ced50941eb61d25bf94b7e4570147bd347d87cd0018ba7`.

The final report hash, staged patch hash, commit, tree, and parent identities are
returned out of band after commit to avoid self-reference.

This session performed zero Lean elaboration, Lake, build, hot-main-cache,
network, endpoint, GitHub, credential, canonical workflow-state, or
research-metrics actions and spawned zero child agents. Lean compile attempts
and cache events are both zero. Token usage is `null`: the collaboration backend
does not expose a per-session token count.

One local pre-generation edit check caught an overly broad JSON patch match;
the unintended F06/F02 allowlist edits were corrected before generation and
validation. No incident remains in the candidate diff.
