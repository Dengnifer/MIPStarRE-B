# QPBT-055 CL structural proof and paper-gap record (A01)

## Result

The pinned paper's level-raising argument at
`conditionally-linear.tex:124-129` is valid but terse. Its displayed full-head,
zero-tail data prove precisely that the unique zero-level function is also a
one-level function. Structural induction then promotes every recursive tail of
an existing certificate, establishing that each level contains the preceding
level. The initial candidate incorrectly read the displayed base witness as a
claimed direct wrapper for an arbitrary function; independent review rejected
that reading, so the proposed `G20` paper gap has been removed.

Lean may implement the same inclusion more directly by prepending an empty
head register with the zero head map, retaining the full register in the
recursive tail, and reusing the original certified function. This is an
equivalent implementation strategy, not a paper repair. It changes no public
F06 declaration, hypothesis, conclusion, import, or signature-manifest byte.

The same pinned source has two downsize-proof defects. At lines 425-428 and
453-455 it indexes an original-field linear map by the downsized prefix even
though that map's source-domain index is the original prefix. The type-correct
reading pulls the prefix back through the coordinate equivalence before
selecting and conjugating the source map. The lemma permits `ell = 0`, but its
proof begins at `ell = 1`; the omitted case is the existing unique zero
certificate. These are recorded together as `G21` because they affect one
proof construction and require no API change.

The independent read-only discovery report is
`/tmp/i038-scout-a03-f06.md`, SHA-256
`da9b7b1d51ae11d9b17efc7caf2ec5adf553a9e6e2bc334e3c44f4383d5972b3`.
The independent downsize report is `/tmp/i038-scout-a03-downsize.md`,
SHA-256
`8c0b1f19c39f05ae99281873d80990ad5212b4210e793676f39188c73a4e11f3`.
It separately preserves the already-known `V x V` seed typo at source line
377; QPBT-055 does not merge or rewrite that finding.

## Changes

- Removed the review-rejected provisional `G20` record and documented the
  paper's valid base-case-plus-structural-induction argument in `F06-CL`.
- Retained reciprocal paper-gap record `G21` for the downsize prefix and omitted
  zero-level case.
- Linked `F06-CL` only to `G21` and documented the level-raising implementation
  alternative and downsize proof repairs in
  `blueprint/metadata/nodes.json`.
- Regenerated only the expected graph, chapter-02, and gap-table outputs.
- Added canonical issue `QPBT-055` as a Stage 04A preflight issue.

The F06 marker remains
`workflow/reviews/qpbt-035-q014-contract-a04.md#F06-A04-SIGNATURES`,
SHA-256
`120d85e82d04ef226509ff6ff2b0f70776b65db537ba76a74c8307312b203461`.

## Statement integrity

| Field | Paper | Lean disposition |
| --- | --- | --- |
| Assumptions | An existing lower-level CL function and the recursive certificate definition | The same certified function and its existing full register |
| Construction | Prove zero-level to one-level inclusion, then structurally promote recursive tails | Direct equivalent wrapper: empty zero head and the original certified function on the full recursive tail |
| Claimed result | Every lower-level function is also a function at the next level | The realized function is definitionally preserved while its certificate level increases |
| Public effect | No new public theorem is stated | No F06 signature changes; internal implementation choice only |
| Verdict | Valid base case plus structural induction | Exact implementation alternative; no paper gap |

For downsize, the paper and Lean hypotheses remain the same. Lean uses the
type-correct original prefix obtained through the inverse coordinate map and
includes the source-permitted zero-level case. The map, sampler pushforward,
and every frozen public signature remain unchanged; this is documented
mismatch `G21`.

## Review disposition

The first immutable review authenticated all 16 manifest entries at candidate
`98c0fe23dee3ee1d657c4e5612708e875f6c405a` and requested changes on one high
source-fidelity finding: provisional G20 misclassified the paper's valid base
case as an incorrect construction. The exact review is
`workflow/reviews/qpbt-055-review-a01.md`, SHA-256
`ca42e1aff706edc80e168bbcc0b555d42820375db39d7a405b94a603c22bda8f`.
This revision accepts that finding, removes G20 and its reciprocal/generated
links, and retains G21 unchanged. A fresh immutable review of the repaired head
is required before issue closure.

## Authentication

- Candidate base: `ead85cbb7ad4a51147686d732e7c04824ce074d4`
- Candidate base tree: `ff6d8d2f5cdf4ceb0cfd95a43982de0dbbe94644`
- Pinned `conditionally-linear.tex` SHA-256:
  `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638`
- `blueprint/metadata/gaps.json` SHA-256 before commit:
  `304a7b1b83ceb2c2f8017131734067d6bda5ef0660b97ae4404c7a83ac38edf6`
- `blueprint/metadata/nodes.json` SHA-256 before commit:
  `0e22725b9f997e48d7d7dcaf7caf28f324f332c1875ac9ecf37bdaec23b233a6`
- `blueprint/generated/graph.json` SHA-256 before commit:
  `d547f64001a90a25bb667a3707e7b6e29863a53d6da4f658e803313caaa5e370`
- `blueprint/src/generated/chapter-02-entries.tex` SHA-256 before commit:
  `fd5f032e3e75c41f0baf7ebd774f87a8528e11bda305c2bf94bd61568869625f`
- `blueprint/src/generated/gaps.tex` SHA-256 before commit:
  `cb6ecee67cb8cc0927b35acd2ded429c2a4e2819a1f12ba4417586232b4c7563`

The final commit, tree, path manifest, and this report's final hash are
recorded after commit to avoid a self-reference.

## Validation

| Command | Result |
| --- | --- |
| `python3 blueprint/check.py --write` | pass twice for the review repair; 54 nodes, 12 chapters; second run byte-idempotent |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | repair pass, 34/34 in 2.813 seconds |
| `python3 blueprint/check.py --check --source-root references/2001.04383v3` | pass, 54 nodes and 12 chapters |
| `python3 scripts/reference_source.py verify --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3 --runtime-root /home/drx/MIPStarRE-auto/.workflow-runtime/reference-source` | pass, 39 files and 646 labels |
| `python3 scripts/workflow.py validate` | pass, 59 issues, 32 PRs, 463 issued sessions, 7 stages |
| `python3 scripts/check_workflow.py --root . --skip-tests` | pass |
| `git diff --check` | pass |

Before the initial candidate, one read-only invocation used the nonexistent path
`scripts/verify_reference_snapshot.py`; it failed before doing work. The
canonical `reference_source.py verify` command above then passed. The review
repair added two byte-idempotence generation runs and one parallel pass each of
the unit, default, pinned-source, reference, workflow, aggregate-workflow, and
diff-hygiene checks. It used zero Lean/Lake/build/cache/network/GitHub/
credential actions. Root token usage is `null` because the backend does not
expose per-operation counts.

Repair evidence cutoff: `2026-09-02T21:22:39Z`.
