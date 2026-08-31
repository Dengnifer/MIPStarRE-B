# LPR-014 immutable review (a07)

## Verdict

**APPROVE.** Findings: **0**.

Reviewed exact base `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe` through exact
head `9c9b49548fabdd6b01916787d7dc17a4bca36513`, tree
`a7409faf8cbd888e3f04d114332f202ea1436d11`, with the base as the head's sole
parent. The worktree was clean before and after review. The diff contains exactly
the three registered modified paths and no rename, addition, deletion, or extra
path.

## Findings and integrity review

No blocker, high, medium, or low finding.

The production change preserves full-tree archive inspection, materialization,
`archive_tree_sha`, and Gitlink-reconstructed `tree_sha`; it additionally rejects
an authenticated archive member at exact `.lake/build` before publication. Only
post-build `verify` uses `compute_source_tree_sha`, and its fixed literal Git index
removal is exactly root-relative `.lake/build`. All siblings, nested lookalikes,
source/config paths, contents, executable modes, symlink targets, and pinned
`160000` Gitlinks remain in the tree identity.

The projected boundary requires real `.lake` and `.lake/build` directories and
rejects symlink, special, and multiply-linked descendants. I found no obvious
path-normalization, traversal, type, or Gitlink bypass. Representative Lake files,
including mode `0600` regular outputs, are accepted. The existing private-staging
concurrency assumption and non-descriptor-bound package walk remain unchanged and
are outside this bounded repair.

Hot-cache order remains materialize, verify, dependency retrieval, build, verify,
then checkout/key/source checks, full root `.lake` inventory, manifest, READY, and
publication. Source drift still produces no READY snapshot. The inventory and
deep seed verification still bind generated package artifacts excluded from the
source projection.

A04's immutable binding rationale was inspected only as provenance, not treated
as approval. A03 is correct that no protocol/recipe change is needed: the exact
source/generated authority split already exists, and the changed materializer is
already a cache identity input.

A05 evidence disposition: its statement that path-package HEAD resolution fails
is imprecise because Git can resolve the enclosing detached project's HEAD.
Nevertheless its no-blocker conclusion remains correct: that HEAD is not the
pinned dependency revision, the resulting Reservoir request fails, installed
curl 7.81 `-f -o` leaves no output on HTTP 404, and Lake writes the trace only
after a successful download. Thus legacy Git-package `build.barrel` files do not
establish a governed path-override incompatibility.

## Independent validation

All seven required acceptance commands passed once on the immutable head:

- materializer focused suite: 28/28, 53.644 s (real 53.92 s)
- hot-cache focused suite: 46/46, 10.536 s (real 10.70 s)
- full serial discovery: 306/306, 79.341 s (real 79.64 s)
- `scripts/check_workflow.py`: embedded 306/306 plus valid state, 80.439 s
  (real 80.62 s)
- compileall: pass, real 0.04 s, with bytecode redirected to `/tmp`
- workflow validate: pass, real 0.10 s; 25 issues, 13 PRs, 0 planned,
  279 issued sessions, 7 stages
- SHA-bound `git diff --check`: pass

Changed-file SHA-256 values:

```text
3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243  scripts/materialize_lake_packages.py
235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe  tests/test_hot_main_cache.py
d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d  tests/test_lake_package_materialization.py
```

Evidence report SHA-256 values:

```text
922943b7ac0866f8aa96e7eae9a8048c07d2eecd0ae774428093cd7dedf42b63  A15
263275da4d0b2312619bd1fec81b92d50993556202c219abc3ad535fd0302b9c  A16
538c83d046b4377c92de8322628df7e61e60569f9c8a3cddf07c8f0f7a632d67  A17
2997a94dd93733bbd699393828e619bdd29366decb6a4c9c7c785be5eef6ebdc  A02
caad36e3d544878e52733100b5f66e1dcc87ad25800f3b02dee8a26e41ef4917  A03
68380edb4d53066c533c617150b6849650736588d30366c772edaf10279bb072  A04
771bdbc6b3a03de0a6ed75831dbfaaead42b8bb41bcbd588651ba4355f99564e  A05
```

## Residual risk and metrics

No governed Lake build or warm was permitted in review. The required singleton
post-integration authenticated warm, status-ready check, and deep inventory check
remain the definitive operational acceptance gate.

Session `i024-reviewer-a07-pr014-immutable`; start
`2026-08-31T16:33:06.353139Z`; evidence cutoff
`2026-08-31T16:49:57.685944556Z`; elapsed `1011.333` seconds. One reviewer,
zero subagents, seven acceptance command invocations, one Python compile attempt,
zero Lean/Lake builds, warm, seed, network, Git write, canonical-state, runtime,
or cache actions. Token usage: JSON `null`; unavailable because the collaboration
backend exposes no per-session token counter. Report SHA-256 is supplied out of
band after finalization because embedding it would change the digest.
