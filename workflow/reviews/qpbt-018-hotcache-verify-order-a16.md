# QPBT-018 hot-cache post-build package verification audit (a16)

## Verdict

The dba1 warm failed because the package verifier treats Lake's normal,
package-local generated output as authenticated package source. The retained
log proves that package materialization and the first verification passed, the
dependency command ran, the full 8,992-job build completed successfully, and
the second verification then stopped on the first pinned package with
`materialized archive tree differs for plausible`.

Keep the post-build verifier exactly where it is. The smallest safe correction
is to make `scripts/materialize_lake_packages.py verify` compare each pinned
package's **source projection**: every package-root entry except the exact
top-level `.lake/` generated-output subtree. This preserves accepted finding
F-LPR005-001/QPBT-004: package sources are still reverified after both Lake
commands and before publication. Moving, deleting, or weakening the second
verification is not acceptable.

No production change is required in `scripts/hot_main_cache.py`; its ordering
at lines 2112-2153 is correct.

## Retained failure evidence

- Exact commit: `c0de0900a01724c2a515311424dcbe5e7526ebd4`.
- Exact cache key:
  `dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276`.
- Failure envelope:
  `.workflow-runtime/cache/failures/dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276-20260831T232823-2/`.
- `failure.json` SHA-256:
  `6585f5226a1163527193dafb0dd49d6614e7917dfdc14d08600bd8f37b6ed401`.
- `build.log` SHA-256:
  `7fcc04ad7e13187dfa3159f1495c2981fdb47d0fa5a253249e69573e691b92bf`.
- `failure.json` records `Lake package verification command failed with exit
  code 1`; the log's final two lines are `Build completed successfully (8992
  jobs).` and `error: materialized archive tree differs for plausible`.
- The log records package `status: published`, then package `status:
  verified`, before either Lake command. Therefore the archive and initial
  materialized source were exact; drift arose during the permitted Lake phase.
- Failure retention moves out only `build.log` and writes `failure.json`, then
  removes staging (`hot_main_cache.py:2230-2253`). The exact changed filenames
  cannot be recovered from this envelope, and should not be invented.

## Current order and failure mechanism

The elected builder currently executes:

1. foundation materialization;
2. eight-package materialization;
3. eight-package verification;
4. Mathlib source preparation;
5. `lake --packages=.lake/package-overrides.json exe cache get`;
6. `lake --packages=.lake/package-overrides.json build`;
7. eight-package verification again;
8. checkout/input/source/Mathlib checks, then `.lake` publication.

This is the required security order. The second call at
`hot_main_cache.py:2146-2153` is the implementation of accepted high finding
F-LPR005-001, whose explicit threat is a build-time mutation under ignored
`.lake/packages` entering a READY cache.

The semantic mismatch is in `materialize_lake_packages.py`:

- `compute_tree_sha` at lines 961-985 stages the whole work tree with
  `git add --all --force`. `--force` deliberately defeats each package's
  ignore file.
- `verify` at lines 1862-1891 calls that whole-tree function for both the raw
  archive tree and Gitlink-reconstructed tree.
- The plausible archive contains no `.lake` entry and its committed
  `.gitignore` is exactly `/.lake`. Its lakefile uses default Lake directories.
  Lake therefore owns `<package>/.lake/` for compiled/generated package state.
- After Lake creates that state, forced staging adds it to the tree. The result
  can no longer equal plausible's pinned raw tree
  `b477789560b0cd76cf3177b9cffa3aaa5cd54e6b`. Plausible is first in pin order,
  so verification reports the raw-tree mismatch there and never reaches its
  reconstructed-tree check or later packages.

## Mutation boundary

Expected and publishable generated mutations are:

- root `.lake/build/**`;
- each pinned package's exact root `.lake/packages/<name>/.lake/**`, including
  Lake configuration elaboration and compiled/build artifacts;
- Mathlib's generated `.lake/**`, which is outside the eight-package verifier
  and is separately checked by the Mathlib Git-source verifier;
- materializer runtime state under `.lake/lake-package-materialization/**`.

These paths are build artifacts, not package source. They remain covered by the
hot-cache artifact inventory and READY/seed integrity contract after the
build; they do not need to equal an upstream source-tree SHA.

Forbidden mutations remain:

- any path in an authenticated package outside its exact root `.lake/`,
  including `.lean` files, `lakefile.*`, `lake-manifest.json`, `lean-toolchain`,
  license/readme files, symlinks, and executable-bit changes represented in a
  Git tree;
- package removal, replacement, or replacement by a symlink/non-directory;
- `.lake/package-overrides.json` drift from the exact pin-derived document;
- root manifest, pin, materializer, recipe, or other cache-key input drift;
- a package-root `.lake` entry that is a symlink, regular file, or other
  non-directory object. Only a real directory is an admissible generated
  boundary.

Directory mtimes and ordinary directory modes are not Git-tree identity and
were never part of post-materialization verification. Special filesystem
objects remain rejected by `_scan_tree`; source file contents, symlink values,
and Git-significant modes remain authenticated.

## Smallest production edit

Edit only `scripts/materialize_lake_packages.py` in production:

1. Add a narrowly named source-tree helper or a keyword-only mode on
   `compute_tree_sha` that excludes exactly the source root's `.lake` entry and
   descendants from the temporary Git index. Do not add a general caller-
   supplied arbitrary exclusion list.
2. Before excluding it, `lstat` the entry when present and require one real
   directory, not a symlink. Continue scanning the complete package tree for
   special objects.
3. In `verify` only, use that source projection for both raw archive-tree and
   Gitlink-reconstructed comparisons. Keep `_materialize_archive_bytes` using
   the current full-tree calculation. This proves the pinned archive itself is
   exact and prevents a future archive containing `.lake` source from being
   silently normalized away.
4. Retain override verification, layout incarnation checks, package iteration,
   and both SHA comparisons unchanged.

Do not edit the canonical recipe version merely to force a key change: the
materializer is already an `additional_identity_file`, so its content hash
changes the cache identity. Do not remove package-local `.lake` before the
check; those artifacts are required in the published cache. Do not move the
second verification earlier, and do not make post-build verification
best-effort.

Expected test edits are confined to
`tests/test_lake_package_materialization.py` and, for integration-level
coverage, `tests/test_hot_main_cache.py`; no other production module is needed.

## Required regressions

1. Materialize a fixture, create `<package>/.lake/build/...` plus representative
   package-local Lake metadata, and prove `verify` still succeeds.
2. With that same generated subtree present, alter an authenticated source
   file such as `src/source.txt` or a `.lean` file and prove `verify` fails with
   a tree mismatch. This is the mandatory malicious-source-mutation test.
3. With generated `.lake` present, alter `lakefile.*` or
   `lake-manifest.json`; prove failure. This guards the exact source/build
   boundary rather than only one payload file.
4. Replace package-root `.lake` with a symlink and with a regular file; both
   must fail, not be ignored.
5. Preserve the hot-cache call-order assertion:
   `package-materialize, package-verify, deps, build, package-verify`.
6. Make the fake build create package-local `.lake` output and prove a warm can
   publish, while the existing post-build source-marker mutation still fails
   and publishes no READY snapshot. This shows the fix does not regress
   F-LPR005-001.
7. Preserve the Aesop Gitlink regression: exclusion of package-local `.lake`
   must not change explicit `160000` reconstruction or allow a nonempty/missing
   Gitlink placeholder.

## Session accounting

- Logical session: `i018-scout-a16-hotcache-verify-order`.
- Issued/start UTC: `2026-08-31T15:33:26.280928Z`.
- Audit cutoff UTC: `2026-08-31T15:39:03Z` (approximately 337 seconds to
  cutoff; final report/checksum work followed).
- Files/evidence families inspected: 19 (two production scripts, two focused
  test files, retained failure JSON/log, package pin/manifests/archive metadata,
  five QPBT-004/QPBT-018 review records, two protocol documents, session and
  metrics ledgers, and repository instructions/status).
- Tests run: 0. Lean/Lake/build/warm/seed/status commands: 0. Network calls: 0.
- Canonical/runtime/cache/reference/worktree/state edits: 0.
- Subagents: 0.
- Output files created: 1, this report under `/tmp`.
- Token usage: unavailable; the collaboration backend does not expose
  per-agent token counts. No estimate was made.
- Report SHA-256: computed after finalization and supplied to the coordinator
  out of band, because a file cannot contain its own ordinary SHA-256 digest.
