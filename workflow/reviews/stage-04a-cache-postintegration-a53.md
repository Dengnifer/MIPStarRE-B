# Stage 04a post-integration hot-cache readiness (a53)

## Verdict

**Conditional GO for exactly one post-integration `warm` attempt from the
canonical primary worktree. NO-GO for warming from the reviewed candidate
clone, and NO-GO for claiming the warm is guaranteed offline.**

The committed pins and every required local archive are present and match. The
canonical runtime is on the same filesystem as the repository and currently
has no published main snapshot, no active hot-cache/Lake/Lean process, and no
observed held hot-cache lock. The command below must bind the exact integrated
40-character SHA, the canonical repository and runtime paths, and exactly one
Mathlib input. A failure remains fail-closed and must not be converted into a
manual `READY` or a second unexamined retry.

## Scope and immutable identities

- Canonical base inspected: `367ed6904d096e841a3849010395296a52be30c8`
  at `/home/drx/MIPStarRE-auto`.
- Reviewed candidate inspected: `6303aab63eeed144fe176969ca7c87f5a852b967`
  at `/tmp/qpbt-021-repair-a05`, clean except ignored Python bytecode.
- Candidate implementation commit:
  `c37431ec44c3d1f281a31c1a2125ace3ca590716`; its changed paths are
  `protocols/CHANGELOG.md`, `protocols/orchestration.md`,
  `scripts/hot_main_cache.py`, `tests/test_hot_main_cache.py`, and
  `workflow/README.md`. The final candidate commit changes only the changelog.
- The candidate is a standalone primary clone, not a linked worktree of the
  canonical repository. Its omitted runtime resolves to
  `/tmp/qpbt-021-repair-a05/.workflow-runtime`, so neither `status` nor `warm`
  should be run there for the integrated snapshot.
- The canonical primary worktree has a real `.git/` directory and its explicit
  shared runtime is `/home/drx/MIPStarRE-auto/.workflow-runtime`. This avoids
  relying on omitted-runtime discovery even though candidate
  `scripts/hot_main_cache.py:620-662` implements the correct primary-worktree
  resolution.

## Authenticated local inputs

### Mathlib

Use archive mode and explicitly unset `MATHLIB_SOURCE`.

- Path: `/tmp/mathlib-81a5d257-shallow-repo.tar.gz`
- Type/mode/link count: regular, `0664`, one link; no symlink component.
- Compressed: `51,938,317` bytes, SHA-256
  `c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`.
- Decompressed tar: `147,712,000` bytes, SHA-256
  `ad9a60b01736070112fbc1008ea98c67e68fa045c5b69e66873e0b9444ddd3ba`.
- Git pack: `27,574,578` bytes, SHA-256
  `4659f2a0cabfec474474f5e83ea3d495e711b735418742dd3d642328adcada02`.
- Archived `HEAD` and `.git/shallow` both contain
  `81a5d257c8e410db227a6665ed08f64fea08e997`.
- Candidate contract: commit above, tree
  `5ea66b811b8461daae82f14d356fed2a287d7c40`; see
  `scripts/hot_main_cache.py:63-80` and `protocols/orchestration.md:160-206`.
- Root `lake-manifest.json` contains exactly one Mathlib entry at the expected
  HTTPS URL and exact commit. `references/mathlib-lake-manifest.json` is the
  expected Mathlib manifest with eight inherited packages.

The candidate validates the compressed archive before either a hit or a build
(`scripts/hot_main_cache.py:1735-1769`), fully authenticates its extracted Git
repository before Lake, injects a sorted local `LAKE_PKG_URL_MAP`, rechecks the
source and pack before publication, and deletes the extracted Mathlib source
before publishing `.lake` (`:1681-1733`, `:1771-1791`, `:2104-2108`,
`:2141-2152`).

### MIPStarRE foundation

- Recommended path:
  `/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz`.
- Type/mode/link count: regular, `0600`, one link, under a `0700` directory;
  no symlink component.
- Compressed: `1,989,153` bytes, SHA-256
  `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.
- Decompressed tar: `10,752,000` bytes, SHA-256
  `4e4850855ac74b63cb9ef292281462174da776628a6278006f3728c9458a1d39`.
- These facts match `references/mipstarre-upstream.json`; the pinned source is
  `507e81220d95266ff3d589d125b2f87c7300a9fb`, output inventory SHA-256 is
  `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.

### Lake package archive reservoir

Use the absolute directory
`/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830`.
It has all eight exact `name-revision.tar.gz` files. Every observed compressed
size and SHA-256 matches `references/lake-packages.json`:

| Package | Bytes | SHA-256 |
|---|---:|---|
| plausible | 42,953 | `2825d6f3d7fc9d26151710ae643e08aabb02251bd94c476fd5217f91b59149b3` |
| LeanSearchClient | 12,983 | `1a86db89a695849ce06590284e6b89c5f2353e3972e60b89b9fb4127e0cfff31` |
| importGraph | 106,222 | `c5ee93880bf68d9ae87280c77390460b8af3ee30f748cd10d098d4121ed7930c` |
| proofwidgets | 3,896,457 | `dffb4652003f31f8e393e0f2887526ec4b6cc8244b960afa8dcbc1918b020c68` |
| aesop | 208,077 | `b8c00f97dac46c4b1dd64f07bb80c0963ea61ff5dd9b239414481a77c05c5908` |
| Qq | 33,003 | `7f5c45d34799e615bf6445c3b7ef14a21c664843f14760468dafc4877ed14772` |
| batteries | 349,383 | `a5066fea2fd1a311c3c95d530f07030146de3a193e86a7271ae0a6cad5241294` |
| Cli | 23,877 | `e2a1d9d7c341bc6d6f9674940de6c1282ebb2fb668a677c8405c5c0039d3db26` |

All are one-link regular files. The package materializer binds the archive
directory and project layout by descriptors, checks each complete archive and
Git tree, atomically publishes the packages and override, and the recipe runs a
second verifier before Lake and after the build
(`scripts/materialize_lake_packages.py:1790-1848`, `:1862-1891`;
`scripts/hot_main_cache.py:2086-2102`, `:2122-2129`).

## Key derivation and expected paths

Candidate `scripts/hot_main_cache.py:1384-1417` computes:

```text
cache_key = SHA256(ASCII(JSON({
  "main_commit": lower(exact_integrated_sha),
  "inputs": committed_file_sha256_map,
  "recipe": canonical_recipe_identity,
  "source_contract": committed_MIPStarRE_and_QPBT_contract
}, sort_keys=true, separators=(",", ":"))))
```

The eight committed input hashes currently agree in the canonical base and the
reviewed candidate:

```text
lean-toolchain                              2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e
lakefile.toml                               a1c61e97b41ec1fcbf15345a18117540ebc2d9f6f6cfa1021580479e2e9bafdf
lake-manifest.json                         d20abbe9525a311d501feb89299492717e27c88f441ac77191d9394b49e47fa9
references/mipstarre-upstream.json         d5db77534d52be40e247715ed7bb5007b1bc89ac437d545854f6f35cebb2461b
scripts/materialize_mipstarre.py           872b462ca048cd965c764aa08126532072e91bc6a15cc302c7e3acb922458d95
references/lake-packages.json              08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0
references/mathlib-lake-manifest.json      015c7e00ead0f05f2a72b32d9bdef782d4689d05a6297f0ceb0ab5d196c164bd
scripts/materialize_lake_packages.py       73bc42b1b4a33806e83ab5502f1b125eae6325f6c0d1063a80d0fa481dd245e5
```

The recipe identity is schema `3`, id `qpbt-hot-main`, version `4`, with exact
argv:

```text
python3 scripts/materialize_mipstarre.py materialize --archive-env MIPSTARRE_ARCHIVE
python3 scripts/materialize_lake_packages.py materialize --archive-directory-env LAKE_PACKAGE_ARCHIVES
python3 scripts/materialize_lake_packages.py verify
lake --packages=.lake/package-overrides.json exe cache get
lake --packages=.lake/package-overrides.json build
```

The source contract at the canonical base has zero committed authored QPBT
files/bytes and empty SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`,
plus the MIPStarRE facts above. The candidate commits do not change any of the
eight inputs or `MIPStarRE/QPBT`, so after a faithful integration only
`main_commit` changes in this payload. If integration changes any such file,
the post-integration `status` output is authoritative.

The exact post-integration key cannot be named before the integration commit
exists because the full resulting commit SHA is itself an identity input. For
cross-checking only, applying the candidate algorithm to the current canonical
base produces key
`717447b31c4139df213ad4e5ce538774a485d8f6fea2bede6afa8318a238402a`;
the standalone candidate SHA produces
`115c24d2232cafa97f993358960b3cd10b277a5d4cb659a213509dca66405f48`.
Neither is the expected integrated key and neither should be warmed.

For the key emitted by post-integration `status`, expected paths are:

```text
/home/drx/MIPStarRE-auto/.workflow-runtime/cache/main/<key>
/home/drx/MIPStarRE-auto/.workflow-runtime/cache/main/<key>/.lake/build
/home/drx/MIPStarRE-auto/.workflow-runtime/locks/hot-main-<key>.lock
/home/drx/MIPStarRE-auto/.workflow-runtime/metrics/hot-main.jsonl
```

## Exact post-integration gate and commands

Set the full SHA manually after integration. Do not substitute `6303aab...`;
that is the reviewed standalone commit, not the integrated main commit.

```bash
export QPBT_REPO_ROOT=/home/drx/MIPStarRE-auto
export QPBT_RUNTIME_DIR=/home/drx/MIPStarRE-auto/.workflow-runtime
export QPBT_MATHLIB_ARCHIVE=/tmp/mathlib-81a5d257-shallow-repo.tar.gz
export QPBT_MIPSTARRE_ARCHIVE=/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz
export QPBT_PACKAGE_ARCHIVES=/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830
export QPBT_INTEGRATED_SHA=<exact-40-character-post-integration-main-SHA>

test "$(git -C "$QPBT_REPO_ROOT" branch --show-current)" = main
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_INTEGRATED_SHA"
test "${#QPBT_INTEGRATED_SHA}" -eq 40
git -C "$QPBT_REPO_ROOT" cat-file -e "$QPBT_INTEGRATED_SHA^{commit}"
git -C "$QPBT_REPO_ROOT" diff --quiet "$QPBT_INTEGRATED_SHA" -- \
  scripts/hot_main_cache.py scripts/materialize_mipstarre.py \
  scripts/materialize_lake_packages.py references/mipstarre-upstream.json \
  references/lake-packages.json references/mathlib-lake-manifest.json \
  lake-manifest.json lakefile.toml lean-toolchain
test "$(sha256sum "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" | cut -d' ' -f1)" = \
  68ac570d18725396ef3fabf209793a86bf54287c27c8ed55748e4bf5ab8f1bfe
test -d "$QPBT_RUNTIME_DIR"
test -f "$QPBT_MATHLIB_ARCHIVE" && test ! -L "$QPBT_MATHLIB_ARCHIVE"
test -f "$QPBT_MIPSTARRE_ARCHIVE" && test ! -L "$QPBT_MIPSTARRE_ARCHIVE"
test -d "$QPBT_PACKAGE_ARCHIVES" && test ! -L "$QPBT_PACKAGE_ARCHIVES"
```

The exact read-only status command is:

```bash
env -u MATHLIB_SOURCE -u LAKE_PKG_URL_MAP \
  MATHLIB_ARCHIVE="$QPBT_MATHLIB_ARCHIVE" \
  MIPSTARRE_ARCHIVE="$QPBT_MIPSTARRE_ARCHIVE" \
  LAKE_PACKAGE_ARCHIVES="$QPBT_PACKAGE_ARCHIVES" \
  python3 "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" \
  --repo-root "$QPBT_REPO_ROOT" \
  --project-dir . \
  --runtime-dir "$QPBT_RUNTIME_DIR" \
  --main-commit "$QPBT_INTEGRATED_SHA" \
  status
```

Expected first result is `status: "miss"`, with `main_commit` exactly equal to
`$QPBT_INTEGRATED_SHA` and all three emitted paths rooted under
`$QPBT_RUNTIME_DIR`. Record the emitted key. `status` validates the committed
identity and any existing `READY`/manifest, but it does **not** validate the
three archive environment variables; the real warm preflight does.

After checking the status envelope, invoke this command **once**. Do not run a
parallel warm and do not run it from the candidate clone:

```bash
env -u MATHLIB_SOURCE -u LAKE_PKG_URL_MAP \
  MATHLIB_ARCHIVE="$QPBT_MATHLIB_ARCHIVE" \
  MIPSTARRE_ARCHIVE="$QPBT_MIPSTARRE_ARCHIVE" \
  LAKE_PACKAGE_ARCHIVES="$QPBT_PACKAGE_ARCHIVES" \
  python3 "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" \
  --repo-root "$QPBT_REPO_ROOT" \
  --project-dir . \
  --runtime-dir "$QPBT_RUNTIME_DIR" \
  --main-commit "$QPBT_INTEGRATED_SHA" \
  warm
```

Successful output must have `result: "built"` (or `hit`/`hit_after_wait` only
if another elected process already published the exact key), `status: "hit"`,
the same key and integrated SHA as status, and recorded lock/build/elapsed
metrics. Confirm the new snapshot contains real `READY`, `manifest.json`, and
`.lake/build`; do not manufacture or edit them.

## Current ignored materializations and runtime state

- Canonical `.lake/` exists with only `.lake/packages/`; `.lake/build` is
  absent. Canonical `MIPStarRE/` is absent. Neither is consumed as build output:
  warm uses a detached clone and materializes both there.
- Canonical `.workflow-runtime/cache/main/` exists and is empty. There is no
  published snapshot and therefore the new integrated status should miss.
- Three retained failure envelopes exist under
  `.workflow-runtime/cache/failures/`; they are old keys and do not collide with
  the new integrated key.
- Existing zero-byte lock files are old key locks plus the metrics lock. No
  active `hot_main_cache.py`, Lake, or Lean process and no held relevant lock
  was observed. Lock files are durable flock rendezvous files, not evidence of
  a current owner.
- The reviewed candidate has no `.lake`, `MIPStarRE`, or `.workflow-runtime`;
  only ignored `scripts/__pycache__/` and `tests/__pycache__/` exist.
- Repository/runtime/archive paths are on device `66314`; approximately 587 GiB
  and 155 million inodes were free at inspection time.
- Current canonical tracked dirt is confined to coordinator-owned workflow
  ledger files and was preserved. The exact tool/input path gate above is
  scoped so those unrelated coordinator changes do not authorize a dirty cache
  tool or pin.

## Fail-closed prerequisites and residual risks

1. Integrate the reviewed candidate faithfully first. If conflict resolution
   changes `scripts/hot_main_cache.py` from SHA-256
   `68ac570d18725396ef3fabf209793a86bf54287c27c8ed55748e4bf5ab8f1bfe`,
   stop for review rather than warming an unreviewed tool.
2. Capture and pass the exact integrated full SHA. Do not rely on a moving
   `main` ref between status and warm.
3. Use the explicit canonical runtime. The candidate clone has an independent
   Git common directory and therefore an independent omitted runtime/lock.
4. Keep exactly one of `MATHLIB_SOURCE`/`MATHLIB_ARCHIVE` nonempty. The command
   unsets the former. It also unsets ambient `LAKE_PKG_URL_MAP` so a conflicting
   Mathlib mapping cannot enter the command.
5. All archives must remain exact regular non-symlink inputs. Warm authenticates
   Mathlib before a hit and again around a miss; MIPStarRE and package
   materializers perform their own exact archive/inventory checks. Any drift,
   missing input, source mismatch, or conflicting mapping exits without
   `READY`.
6. `lake --packages=.lake/package-overrides.json exe cache get` can still need
   Reservoir/cache service. Candidate protocol explicitly does not promise an
   offline warm (`protocols/orchestration.md:208-213`). A nonzero dependency
   result is retained as failure evidence and publishes no snapshot.
7. The detached-clone command remains `git clone --local --no-checkout` without
   `--no-hardlinks` (`scripts/hot_main_cache.py:1891-1901`). Two prior cache
   attempts failed closed with `Invalid cross-device link` while hardlinking
   local Git objects; a later attempt passed clone and reached dependency
   caching. The repository and runtime currently report the same device, but
   this historical failure is not eliminated by QPBT-021. If it recurs, inspect
   the retained failure and open/fix the clone failure class; do not blindly
   consume the one-warm instruction as permission for repeated attempts.
8. `/tmp/mathlib-81a5d257-shallow-repo.tar.gz` is root-owned but lies under a
   sticky world-writable parent. The script's no-symlink, one-link, bounded-read,
   size, digest, and revalidation checks are the safety boundary. Do not replace
   it between the status gate and warm.
9. `status` uses shallow readiness checks; later `seed` performs deep artifact
   inventory verification. No seed is part of this task.

## Scout metrics

- Elapsed: approximately 18 minutes of read-only inspection.
- Subagents: `0` (topology: single scout).
- Compile/build attempts: `0`.
- Cache actions: `status=0`, `warm=0`, `seed=0`.
- Lake/Lean invocations: `0`.
- Network invocations: `0`.
- Token usage: `null`; availability reason: this session does not expose a
  token-usage counter, so no estimate was made.
