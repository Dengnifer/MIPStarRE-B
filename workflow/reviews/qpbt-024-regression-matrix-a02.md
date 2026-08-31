# QPBT-024 source-projection security and regression matrix (a02)

## Verdict

QPBT-024 should change only the package materializer's **post-build** source-tree
calculation.  The authenticated archive must still be inspected and hashed as a
complete tree before Lake runs.  During `verify`, and only after validating the
generated boundary, both the raw archive-tree comparison and the Gitlink-
reconstructed comparison may project out exactly the package-root path
`.lake/build` and its descendants.

A16's recommendation to exclude the complete package-root `.lake` subtree is
too broad and is superseded by QPBT-024's explicit acceptance gate.  It would
make `.lake/not-build`, package metadata placed directly under `.lake`, and any
future authenticated source there invisible to the source verifier.  A15's
narrow `.lake/build` boundary matches the issue text and is the safe basis.

The current base has the expected defect: `compute_tree_sha` force-stages the
entire package (`scripts/materialize_lake_packages.py:961-985`), and `verify`
uses it unchanged after Lake (`:1862-1891`).  This correctly catches all drift
today, but also includes the legitimate 169 `plausible/.lake/build/**` files
identified by A15.  No change is needed to hot-cache ordering: the two package
verification calls already surround dependency retrieval and compilation at
`scripts/hot_main_cache.py:2112-2153`, and inventory/publication follows at
`:2167-2205`.

## Exact security invariants

1. **Full archive identity before Lake.** `inspect_archive_bytes`, extraction,
   `archive_tree_sha`, and reconstructed `tree_sha` remain whole-tree checks in
   `_materialize_archive_bytes` (`materialize_lake_packages.py:988-1012`).  The
   projection must not be a default mode of `compute_tree_sha` and must never be
   used by materialization/archive inspection.
2. **No ambiguous authenticated/generated overlap.** Any archive member equal
   to `.lake/build` or beginning `.lake/build/` is rejected structurally before
   publication, even if every archive fact and pinned tree SHA were rebound.
   Merely relying on a pin mismatch is insufficient because a future pin could
   authenticate the ambiguous layout.
3. **Exact root-relative exclusion.** The sole ignored index entry/prefix is
   `.lake/build`.  `.lake`, `.lake/not-build`, `.lake/build-sibling`,
   `.lake/Build`, and `src/.lake/build` remain authenticated.  The implementation
   must use a fixed literal Git path, not a caller-provided pattern, glob,
   `.gitignore`, or `.lake`-wide pathspec.
4. **Validated boundary before projection.** If the generated subtree is
   present, package-root `.lake` and its child `build` must each be real
   directories under no symlink traversal.  A symlink, regular file, FIFO, or
   other object at either boundary is fatal and is not removed from the index.
5. **Excluded descendants are still safe objects.** Walk `.lake/build` without
   following symlinks.  Permit only real directories and single-link regular
   files; reject symlinks, FIFOs, sockets/devices, and regular files whose
   `st_nlink != 1`.  The existing `_scan_tree` (`:1852-1859`) rejects ordinary
   special files but deliberately permits authenticated source symlinks and
   does not reject hardlinks, so it is not by itself sufficient for bytes that
   will be excluded from source identity.
6. **Every non-generated Git identity bit remains bound.** Outside the exact
   subtree, contents, symlink targets, executable-bit changes, additions,
   removals, and renames must still change the computed tree.  As before, Git
   tree identity does not bind directory modes/mtimes or non-executable regular
   permission bits.
7. **Both tree comparisons retain their meaning.** Post-build verification
   computes a projected raw archive tree with no Gitlinks and a projected
   reconstructed tree with all pinned `160000` entries.  Gitlink placeholder
   missing/nonempty checks at `:973-983` remain active; projection must not drop,
   rewrite, or mask a Gitlink outside `.lake/build`.
8. **Override/layout/package checks remain unchanged.** Exact override JSON,
   manifest checks, package iteration, real package roots, bound layout
   incarnation checks, and `_scan_tree` still execute (`:1862-1890`).
9. **The second verifier stays a hard publication gate.** Required order is
   `package-materialize -> package-verify -> deps -> build -> package-verify ->
   source/key checks -> inventory -> READY`.  A post-build source/config change
   must retain the failure envelope and publish no READY snapshot.
10. **Generated output is separated, not trusted as source.** Projection means
    only that `.lake/build/**` is not compared with the upstream source SHA.
    The complete resulting `.lake` remains content-inventoried before READY and
    rechecked during seed.  A successful source projection must not bypass that
    later artifact inventory.

## Bypass matrix

| Unsafe implementation | Security loss | Regression that must fail it |
|---|---|---|
| Exclude all `.lake/**` as suggested in A16 | Authenticated `.lake/not-build` or future package metadata can drift | M4 exact-scope cases |
| Use projection during archive materialization | An archive can ship preexisting build bytes that are silently normalized away | M1 archive-boundary rejection plus unchanged full-tree materialization |
| Exclude `.lake/build` without validating its type | A symlink/file boundary is hidden rather than authenticated or rejected | M5 malformed-boundary cases |
| Keep only `_scan_tree` before exclusion | Symlinks and multiply-linked regular files inside the unauthenticated subtree survive | M6 descendant-object cases |
| Use an ignore file, glob, or unrestricted exclusion list | Siblings/nested lookalikes can fall outside identity accidentally | M4 literal-path cases |
| Remove the subtree before staging but omit reconstructed Gitlink processing | Aesop-style `160000` entries can disappear or become ordinary empty directories | M7 Gitlink projection case |
| Accept build output only by deleting it before verify | Published cache loses the dependency artifacts the warm was intended to preserve | H1 asserts artifact remains in published `.lake` |
| Move/delete/make best-effort the second verify | Build-time mutation under ignored package roots can reach READY, reopening F-LPR005-001 | H2 no-READY drift case and H1 call order |
| Test only a successful generated file | A broad `.lake` ignore and source-drift bypass both pass | M2 must be paired with M3/M4/M5/M6 |

## Minimal regression matrix

The smallest adequate edit surface is the two requested test files.  Existing
tests should be extended rather than replaced.

| ID | File / proposed focused behavior | Required assertion |
|---|---|---|
| M1 | `tests/test_lake_package_materialization.py`: construct an otherwise canonical archive containing `.lake/`, `.lake/build/`, and one file below it | `inspect_archive_bytes`/materialization rejects the generated-source boundary explicitly, before any package publication; rebinding archive size/facts must not turn it into an accepted archive |
| M2 | Materialize, then create representative regular outputs under `plausible/.lake/build/lib/lean/` and `.../ir/`, including one mode `0600` file | `verify` succeeds and the generated files remain present |
| M3 | With the M2 subtree present, independently mutate `src/source.txt`, `lakefile.toml`, and `lake-manifest.json` (rematerializing between cases) | Every case fails with package tree drift |
| M4 | With a valid `.lake/build` present, independently add `.lake/not-build/file`, `.lake/build-sibling/file`, and `src/.lake/build/file` | Every lookalike remains hashed and fails verification; this is the direct guard against A16's overbroad boundary |
| M5 | Independently replace `.lake/build` with a symlink, regular file, and FIFO; also make `.lake` a symlink whose target has `build` | Every malformed boundary fails closed and no external target is traversed |
| M6 | Under a real `.lake/build`, independently create a symlink, FIFO, and a hardlinked regular file | Every excluded-subtree object case is rejected before projection |
| M7 | Extend the existing explicit-Gitlink fixture (`test_lake_package_materialization.py:501-540`) with valid `.lake/build` output and invoke the new post-build projection | The projected tree with the pinned Gitlink equals the pristine reconstructed tree, a changed Gitlink SHA changes it, and a missing/nonempty placeholder still fails |
| H1 | `tests/test_hot_main_cache.py`: extend `test_packages_are_identity_bound_materialized_and_verified_before_lake_steps` (`:598-622`) so the dependency/build callback creates `fixture/.lake/build/...` | Warm returns `built`; calls remain exactly materialize, verify, deps, build, verify; the package artifact survives in the published snapshot |
| H2 | Preserve `test_warm_rejects_post_build_package_drift` (`:624-646`) unchanged or minimally strengthen its READY/failure assertions | Mutation of `fixture/marker` outside `.lake/build` raises the verifier error, leaves `is_ready()` false, and retains one failure envelope |

M2-M6 can share one small fixture helper that rematerializes a pristine package
publication between subcases.  They should exercise the public `verify` path,
not only a helper, except M7 where a direct tree helper is appropriate to
isolate Gitlink semantics.  No broad new test module or hot-cache production
change is justified.

## Implementation constraints exposed by the tests

- Prefer a narrowly named post-build/source-projection helper or a keyword-only
  fixed mode.  Do not expose arbitrary exclusion paths to callers.
- Stage with the current `--all --force` semantics so ignored and untracked
  source drift remains visible, then remove only the fixed literal index prefix,
  or use an equivalently exact structured Git pathspec.  Apply pinned Gitlinks
  afterward without changing their validation.
- The archive-member prohibition belongs in archive inspection, where it cannot
  be bypassed by rebinding output SHAs.  The filesystem boundary/object checks
  belong immediately before the post-build projected tree computation.
- The implementation should report boundary/object errors distinctly from
  ordinary source-tree drift; this makes M1/M5/M6 prove the intended guard
  rather than pass incidentally due to a later SHA mismatch.

## Residual risk and scope

The base verifier already performs pathname checks and a final bound-layout
incarnation assertion, but package source walking/tree construction is not a
descriptor-bound atomic snapshot.  QPBT-024 should not silently claim to solve
arbitrary concurrent filesystem replacement races; the hot builder operates in
a private staging checkout.  The bounded repair must at least avoid adding a
new obvious validation/projection time-of-check bypass.  A larger descriptor-
bound tree-hashing redesign is outside the issue's minimum repair and should be
separately tracked if required.

## Provenance and accounting

- Governed session: `i024-scout-a02-regression-matrix`
- Canonical base/HEAD audited: `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe`
- Issue gate anchor: `workflow/state/issues.json:774-808`, especially
  `:790-796`
- Prior report anchors: A15 `:110-162`; A16 `:111-161`; A17 `:44-86`
- Role/topology: parent
  `/root/i024_orchestrator_a01_source_projection` -> this read-only scout
  `/root/i024_orchestrator_a01_source_projection/i024_scout_a02_regression_matrix`;
  0 subagents; one parent/child edge; this session spawned no agents
- Repository edits: 0; output files: 1 (this `/tmp` report)
- Tests/builds/Lean/Lake/warm/seed/status/workflow commands: 0
- Network/cache/runtime/canonical-state actions: 0
- Token usage: JSON `null`; availability reason: the collaboration backend does
  not expose per-agent token usage, so no estimate was made
- First observed timestamp: `2026-09-01T00:00:14.241701906+08:00`
- Finalization timestamp: `2026-09-01T00:07:56.689505804+08:00`
- Elapsed through report finalization: `462.448` seconds (agent measured from
  first observed timestamp)
- Report SHA-256: supplied to the coordinator out of band after finalization,
  because embedding an ordinary file's own digest would change the digest

Exact base-file SHA-256 values (bytes from `git show <base>:<path>`):

```text
398397242ce474fd258d2489eab5a553cf8b7203327d64e29b078c32f82e8b75  workflow/state/issues.json
922943b7ac0866f8aa96e7eae9a8048c07d2eecd0ae774428093cd7dedf42b63  workflow/reviews/qpbt-018-plausible-drift-a15.md
263275da4d0b2312619bd1fec81b92d50993556202c219abc3ad535fd0302b9c  workflow/reviews/qpbt-018-hotcache-verify-order-a16.md
538c83d046b4377c92de8322628df7e61e60569f9c8a3cddf07c8f0f7a632d67  workflow/reviews/qpbt-018-failure-disposition-a17.md
73bc42b1b4a33806e83ab5502f1b125eae6325f6c0d1063a80d0fa481dd245e5  scripts/materialize_lake_packages.py
12eafd5a41b642ce16e55d378d621544160af81503090060771adaf4a1ebf6c4  tests/test_lake_package_materialization.py
ed2bed4d4aab27f2bd1e7dd98c484d0e1ebee0e80f5265ac6bccc84a03674b75  tests/test_hot_main_cache.py
```
