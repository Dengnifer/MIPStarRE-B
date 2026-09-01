# QPBT-004 independent foundation closure review (A38)

## Findings

No findings.

## Verdict

**Approve QPBT-004 for closure.** All three written acceptance gates at
`workflow/state/issues.json:183-186` pass. The A37 conclusion at
`workflow/reviews/qpbt-004-foundation-closure-a37.md:5-21` is supported by the
immutable Git objects, committed pins and provenance, independently approved
LPR-005 evidence, and raw exact-key cache publication. No tracked project-byte
change was required by a written gate, a concrete safety issue, or the direct
acceptance-only rule.

| Written gate | Independent check | Verdict |
|---|---|---|
| Lean and Mathlib pins are recorded | `lean-toolchain:1` fixes Lean 4.32.0; `lake-manifest.json:5` fixes Mathlib `81a5d257c8e410db227a6665ed08f64fea08e997`; `references/mipstarre-upstream.json:40-43` agrees with both | pass |
| Reusable imported foundations have provenance | `references/mipstarre-upstream.json:3-38` binds source commit, archive, rights boundary, and 337-file inventory; `:45-100` records nine unique path/hash foundation entries; all ten available input archives match their committed SHA-256 pins | pass |
| Empty project build and local cache gate pass | Raw key `4a5d9cf4d7de3d89c9bf7805d59f5c1739b39fd56d66b19b2454941da8873807` binds base `942f9438b991ece8942815db16c019b92d9cdd8e`, recipe 5, the exact pins, one elected build, READY/manifest equality, successful 8,992-job log, a private seed with zero builds, and no matching failure envelope | pass |

QPBT-003 and QPBT-024 are already `done`; the dependency precondition for
closing QPBT-004 is therefore satisfied as well.

## Immutable authentication

The review target is a clean detached
`1c3742b02c08883572d2baf00e96fe8b019b6b6e`, tree
`1e837d795595922c65916db84e4db78af61c5647`, with sole parent
`fc3730f2abd97b272362b6ef9b752b4825d84e8c`, parent tree
`24907947199583eab2c56c66b8cb6f7d7bc2d353`. Its diff adds exactly one path,
`workflow/reviews/qpbt-004-foundation-closure-a37.md`, and passes
`git diff --check`.

The imported report has SHA-256
`8a4d94a2cf257ab36547542cae60c3019d5fe410e37cf6b1a84b293dff121fe2`
and Git blob `9b285442e52dd57c64087f8e93db1e9de5a41e36`. It is byte-identical to the
same path in candidate commit
`0f98de6681da3e19b60d18619a6eda8fa8f61c54`. Thirteen of thirteen explicit
target/candidate identity, scope, cleanliness, hash, blob, and byte-equality
assertions passed.

LPR-005 is recorded merged at `workflow/state/prs.json:1383-1392`; its fresh
independent A35 review approved exact head `4de4524...` with no findings at
`:1515-1523`, and both earlier high findings are resolved at `:1528-1553`.
Integration `687e182...` is an ancestor of the A37 base. The known approved-head
versus integration difference contains exactly eight later workflow,
orchestration, test, and report paths; none is one of the seven project/pin
paths. All seven project/pin paths are byte-identical from integration through
the A37 base and their SHA-256 values match A37 lines 46-52. Thus the historical
provenance wrinkle does not invalidate any written QPBT-004 gate.

## Raw cache and provenance checks

The raw publication independently matches A37 lines 68-111:

- `manifest.json` SHA-256 and READY content:
  `86d9aa6c53a0ffa468f55a7a285b24f2fe21137150c7b7c0b1e2dcb1e55e28bb`;
  READY-file SHA-256:
  `2307e22ff78ec0489504b8735b2d6c9be89b7c91e04477bed86c092285465ae1`.
- Build-log SHA-256:
  `297a3a4486e153298546691b674bf66c3de73fe73855eea2147ff0b098d2612c`;
  its terminal records are `Build completed successfully (8992 jobs).` and
  package verification status `verified`.
- Warm metric raw-line SHA-256:
  `464809b136decd0f1a41c8a29524f8094d5be198a9154b71f52b54f81279866c`.
  It records `built` / `hit`, one miss, one build, zero retries, zero lock wait,
  `884.495783s` build time, and `1039.829438s` elapsed.
- QPBT-004 seed metric raw-line SHA-256:
  `3f6f4407790e9aca63d588f282efcbfdbc62fbd6756491e7da6ab6451caf5fb8`.
  It records one cache hit, zero builds, 124,925 private regular-file copies,
  three symlinks, 10,097,592,794 bytes, and `267.003357s` elapsed.
- Manifest artifact inventory is 124,925 files, 4,147 directories, three
  symlinks, 10,097,592,794 bytes, digest
  `ba096053b9ceb4232b646dd896d5ecefac739dbba37c9f78498d4fd820fb1548`.
  No failure envelope exists for this key.

Three of three publication-object hashes, two of two metric-line hashes, the
terminal build record, and the no-failure assertion passed. The MIPStarRE and
Mathlib archive hashes independently match
`656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`
and `c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`.
All eight Lake package archives also match their committed hashes: ten of ten
archive checks passed.

## Historical dispositions

**Pre-copy seed refusal: correctly disposed.** The main-worktree refusal at
`scripts/hot_main_cache.py:2300` is reached by `_eligible_seed_target` before
`seed` computes a destination, acquires locks, creates a staging directory, or
copies at `:2401`. The corrected invocation then produced the authenticated
private seed metric above. Reporting two seed attempts, one pre-copy refusal,
one success, and no cache/project mutation from the refusal is accurate.

**Exact-base stage counters: correctly disposed.** A37 lines 132-145 preserve
the fail-fast exact-base aggregate result instead of calling it a pass. Commit
`743051546a52128cf910157d3e57e42e726ccbad`, an ancestor of current `main`,
updates the root-owned Stage 2/3/4A counters from `108/36/173` to
`110/38/174`; it does not rewrite base `942f943...`. The review target's
read-only `python3 scripts/workflow.py validate` passes with 31 issues, 18 PRs,
zero planned sessions, 358 issued sessions, and seven stages. The superseded
accounting drift is outside all three QPBT-004 gates and does not justify a
project edit.

## Residual risk

Per the registered review boundary, this session did not rerun Lean, Lake, a
build, cache operations, focused tests, package suites, or the aggregate suite.
It therefore relies on the authenticated raw build/publication artifacts and
the earlier independent deep-inventory evidence rather than duplicating those
expensive checks. The raw successful root build includes `MIPStarRE`, which
also corroborates the separately reported direct `MIPStarRE.lean` typecheck.
No closure blocker remains.

## Accounting

- Logical session: `i004-reviewer-a38-foundation-closure`.
- Topology: root coordinator -> one fresh read-only reviewer; child agents `0`;
  depth `1` below root.
- Canonical start: `2026-09-01T08:41:49.314421Z`.
- Evidence cutoff: `2026-09-01T08:47:29.207629200Z`.
- Exactly measured canonical-start-to-cutoff interval: `339.8932082s`.
- Acceptance gates: `3/3` pass; immutable-authentication assertions: `13/13`;
  project/pin byte comparisons: `7/7`; archive hashes: `10/10`; publication
  object hashes: `3/3`; metric-line hashes: `2/2`; workflow validations: `1/1`.
- Lean commands, Lake commands, builds, warm/status/seed actions, test-suite
  runs, cache mutations, network, endpoint, GitHub, credential operations,
  external reviews, Git writes, repository/state/metric edits, and nested-agent
  dispatches by this reviewer: all `0`.
- Authored output: `/tmp/qpbt-004-foundation-review-a38.md` only.
- Token usage: JSON `null`; availability reason: the collaboration backend does
  not expose per-agent token usage. No estimate is made.

The report SHA-256 is supplied out of band because embedding it would change
the report bytes.
