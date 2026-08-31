# QPBT-025 sidecar test-matrix scout (a03)

## Session identity

- Stable logical name: `i025-scout-a03-sidecar-tests`.
- Role: read-only focused-test scout under the sole QPBT-025 orchestrator.
- Task path: `/root/i025_orchestrator_a01_sidecar_removal/i025_scout_a03_sidecar_tests`.
- Topology: root/orchestrator -> one read-only scout; subagents spawned by this scout: `0`.
- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-025-sidecar-a01`.
- Branch: `issue/qpbt-025-sidecar-a01`.
- Worktree base and observed HEAD: `45d2fe657af587e8e10952aced2e156d349fd65e`.
- Worktree base and observed committed tree: `07df5125163a5bdddd1b80549cf622f8a0a628cd`.
- HEAD parent, the integrated failed-warm main: `9c9b49548fabdd6b01916787d7dc17a4bca36513`.
- Parent committed tree: `a7409faf8cbd888e3f04d114332f202ea1436d11`.
- HEAD commit subject: `chore(workflow): record proofwidgets cache repair gate`.
- HEAD commit time: `2026-09-01T02:18:12+08:00`.
- Final evidence capture time: `2026-09-01T02:40:43,010028723+08:00`.
- Elapsed seconds: JSON `null`.
- Timing availability reason: the scout did not capture a start timestamp, and the collaboration backend exposes individual command wall times but no reliable session-start time. No elapsed estimate was made.
- Token usage: JSON `null`.
- Token availability reason: the collaboration backend does not expose per-agent token usage. No estimate was made.

## Scope and verdict

All assigned sources and the relevant current implementation/test seams were inspected read-only. The accepted authority is A14/A15 and the QPBT-025 issue gate: exact revision-bound validation, explicit flagged removal, bare-`verify` purity, canonical recipe version 5, build-recipe schema version 3, no new phase or recipe field, and no sidecar in a published or seeded cache.

A16's statement that recipe version 4 remains unchanged is stale and must not be asserted. A11's retained-sidecar result is forensic input but its retention recommendation is superseded. Tests must assert removal before publication and seed.

The smallest complete suite is:

1. Six grouped materializer tests covering exact success/purity, malformed payloads, unsafe objects, target/parent/name races, source/path guards, and archive provenance.
2. One strengthened realistic Gitlink test proving that both independent tree authorities remain active.
3. One strengthened successful hot-cache lifecycle test.
4. One table-driven failed hot-cache lifecycle test.
5. Exact canonical-recipe and identity-churn assertions in the existing recipe test.
6. The three existing `.lake/build` boundary tests retained unchanged in substance.

## Source anchors read

- `AGENTS.md`, all 139 lines.
- `workflow/reviews/qpbt-024-postintegration-warm-failure-9b6.md`, all 160 lines.
- `workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md`, all 293 lines.
- `workflow/reviews/qpbt-024-sidecar-security-a12.md`, all 326 lines.
- `workflow/reviews/qpbt-024-sidecar-synthesis-a14.md`, all 359 lines.
- `workflow/reviews/qpbt-024-sidecar-hooks-a15.md`, all 290 lines.
- `workflow/reviews/qpbt-024-sidecar-tests-a16.md`, all 250 lines.
- `workflow/state/issues.json:870-920`, including the exact QPBT-025 acceptance gates.
- `references/lake-packages.json:118-172`, including the production proofwidgets facts.
- `workflow/state/prs.json`, `workflow/state/sessions.json`, and `workflow/events.jsonl` through bounded searches for the issue worktree/LPR/base identity.

## Current code and test seams inspected

- `scripts/materialize_lake_packages.py`: constants/pin schema; project and child descriptor bindings; bounded readers; archive inspection; Git tree computation; `.lake/build` projection; transaction bindings; current exact sidecar contract, selector, archive guard, metadata predicate, phase hook, descriptor-relative removal, prepared package context, `verify`, parser, and CLI dispatch.
- `scripts/hot_main_cache.py`: `BuildRecipe`, canonical recipe, artifact inventory, cache identity, readiness, warm ordering/failure retention, destination validation, and seed publication.
- `tests/test_lake_package_materialization.py`: archive fixture/setup, publication helper, existing source and `.lake/build` tests, Gitlink test, and concurrent new proofwidgets fixture/tests.
- `tests/test_hot_main_cache.py`: package recipe/fake callback, package success/failure tests, canonical recipe test, recipe identity/readiness test, and deep seed verification tests.

At final observation, the relevant live seams were:

- Contract and selector: `scripts/materialize_lake_packages.py:46,57,328`.
- Canonical-path hardening: `scripts/materialize_lake_packages.py:354-355`.
- Archive provenance guard: `scripts/materialize_lake_packages.py:823`.
- Phase seam and metadata predicate: `scripts/materialize_lake_packages.py:1348,1419`.
- Prepared cleanup and package source: `scripts/materialize_lake_packages.py:1431,1471,1552`.
- Flagged verifier and parser: `scripts/materialize_lake_packages.py:2241,2451`.
- Recipe schema/version/flag: `scripts/hot_main_cache.py:37,205-220`.
- Inventory/readiness/warm/seed: `scripts/hot_main_cache.py:247,1794,1978,2320,2361`.
- Six current materializer test methods: `tests/test_lake_package_materialization.py:443,497,523,588,736,791`.
- Hot success/failure methods: `tests/test_hot_main_cache.py:629,662`.

## Omission-sensitive acceptance matrix

| ID | Required guarantee | Smallest robust test and assertions |
|---|---|---|
| M1 | Exact contract package/revision | Put the exact path and bytes under a wrong revision and another package. Flagged verification must not remove it; ordinary exact-tree verification must fail and the path must remain. |
| M2 | Archive target and sidecar provenance | Under the patched synthetic proofwidgets contract, exact regular target/digest plus sidecar absence passes archive inspection. Wrong target type/digest and an archive-owned declared sidecar fail before materialization. |
| M3 | Production provenance is frozen | Assert the sole production tuple's exact name, revision, target, target SHA-256, sidecar path, and 16 bytes, plus the production pin's revision/archive size/archive SHA/tree facts. The synthetic archive tests mechanics without pretending its target bytes have the production digest. |
| M4 | Bare verify is pure | Materialize, create the exact sidecar, call unqualified `verify`, require tree-drift failure, and assert the sidecar, target bytes/mode/inode, and package observation are unchanged. |
| M5 | Flagged absent-path no-op | Call flagged verify before Lake with no sidecar. Require success, explicit normalization mode, empty removal evidence, no `fsync`, and unchanged recursive package content/modes/identities. |
| M6 | Exact removal and evidence | Add real `.lake/build` output and the exact regular one-link non-executable sidecar. Flagged verify succeeds, reports exactly `proofwidgets/widget/package-lock.json.hash`, removes only it, calls `fsync` on the bound parent, leaves the target tuple unchanged, and retains build output byte-for-byte. |
| M7 | Payload is exact, not normalized | Table wrong lowercase 16-hex, uppercase, 15 bytes, 17 bytes, exact bytes plus newline, and 16-byte nonhex. Each raises, leaves the suspect present, and does not change the target. Do not use `.strip()`. |
| M8 | Sidecar type/link/mode safety | Real symlink, directory, FIFO, AF_UNIX socket, hardlink, executable, setuid, setgid, and sticky cases all fail before unlink. Assert symlink target and hardlink peer remain unchanged. Exercise character/block modes through the pure metadata predicate. |
| M9 | Target object safety | Target symlink, directory, FIFO/socket, hardlink, and wrong bytes fail before cleanup; external targets/peers and the exact sidecar remain. Target execute-mode drift may remove an authenticated sidecar but must then fail the unprojected tree comparison. |
| M10 | Parent no-follow boundary | A pre-existing symlinked `widget` parent fails before any external read/write, with an external sentinel unchanged. |
| M11 | Target identity race | At `after_target_authenticated`, replace the name with a same-byte new inode. Verification must fail on identity before unlink and leave the sidecar present. |
| M12 | Sidecar open/name identity race | At `after_sidecar_authenticated` and `before_unlink`, replace the selected sidecar with a same-byte new inode. Verification must fail on identity and must not unlink the replacement. |
| M13 | Directory incarnation and post-unlink races | Swap `widget` and the package root before/after unlink, and recreate the sidecar at `after_unlink`. Every case fails; replacement/external sentinels remain; no write escapes the selected bound parent. |
| M14 | Canonical contract paths | Patch internal contracts with absolute, traversal, repeated-separator, dot-component, non-adjacent sidecar, noncanonical bytes, and overlapping cases. Selection must reject them. The repeated-separator/dot tests caught a likely gap during scouting; canonical `PurePosixPath(...).as_posix()` checks were observed added at final capture. |
| M15 | No arbitrary hash authority | Add `widget/other.hash`, a nested same basename, the same basename under another parent, and the exact relative path under another package. Each remains and causes tree failure. A valid exact sidecar may be removed first, but no lookalike may be removed. |
| M16 | Cleanup does not repair source drift | With an exact sidecar, independently mutate target, trace, `widget/package.json`, lakefile, package manifest, Lean/ordinary source, and add an extra file. Target digest drift fails before cleanup; other drift may follow legitimate cleanup but must fail the later exact tree check. |
| M17 | Archive-owned `.hash` stays source | Add authenticated `docs/reference.hash` to the matching proofwidgets fixture, recompute all facts/trees, materialize it, and prove unchanged verification preserves it while mutation and deletion fail tree identity. |
| M18 | Both source-tree authorities remain | Build a package fixture where archive tree and Gitlink-reconstructed tree differ. Prove success with both exact values, then independently corrupt each expected SHA and observe the corresponding failure. The pre-existing direct compute test alone does not prove `verify` invokes both. |
| B1 | Valid generated boundary retained | Keep `test_verify_projects_only_validated_generated_build_output`: real `.lake/build/**` passes and remains, while source/config/manifest and sibling/nested lookalikes fail. |
| B2 | Generated-boundary defenses retained | Keep symlink, file, FIFO, nested symlink/FIFO, hardlink, malformed `.lake`, and archive-owned `.lake/build` rejection tests. |
| C1 | Flag is explicit and non-parameterized | Parser bare mode is false and exact flag mode is true. `--remove-validated-generated-sidecars=value` and a trailing path/package/hash argument must raise `SystemExit`. |
| H1 | Warm order is unchanged | Fake materialization creates target; fake build creates the exact sidecar. Calls remain materialize, flagged verify, dependencies, build, flagged verify. The second verify removes it before inventory. |
| H2 | Successful publication omits only sidecar | Snapshot and registered private seed omit the sidecar, retain `fixture/.lake/build/Fixture.olean`, pass `is_ready(deep=True)`, and match the manifest inventory exactly. Direct path absence/presence assertions are mandatory because inventory is aggregate. |
| H3 | Absence is negatively inventory-bound | Inject the sidecar into a writable snapshot and require deep readiness to fail. Inject it into a seeded destination and require destination validation to fail. |
| H4 | Failure publishes no READY | Fresh-runtime subtests for malformed sidecar and exact sidecar plus package-source drift must fail at final package verification, create no snapshot, leave `runtime.rglob("READY")` empty, and retain one failure directory with `failure.json` and no READY. |
| H5 | Key binds code, argv, and recipe version | Dirty uncommitted materializer bytes do not change committed identity; committing them does. With one main commit, changing only verifier argv or only recipe version changes the key. |
| H6 | Canonical recipe surface is exact | Assert exact package materialize argv, exact flagged verify argv, canonical recipe version 5, build-recipe schema 3, no new serialized field/phase, and materializer/pins remain identity files. The flagged verifier must occupy both existing call positions. |

## Fixture and helper recommendations

Use the existing synthetic eight-package archive fixture rather than a production archive or network acquisition. Add proofwidgets target, trace, `package.json`, and optionally one `.lean` member only for proofwidgets. Keep its synthetic revision. Patch `GENERATED_SIDECAR_CONTRACTS` to a test tuple keyed to that revision and `sha256(FIXTURE_WIDGET_TARGET)`.

The minimum reusable helpers are:

- proofwidgets package/root accessors;
- one fixture `GeneratedSidecarContract` constructor;
- one context manager patching the immutable contract tuple;
- exact sidecar writer;
- fixture-archive replacement that reruns archive inspection, writes entries, recomputes both tree identities, and updates the in-memory/file pin;
- recursive package observation for the absent/pure cases;
- fresh/rematerialized package setup per destructive subtest.

Use the existing `_generated_sidecar_phase` module-private seam for deterministic races. The hook should remain non-caller-controlled and accept only a fixed phase name. Closures in tests can use known fixture paths. Use same-content replacement inodes so identity checks, rather than payload checks, decide the result.

Patch `os.fsync` with `wraps=os.fsync` in the exact-success case and record the descriptor identity. The phase ordering alone does not prove that `fsync` occurred.

In hot-cache tests, make the fake verifier recognize only the exact flagged argv. It should authenticate/remove the exact fake sidecar before checking the source marker, so the drift case mirrors real cleanup-then-tree-failure semantics. A near-match verifier command should return nonzero rather than fall through as success.

## Observed implementation disposition

The implementation changed concurrently while this read-only scout was active. No change was authored or requested by this scout.

At final capture:

- Exact compiled-in `GeneratedSidecarContract` support was present.
- Contract canonical-path hardening using `PurePosixPath(...).as_posix()` was present at lines 354-355, addressing the repeated-separator/dot-component gap reported by this scout.
- Exact archive target/sidecar provenance checks were present.
- Descriptor-bound target/sidecar validation, exact bytes, metadata checks, unlink, parent `fsync`, absence check, and incarnation rechecks were present.
- Bare `verify` defaulted to read-only; explicit flagged mode and deterministic removal evidence were present.
- Canonical recipe version was 5 and `BUILD_RECIPE_SCHEMA_VERSION` remained 3.
- The canonical verifier argv carried the explicit flag without a new phase/field.
- All six named materializer test methods were present and additional hot-cache test edits were in progress.
- No test result is claimed by this scout; running tests was prohibited for this session.

Final concurrent diff summary:

```text
 scripts/hot_main_cache.py                  |   3 +-
 scripts/materialize_lake_packages.py       | 407 +++++++++++++++++++++--
 tests/test_hot_main_cache.py               |  32 +-
 tests/test_lake_package_materialization.py | 506 +++++++++++++++++++++++++++++
 4 files changed, 925 insertions(+), 23 deletions(-)
```

## Exact read-only command record

Commands were executed with working directory
`/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-025-sidecar-a01`.
Parallel invocations below were separate shell commands.

```text
pwd && wc -l AGENTS.md && sed -n '1,260p' AGENTS.md
wc -l workflow/reviews/qpbt-024-postintegration-warm-failure-9b6.md
wc -l workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md
wc -l workflow/reviews/qpbt-024-sidecar-security-a12.md
wc -l workflow/reviews/qpbt-024-sidecar-synthesis-a14.md
wc -l workflow/reviews/qpbt-024-sidecar-hooks-a15.md
wc -l workflow/reviews/qpbt-024-sidecar-tests-a16.md
wc -l tests/test_lake_package_materialization.py
wc -l tests/test_hot_main_cache.py
wc -l scripts/lake_package_materialization.py
wc -l scripts/hot_main_cache.py
rg --files scripts tests | rg 'lake.*package|material|hot_main_cache'
nl -ba workflow/reviews/qpbt-024-postintegration-warm-failure-9b6.md
nl -ba workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md
nl -ba workflow/reviews/qpbt-024-sidecar-security-a12.md
nl -ba workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md | sed -n '180,320p'
nl -ba workflow/reviews/qpbt-024-sidecar-security-a12.md | sed -n '1,180p'
nl -ba workflow/reviews/qpbt-024-sidecar-security-a12.md | sed -n '181,360p'
nl -ba workflow/reviews/qpbt-024-sidecar-synthesis-a14.md | sed -n '1,190p'
nl -ba workflow/reviews/qpbt-024-sidecar-hooks-a15.md | sed -n '1,160p'
nl -ba workflow/reviews/qpbt-024-sidecar-tests-a16.md | sed -n '1,140p'
nl -ba workflow/reviews/qpbt-024-sidecar-synthesis-a14.md | sed -n '191,380p'
nl -ba workflow/reviews/qpbt-024-sidecar-hooks-a15.md | sed -n '161,330p'
nl -ba workflow/reviews/qpbt-024-sidecar-tests-a16.md | sed -n '141,300p'
git status --short --branch
rg -n 'QPBT-025|qpbt-025' workflow research protocols tests scripts
nl -ba workflow/state/issues.json | sed -n '870,950p'
rg -n '^(class |    def test_|    def _|def |[A-Z][A-Z0-9_]+\s*=)' tests/test_lake_package_materialization.py
rg -n '^(class |    def test_|    def _|def |[A-Z][A-Z0-9_]+\s*=)' tests/test_hot_main_cache.py
rg -n '^(class |def |[A-Z][A-Z0-9_]+\s*=)' scripts/materialize_lake_packages.py
rg -n '^(class |def |[A-Z][A-Z0-9_]+\s*=)' scripts/hot_main_cache.py
nl -ba tests/test_lake_package_materialization.py | sed -n '1,180p'
nl -ba tests/test_lake_package_materialization.py | sed -n '181,380p'
nl -ba tests/test_lake_package_materialization.py | sed -n '381,570p'
nl -ba tests/test_lake_package_materialization.py | sed -n '570,720p'
nl -ba scripts/materialize_lake_packages.py | sed -n '1,330p'
nl -ba scripts/materialize_lake_packages.py | sed -n '326,660p'
nl -ba scripts/materialize_lake_packages.py | sed -n '748,1080p'
nl -ba scripts/materialize_lake_packages.py | sed -n '350,650p'
nl -ba scripts/materialize_lake_packages.py | sed -n '1180,1295p'
nl -ba scripts/materialize_lake_packages.py | sed -n '1900,1980p'
nl -ba scripts/materialize_lake_packages.py | sed -n '2080,2160p'
nl -ba tests/test_hot_main_cache.py | sed -n '1,275p'
nl -ba tests/test_hot_main_cache.py | sed -n '312,670p'
nl -ba tests/test_hot_main_cache.py | sed -n '1330,1510p'
nl -ba scripts/hot_main_cache.py | sed -n '105,240p'
nl -ba scripts/hot_main_cache.py | sed -n '240,350p'
nl -ba scripts/hot_main_cache.py | sed -n '1360,1430p'
nl -ba scripts/hot_main_cache.py | sed -n '1770,1850p'
nl -ba scripts/hot_main_cache.py | sed -n '1849,2210p'
nl -ba scripts/hot_main_cache.py | sed -n '2290,2455p'
nl -ba tests/test_hot_main_cache.py | sed -n '658,715p'
nl -ba tests/test_hot_main_cache.py | sed -n '1450,1505p'
nl -ba workflow/reviews/qpbt-024-sidecar-synthesis-a14.md | sed -n '139,180p'
nl -ba workflow/state/issues.json | sed -n '894,903p'
nl -ba references/lake-packages.json | sed -n '118,172p'
nl -ba scripts/hot_main_cache.py | sed -n '2204,2288p'
git diff -- scripts/materialize_lake_packages.py
git diff -- scripts/hot_main_cache.py
rg -n 'GeneratedSidecarContract|GENERATED_SIDECAR_CONTRACTS|def _generated_sidecar_contract_for|def _validate_generated_sidecar_archive_contract|def _generated_sidecar_phase|def _validate_generated_sidecar_metadata|class _PreparedPackageSource|def _remove_generated_sidecar|def _prepared_package_source|def verify|remove-validated-generated-sidecars' scripts/materialize_lake_packages.py
rg -n 'CANONICAL_BUILD_RECIPE|version=5|remove-validated-generated-sidecars|def artifact_inventory|def is_ready|def warm|def _validate_seeded_destination|def seed' scripts/hot_main_cache.py
rg -n 'def make_archive|class LakePackage|def _materialize|test_publish_verify|test_verify_projects|test_verify_rejects_malformed|test_archive_generated|test_exact_gitlink' tests/test_lake_package_materialization.py
rg -n 'PACKAGE_MATERIALIZING_TEST_RECIPE|def fake_success|test_packages_are_identity|test_warm_rejects_post_build_package_drift|test_canonical_lake_commands|test_recipe_is_bound|test_seed_deeply' tests/test_hot_main_cache.py
git diff -- tests/test_lake_package_materialization.py
git diff -- tests/test_hot_main_cache.py
git status --short --branch
git diff --name-only
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
date --iso-8601=ns
git diff --stat
rg -n 'PurePosixPath\(contract\.(target|sidecar)\)\.as_posix|version=5|BUILD_RECIPE_SCHEMA_VERSION|test_proofwidgets_sidecar|test_packages_are_identity|test_warm_rejects_post_build_package_drift' scripts/materialize_lake_packages.py scripts/hot_main_cache.py tests/test_lake_package_materialization.py tests/test_hot_main_cache.py
rg -n -C 12 'LPR-015|issue/qpbt-025-sidecar-a01|45d2fe657af587e8e10952aced2e156d349fd65e' workflow/state/prs.json workflow/state/sessions.json workflow/events.jsonl
git show -s --format='%H%n%T%n%P%n%cI%n%s' HEAD
git rev-parse '9c9b49548fabdd6b01916787d7dc17a4bca36513^{tree}'
```

The `wc -l scripts/lake_package_materialization.py` probe returned not found; `rg --files` immediately resolved the actual owned materializer as `scripts/materialize_lake_packages.py`. This was read-only and changed nothing.

## Activity accounting

```json
{
  "repository_edits": 0,
  "canonical_state_edits": 0,
  "implementation_edits": 0,
  "tests_executed": 0,
  "builds": 0,
  "cache_warms": 0,
  "cache_seeds": 0,
  "lean_commands": 0,
  "lake_commands": 0,
  "network_operations": 0,
  "runtime_mutations": 0,
  "cache_mutations": 0,
  "subagents": 0,
  "temporary_evidence_files_authored": 1
}
```

The sole authored file is this requested report under `/tmp`; it is outside the repository and runtime/cache trees.

## Final Git status

```text
## issue/qpbt-025-sidecar-a01
 M scripts/hot_main_cache.py
 M scripts/materialize_lake_packages.py
 M tests/test_hot_main_cache.py
 M tests/test_lake_package_materialization.py
```

These four modifications were made concurrently by the owning orchestrator/implementation session. This scout made zero repository edits and did not stage, commit, restore, or otherwise modify them.
