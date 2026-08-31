# QPBT-024 source-projection implementation report (a01)

## Outcome

Implemented and committed the bounded package-source projection repair on the
exact governed branch. Post-build verification now excludes only a validated
package-root `.lake/build` subtree. Archive materialization remains a full-tree
identity check, archives containing `.lake/build` are rejected structurally,
and all paths outside the exact generated subtree remain authenticated.

The validation boundary rejects non-directory `.lake` or `.lake/build`
boundaries, symlinks and special objects below `.lake/build`, and regular files
with multiple hard links. Gitlink reconstruction is unchanged. The hot-cache
order remains `materialize -> verify -> deps -> build -> verify`; generated
package output remains in the published `.lake` inventory, while post-build
source drift still fails with no READY snapshot.

No recipe version, hot-cache production code, protocol, changelog, canonical
state, metrics, runtime/cache, reference, Lean, or blueprint file changed.

## Exact Git identity

- Branch: `issue/qpbt-024-postbuild-a01`
- Base/parent: `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe`
- Head: `9c9b49548fabdd6b01916787d7dc17a4bca36513`
- Tree: `a7409faf8cbd888e3f04d114332f202ea1436d11`
- Commit subject: `fix(cache): project package build output from source identity`
- Worktree after commit: clean
- Diff: 3 files, 197 insertions, 3 deletions

Changed blobs:

```text
a8380456ca97130cbc81be734f7ff9a3ecd2a128  scripts/materialize_lake_packages.py
9e6a5532d6898075b1379f9e58b7b9d7fb13be68  tests/test_hot_main_cache.py
a757022254e391bf05e25757bc433140e2abc6df  tests/test_lake_package_materialization.py
```

Changed-file SHA-256:

```text
3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243  scripts/materialize_lake_packages.py
235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe  tests/test_hot_main_cache.py
d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d  tests/test_lake_package_materialization.py
```

`git diff --name-status <base>..HEAD`:

```text
M  scripts/materialize_lake_packages.py
M  tests/test_hot_main_cache.py
M  tests/test_lake_package_materialization.py
```

## Validation on exact candidate

- Focused materializer: `python3 -m unittest discover -s tests -p 'test_lake_package_materialization.py' -v`; 28 tests, PASS, 55.801 seconds.
- Focused hot cache: `python3 -m unittest discover -s tests -p 'test_hot_main_cache.py' -v`; 46 tests, PASS, 11.554 seconds.
- Full serial aggregate: `python3 -m unittest discover -s tests -p 'test_*.py' -v`; 306 tests, PASS, 80.303 seconds.
- Workflow checker: `python3 scripts/check_workflow.py`; embedded 306 tests, PASS, 81.780 seconds; workflow state valid.
- Python compilation: `python3 -m compileall -q scripts tests`; PASS.
- Workflow validation: `python3 scripts/workflow.py validate`; PASS; 25 issues, 13 pull requests, 0 planned sessions, 279 issued sessions, 7 stages.
- Diff hygiene: `git diff --check` before commit and `git diff --check <base>..HEAD` after commit; PASS.
- Exact identity/name-status/stat/status checks: PASS; parent equals the required base and only the three owned files changed.
- Lean/Lake/build/warm/seed/network/shared-cache actions: 0.

Development attempts were recorded rather than hidden: one initial invalid
Python module-style focused command failed because `tests` is not a package;
one focused materializer run failed after adding a FIFO-boundary regression
because the assertion expected the later boundary diagnostic while the existing
whole-tree scan correctly rejected the FIFO earlier as a special file. The
assertion was narrowed to accept either fail-closed diagnostic. All final exact
candidate gates above passed. An initial non-escalated commit attempt failed
because the linked-worktree Git index is under the managed read-only `.git`
area; the approved narrow Git operation then committed only the owned paths.

Observed test/compile command counts across implementation, including
development reruns: 5 full focused materializer invocations (one was a
three-test targeted invocation), 3 focused hot-cache invocations, 2 full serial
aggregates, 2 workflow-checker invocations, and 2 compileall invocations.
There were 0 Lean/Lake compilation attempts and 0 hot-cache operations.

## Regression coverage

- Accept representative mode-0600 and ordinary files under exact root
  `.lake/build/lib/lean` and `.lake/build/ir`.
- Reject source, `lakefile.toml`, and `lake-manifest.json` drift while generated
  output exists.
- Reject exact-scope lookalikes `.lake/not-build`, `.lake/build-sibling`, and
  `src/.lake/build`.
- Reject `.lake`/`.lake/build` file or symlink boundaries, FIFO boundaries and
  descendants, symlink descendants, and multiply-linked generated files.
- Reject authenticated archives that supply `.lake/build`.
- Preserve explicit `160000` Gitlink reconstruction under projection and
  distinguish changed Gitlink SHAs.
- Preserve package materialize/verify/Lake/verify call order, generated artifact
  survival in the READY snapshot inventory, and no-READY behavior for source
  drift.

## Scout inspection and disposition

Topology: root coordinator -> this writable orchestrator -> two parallel
read-only scouts; 2 subagents, one parent/child edge per scout, maximum depth 1
below this session. Neither scout spawned children.

- `i024-scout-a02-regression-matrix`, external collaboration ID
  `/root/i024_orchestrator_a01_source_projection/i024_scout_a02_regression_matrix`:
  inspected and accepted. Its exact-scope matrix caused explicit regressions for
  `lake-manifest.json`, `.lake/build-sibling`, and `src/.lake/build`; all pass.
  Report `/tmp/qpbt-024-regression-matrix-a02.md`, SHA-256
  `2997a94dd93733bbd699393828e619bdd29366decb6a4c9c7c785be5eef6ebdc`.
- `i024-scout-a03-protocol-scope`, external collaboration ID
  `/root/i024_orchestrator_a01_source_projection/i024_scout_a03_protocol_scope`:
  inspected and accepted. The bounded repair is an implementation correction,
  not a normative protocol change; no protocol/changelog edit or separate
  protocol review is required. Fresh immutable code review remains required.
  Report `/tmp/qpbt-024-protocol-scope-a03.md`, SHA-256
  `caad36e3d544878e52733100b5f66e1dcc87ad25800f3b02dee8a26e41ef4917`.

## Accounting

- Governed session: `i024-orchestrator-a01-source-projection`
- Accounting window start: `2026-09-01T00:00:14.241701906+08:00` (first child-observed timestamp)
- Commit time: `2026-09-01T00:17:01+08:00`
- Evidence cutoff: `2026-09-01T00:17:36.334716392+08:00`
- Elapsed through evidence cutoff: 1042.093014486 seconds
- Owned repository files edited: 3; committed files: 3; unauthorized repository edits: 0
- Subagents: 2, both read-only and completed; scout repository edits/tests/build/network/cache actions: 0
- Token usage: JSON `null`; availability reason: the collaboration backend does not expose per-agent token usage. No estimate was made.
- Statement-integrity table: not applicable; no paper-labelled Lean theorem or mathematical statement changed.
- Report SHA-256: supplied out of band after finalization because embedding the report's own ordinary digest would change it.
