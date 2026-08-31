# QPBT-024 generated hash-sidecar security design (a12)

Logical session: `i024-scout-a12-sidecar-security`
Integrated main: `9c9b49548fabdd6b01916787d7dc17a4bca36513`
Failed cache key: `9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36`

## Verdict

**Recommend strict validation followed by pre-publication removal of one
exact, source-derived, revision-bound generated sidecar.** Do not project the
path out while retaining it, and do not introduce a generic `*.hash` exclusion.

The smallest secure implementation is confined to
`scripts/materialize_lake_packages.py` plus its focused and hot-cache tests.
Keep the existing full source-tree comparison after cleanup. The accepted
sidecar contract should be keyed to exact package `proofwidgets`, revision
`6e311e2a844da9b2cc3971187df2fe0066947b93`, source target
`widget/package-lock.json`, and generated path
`widget/package-lock.json.hash`. Require the source target to remain the exact
authenticated archive file, require the sidecar to be the exact regular
single-link 16-byte lowercase Lake hash `179e66574f04806e`, then unlink the
sidecar through a bound parent descriptor before computing both pinned Git
trees. The published cache and every seed must contain no such sidecar.

This avoids publishing active metadata that Lake trusts by default. It also
preserves detection of every source/config mutation and every legitimate
archive-owned `.hash` file.

## Authenticated failure and archive evidence

The retained failure directory is:

```text
/home/drx/MIPStarRE-auto/.workflow-runtime/cache/failures/
  9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36-20260901T010852-2/
```

- `failure.json`: 3,247 bytes, regular, one link, SHA-256
  `a97fa0f97189d1e704808d1ea5e0aa209d269d915b6c5b293b7e117f9d536c48`.
- `build.log`: 39,195 bytes, regular, one link, SHA-256
  `ed0f4d6e2f05f52e175723aac2d69b60230b50962c706c67098d81c665e1fe45`.
- Matching raw metric-line SHA-256:
  `9ce27db86209c0e33b0b80f79d641d72a123ef74b105970d0c37e75be7aa7689`.
- Metric: one miss, one build, no lock wait, `build_seconds: 643.111606`,
  `elapsed_seconds: 650.317818`, terminal `result: failed`.
- The log records initial package verification, then `Build completed
  successfully (8992 jobs).`, then `materialized archive tree differs for
  proofwidgets`. No `READY` was published.

The exact proofwidgets archive is a regular one-link 3,896,457-byte file with
SHA-256
`dffb4652003f31f8e393e0f2887526ec4b6cc8244b960afa8dcbc1918b020c68`.
This matches `references/lake-packages.json`, which binds revision
`6e311e2...`, tar SHA-256
`f3d97bdf80e98ff87475a7fa97ef1e9802eba27300ba7d121ab8e4c02718ba11`,
111 regular files, no symlinks, inventory SHA-256
`b001b475d24f2bfe99e9d1d75fbcb3b18622f8fb3d085377a42135bcca766ca2`,
and archive/Git tree `bec90bac5dd8afade168e76c5b508482f9043b26`.

Authenticated members relevant to the sidecar are:

| Member | Archive status | SHA-256 / fact |
|---|---|---|
| `lakefile.lean` | present | `0a319fffbf511dab4c3307dc105f8e8fdb4f6160020995cef5f442061cc0abca` |
| `widget/package.json` | present | `92389771927d5841d9ef85e021888e1aca6a077f8398e41d7f788ea41e6d82fc` |
| `widget/package-lock.json` | present, 172,140 bytes | `3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d` |
| `widget/package-lock.json.trace` | present, 1,182 bytes | `154a4f212697184548830b6bcca3fab192d93b6af145c64cd0ee9c996158fe1d` |
| `widget/package-lock.json.hash` | absent | not archive source |

The authenticated trace has `outputs: "179e66574f04806e.art"`. Lake's artifact
descriptor names its content hash before `.art`, so the expected cached file
hash is `179e66574f04806e`. None of the eight current pinned package archives
contains a path ending in `.hash`; this is current evidence, not a license to
ignore such files in future archives.

### Evidentiary boundary

Warm failure cleanup intentionally removed staging and retained only the log
and failure envelope. The log does not print an observed tree SHA or a path
diff. Therefore the retained failure alone proves the first mismatching package
was proofwidgets, but not that this sidecar was the sole changed path or what
its bytes were. The sidecar attribution is a strong source-derived causal
inference from three independent authenticated facts: it is absent from the
archive, the pinned lakefile fetches `package-lock.json` through
`buildFileAfterDep`, and pinned Lake writes exactly the adjacent `.hash` file.
Acceptance tests must reproduce the path; canonical history must not claim the
deleted staging file was directly observed.

## Lake 4.32.0 semantics

The project pins `leanprover/lean4:v4.32.0`. The installed matching source is
under
`/home/drx/.elan/toolchains/leanprover--lean4---v4.32.0/src/lean/lake/`.
Relevant source hashes are:

```text
Lake/Build/Common.lean       405af4398143b2c6917d6e6ba93016852a8c109a63c889f98fc043e05084c145
Lake/Build/Trace.lean        c763e3166a1c12874bd550731333769ff185f8ca02e8d52cbc202c933d5c424b
Lake/Build/Context.lean      6ef3b48c7c40c00530f57eeab7c236fe70493294aef216dd703f2dfc5dc28a9c
Lake/Load/Materialize.lean   3b031d66f31afb202a8022cfbae05ac402f39d7f92831e85f7057c360ed9439c
Lake/CLI/Main.lean           4b95ab56b87319c0a1e2b55d0d31e3c077977a376020c326579d0802b9399010
```

The exact chain is:

1. ProofWidgets `lakefile.lean:33-37` defines `widgetPackageLock` with
   `buildFileAfterDep (text := true)` for `widget/package-lock.json`.
2. Lake `Build/Common.lean:759-766` routes that target through
   `buildArtifactUnlessUpToDate`.
3. `computeArtifact` at `:634-637` calls `fetchFileHash`.
4. `fetchFileHash` at `:401-409` names `<file>.hash`; if default
   `trustHash` is true and `Hash.load?` succeeds, it returns the sidecar without
   reading the target. Otherwise it computes the target hash and writes the
   sidecar.
5. `Hash.load?` at `Build/Trace.lean:139-156` accepts exactly 16 hexadecimal
   digits. Lake writes the lowercase 16-digit `Hash.toString` form.
6. `BuildConfig.trustHash` defaults to true at
   `Build/Context.lean:16-23`; only `--rehash`/`-H` changes it to false.
7. Lake itself warns at `Load/Materialize.lean:42-46` that leftover `.hash`
   files are trusted unconditionally and can cause incorrect trace
   computations; Git dependency updates clean such files for that reason.

Thus a parseable retained sidecar is executable build-control metadata, not an
inert generated file. Manifest inventory binding protects its bytes in the
immutable hot cache, but seed deliberately makes the copy writable and Lake
will trust the copied value. Inventory binding is not a substitute for removing
this trust-bearing file.

## Design comparison

| Design | Source mutation detection | Seed/trust safety | Archive `.hash` compatibility | Verdict |
|---|---|---|---|---|
| Exclude only `widget/package-lock.json.hash`, retain it | All other paths remain checked, but this path is unchecked | Bad: arbitrary/stale parseable content is published and trusted | Exact path becomes an implicit permanent exception | **Reject** |
| Project every `*.hash` | Mutations/deletions of archive-owned hash files become invisible | Bad: all attacker-created sidecars persist | Bad by construction | **Reject** |
| Validate sidecar shape/content, retain it | Good if recomputation is exact | Better initially, but needlessly seeds trusted mutable metadata and is brittle across Lake hash semantics | Requires complicated source/generated classification | **Reject as standalone** |
| Reconstruct/overlay all source from archives | Can be strong if comparison precedes replacement | Strong if generated trust files are omitted | Strong | Secure but too large and risks silently repairing rather than reporting drift |
| Strictly validate then remove only the exact revision-bound new sidecar | Full pinned tree check runs after removal | Strong: no trusted sidecar is published or seeded | Unrelated and future archive-owned `.hash` files remain source | **Recommend** |

### Unsafe-option details

Fixed-path exclusion solves only the tree mismatch. It does not solve the
security problem because the excluded file survives into the READY inventory
and private seed. A malicious but syntactically valid 16-hex value passes
Lake's loader and controls the trace without target recomputation.

Generic `*.hash` projection is strictly worse. A future archive may legitimately
track `foo.hash`; pre-Lake full-tree verification would authenticate it, but
post-build projection would stop detecting its mutation or deletion. The
current absence of archive hash files cannot become a global schema rule.

Validation without removal depends on correctly reproducing Lake's
non-cryptographic `Hash.ofText` behavior and still exports trust-bearing state.
The authenticated trace gives an exact value for this revision, but retaining
it gains nothing: Lake cheaply regenerates it when missing.

An archive-derived overlay is a reasonable future generalization if distinct
packages repeatedly generate source-adjacent metadata. For this one exact
sidecar it adds archive reacquisition, path-set reconciliation, replacement,
and additional race boundaries. It can also hide a build-time source mutation
by repairing it unless the comparison is separately fail-closed. It is not the
smallest sufficient correction.

## Recommended implementation

Add an internal immutable contract in `scripts/materialize_lake_packages.py`,
bound to exact package name and revision. It should include:

```text
package       proofwidgets
revision      6e311e2a844da9b2cc3971187df2fe0066947b93
target        widget/package-lock.json
target_sha256 3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d
sidecar       widget/package-lock.json.hash
lake_hash     179e66574f04806e
```

At archive inspection/materialization, require the target to be the pinned
regular member with the exact SHA-256 and require the declared generated
sidecar to be absent. This is what makes later removal apply only to a newly
generated path. A future revision that legitimately archives that path must
have no generated-sidecar contract until separately reviewed; its `.hash` then
remains ordinary authenticated source.

During each `verify` call, before `compute_source_tree_sha`:

1. Bind the package and sidecar parent directories without following symlinks;
   recheck the package-root incarnation through the existing layout binding.
2. If the sidecar is absent, continue. This is the expected pre-Lake case.
3. If present, require the target and sidecar to be regular, non-symlink files
   with `st_nlink == 1`; require the target SHA-256 above.
4. Open the sidecar descriptor-relative with `O_NOFOLLOW`, compare `fstat` to
   `lstat`, read at most 17 bytes, and require exactly the lowercase ASCII bytes
   `179e66574f04806e` with no newline.
5. Recheck name/inode identity immediately before descriptor-relative unlink;
   unlink only that exact entry, fsync its parent, and require the name absent.
   Any swap, symlink, special object, hardlink, malformed content, or identity
   mismatch fails closed.
6. Run the existing `_scan_tree` and both exact `compute_source_tree_sha`
   comparisons. These checks must still fail on package-lock, lakefile,
   manifest, Lean source, symlink target/mode, Gitlink, or any other path drift.
7. Return/log the removed package/path as explicit evidence. Do not remove an
   undeclared `.hash` path.

The sidecar is removed before `HotMainCache` computes the whole `.lake`
artifact inventory. Package-local `.lake/build/**` remains intact and is bound
by that inventory; only the source-adjacent trust sidecar is absent. A seeded
worktree therefore begins without stale trust metadata. Its next Lake command
recomputes the sidecar from the authenticated target.

The verifier is already invoked before Lake and after the full build. The same
argv can remain: the first call is a no-op sanitizer plus verification, and the
second validates/removes the generated file then verifies. Do not add a broad
cleanup command and do not weaken or move the second verification.

`scripts/materialize_lake_packages.py` is already an
`additional_identity_file` in canonical recipe version 4, and the exact main
commit is also in the key. Changing its bytes necessarily produces a new cache
key. No `scripts/hot_main_cache.py` edit or recipe-version bump is needed merely
to force identity churn. If a separate sanitize subcommand is chosen instead,
its exact argv must be added to `BuildRecipe.identity_payload` and it must run
after every Lake phase; that is larger than necessary and is not recommended.

### TOCTOU boundary

Descriptor-relative no-follow checks close symlink traversal and ordinary name
replacement around the cleanup. A same-UID adversary racing the staging tree
can never be completely excluded by path validation followed by unlink and Git
hashing; full closure would require a private descriptor-only tree walker or a
fresh immutable copy. The hot-cache design already relies on a private staging
directory and sequential child completion. Within that trust model, bind and
recheck directory incarnations before/after cleanup and again after tree
computation. Any observed swap fails with no READY. Do not claim protection
against an actively racing process with equal filesystem authority.

## Exact owned files

Implementation ownership should be limited to:

```text
scripts/materialize_lake_packages.py
tests/test_lake_package_materialization.py
tests/test_hot_main_cache.py
```

Do not edit `references/lake-packages.json`: the exact sidecar contract is tied
to the already authenticated package/revision and is identity-bound through the
materializer script. Do not edit `scripts/hot_main_cache.py` or broaden the
recipe. Root-owned issue/incident/session metrics are separate coordinator
work, not implementation ownership. If the verifier's new cleanup behavior is
deemed a normative protocol revision, delegate a disjoint documentation change
and independent protocol review rather than expanding this proof repair
silently.

## Acceptance tests

Add focused tests with these exact properties:

1. The pinned proofwidgets archive has the exact hash/size/tree facts above,
   contains target and trace, derives trace output `179e66574f04806e.art`, and
   contains no declared sidecar.
2. A regular one-link exact sidecar is removed; verification succeeds; target
   bytes and mode are unchanged; the removed path is reported.
3. The same call before Lake, with no sidecar, is read-only and succeeds.
4. Valid-looking but wrong 16-hex content, uppercase content, short/long
   content, newline, and non-hex content each fail closed rather than being
   removed as legitimate.
5. Sidecar symlink, directory, FIFO/socket, and multiply-linked regular file
   fail. The symlink target and hardlink peer remain unchanged.
6. Target symlink, special file, hardlink, wrong size/content, or inode swap
   fails before cleanup.
7. Inject swaps at parent bind, open/fstat, pre-unlink identity recheck, and
   post-unlink/package-root recheck; every case is confined and publishes no
   external write.
8. Mutate `package-lock.json`, `package.json`, lakefile, manifest, or a Lean
   source while supplying an otherwise exact sidecar; cleanup may occur, but
   the subsequent pinned tree comparison must fail.
9. Add an undeclared live `other.hash`; verification fails tree identity and
   does not remove it.
10. Put a legitimate `.hash` member in an authenticated fixture archive; it is
    preserved and its mutation/deletion fails. Put the declared sidecar path in
    the declared generated contract's archive; archive inspection rejects the
    contradictory provenance.
11. Preserve all `.lake/build` boundary tests: real generated output accepted;
    symlink/special/hardlink boundary rejected; archive `.lake/build` rejected.
12. Hot-cache fake build creates the exact proofwidgets sidecar. The ordered
    materialize/verify/deps/build/verify sequence succeeds, the snapshot and
    seeded copy omit the sidecar, generated `.lake/build` artifacts remain, and
    deep inventory matches.
13. Hot-cache fake build creates malformed/stale sidecar content or mutates
    source beside an exact sidecar. Warm fails, retains evidence, and publishes
    no READY.
14. Changing the generated-sidecar contract changes the cache key through the
    materializer identity input; canonical command arrays and recipe version 4
    remain exact.

Required validation after implementation, not run by this scout:

```text
python3 -m unittest discover -s tests -p test_lake_package_materialization.py -v
python3 -m unittest discover -s tests -p test_hot_main_cache.py -v
python3 -m unittest discover -s tests -v
python3 scripts/check_workflow.py
python3 -m compileall -q scripts tests
python3 scripts/workflow.py validate
git diff --check <exact-base>..<exact-head>
```

After fresh immutable review and faithful integration, only one newly
authorized changed-hypothesis authenticated warm may be attempted. Failure is
retained and diagnosed; it does not authorize an unchanged retry.

## Session accounting

- Start: `2026-09-01T01:19:50.258550528+08:00`.
- End: `2026-09-01T01:36:49.565887819+08:00`.
- Elapsed: `1019.307337284` seconds, agent-measured from the timestamps above.
- Topology: one independent read-only security designer, `0` subagents.
- Token usage: JSON `null`.
- Token availability reason: collaboration backend does not expose per-agent
  token usage; no estimate was made.
- Tests, builds, Lean, Lake, warm, seed, network, Git writes, repository/state
  edits, and cache/runtime mutations: `0` each.
- Read-only evidence operations: committed sources/tests/pins, authenticated
  local archive bytes, installed pinned Lake source, and retained failure/log/
  metric records.
- Authored output: this `/tmp` report only. SHA-256 is reported out of band.
