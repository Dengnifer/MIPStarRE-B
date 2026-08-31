# QPBT-018 plausible tree-drift diagnosis (a15)

## Verdict

The warm failure is deterministic verifier-domain drift, not source drift and not a failed
Lean build.  The first package verification passed on the exact archive tree.  The dependency
command

```text
lake --packages=.lake/package-overrides.json exe cache get
```

then restored 13 cached `plausible` modules into the package-local generated-output subtree
`.lake/packages/plausible/.lake/build/`.  `materialize_lake_packages.py verify` subsequently
ran `git add --all --force` over the *entire* package directory, so those expected build outputs
became 169 added Git-tree entries.  It compared that post-cache source-plus-build tree against
the archive-only pin `b477789560b0cd76cf3177b9cffa3aaa5cd54e6b` and failed at the first
package, `plausible`.

The full build itself succeeded (`8992 jobs`).  It did not repair or cause the mismatch; the
cache-get command had already populated the differing subtree.  The build then reused those
artifacts (there are no `Plausible` build jobs in the retained full-build portion).

## Exact differing paths and metadata

Relative to `.lake/packages/plausible`, the archive contains no `.lake` entry.  Cache-get adds
exactly the following Cartesian product of paths (13 modules times 13 files = 169 regular
files):

```text
M in {
  Plausible,
  Plausible/Arbitrary,
  Plausible/ArbitraryFueled,
  Plausible/Attr,
  Plausible/DeriveArbitrary,
  Plausible/DeriveShrinkable,
  Plausible/Functions,
  Plausible/Gen,
  Plausible/Random,
  Plausible/Sampleable,
  Plausible/Shrinkable,
  Plausible/Tactic,
  Plausible/Testable
}

.lake/build/lib/lean/${M}.trace
.lake/build/lib/lean/${M}.olean
.lake/build/lib/lean/${M}.olean.server
.lake/build/lib/lean/${M}.olean.private
.lake/build/lib/lean/${M}.olean.hash
.lake/build/lib/lean/${M}.olean.server.hash
.lake/build/lib/lean/${M}.olean.private.hash
.lake/build/lib/lean/${M}.ilean
.lake/build/lib/lean/${M}.ilean.hash
.lake/build/lib/lean/${M}.ir
.lake/build/lib/lean/${M}.ir.hash
.lake/build/ir/${M}.c
.lake/build/ir/${M}.c.hash
```

The exact new directory set is:

```text
.lake/
.lake/build/
.lake/build/ir/
.lake/build/ir/Plausible/
.lake/build/lib/
.lake/build/lib/lean/
.lake/build/lib/lean/Plausible/
```

Disposable extraction of the exact 13 local cache archives used by cache-get observed:

- 169 regular files, 13,011,750 payload bytes, maximum file 1,286,120 bytes;
- every regular file had filesystem mode `0600` after `leantar` extraction;
- every generated directory had filesystem mode `0775`;
- Git normalized all 169 non-executable regular files to mode `100644`; directories are not
  Git-tree entries;
- the archive's 35 source entries were unchanged; the combined tree has 204 files;
- reconstructed combined Git tree: `2eca3812e4d4191ea6ccc0b64b1b98a952dec281`, which differs
  from pinned archive tree `b477789560b0cd76cf3177b9cffa3aaa5cd54e6b` solely by the 169
  entries above.

The path list was recovered both from the 13 `.ltar` member tables and from their disposable
extraction.  The failed staging checkout itself was removed by warm's failure cleanup, so this
reconstruction uses the exact retained cache archives that the log reports as already cached;
the pristine side comes from the authenticated pinned `plausible` tarball.

## Causal chain

1. `build.log:20` records exact package materialization; `build.log:21` records successful
   initial package verification.
2. `failure.json` binds the dependency command to `lake --packages=... exe cache get` and the
   post-build package command to `materialize_lake_packages.py verify`.
3. `build.log:65-68` records `8638` cache files decompressed successfully.
4. Pinned Mathlib cache code maps each dependency module to
   `<package source>/.lake/build/lib/lean` and `<package source>/.lake/build/ir`; the retained
   `.ltar` members name `.lake/packages/plausible/.lake/build/...` explicitly.
5. `build.log:406` records `Build completed successfully (8992 jobs)`.
6. `scripts/materialize_lake_packages.py:1876-1883` hashes the whole package source and compares
   it with `output.archive_tree_sha`; `compute_tree_sha` at lines 957-985 uses
   `git add --all --force` without a generated-output exclusion.
7. `build.log:407` therefore reports `materialized archive tree differs for plausible`.

This is an identity-boundary bug: `archive_tree_sha` is a source identity, while the second
verification feeds it source plus mutable build products.

## Smallest safety-preserving repair

Keep both pre-Lake and post-build verification.  Do not remove the second verify and do not
delete package build output before publication; either action would respectively lose tamper
detection or discard dependency artifacts from the hot snapshot.

In `scripts/materialize_lake_packages.py`, add a dedicated post-build source-tree computation
that excludes only the exact relative subtree `.lake/build` from the Git index.  Keep the
current full-tree computation during archive inspection/materialization, so the authenticated
archive remains checked byte-for-byte.  Before applying the post-build exclusion:

1. require that an acquired archive has no `.lake/build` entry (true for all eight pinned
   archives), making the source/generated boundary unambiguous;
2. if post-build `.lake/build` exists, require it to be a real directory and retain the existing
   special-file scan (preferably reject symlinks and multiply-linked regular files within this
   generated subtree too);
3. continue hashing every path outside `.lake/build`, including `lakefile.*`,
   `lake-manifest.json`, Lean sources, and any other `.lake/*` path;
4. continue the later hot-cache artifact inventory over the full root `.lake`, which binds the
   generated artifacts that are intentionally excluded from source identity.

This is smaller and safer than an unrestricted ignore rule: only the canonical Lake build
directory is projected out, and source/config drift remains fatal.

## Exact regressions

Add focused cases to `tests/test_lake_package_materialization.py`:

1. Materialize, add representative regular outputs under
   `plausible/.lake/build/lib/lean/` and `plausible/.lake/build/ir/` (including mode `0600`), and
   assert post-build `verify` succeeds.
2. In the same fixture, mutate an archived Lean/source/config file and assert `verify` still
   fails with tree drift.
3. Add a file under `.lake/not-build/` and assert it still fails; this proves the exclusion is
   exact, not `.lake`-wide.
4. Make `.lake/build` a symlink, or place a FIFO/symlink/hardlinked regular file beneath it, and
   assert fail-closed behavior.
5. Construct an input archive containing `.lake/build/...` and assert archive inspection rejects
   it before publication.
6. Preserve gitlink tests and verify that a gitlink/source mutation outside `.lake/build` still
   changes the computed source tree.

Add/extend `tests/test_hot_main_cache.py`:

7. In the dependency callback, create a package-local `.lake/build` artifact; require the two
   package-verification calls to remain ordered materialize -> verify -> deps -> build -> verify,
   and require warm publication to succeed.
8. Retain `test_warm_rejects_post_build_package_drift` with a mutation outside `.lake/build`;
   it must continue to fail and preserve the failure envelope.

Production acceptance after review should be one authorized warm of the exact new key, with
evidence for initial verify, cache-get, successful 8992-job build, successful post-build verify,
and a deep-ready published cache.  No warm/build/test was run by this scouting session.

## Session metrics

- Session: `i018-scout-a15-plausible-tree-drift`
- Role/topology: one read-only scout; 0 subagents; topology depth 0
- Started: `2026-08-31T23:32:44.292596125+08:00`
- Diagnosis cut: `2026-08-31T23:44:39.754559714+08:00`
- Elapsed through diagnosis: `715.462` seconds (agent measured)
- Tool calls including report write/check: 32 total (`functions.exec`: 31,
  `apply_patch`: 1)
- Shell command strings submitted: 120; network calls: 0; Lean calls: 0; Lake calls: 0;
  builds/tests/warm/seed/status: 0
- Disposable helpers: 2 `/tmp` directories; one standalone `leantar` extraction of 13 retained
  cache archives; repository/runtime/reference trees were not written
- Token usage: JSON `null`; availability reason: collaboration backend does not expose
  per-agent token usage
- Report SHA-256: reported externally because embedding a file's own SHA-256 would change it
