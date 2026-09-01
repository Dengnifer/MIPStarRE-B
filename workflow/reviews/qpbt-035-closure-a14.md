# QPBT-035 closure verification (A14)

## Findings

No closure findings. LPR-023 is recorded as `merged`, QPBT-035 is recorded as
`done`, and the guarded integration, immutable review, path lease, source
provenance, and validation evidence are internally consistent.

## Verified identities

| Item | Value |
| --- | --- |
| Approved candidate | `9cd85aaf809b4cfce64f7159ce3f92929b388270` |
| Candidate tree | `29c2275a5770332d07d0080e5389f917c36b9074` |
| Canonical integration | `14b1363c9de8e7cd16c7c545333fcc8f7631a65c` |
| Integration tree | `50677d510bcdcfd4c066a12440803aa8627d5d6e` |
| Ordered integration parents | `3bb7d1e151cba5c78ac32d698bb1b764347b5fd0`, `9cd85aaf809b4cfce64f7159ce3f92929b388270` |
| PR integration SHA | `14b1363c9de8e7cd16c7c545333fcc8f7631a65c` |
| PR merged at | `2026-09-01T21:46:45.404147Z` |

The integration commit is present locally and has exactly the expected
two-parent topology. The 16-path name manifest is
`f46174ba7e1e9f5144399466edb4671f10320711db66c53dab33f217ad63eb80`; the
selected `git ls-tree -r` manifest is
`4dc09f6b5d9279e26ff5fd5dee289e26e858f5cfe93d6430ffa03392c0631da3`. Both
manifests were independently recomputed and match at the candidate and
integration trees. The base-to-integration diff contains exactly those 16
paths and no paths outside the lease.

## Acceptance gates

1. QPBT-033 findings 1-3, 5, and 7 are dispositioned in the A04/A07/A12
   repair chain; the final A06 review confirms the eight source-contract
   repairs and retains documented paper gaps.
2. The callable-contract and signature evidence is recorded in the A02/A04,
   A06, A07, A08, and QPBT-048 reports, with direct ownership/import boundaries
   and statement-integrity tables.
3. The integration check records 54 nodes and 12 chapters, deterministic
   generated output, exact F06A/F04A/F07/F07A ownership, and no public bridge
   assumptions.
4. The integration check records 32/32 blueprint tests, default and pinned
   checks, 39-file/646-label source verification, two byte-idempotent writes,
   compileall, workflow validation, checker validation, and diff hygiene.
5. Independent immutable review `review-qpbt-048-pr023-a06-source-fidelity`
   approved candidate `9cd85aa...` before the guarded integration; its report
   SHA-256 is
   `bd3ac5acd186b311da4c03e7feb00a8c58decf0aa550b2ec016ec1589041caa2`.

## Immutable report authentication

The cited report files were read and SHA-256 authenticated:

| Report | SHA-256 |
| --- | --- |
| `qpbt-033-q014-split-a01.md` | `5b6e073865225ef6a8c70a78ce3ad43e2a41d26c1d19b42534e7ef01eb03f55c` |
| `qpbt-035-pr023-review-a03.md` | `a1ed48ff7a642c8811f56d1aa77caec32e3cf1608a33dd474fffb16b367e4caf` |
| `qpbt-035-q014-contract-a04.md` | `a55e7789d6a899b31e6fc8625dfb6116c9430884fb2ce83fc6e1182bb2d3225e` |
| `qpbt-035-detype-source-a05.md` | `de9c4c87820f76c8162f7d2f06bbcd0a66a6ed14cc8d57ed2c6d1414bccd81fb` |
| `qpbt-035-directsum-api-a06.md` | `2bd9b52a679ba2bc155a28ea6b6f352375f0d5a1ee2f3db065739eba45ab24e6` |
| `qpbt-035-q014-contract-a07.md` | `f98f21f7a9f355ca2f2af4e8ef20a3390f995430d045427b79b1c1a7ed93e1e8` |
| `qpbt-035-game-semantics-api-a08.md` | `f37ab823449c85b078330f3912b4ec8eedfc67b8c9ffedb1d1b261434ccc4b27` |
| `qpbt-035-contract-review-repair-a12.md` | `df93700d6879e8c67649b5b25b641fe2a498c963eb2d7e77f504f024b8bb53b0` |
| `qpbt-035-guarded-integration-a13.md` | `a5f16c8e10e69b3a0fe61034e581a41e69a59803e84c624ceb7d93f5b44e2db9` |
| `qpbt-048-executable-cl-contract-a01.md` | `bb1f714998e774f95d25327efe4285adc2e6817eb4c66e6b2dea8ba3f89198aa` |
| `qpbt-048-generated-sync-a03.md` | `8d95d622e13479d1f1f42b0532db6657e6e5437dbb2e7bf2da65c73ca0647c59` |
| `qpbt-048-source-fidelity-repair-a04.md` | `aa5681300a77f661fd467dfa6fe1e9bde5b0ea4ed6fe79800d80f01e68eda013` |
| `qpbt-048-source-fidelity-review-a06.md` | `bd3ac5acd186b311da4c03e7feb00a8c58decf0aa550b2ec016ec1589041caa2` |

## Accounting

- Stable session: `i035-closure-a14` (external thread: `/root/i035_closure_bootstrap`).
- Topology: root coordinator -> closure verifier; nested agents: 0.
- Token usage: `null` (collaboration backend does not expose per-agent token telemetry); no estimate made.
- Compile/build attempts: 0; network, GitHub, endpoint, and credential actions: 0.
- Repository edits: 0. Only this isolated closure report was created.
- Actions: 0 code changes, 0 new issues, 0 reviewer findings, 0 retries, 0 incidents.
- Timing quality: wall-clock session timing is not exposed by the collaboration backend; report generation completed in the current bounded run.

