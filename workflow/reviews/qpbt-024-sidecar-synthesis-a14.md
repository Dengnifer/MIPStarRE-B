# QPBT-024 sidecar security synthesis (A14)

## Scope and exact verdict

Logical session: `i024-reviewer-a14-sidecar-synthesis`.

**Choose A12's strict validation followed by descriptor-relative removal.**
For the one exact `proofwidgets` revision, validate the exact Lake-generated
`widget/package-lock.json.hash`, unlink only that bound entry, fsync and recheck
its parent, and only then run both existing source-tree comparisons. Publish
and seed no copy of this sidecar. Reject A11's alternative of retaining the
validated sidecar while projecting it only from source identity.

This is an implementation-only correction. It does not require a protocol
revision. The exact writable ownership is frozen to:

```text
scripts/materialize_lake_packages.py
scripts/hot_main_cache.py
tests/test_lake_package_materialization.py
tests/test_hot_main_cache.py
```

The writer must not change:

```text
references/lake-packages.json
protocols/local-development.md
protocols/orchestration.md
protocols/CHANGELOG.md
tests/test_cache_protocol.py
```

Canonical workflow/state, incident, PR, session, and metric files remain
root-coordinator-only and are outside implementation ownership.

## Security basis

The pinned toolchain is `leanprover/lean4:v4.32.0`. Its Lake source establishes:

1. `BuildConfig.trustHash` and CLI `LakeOptions.trustHash` default to `true`.
2. `fetchFileHash` returns a successfully parsed adjacent `<target>.hash`
   without reading or hashing the target.
3. `Hash.load?` accepts exactly 16 hexadecimal digits, including upper case;
   Lake writes a 16-digit lower-case form.
4. `computeArtifact`, artifact saving, and restoration create or consume these
   sidecars.
5. Lake's own Git-package materializer removes untracked leftovers on revision
   changes because stale `.hash` files can cause incorrect trace computation.

The established exact evidence is:

```text
package        proofwidgets
revision       6e311e2a844da9b2cc3971187df2fe0066947b93
target         widget/package-lock.json
target_sha256  3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d
sidecar        widget/package-lock.json.hash
sidecar_bytes  179e66574f04806e
trace          widget/package-lock.json.trace
trace_sha256   154a4f212697184548830b6bcca3fab192d93b6af145c64cd0ee9c996158fe1d
trace_output   179e66574f04806e.art
```

The deletion constant needs only package, revision, target, target SHA-256,
sidecar, and exact sidecar bytes. The trace facts are provenance corroboration;
do not make deletion depend on a new trace parser. The unchanged trace remains
ordinary authenticated source and is checked by the full tree comparison after
cleanup.

The sidecar is absent from the authenticated archive. A11's independently
authenticated same-revision comparison found it to be the sole retained path
outside `.git` and `.lake` that differed from the archive across all eight
packages. Its 16 exact bytes equal the authenticated trace output hash. The
pinned ProofWidgets target reaches Lake's artifact/hash helpers, so this is
generated trust metadata rather than package source.

## Why retaining it is insufficient

A strictly validated retained sidecar is correct at the moment of publication;
this decision does not treat it as arbitrary or already malicious. The defect
is that its guarantee ends at that moment:

- `READY` and the full `.lake` inventory authenticate the immutable snapshot's
  bytes and path set. They do not establish a continuing freshness relation
  between a sidecar and its target after copying.
- Every issue worktree intentionally receives a private writable `.lake` copy.
  If the target is changed after seed and before its first Lake action, the
  retained sidecar becomes stale. Default Lake accepts it without reading the
  changed target. Deep seed verification occurred before that mutation and
  cannot prevent it.
- Projecting the path from source identity proves the remaining source tree but
  does not neutralize this build-control meaning. Inventory binding is transport
  integrity, not rehashing.
- Retention provides no necessary artifact: when absent, Lake recomputes the
  target hash and recreates the sidecar. Omission therefore removes inherited
  trust state at negligible cost.

Removal does not claim to defeat an active same-UID process. Such a process can
recreate the path after verification or after seed. It does improve the honest
and accidental-mutation case by ensuring that the first Lake use of each seed
starts without inherited trusted metadata. This is the strongest result
available without changing every downstream Lake invocation to `--rehash`.

A generic `*.hash` removal or projection remains forbidden. It would erase the
authority of a future archive-owned `.hash` file and provide a broad mutation
mask. An archive overlay is also rejected for this issue: it is larger, adds
replacement/race surfaces, and can silently repair unrelated source drift
unless preceded by another full comparison.

## Contract location and caller authority

Put one internal, immutable, exact-revision contract in
`scripts/materialize_lake_packages.py`. Do not expose a caller-controlled ignore
list and do not extend the pin schema.

This is preferable to structured deletion data in
`references/lake-packages.json`. That file authenticates external package source
facts. Giving it a `post_build_hash_sidecars` field would also make pin data an
authority for deleting package-tree entries. Even with strict shape checks and
cache-key binding, a future pin-only edit could grant a new deletion exception
without changing reviewed deletion code. The one observed revision-specific
case does not justify that generalized authority or a schema migration.

The internal constant is still identity-bound: the exact main commit and
`scripts/materialize_lake_packages.py` digest are cache inputs. The canonical
verify argv is also in the recipe identity. A change to the contract, code,
flag, or recipe version therefore changes the key. The CLI must accept no
package, path, target digest, or expected sidecar bytes from the caller; its
only choice is whether to request the one compiled-in normalization policy.
Omitting that request fails closed on a post-build sidecar rather than causing
an unsafe publication.

`references/lake-packages.json` must not be owned or edited for this repair.
Its existing revision, archive inventory, and tree identities remain the
external source authority against which the internal exact-revision contract is
checked.

## Mutation/API boundary

A12's proposal makes the unqualified `verify` operation validate and unlink in
both invocations. That is secure inside the current private staging trust model,
but it is unnecessarily surprising: `verify` is presently observational, is
called directly by tests and operators, and a successful check should not
silently rewrite the checked tree.

Do not add a new normalize command field or a third package phase to
`BuildRecipe`; that would expand command pairing, timing, manifest, metrics, and
ordering state for one 16-byte file. Instead, keep default `verify` read-only and
add one explicit Boolean CLI flag with a name such as
`--remove-validated-generated-sidecars`. The flag exposes no values. The
canonical `package_verify_command` in `scripts/hot_main_cache.py` must include
that exact flag, so both existing invocations use an explicitly mutating mode:
the pre-Lake invocation is a proven no-op because the sidecar is absent, and the
post-build invocation validates/removes it before performing the ordinary
verification.

This is the smallest secure and least-surprising boundary: mutation is visible
in exact argv and cache identity, the default API stays read-only, the call
graph/order stays unchanged, and no caller gains path-selection authority.
Because canonical argv semantics change, bump the recipe version from 4 to 5
rather than leaving version 4 attached to different behavior. The argv change, recipe
version, materializer digest, and main SHA each independently cause key churn.
This command/recipe edit is why `scripts/hot_main_cache.py` is required writer
ownership.

## Smallest secure implementation

At archive inspection/materialization:

1. Apply the contract only when package name and revision both match exactly.
2. Require the target to be the exact regular archive member with the stated
   SHA-256.
3. Require the declared sidecar path to be absent from the archive.
4. Keep the existing complete archive facts, inventory, archive-tree, and
   Gitlink-reconstructed-tree checks. A future revision or archive that owns the
   path receives no automatic exception.

When and only when the explicit normalization flag is set, before `_scan_tree`
and before either `compute_source_tree_sha` call:

1. Bind the exact package directory and each fixed parent component from the
   already bound `.lake/packages` descriptor, using `O_DIRECTORY|O_NOFOLLOW`.
   Recheck package, parent, and project-layout incarnations throughout.
2. If the exact sidecar name is absent, make no mutation and continue. This is
   the normal pre-Lake case. Without the flag, perform no cleanup; ordinary
   source verification must reject a present sidecar.
3. If present, open it descriptor-relatively with `O_NOFOLLOW|O_NONBLOCK`.
   Require one regular link, exactly 16 bytes, no execute or special permission
   bits, and exact lower-case ASCII bytes `179e66574f04806e` with no newline.
4. Bind the exact target descriptor-relatively. Require one regular link and
   exact SHA-256 `3850e21b...`. The later full tree comparison remains the
   authority for its mode and for the tracked trace, lakefile, manifest, and all
   other source.
5. Compare `fstat` with a no-follow name `stat`, recheck all bound directories,
   then call `unlink` with `dir_fd` for only that exact entry. Fsync the parent;
   require the name absent; recheck parent, package, and layout identities.
6. Run `_scan_tree` and both existing exact source-tree comparisons with no new
   source projection. Any other path or source mutation must still fail.
7. Return the exact removed package/path and the explicit normalization mode in
   verifier JSON so the existing logged verify command leaves evidence.

Do not use lexical `Path.unlink`, a glob, `shutil`, an archive overlay, or Git
index exclusion for this sidecar. Do not delete malformed or unlisted objects.
Failure must leave external targets and hardlink peers untouched and must never
publish `READY`.

The current warm order is already correct and must remain exact:

```text
package materialize
package verify --remove-validated-generated-sidecars (normally a no-op)
dependency command
full build
package verify --remove-validated-generated-sidecars (validate/remove, then verify)
project/source rechecks
whole-.lake inventory
manifest and READY
atomic publication
```

## READY and source-faithfulness adjudication

`protocols/local-development.md` requires an inventory of the entire `.lake`
tree that is published. It does not require preservation of every transient
file ever created during the build. After exact removal, the inventory binds
the complete remaining tree and, through its path-set digest/counts, binds the
sidecar's absence. Deep seed verification must reject a source or destination
where the sidecar is injected. All retained `.lake/build/**` output remains in
the inventory unchanged.

Removal is source-faithful because the path is proven absent from the exact
archive and is removed only when its revision, target, type, link count,
permissions, size, and bytes match the one generated contract. The subsequent
unprojected Git-tree comparisons authenticate every source path. A malformed
lookalike is reported as drift rather than repaired.

A13's phrase about binding "excluded generated artifacts" was an acceptance
outline written before this A11/A12 adjudication, not a protocol rule requiring
this trust sidecar to be retained. The correct reading is that READY binds all
generated artifacts permitted in the published tree. This exact sidecar is now
classified as transient trust metadata that is deliberately not permitted in
that tree; `.lake/build` remains permitted and fully bound.

## Omission-sensitive regression matrix

Every row is required. Each test must assert the positive/negative state, not
merely the presence of a helper name or error substring.

| Omitted guarantee detected | Fixture or injection | Required result |
|---|---|---|
| Exact package/revision guard | Same path/content under another package or revision | No removal; exact tree verification fails |
| Archive absence guard | Declared exact sidecar included as an archive regular member | Archive inspection rejects the contradictory contract |
| Archive source ownership | An unrelated archive-owned `other.hash` | Materialize and verify preserve it; mutation/deletion later fails tree identity |
| Exact target binding | Sidecar exact, target bytes changed | Fail; no READY; do not treat cleanup as source repair |
| Target object safety | Target is symlink, directory, FIFO/socket/device, or multi-link regular | Fail before unlink; external object/peer unchanged |
| Exact sidecar bytes | Wrong valid 16-hex value | Fail and leave it present |
| Lake-written canonical form | Uppercase, short, long, newline, or non-hex sidecar | Fail and leave it present |
| Sidecar object safety | Sidecar is symlink, directory, FIFO/socket/device, executable/special-mode, or multi-link regular | Fail; target and any peer unchanged |
| Parent no-follow binding | `widget` or a parent is replaced by a symlink | Fail before any external read/write |
| Open/name identity recheck | Swap sidecar between open/fstat and pre-unlink stat | Fail; do not unlink replacement |
| Directory incarnation recheck | Swap package or parent before/after unlink | Fail; no READY; no write outside selected bound parent |
| Exact unlink and fsync | Exact regular one-link sidecar | Verify succeeds, path is absent, target bytes/mode unchanged, removal is reported |
| Default API purity | Exact package with exact sidecar, unqualified `verify` | No removal; verification fails on the extra path |
| Absent-path no-op | Pre-Lake exact package with no sidecar and explicit flag | Verify succeeds and tree metadata/content are unchanged |
| No arbitrary ignore boundary | `other.hash`, sibling, nested lookalike, or another package's same basename | Remains present and causes source-tree failure |
| Full source check after cleanup | Exact sidecar plus changed trace, `package.json`, lakefile, manifest, Lean source, or extra file | Sidecar may be removed, but verification fails and no READY is published |
| Both tree authorities | Gitlink fixture and ordinary archive-tree fixture | Both archive-tree and reconstructed-tree comparisons still run and match/fail independently |
| Existing generated boundary | Valid `.lake/build/**` output | Accepted, retained, and inventoried |
| Existing boundary defenses | `.lake/build` symlink/special/hardlink, archive-owned `.lake/build`, `.lake/not-build`, `.lake/build-sibling`, `src/.lake/build` | Existing exact pass/fail behavior is unchanged |
| Warm call order | Fake build generates the exact sidecar | Calls remain materialize/flagged-verify/deps/build/flagged-verify; second verify removes it before inventory |
| Publication absence | Successful exact-sidecar fake build | Snapshot and seeded copy omit sidecar; generated build artifacts remain; deep inventories match |
| Inventory negative binding | Inject sidecar into published snapshot or copied seed before deep validation | Deep readiness/seed validation fails |
| Fail-closed publication | Fake build produces wrong/malformed/special/unlisted sidecar | Failure envelope exists; snapshot and READY do not |
| Drift after legitimate generation | Fake build creates exact sidecar and mutates any authenticated source | Post-build verify fails; no READY |
| Cache identity binding | Change committed contract/code, flag argv, or recipe version independently | Cache key changes; dirty uncommitted copy does not redefine main identity |
| Explicit non-parameterized authority | Try to pass a path/package/hash value through the flag/CLI | Parser rejects it; no arbitrary cleanup authority exists |
| Minimal command surface | Canonical recipe assertions | No new phase/field; exact flagged verify argv appears twice in the existing positions; recipe version is exactly 5 |

Focused test names may be consolidated, but no matrix row may be omitted. Race
tests should patch narrow filesystem hooks around bind/stat/unlink/fsync rather
than introduce a production caller-controlled cleanup hook.

## Protocol disposition

No protocol revision is required:

- A11 supplies the exact path, object, content, archive delta, and Lake producer
  that A13 required before implementation resumed.
- Existing authority already separates authenticated package source from
  permitted generated artifacts, mandates post-build source verification,
  inventories the entire published `.lake`, and deep-verifies seeds.
- Exact sanitization implements those authorities; it does not change
  publication order, source authority, inventory authority, or seed isolation.
- The failed acceptance gate and concrete `trustHash` safety issue fall within
  the direct acceptance/safety allowance in `protocols/meta.md:46-52`.
- This is not a third recurrence and does not justify a generic sidecar policy.

A protocol issue should be reconsidered only if another distinct package-root
trust-metadata class appears and the existing exact source/generated authority
cannot decide ownership. That future evidence must not broaden this repair now.

## Residual risk

1. The failed warm did not preserve its staging tree. A11's sole-path result is
   from an independently authenticated same-revision retained package, supported
   by pinned Lake source and the authenticated trace, rather than a byte-for-byte
   examination of the deleted staging directory.
2. Descriptor-relative checks reduce ordinary substitution races but cannot
   defeat an actively racing same-UID process with equal filesystem authority.
   The design relies on the existing private staging and serialized builder
   trust boundary.
3. Lake recreates the sidecar on the first later use of a writable seed. A
   subsequent target mutation can again make it stale. Complete ongoing
   protection would require canonical `--rehash` use or immutable dependency
   sources, both outside this smallest repair.
4. The exact constant is revision-bound. A ProofWidgets revision change must
   fail closed and receive new evidence; it must not inherit this exception.

## Evidence hashes

```text
5b2e0067c507b8a8ef610f700198b60be803ef24681b4df5ff3005db6bd4c4b6  workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md
72388d58782faa23ce28ed6abbcc2a12b9923446e82834c2b8ab5cdd9eca38d0  workflow/reviews/qpbt-024-sidecar-security-a12.md
e590a72922a24abf6f0fd5346cac540a96da49f678b6065e2d435d3f8affac5f  workflow/reviews/qpbt-024-protocol-evolution-a13.md
3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243  scripts/materialize_lake_packages.py
0fd404e2cead596370fbda144dc86810f0fd2b87fe7a6ba011d7e72b661daeab  scripts/hot_main_cache.py
d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d  tests/test_lake_package_materialization.py
235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe  tests/test_hot_main_cache.py
08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0  references/lake-packages.json
c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c  AGENTS.md
3b111e8a95025270bf24c7fd7d8601ca5000b6cc37582ca1bf3bff487c7c874a  protocols/local-development.md
389d2211b0c847069e158b1355f577fce66aee0225f9545c93417a2036ec21f9  protocols/orchestration.md
04525efbfbf1074c84497d26d6de6173bd3c63567898dafab1252cd6d24516c8  protocols/meta.md
94f983ca1bb2fc11c161ec4ac18eed38fbad97239838c31a26f044c2daa61380  protocols/CHANGELOG.md
2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e  lean-toolchain
405af4398143b2c6917d6e6ba93016852a8c109a63c889f98fc043e05084c145  Lake/Build/Common.lean (installed v4.32.0)
c763e3166a1c12874bd550731333769ff185f8ca02e8d52cbc202c933d5c424b  Lake/Build/Trace.lean (installed v4.32.0)
6ef3b48c7c40c00530f57eeab7c236fe70493294aef216dd703f2dfc5dc28a9c  Lake/Build/Context.lean (installed v4.32.0)
3b031d66f31afb202a8022cfbae05ac402f39d7f92831e85f7057c360ed9439c  Lake/Load/Materialize.lean (installed v4.32.0)
4b95ab56b87319c0a1e2b55d0d31e3c077977a376020c326579d0802b9399010  Lake/CLI/Main.lean (installed v4.32.0)
```

## Session accounting

- Start: `2026-09-01T01:42:54+08:00` (one-second clock resolution).
- Evidence cutoff/end: `2026-09-01T01:57:02+08:00` (one-second clock resolution).
- Elapsed: `848` seconds, computed from the recorded timestamps.
- Token usage: JSON `null`; availability reason: collaboration backend does
  not expose per-session token usage. No estimate was made.
- Subagents: `0`; topology: root coordinator -> one fresh read-only A14
  reviewer. A peer A15 scout received the provisional verdict/ownership freeze
  but performed no work for this review.
- Repository/state/Git/runtime/cache edits: `0`.
- Tests, builds, warm, seed, Lean, Lake, network: `0`.
- Authored artifact: `/tmp/qpbt-024-sidecar-synthesis-a14.md` only.

The report SHA-256 is supplied out of band because embedding it would change
the digest.
