# QPBT-024 proofwidgets post-build sidecar forensic scout (a11)

## Verdict

**Confirmed, bounded cause.** The failed 9b6 warm completed all 8,992 build
jobs, then post-build verification rejected `proofwidgets`. The independently
authenticated same-revision retained package differs from its authenticated
archive by exactly one path outside `.git` and `.lake`:

```text
widget/package-lock.json.hash
```

It is a regular, singly linked, non-executable 16-byte file whose exact ASCII
content is `179e66574f04806e`. The authenticated archive contains the unchanged
tracked sibling `widget/package-lock.json.trace`; its `outputs` field is
`179e66574f04806e.art`. Installed Lake 4.32.0 source shows that
`buildArtifactUnlessUpToDate` reaches Lake's artifact/hash helpers for the
proofwidgets `widgetPackageLock` target. `fetchFileHash`, `Cache.saveArtifact`,
and artifact restoration all write the exact adjacent `.hash` form; the
observed retained path is therefore normal Lake metadata.

No analogous archive-absent path was found in the other seven retained pinned
packages. The secure smallest repair is an exact, pin-declared sidecar
allowlist with structural and content validation, followed by projection of
only that exact validated path from post-build source identity. Do not exclude
generic `*.hash` paths, and do not make verification delete build output.

## Failed envelope authentication

Failure directory:

```text
.workflow-runtime/cache/failures/
9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36-20260901T010852-2/
```

| Artifact | Type/mode | Bytes | SHA-256 |
|---|---:|---:|---|
| `failure.json` | regular `0600` | 3,247 | `a97fa0f97189d1e704808d1ea5e0aa209d269d915b6c5b293b7e117f9d536c48` |
| `build.log` | regular `0664` | 39,195 | `ed0f4d6e2f05f52e175723aac2d69b60230b50962c706c67098d81c665e1fe45` |

`failure.json` binds schema 3, exact key `9b6ccb...`, exact main
`9c9b49548fabdd6b01916787d7dc17a4bca36513`, exact changed materializer
SHA-256 `3325a1ad...`, failed time `2026-08-31T17:08:52.439761Z`, and exact error
`Lake package verification command failed with exit code 1`. It also binds the
authenticated Mathlib archive, commit, tree, and pack facts.

The 407-line build log records the bounded EXDEV fallback, successful initial
package verification, successful build completion (`8992 jobs`), then the
single terminal diagnostic:

```text
error: materialized archive tree differs for proofwidgets
```

The log's initial materialization facts bind proofwidgets archive tree
`bec90bac5dd8afade168e76c5b508482f9043b26`, output inventory
`b001b475d24f2bfe99e9d1d75fbcb3b18622f8fb3d085377a42135bcca766ca2`,
111 regular files, 18 archive directories including the root, and 9,603,230
regular bytes.

## Archive and retained package authentication

Pinned proofwidgets identity:

| Fact | Value |
|---|---|
| Revision | `6e311e2a844da9b2cc3971187df2fe0066947b93` |
| Git tree | `bec90bac5dd8afade168e76c5b508482f9043b26` |
| Compressed bytes | 3,896,457 |
| Compressed SHA-256 | `dffb4652003f31f8e393e0f2887526ec4b6cc8244b960afa8dcbc1918b020c68` |
| Tar bytes | 9,707,520 |
| Tar SHA-256 | `f3d97bdf80e98ff87475a7fa97ef1e9802eba27300ba7d121ab8e4c02718ba11` |
| Exact prefix | `ProofWidgets4-6e311e2a844da9b2cc3971187df2fe0066947b93/` |

The retained package at
`/home/drx/.cache/mipstarre-dev/hot-main/repo/.lake/packages/proofwidgets`
has exact HEAD `6e311e2...` and exact tree `bec90bac...`. Its tracked
`package-lock.json` and `.trace` SHA-256 values are byte-identical to the
authenticated archive:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `widget/package-lock.json` | 172,140 | `3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d` |
| `widget/package-lock.json.trace` | 1,182 | `154a4f212697184548830b6bcca3fab192d93b6af145c64cd0ee9c996158fe1d` |
| `widget/package-lock.json.hash` | 16 | `971a4e08a78d3b185902cde49867376deb03135a517d4380eb1cb6604cfcb38b` |

The sidecar has mode `0664`, link count 1, and content bytes:

```text
31 37 39 65 36 36 35 37 34 66 30 34 38 30 36 65
```

Those bytes decode exactly to `179e66574f04806e`. Git does not track the
sidecar; proofwidgets `.gitignore` explicitly contains `/widget/*.hash`. None
of the eight authenticated archives contains any member ending in `.hash`.

## Exact eight-package comparison

All eight compressed archive SHA-256 values matched
`references/lake-packages.json`. All eight retained Git HEADs matched the
pinned revisions, and their trees matched the pinned final `tree_sha` values.
After extracting all eight authenticated archives into a disposable `/tmp`
directory, `diff -qr --exclude=.git --exclude=.lake` produced exactly one line
over all packages:

```text
Only in .../.lake/packages/proofwidgets/widget: package-lock.json.hash
```

Counts below exclude the package-root directory itself and exclude retained
`.git` and `.lake` subtrees. Bytes count regular-file payload bytes.

| Package | Archive dirs/files/symlinks/bytes | Retained dirs/files/symlinks/bytes | Delta outside `.git`/`.lake` |
|---|---:|---:|---|
| plausible | 6 / 35 / 0 / 163,509 | 6 / 35 / 0 / 163,509 | 0 paths |
| LeanSearchClient | 4 / 15 / 0 / 54,606 | 4 / 15 / 0 / 54,606 | 0 paths |
| importGraph | 13 / 56 / 0 / 401,283 | 13 / 56 / 0 / 401,283 | 0 paths |
| proofwidgets | 17 / 111 / 0 / 9,603,230 | 17 / 112 / 0 / 9,603,246 | +1 regular, +16 bytes |
| aesop | 29 / 258 / 0 / 834,198 | 29 / 258 / 0 / 834,198 | 0 paths |
| Qq | 5 / 35 / 0 / 111,614 | 5 / 35 / 0 / 111,614 | 0 paths |
| batteries | 50 / 283 / 1 / 1,378,710 | 50 / 283 / 1 / 1,378,710 | 0 paths |
| Cli | 4 / 12 / 0 / 115,346 | 4 / 12 / 0 / 115,346 | 0 paths |

The only non-`.lake` retained files with build-sidecar suffixes were under
proofwidgets. Both `widget/package-lock.json.trace` and
`widget/js/lake.trace` are tracked, authenticated archive files; only generated
`widget/package-lock.json.hash` is archive-absent. The authoritative direct
comparison therefore remains the exact one-path result above.

## Causal chain in Lake 4.32.0

The pinned proofwidgets `lakefile.lean` declares at lines 32-37:

1. target `widgetPackageLock` chooses `widget/package-lock.json`;
2. it calls `buildFileAfterDep (text := true)`; and
3. its build action is `npm install`.

Installed Lake source at
`Lake/Build/Common.lean:681` implements `buildArtifactUnlessUpToDate`. For an
up-to-date output it selects an artifact-cache or `computeArtifact` path.
`computeArtifact` calls `fetchFileHash`, which at lines 401-408 creates
`file.toString ++ ".hash"` whenever no trusted sidecar exists;
`Cache.saveArtifact` and `restoreArtifact` also call `writeFileHash`.
`Hash.toString` at `Lake/Build/Trace.lean:163-166` is a 16-digit lowercase
hexadecimal string.

The retained authenticated trace is decisive corroboration:

```text
trace.outputs = 179e66574f04806e.art
sidecar bytes = 179e66574f04806e
```

Thus this is normal Lake metadata adjacent to a source-tree build target, not
archive source drift and not `.lake/build` output. The current verifier stages
all paths with `git add --all --force`, so `.gitignore` correctly does not hide
it; only `.lake/build` is then removed from the synthetic index. The sidecar
therefore changes the synthetic source tree and causes the observed rejection.

## Repair assessment

### Reject generic `*.hash` exclusion

A package-wide glob is too broad. It would authorize arbitrary new paths
outside the existing generated boundary and could hide mutation of a
future archive-tracked `.hash` file. More importantly, Lake trusts syntactically
valid `.hash` files by default, so an unvalidated adjacent sidecar can affect
build/artifact decisions. Merely requiring 16 lowercase hex characters does
not establish which output it describes or whether its value is legitimate.

### Recommended smallest secure repair

Extend each package pin with an exact append-only list such as
`post_build_hash_sidecars`; seven lists are empty and proofwidgets contains only
`widget/package-lock.json.hash`. Validate the declaration and the observed path
as follows:

1. The relative path is normalized, unique, outside `.lake/build`, ends in
   `.hash`, and is absent from the authenticated archive.
2. Its target sibling (path without `.hash`) and exact sibling `.trace` are
   authenticated archive regular files; their paths remain in source identity.
3. If the sidecar is absent, pre-build verification remains valid. If present,
   every parent is a real pinned directory and the sidecar is a regular,
   singly-linked, non-executable file with no special permission bits, exactly
   16 bytes, and exact lowercase hexadecimal content.
4. Parse the unchanged tracked trace and require its `outputs` value to be
   exactly `<sidecar-content>.art`. A modified/malformed trace remains in the
   synthetic tree and must fail the pinned tree comparison.
5. Only after all checks pass, remove that exact literal path from the
   temporary Git index used by `compute_source_tree_sha`. Do not remove it from
   disk. Every unlisted `.hash` or other extra path remains source drift.
6. Keep full pre-build archive verification, exact source/config/manifest and
   Gitlink checks, validated `.lake/build` handling, and final full `.lake`
   artifact inventory unchanged. The final inventory must bind the sidecar.

This is slightly more schema work than a hard-coded proofwidgets special case,
but it keeps the generated authority explicit in the existing package pin and
changes the cache key automatically because both the pin and materializer are
identity files. It is narrower and more auditable than a name glob.

### Archive-derived source overlay

A complete archive-derived path manifest is the strongest general model:
verify every authenticated archive path directly and classify every extra path
against explicit generated namespaces. It would naturally distinguish source
from output without reconstructing identity by subtractive globs. The current
pin, however, stores only aggregate inventory/tree digests, not the complete
path manifest, and `verify` does not reopen archives. Implementing an authority
manifest or re-reading all archives is a larger contract change than this
single exact sidecar requires. Adopt it if further package-root output classes
appear; do not improvise successive broad globs.

### Pre-publication removal

Removing the sidecar can make the existing tree comparison pass, but is not the
preferred repair. A secure removal still needs all exact-path/type/content and
parent-boundary checks above, after which index projection is simpler and
non-mutating. Deletion would make `verify` stateful, discard legitimate Lake
up-to-date metadata, risk path-replacement/unlink races, and ensure a later Lake
invocation recreates a path absent from the published inventory. If removal is
ever chosen, it must be descriptor-relative, identity-bound, fsynced, limited
to the one validated sidecar, and tested as a publication mutation.

## Acceptance regression matrix

| Case | Expected result |
|---|---|
| Pre-build package with declared sidecar absent | pass |
| Post-build proofwidgets with exact 16-byte sidecar matching authenticated trace | pass; sidecar remains on disk and enters final inventory |
| Exact sidecar with wrong hex, length, case, or trace output | fail closed; no READY |
| Exact sidecar as symlink, directory, FIFO/socket/device, executable, special-mode, or multiply-linked file | fail closed |
| Exact sidecar under a replaced/symlinked parent | fail before following or reading external paths |
| Valid-looking `*.hash` at any undeclared path | fail as source drift |
| Future archive containing a declared generated sidecar | reject the pin/archive contract |
| Mutated target, trace, source, config, or manifest with a valid sidecar | fail pinned source-tree comparison |
| `.lake/build`, sibling, nested lookalike, symlink, special, and hardlink cases | retain current exact pass/fail behavior |
| Gitlink package with valid generated output | retain exact reconstructed Gitlink tree |
| All eight packages with proofwidgets sidecar and normal generated builds | both package verifies pass; only declared output projected |
| Hot-cache build callback creates exact sidecar | call order remains materialize, verify, dependencies, build, verify; READY publishes once |
| Hot-cache build callback creates invalid/unlisted sidecar | terminal failure envelope; no snapshot/READY |
| Published manifest and deep seed verification | full inventory includes and authenticates the retained sidecar |
| Pin/materializer change | new cache key; old 9b6 failure remains retained and is not retried |

Focused materializer tests should exercise the path validator directly and the
realistic proofwidgets trace fixture. Hot-cache tests should assert both
post-build acceptance and fail-closed publication behavior. Then run the exact
focused suites, full serial suite, aggregate checker, compile check, workflow
validation, SHA-bound diff hygiene, fresh immutable review, guarded integration,
and exactly one newly reviewed changed-hypothesis warm.

## Limitations

- The retained package is an independently authenticated same-revision dev
  checkout, not the deleted/private staging tree from the failed warm. The
  retained failure artifacts contain only `failure.json` and `build.log`, so
  they do not preserve the rejected package tree itself.
- No Lean or Lake executable was run. The 16-byte hash was not recomputed by
  executing Lake; causality is established from installed pinned source plus
  the byte-identical authenticated trace/output match.
- The comparison covers one retained snapshot at all eight exact revisions. It
  does not prove future package targets cannot create different outside-build
  metadata.
- Current archives contain zero `.hash` members. The generic-glob risk remains
  a forward-compatibility and security concern even though it is not exercised
  by these eight archives.

## Session accounting

- Logical session: `i024-scout-a11-proofwidgets-sidecar`.
- Topology: read-only forensic scout under root coordinator; subagents 0;
  depth 1.
- Canonical start: `2026-08-31T17:16:24.925447Z`.
- Evidence cutoff/end: `2026-08-31T17:33:03.268252094Z`.
- Exact elapsed: `998.342805094` seconds.
- Base revision: `9c9b49548fabdd6b01916787d7dc17a4bca36513`.
- Token usage: JSON `null`; availability reason: collaboration backend does
  not expose per-agent token usage. No estimate was made.
- Repository/state/Git edits, tests, builds, warm, seed, Lean, Lake execution,
  network, and cache/runtime mutations: 0 each.
- Disposable action: extracted the eight already authenticated local archives
  under `/tmp/qpbt024-a11-extract.xCBcP0` for read-only comparison.
- Authored artifact: `/tmp/qpbt-024-proofwidgets-sidecar-a11.md` only.

Read-only evidence commands were scoped uses of `cat`, `date`, `stat`,
`sha256sum`, `jq`, `rg`, `find`, `git rev-parse/status/ls-files/check-ignore/
hash-object`, `tar -tzf`, `gzip -dc`, `od`, `tr`, `sed`, `wc`, `tail`, and
`diff -qr`. `mktemp -d` and `tar -xzf` wrote only the disposable extraction
directory. No validation command was run.

Report SHA-256 is supplied out of band after finalization because embedding it
would change the digest.
