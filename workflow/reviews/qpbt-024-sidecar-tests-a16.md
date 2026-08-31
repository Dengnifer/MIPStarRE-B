# QPBT-024 proofwidgets sidecar focused-test scout (a16)

## Verdict

Freeze the A12 removal design, not A11's earlier retained-projection design.
The accepted post-build object is exactly
`proofwidgets/widget/package-lock.json.hash`, for proofwidgets revision
`6e311e2a844da9b2cc3971187df2fe0066947b93`, with exact bytes
`179e66574f04806e`. Verification validates the authenticated target and the
sidecar through bound, no-follow descriptors, removes the sidecar, then runs
the existing full source-tree comparisons. Pre-build absence is valid. A
published snapshot and every seed must omit the sidecar, while package-local
`.lake/build` output remains present and inventory-bound.

A11 is useful forensic evidence and supplies the original broad acceptance
list, but its recommendation to retain the validated sidecar conflicts with
A12. A12 is the later security decision and explains why retention exports
trust-bearing Lake metadata into writable seeds. Tests must therefore assert
absence from snapshot and seed; they must not bind the A11 retained-sidecar
expectation.

The smallest omission-sensitive change is six grouped materializer tests plus
two strengthened hot-cache tests. Keep the three existing `.lake/build` tests
as-is. Do not duplicate path-type or race cases in the hot-cache suite.

## Exact test seams and fixtures

### `tests/test_lake_package_materialization.py`

Use the existing synthetic eight-package archive fixture at lines 82-243. It
already includes proofwidgets, derives archive facts and exact Git trees from
the fixture bytes, and gives every test a private repository.

Add proofwidgets fixture constants after the module loader at lines 19-25:

- `FIXTURE_WIDGET_TARGET = b"fixture package lock\n"`
- `FIXTURE_WIDGET_TRACE` containing an `outputs` value ending in
  `179e66574f04806e.art`
- `FIXTURE_LAKE_HASH = b"179e66574f04806e"`
- the relative target, trace, and sidecar paths

In `make_archive` at lines 82-107, append `widget/`, the target, the trace, and
`widget/package.json` only when `package["name"] == "proofwidgets"`. Keep the
synthetic revision (`"4" * 40`); do not pretend its target bytes have the real
target SHA-256. New focused tests should patch the module's immutable contract
table with a test contract keyed to that synthetic revision and to
`sha256(FIXTURE_WIDGET_TARGET)`. This tests contract mechanics without needing
the 3.9 MB production archive or weakening the production constant.

Add these reusable test helpers immediately after `_materialize` at lines
253-254:

- `_proofwidgets_package()` and `_proofwidgets_root()`
- `_fixture_sidecar_contract()`
- `_materialize_with_sidecar_contract(replace_existing=False)` (a narrow
  `mock.patch.object` context around the production contract table)
- `_write_sidecar(payload=FIXTURE_LAKE_HASH)`
- `_replace_fixture_archive(name, *, extra=..., replace_entries=...)`, which
  reruns `inspect_archive_bytes`, `_write_entries`, and `compute_tree_sha`, then
  updates `self.archive_bytes`, the archive file, `self.pin`, and `self.pin_path`

The last helper is reusable for both unrelated archive-owned `.hash` and the
contradictory declared-sidecar archive. It avoids ad hoc edits to counts,
digests, or Git trees.

Add the six new test methods after
`test_publish_verify_override_and_file_modes` (current line 343), before the
existing generated-build boundary block:

1. `test_proofwidgets_sidecar_absent_or_exact_is_safely_removed`
2. `test_proofwidgets_sidecar_rejects_malformed_payloads`
3. `test_proofwidgets_sidecar_rejects_unsafe_types_links_and_modes`
4. `test_proofwidgets_sidecar_rejects_target_and_parent_replacement`
5. `test_proofwidgets_sidecar_cleanup_does_not_mask_tree_drift`
6. `test_proofwidgets_sidecar_archive_provenance_is_exact`

### `scripts/materialize_lake_packages.py` seams exercised

The tests should target small internal helpers rather than mock
`compute_source_tree_sha`:

- Put the frozen contract type/table beside constants at lines 25-60.
- Put exact package/revision selection after `load_pin` (ending at line 300).
- Put descriptor-relative target/sidecar validation and removal after
  `_read_regular_exact_at` (lines 612-638), reusing `_open_child_directory`,
  `BoundDirectory`, `_directory_identity`, and `O_NOFOLLOW | O_NONBLOCK`.
- Validate archive absence/presence against the exact contract inside
  `inspect_archive_bytes` after the complete entry map is known (lines
  852-875), before facts are returned.
- In `verify`, bind each package root below `layout.packages`, invoke the
  sanitizer before `_scan_tree` and both tree computations (current lines
  1941-1954), and recheck package/layout identities after cleanup and after
  tree hashing.
- Return a deterministic
  `removed_generated_sidecars: ["proofwidgets/widget/package-lock.json.hash"]`
  evidence list; the absent case returns an empty list.

For replacement tests, use one private phase hook on the internal sanitizer,
not production timing sleeps. Required phases are after target authentication,
after sidecar open/read, immediately before unlink, and after unlink/before the
final parent/package-root recheck. The hook is only an injection point; all
production checks and system calls still run.

### `tests/test_hot_main_cache.py`

Keep `PACKAGE_MATERIALIZING_TEST_RECIPE` at lines 45-59. Add exact fake sidecar
path/content constants immediately after it. Extend `fake_success` at lines
209-238 so fake package materialization creates a proofwidgets widget target
and fake package verification applies only the exact fake-sidecar contract:
absence passes, exact content is removed, malformed content or marker drift
returns nonzero. The focused suite, not this fake, proves filesystem safety.

Strengthen these existing tests rather than adding parallel orchestration
tests:

- `test_packages_are_identity_bound_materialized_and_verified_before_lake_steps`
  (line 601): have the fake build create the exact sidecar; retain the exact
  five-command order assertion; assert the snapshot has no sidecar, contains
  `fixture/.lake/build/Fixture.olean`, and passes `is_ready(deep=True)`; seed a
  registered issue worktree and assert the seeded copy also omits the sidecar,
  preserves the build artifact, and has the manifest's exact artifact
  inventory. Extend this same test with the existing dirty-then-commit pattern
  from lines 586-599, applied to
  `scripts/materialize_lake_packages.py`, to prove contract-byte changes churn
  the key without a recipe version or command change.
- `test_warm_rejects_post_build_package_drift` (line 634): table-drive two
  fresh-runtime subtests: malformed sidecar; exact sidecar plus package-source
  mutation. In both, assert verification failure, no snapshot directory, no
  `READY` anywhere below the runtime, one retained failure envelope, and no
  `READY` in that envelope.

Do not add a separate cache-key test: extending line 601 proves the exact
identity input and avoids duplicating
`test_elected_builder_materializes_once_and_identity_binds_materializer`.

## Frozen regression matrix

| ID | Case and exact assertion | Owner |
|---|---|---|
| M1 | Pre-build sidecar absent: verify succeeds, returns no removal, and changes no target/package bytes or modes. Then add real package `.lake/build` output plus exact regular, one-link, non-executable 16-byte lowercase sidecar: verify succeeds, reports the exact removal, sidecar is absent, authenticated target bytes/mode/inode are unchanged, and `.lake/build` remains byte-identical. | New materializer test 1 |
| M2 | Subtests for wrong but valid lowercase 16-hex, uppercase, 15 bytes, 17 bytes, exact hash plus newline, and non-hex. Every case raises, retains the suspect path for evidence, and does not alter the target. | New materializer test 2 |
| M3 | Real filesystem subtests: symlink, directory, FIFO, Unix socket, multiply-linked regular file, executable regular file, and setuid/setgid/sticky regular file. Each raises before unlink; symlink target and hardlink peer remain unchanged. Exercise character/block-device `st_mode` through the pure metadata predicate because portable unprivileged tests cannot create device nodes; FIFO/socket separately prove nonblocking handling of live special objects. | New materializer test 3 |
| M4 | Target subtests: symlink, FIFO/socket, hardlink, wrong bytes, executable-mode drift, and replacement with a new inode during the authentication/unlink window. Parent subtests replace `widget/` and the package root after binding. Every case fails on identity, never follows the replacement, and leaves an external sentinel unchanged. | New materializer test 4 |
| M5 | With an otherwise exact sidecar, independently mutate the target, ordinary source (`src/source.txt`), package config (`lakefile.lean`), and package manifest. Target failure occurs before cleanup; the other three may remove the legitimate sidecar but must then fail exact tree comparison. Add valid-looking `widget/other.hash`; it remains on disk and fails as ordinary source drift. | New materializer test 5 |
| M6 | Add an authenticated unrelated `docs/reference.hash` archive member, recompute exact fixture facts, materialize it, and prove unchanged verify passes while mutation and deletion fail tree identity. Separately put the declared generated sidecar path in the matching contract archive and require archive inspection to reject the provenance contradiction. Assert the production contract matches the exact name, revision, target path/SHA-256, sidecar path, and Lake hash from A12 and the production pin's outer proofwidgets facts. | New materializer test 6 |
| B1 | Real `.lake/build` files are projected only from source identity; source/config/manifest and sibling/nested lookalikes still fail. | Existing `test_verify_projects_only_validated_generated_build_output` |
| B2 | `.lake/build` symlink, file, FIFO, nested symlink/FIFO, hardlink, and malformed `.lake` fail. | Existing `test_verify_rejects_malformed_generated_build_boundaries` |
| B3 | Archive-owned `.lake/build` is rejected. | Existing `test_archive_generated_build_output_is_rejected` |
| H1 | Exact call order is materialize, verify, dependencies, build, verify. The build-created exact sidecar is removed by the second verify. One READY snapshot publishes; snapshot and deep-verified seed omit the sidecar, retain `.lake/build`, and match the sealed inventory. Dirty materializer bytes do not change committed identity; committing a contract-byte change does. Recipe version 4 and command arrays remain unchanged. | Strengthened cache test at line 601 |
| H2 | Malformed sidecar, and exact sidecar beside source drift, both terminate at post-build verification. There is no snapshot or READY; one failure envelope is retained. | Strengthened cache test at line 634 |

This matrix is nonredundant by layer. M1-M6 test the real sanitizer and archive
contract. B1-B3 keep the already-covered generated-build boundary. H1-H2 test
only the orchestration consequences. Existing generic READY, manifest, deep
inventory, seed rollback, and tracked-source tests remain useful but are not
part of the minimum sidecar-specific acceptance subset.

## Important assertion details

- Exact success is `b"179e66574f04806e"`, not `.strip()` equality. A trailing
  newline must fail.
- "Wrong hash" needs a different lowercase 16-hex value; uppercase and non-hex
  are distinct parser cases.
- Sidecar mode checks use `stat.S_IMODE`: reject every execute bit and
  `S_ISUID | S_ISGID | S_ISVTX`. Require `st_nlink == 1`.
- Open FIFO/socket candidates with `O_NONBLOCK` so a malicious special entry
  cannot hang verification.
- Recheck descriptor/name `(st_dev, st_ino)` identity immediately before
  unlink; fsync the bound parent; require the name absent; then recheck target,
  parent, package root, packages root, and project layout incarnations.
- Do not assert that all invalid cases leave the valid sidecar present after a
  later source-tree failure. Once the sidecar itself is authenticated, removal
  before tree comparison is intended. Assert non-removal only for malformed or
  unsafe sidecars and for failures before sidecar authentication.
- `artifact_inventory` is aggregate, not path-listed. H1 must therefore assert
  path absence/presence directly in addition to equality with the manifest's
  aggregate inventory.
- A generic `*.hash` exclusion would make M5/M6 fail; these are the two tests
  that freeze forward compatibility with archive-owned hash files.

## Validation gates after implementation

Run only after the implementation is stable, in repository-prescribed order:

```text
python3 -m unittest discover -s tests -p test_lake_package_materialization.py -v
python3 -m unittest discover -s tests -p test_hot_main_cache.py -v
python3 -m unittest discover -s tests -v
python3 scripts/check_workflow.py
python3 -m compileall -q scripts tests
python3 scripts/workflow.py validate
git diff --check 9c9b49548fabdd6b01916787d7dc17a4bca36513..<exact-head>
```

No warm, seed, Lake, Lean, build, or network command belongs to this scout or
to pre-review implementation iteration.

## Residual risks

- The phase hook makes deterministic replacement tests possible but cannot
  prove safety against an actively racing same-UID process. The production
  trust boundary remains the private staging directory plus descriptor and
  incarnation rechecks described by A12.
- Aggregate inventory equality detects snapshot/seed byte differences but
  does not expose member paths. Direct sidecar absence and build-artifact
  presence assertions are therefore mandatory in H1.
- A mocked character/block-device metadata case covers the shared regular-file
  predicate, not kernel device-node open behavior. Real FIFO and Unix socket
  cases cover the important nonblocking live-object behavior without requiring
  privileges.
- The synthetic archive cannot authenticate the real target payload. M6 must
  separately freeze the production contract and pin facts; a future real
  archive refresh still requires independent provenance review.
- The A11 retained-sidecar expectations are intentionally superseded. Any
  implementation that retains the sidecar must return to security design
  review rather than changing these tests.

## Evidence and session accounting

- Logical session: `i024-scout-a16-sidecar-tests`.
- Base and observed `HEAD`:
  `9c9b49548fabdd6b01916787d7dc17a4bca36513`.
- First recorded timestamp: `2026-09-01T01:45:06.681436832+08:00`.
- Report drafting timestamp: `2026-09-01T01:51:02.849845057+08:00`.
- Recorded evidence interval: `356.168408225` seconds. Initial AGENTS/report
  reads preceded the first timestamp and are not falsely included in this
  measured interval.
- Topology: root coordinator -> one read-only scout; subagents `0`; depth `1`.
- Token usage: JSON `null`.
- Token availability reason: the collaboration backend does not expose
  per-agent token usage; no estimate was made.
- Tests, builds, warm, seed, Lean, Lake, network, Git writes, repository/state
  edits, and cache/runtime mutations: `0` each.
- Authored output: this `/tmp` report only.

Evidence SHA-256 values:

```text
c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c  AGENTS.md
5b2e0067c507b8a8ef610f700198b60be803ef24681b4df5ff3005db6bd4c4b6  workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md
72388d58782faa23ce28ed6abbcc2a12b9923446e82834c2b8ab5cdd9eca38d0  workflow/reviews/qpbt-024-sidecar-security-a12.md
08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0  references/lake-packages.json
d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d  tests/test_lake_package_materialization.py
235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe  tests/test_hot_main_cache.py
3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243  scripts/materialize_lake_packages.py
0fd404e2cead596370fbda144dc86810f0fd2b87fe7a6ba011d7e72b661daeab  scripts/hot_main_cache.py
```

The report SHA-256 is supplied out of band because embedding it would change
the digest.
