# QPBT-024 exact proofwidgets sidecar implementation hooks (a15)

## Verdict

A14's final communicated API boundary selects strict exact validation followed
by descriptor-relative removal before both source-tree comparisons and cache
publication, while keeping bare `verify` read-only. The smallest safe hook is
one non-parameterized explicit CLI flag,
`verify --remove-validated-generated-sidecars`, placed in the canonical
`package_verify_command`. The same flagged argv runs pre-Lake as an absent-file
no-op and post-build as validate/remove-plus-verify. The package pin schema and
`references/lake-packages.json` remain unchanged; the canonical hot-cache
recipe changes only by this argv token and recipe version 4 to 5.

The exact authority is one tuple, not a suffix rule:

| Field | Exact value |
|---|---|
| package | `proofwidgets` |
| revision | `6e311e2a844da9b2cc3971187df2fe0066947b93` |
| target | `widget/package-lock.json` |
| target SHA-256 | `3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d` |
| sidecar | `widget/package-lock.json.hash` |
| sidecar bytes | exact ASCII `179e66574f04806e`, 16 bytes, no newline |

The observed sidecar payload SHA-256 is
`971a4e08a78d3b185902cde49867376deb03135a517d4380eb1cb6604cfcb38b`.
No `*.hash` glob or package-wide generated namespace should be introduced.

## Current data flow and exact hooks

1. Pin parsing is closed-schema at
   `scripts/materialize_lake_packages.py:43-56,207-300`. The production pin's
   proofwidgets record is at `references/lake-packages.json:127-163`; it binds
   the exact revision, archive digest/inventory, and archive/Git tree
   `bec90bac5dd8afade168e76c5b508482f9043b26`. Leave this schema and record
   unchanged under the A14 design.
2. `inspect_archive_bytes` at
   `scripts/materialize_lake_packages.py:761-891` already produces a complete
   normalized entry list with kind, path, mode, size, SHA-256, and payload for
   every regular member. Add `_validate_generated_sidecar_archive_contract`
   after parent/gitlink/empty-directory validation (`:852-875`) and before
   facts are returned. For the exact name/revision it must require the target
   entry to be a regular file with the exact SHA-256 and require the sidecar
   path to be absent. The existing authenticated archive facts continue to bind
   member sizes and complete inventory. This check is reached by materialization via
   `_materialize_archive_bytes` (`:1052-1076`) before any package publication.
3. The repository, `.lake`, and `.lake/packages` directories are already bound
   with no-follow descriptors by `_bound_project_layout` (`:498-556`). Reuse
   `_bind_child` and `BoundChild.matches` (`:1206-1260`) to bind the exact
   proofwidgets package directory, its `widget` child, the target, and the
   sidecar. Do not validate or unlink through a recomposed absolute path.
4. Add a narrow context helper such as `_prepared_package_source` adjacent to
   `_bind_child`. It should activate only when `_sidecar_contract_for(package)`
   matches both exact package name and revision. It holds the package/widget/
   target bindings across cleanup and both Git tree computations, yields the
   package source as `/proc/self/fd/<package-fd>`, and rechecks bindings on exit.
   `_run_git` already detects `/proc/self/fd/` arguments and passes their file
   descriptors to Git (`:936-955`), so no Git runner change is needed.
5. Add descriptor readers rather than use path-based `_file_sha256`: an exact
   16-byte reader for the sidecar and a bounded SHA-256 reader for the target.
   They can reuse the bounded-read pattern from `_read_regular_exact_at`
   (`:612-638`) but must read the already-bound file descriptors, compare
   pre/post `fstat`, and retain the bindings for the unlink identity check.
   These are necessary new helpers; `_read_regular_exact_at` closes its
   descriptor and therefore is insufficient for removal. The immutable
   contract need not duplicate target size; the digest plus authenticated
   archive facts supply the exact identity.
6. Give `verify` (`:1926-1957`) a keyword-only boolean such as
   `remove_validated_generated_sidecars=False`. Enter the bound package-source
   context before `_scan_tree`. If the exact sidecar is absent, record no
   removal and continue. If it is present and the boolean is false, do not
   unlink it: bare verification remains read-only and the ordinary exact tree
   comparison rejects the drift. If the boolean is true, validate and remove
   it as specified below. Then run the existing `_scan_tree`, archive-tree
   `compute_source_tree_sha`, and Gitlink-aware `compute_source_tree_sha` in
   their current order. Both comparisons remain exact. Extend the returned
   JSON with a deterministic exact-path list such as
   `removed_generated_sidecars`, empty pre-build and containing only
   `.lake/packages/proofwidgets/widget/package-lock.json.hash` post-build, and
   include the requested normalization boolean/mode even when the list is empty.
7. In `build_parser` (`:2097-2108`), retain the `verify` parser and add exactly
   `--remove-validated-generated-sidecars` as a `store_true` flag. Pass it to
   `verify` at `main:2121-2122`. No hash value, path, package, revision, or glob
   is accepted from the CLI. The CLI already prints verifier JSON
   (`:2116-2146`), and hot-cache `_run_logged` records it in `build.log`
   (`scripts/hot_main_cache.py:1868-1889`).

The new context/helper split is preferable to adding a generic exclusion
parameter to `compute_source_tree_sha` (`:1022-1049`). It localizes mutation
authority to the exact contract and leaves the only current projection,
validated `.lake/build`, unchanged.

## Exact removal sequence

For the one matching contract, the helper should perform all validation before
mutation:

1. Bind package and `widget` with `O_DIRECTORY|O_NOFOLLOW`; bind target and
   sidecar with `O_NOFOLLOW|O_NONBLOCK`. Require both files regular and
   singly-linked. Existing `_bind_child` supplies these type/link checks.
2. Require the bounded descriptor-read target SHA-256 to match the exact
   contract. Require sidecar size 16 and descriptor-read bytes to equal exact lowercase
   ASCII `179e66574f04806e` with no newline.
3. Reject executable bits and setuid/setgid/sticky bits on the sidecar. A
   symlink, directory, FIFO/socket/device, hardlink, malformed content, or
   changed target fails before unlink. The eventual exact Git tree check still
   authenticates all ordinary target/source modes and content.
4. Immediately before removal, call `BoundChild.matches` for sidecar under the
   widget FD, target under the widget FD, widget under the package FD, and
   package under the bound packages FD; call `layout.assert_current()`.
5. Call `os.unlink(sidecar_name, dir_fd=widget_fd)`, `os.fsync(widget_fd)`, and
   require `_child_exists(widget_fd, sidecar_name)` to be false. Recheck the
   remaining bindings and layout.
6. Hold the package/widget/target descriptors while `_scan_tree` and both tree
   computations run; recheck them and `layout.assert_current()` after each tree
   computation and before closing. Any detected replacement fails, so no READY
   snapshot can be published.

If the sidecar is absent, absence is valid because this is the pre-Lake state.
If a path appears after the absence check, the exact tree comparison normally
catches it. The implementation must not claim complete protection against an
actively racing same-UID process; the canonical warm relies additionally on a
private staging tree and one cache-election owner.

## Hot-cache ordering, identity, inventory, and seed

The selected explicit flag requires one narrow hot-cache recipe change:

- At `scripts/hot_main_cache.py:205-228`, bump canonical recipe version 4 to 5
  and append `--remove-validated-generated-sidecars` to
  `package_verify_command`. Keep the one existing verifier field and both
  existing call sites. The recipe already lists both
  `references/lake-packages.json` and `scripts/materialize_lake_packages.py` as
  identity files.
- `CacheIdentity.create` hashes the exact main commit, committed identity-file
  digests, recipe payload, and source contract (`:1377-1417`). Changing the
  materializer bytes, changed canonical argv, version 5, and changed main
  commit therefore create a new key. The hard-coded contract is also bound to
  the exact proofwidgets revision. Dirty local bytes do not affect the
  committed key. `BUILD_RECIPE_SCHEMA_VERSION` stays 3 because no serialized
  field is added or removed.
- `warm` already orders package materialize, verify, dependency command, build,
  verify (`:2110-2153`). The first flagged verifier sees no sidecar and makes no mutation;
  the final verifier validates/removes it before HEAD/input/source rechecks and
  before `.lake` is detached for publication (`:2154-2177`). Do not move or
  weaken the final verifier.
- Full `artifact_inventory` runs only after final verification/removal and
  covers all remaining `.lake` entries, including package-local
  `.lake/build/**` (`:2179-2199`; inventory implementation `:246-305`). The
  sidecar must therefore be absent from the published inventory; all legitimate
  build artifacts remain present.
- `is_ready(deep=True)` recomputes that complete inventory (`:1793-1837`).
  `seed` requires deep readiness, copies the complete `.lake`, makes only the
  private copy writable, publishes it, and recomputes the same inventory at the
  destination (`:2319-2332,2360-2448`). A seed consequently contains no stale
  trusted sidecar. Lake may regenerate it later from the authenticated target
  in the private worktree.

## API alternatives and exact identity effects

The selected interface is the reused verifier flag below. Two broader or less
clear alternatives are recorded to prevent accidental expansion.

### Reused verifier flag (selected)

Add `verify --remove-validated-generated-sidecars` in
`materialize_lake_packages.build_parser` (`:2097-2108`) and gate removal in
`verify`; without the flag, a present sidecar remains ordinary drift and fails.
Change `CANONICAL_BUILD_RECIPE.package_verify_command` at
`hot_main_cache.py:218-220` to include the flag. Because one argv is reused at
both `warm` call sites, it is an explicit no-op sanitizer before Lake and an
explicit sanitizer after Lake, not literally post-build-only.

Its changed argv is already serialized by `BuildRecipe.identity_payload`
(`:163-175`), and the changed committed main SHA also enters `CacheIdentity`;
key churn is automatic. Bump canonical recipe version 4 to 5 to name the
behavioral revision. No new recipe field or recipe-schema bump is required.

### Implicit mutation inside bare verify (rejected)

This saves the one hot-cache argv edit, and changing the identity-bearing
materializer still changes the key. It is rejected because a command named
`verify` would unexpectedly mutate standalone package trees. The explicit
flag preserves a clear read-only default without granting any caller control
over which path or bytes are accepted.

### Truly post-build-only combined verify (larger option)

Add an identity-bearing `package_post_build_verify_command` to `BuildRecipe`,
its `for_testing` constructor, `identity_payload`, canonical recipe, dry-run/
metric/manifest records, and use it only at `warm:2146-2153`; retain the current
plain verifier at `:2120-2126`. The post-build argv should be combined
`verify --remove-validated-generated-sidecars`, not a standalone remove command
followed later by verification. This avoids a mutation/verification gap.

Because the serialized recipe shape changes, this alternative would bump
`BUILD_RECIPE_SCHEMA_VERSION` 3 to 4 as well as canonical recipe version 4 to
5. This option is materially broader, expands implementation ownership to
`scripts/hot_main_cache.py`, and requires updating the command-order and
identity tests. It is not needed for the adjudicated design.

A standalone `sanitize` subcommand is the weakest explicit form: it creates a
race gap unless it performs both cleanup and both exact source comparisons.
Do not add a mutation-only command.

## Projection branch, now rejected

Had A14 selected retention, the smallest hook would have been an exact validated
path parameter to `compute_source_tree_sha`, followed after `git add --all
--force` by literal `git rm --cached --ignore-unmatch --
widget/package-lock.json.hash` for both tree computations. Validation would
still need every descriptor/archive check above, and full inventory/seed would
then retain and authenticate the sidecar. Do not implement this branch: A14
rejects publishing Lake metadata that the writable seed later trusts by
default. Never generalize it to `*.hash`.

## Owned paths and acceptance boundary

Frozen writer ownership for the adjudicated explicit-flag design is exactly:

```text
scripts/materialize_lake_packages.py
scripts/hot_main_cache.py
tests/test_lake_package_materialization.py
tests/test_hot_main_cache.py
```

Do not edit `references/lake-packages.json`, pin/cache manifest schemas,
`BUILD_RECIPE_SCHEMA_VERSION`, protocol files, or root-owned workflow/metrics
state. Do not add a new hot-cache recipe field or phase.

Focused tests should directly cover archive target/absence, absent no-op,
valid removal/evidence, malformed bytes/mode/type/link cases, target mismatch,
parent/name/inode swaps, exact source drift after cleanup, undeclared `.hash`
drift, and both `.lake/build` and Gitlink preservation. The hot-cache test hook
is the existing `PACKAGE_MATERIALIZING_TEST_RECIPE` and ordered callback at
`tests/test_hot_main_cache.py:45-56,601-656`; extend it to create the exact
sidecar during the fake Lake phase and assert snapshot/seed absence, full deep
inventory, and no READY on malformed/drift cases. Existing materializer fixture
and boundary tests are at
`tests/test_lake_package_materialization.py:125-254,343-457,533-642`.

## Residual risks

- Descriptor-relative binding, identity rechecks, and parent fsync close the
  intended symlink/name-swap boundaries, but cannot prove freedom from an
  actively racing process with equal filesystem authority.
- Removal is a deliberate verifier mutation. On unrelated source drift, the
  exact sidecar can be removed before the later tree mismatch is reported; in
  canonical warm this affects only disposable private staging.
- The internal contract must not silently follow future proofwidgets
  revisions. A new revision or second generated path requires fresh evidence
  and review; otherwise it remains source drift.
- Archive absence is explicitly checked during materialization. A standalone
  later `verify` does not reopen archives, but after exact cleanup its two
  pinned tree comparisons still require the remaining package to equal the
  authenticated archive/Git identities.

## Evidence and session accounting

- Logical session: `i024-scout-a15-sidecar-hooks`.
- Base/observed HEAD: `9c9b49548fabdd6b01916787d7dc17a4bca36513`.
- Start: `2026-09-01T01:44:20.064770+08:00`.
- End: `2026-09-01T01:59:41.183991305+08:00`.
- Elapsed: `921.119221305` seconds.
- Topology: read-only implementation-hook scout under root; subagents `0`.
- Token usage: JSON `null`; availability reason: collaboration backend does
  not expose per-agent token usage, so no estimate was made.
- Tests, builds, warm, seed, Lean, Lake, network, Git writes, repository/state
  edits, and cache/runtime mutations: `0` each.
- Authored artifact: `/tmp/qpbt-024-sidecar-hooks-a15.md` only.

Evidence SHA-256 values at the observed base/worktree:

| File | SHA-256 |
|---|---|
| `AGENTS.md` | `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c` |
| A11 report | `5b2e0067c507b8a8ef610f700198b60be803ef24681b4df5ff3005db6bd4c4b6` |
| A12 report | `72388d58782faa23ce28ed6abbcc2a12b9923446e82834c2b8ab5cdd9eca38d0` |
| A14 synthesis | `bd0d1a613db912bd45e64c4db435135fba547c73c35db496a540603b6f187407` |
| `scripts/materialize_lake_packages.py` | `3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243` |
| `scripts/hot_main_cache.py` | `0fd404e2cead596370fbda144dc86810f0fd2b87fe7a6ba011d7e72b661daeab` |
| `references/lake-packages.json` | `08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0` |
| `tests/test_lake_package_materialization.py` | `d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d` |
| `tests/test_hot_main_cache.py` | `235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe` |

The five tracked implementation inputs match their blobs at the base. The
report SHA-256 is supplied out of band after finalization because embedding it
would alter the digest.
