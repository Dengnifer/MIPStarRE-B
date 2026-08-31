# QPBT-024 / LPR-014 package compatibility scout (a05)

## Findings

No compatibility finding on candidate `9c9b49548fabdd6b01916787d7dc17a4bca36513`
relative to base `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe`.

The eight authenticated local source archives are all free of `.lake` entries,
and therefore free of `.lake/build`. Their 942 authenticated members comprise
136 directories, 805 regular files, and one safe source symlink; there are no
hardlinks or special/unsupported member types. Thus the new archive rejection at
`scripts/materialize_lake_packages.py:824-825` does not reject any pinned input.

The post-build validator at `scripts/materialize_lake_packages.py:990-1019`
accepts real directories and single-link regular files below the exact
package-root `.lake/build` boundary, while rejecting symlinks, special objects,
and multiply-linked regular files. Retained same-revision/same-toolchain Lake
output contains 178 directories and 5,137 regular files below `.lake/build` for
seven of the eight pinned packages, with zero symlinks, zero special objects,
and zero multiply-linked regular files. `Cli` had no retained build directory.
This observed type set is compatible with the candidate.

## Important compatibility distinction: Reservoir barrels

A retained legacy Git-package build has two generated regular files outside the
excluded subtree:

* `batteries/.lake/build.barrel`: 97,305,055 bytes, one link, SHA-256
  `2feb2da54ec7342fff634819b31d361404d024d6c85c6845f33e0b8ca4a38dff`.
* `batteries/.lake/build.barrel.trace`: 500 bytes, one link, SHA-256
  `1871d9706a78eedee73152e9ef9c4dfe86e0cc2e9b73ba58da294665f2a1f178`.

This is not a candidate incompatibility. The retained package is a detached Git
checkout at the exact pinned Batteries revision. By contrast, the governed
materializer writes archive-backed path packages without `.git`. Installed Lake
4.32.0 source computes a Reservoir URL by resolving `GitRepo.mk self.dir` HEAD
before calling the archive fetch (`Lake/Build/Package.lean:113-125,139-165`).
For the governed path package, URL computation fails before either barrel file
is created, and the optional cache path falls back to building source under
`.lake/build`. The candidate's test deliberately rejects generated-looking
siblings such as `.lake/build-sibling` (`tests/test_lake_package_materialization.py:392-404`),
which remains compatible with this acquisition mode.

## Authenticated archive audit

Pin file SHA-256:
`08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0`.
Every observed compressed and uncompressed value below equals its pin.
`d/f/l` are directory/regular-file/symlink counts. Every `.lake` count is zero;
every hardlink and special/other count is zero.

| package (revision) | compressed bytes / SHA-256 | tar bytes / SHA-256 | members (`d/f/l`) | `.lake` |
|---|---|---|---:|---:|
| plausible (`e12c1910fe855cbfc38803cd4e55543906d5fa62`) | 42,953 / `2825d6f3d7fc9d26151710ae643e08aabb02251bd94c476fd5217f91b59149b3` | 204,800 / `769c84219b93424773b44042ce10959ce67874f78ab2500e79f0020213f40bca` | 42 (`7/35/0`) | 0 |
| LeanSearchClient (`c5d5b8fe6e5158def25cd28eb94e4141ad97c843`) | 12,983 / `1a86db89a695849ce06590284e6b89c5f2353e3972e60b89b9fb4127e0cfff31` | 71,680 / `f7b604c8c600c6019486d1375b4d698a085056a3e264f95aa31f811d53f066ab` | 20 (`5/15/0`) | 0 |
| importGraph (`7e9612bf0b9ee66db3cb5b9988a35afc706f5a12`) | 106,222 / `c5ee93880bf68d9ae87280c77390460b8af3ee30f748cd10d098d4121ed7930c` | 460,800 / `46df1fedca1ab6cf15aa23757c0d92a2d670204d43f9108606c290f96a0e5762` | 70 (`14/56/0`) | 0 |
| proofwidgets (`6e311e2a844da9b2cc3971187df2fe0066947b93`) | 3,896,457 / `dffb4652003f31f8e393e0f2887526ec4b6cc8244b960afa8dcbc1918b020c68` | 9,707,520 / `f3d97bdf80e98ff87475a7fa97ef1e9802eba27300ba7d121ab8e4c02718ba11` | 129 (`18/111/0`) | 0 |
| aesop (`a7dbf0c63b694e47f425f3dcddbc0e178bb432d3`) | 208,077 / `b8c00f97dac46c4b1dd64f07bb80c0963ea61ff5dd9b239414481a77c05c5908` | 1,054,720 / `327695f22a02175bf1e7fe1e47b072953dec2a444d81507e928d289513d72482` | 288 (`30/258/0`) | 0 |
| Qq (`38d591e778f100aec9762bb582f9c7f55f50e9dc`) | 33,003 / `7f5c45d34799e615bf6445c3b7ef14a21c664843f14760468dafc4877ed14772` | 153,600 / `3faa7d95e5cbfffe48760ae59cab6278cf156a5c2ba0d0be5bbf5695294e9978` | 41 (`6/35/0`) | 0 |
| batteries (`023ce7d62a0531e22a5331e20b587817a80d49ff`) | 349,383 / `a5066fea2fd1a311c3c95d530f07030146de3a193e86a7271ae0a6cad5241294` | 1,628,160 / `e04e167a6474a2a72e2b67a243b964e8a596267e1ad2d9105f5c71993495b885` | 335 (`51/283/1`) | 0 |
| Cli (`88679d088c9720c27ebdf2ba4dafe17341747f94`) | 23,877 / `e2a1d9d7c341bc6d6f9674940de6c1282ebb2fb668a677c8405c5c0039d3db26` | 133,120 / `6b97cfa24ce532649b102911d4525aff92a6e27b2403809b7b219e5dc67f6c80` | 17 (`5/12/0`) | 0 |

The sole source symlink is Batteries `docs/README.md -> ../README.md`; it is
outside generated output and is already represented by the authenticated pin.

## Retained build/cache evidence

Evidence root: `/home/drx/.cache/mipstarre-dev/hot-main/repo`, detached head
`02777b586cf23df58c616e482c6c5a2a2e4affad`. Its root manifest is not bytewise
identical to the candidate manifest, but all eight package `(name, URL, revision,
type)` tuples and the Mathlib tuple match exactly. The toolchain file is bytewise
identical, SHA-256
`2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e`,
and names `leanprover/lean4:v4.32.0`.

Observed pinned-package `.lake/build` descendants:

| package | directories | regular files | symlinks | special | multi-link regular |
|---|---:|---:|---:|---:|---:|
| plausible | 5 | 169 | 0 | 0 | 0 |
| LeanSearchClient | 5 | 52 | 0 | 0 | 0 |
| importGraph | 13 | 130 | 0 | 0 | 0 |
| proofwidgets | 13 | 169 | 0 | 0 | 0 |
| aesop | 51 | 1,716 | 0 | 0 | 0 |
| Qq | 7 | 182 | 0 | 0 | 0 |
| batteries | 84 | 2,719 | 0 | 0 | 0 |
| Cli | 0 | 0 | 0 | 0 | 0 |
| **total pinned** | **178** | **5,137** | **0** | **0** | **0** |

The same snapshot also retained Mathlib's 2,326 directories and 107,560 regular
files below its build tree, again with no disallowed type/link count. The local
Mathlib cache contains 8,639 `.ltar` files totaling 439,161,263 bytes; all are
single-link regular files. The governed failed warm log independently records
8,638 already-cached files decompressed and a successful 8,992-job build before
the pre-candidate verifier stopped at `materialized archive tree differs for
plausible`.

## Candidate binding and coverage inspected

Candidate worktree was clean and at the assigned head. The exact diff contains
three files, 197 insertions and 3 deletions. Diff SHA-256:
`1789db7cef3dc499a91ff1cbd63115ce07c37e09ee368995e818165cc242858b`.

Changed-file SHA-256 values:

* `scripts/materialize_lake_packages.py`:
  `3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243`.
* `tests/test_lake_package_materialization.py`:
  `d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d`.
* `tests/test_hot_main_cache.py`:
  `235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe`.

The tests cover archive `.lake/build` rejection; valid regular generated files;
source/config/manifest drift; exact-boundary siblings; symlink, FIFO/special,
and hardlink rejection; Gitlink preservation; and post-build cache verification.

## Limitations and session metrics

The governed failed warm staging tree was cleaned, so its exact post-build paths,
types, and link counts cannot be inspected. No claim is made that the retained
legacy snapshot is a byte-for-byte reproduction of the candidate path-override
run; it is used only for same-revision/toolchain output-type compatibility. A
successful post-integration governed warm remains the definitive acceptance gate.

No tests, builds, workflow commands, Lean, Lake, network, Git writes, repository
edits, canonical/runtime/cache/reference edits, or subagents were used. All
inspection was read-only; no disposable extraction was necessary.

* Session: `i024-scout-a05-package-compatibility`.
* Inspection start: `2026-08-31T16:28:37Z`.
* Evidence freeze: `2026-08-31T16:38:53Z`.
* Inspection elapsed: 616 seconds.
* Subagent count/topology: 0 / none.
* Compile attempts: 0.
* Token usage: `null`; availability reason: the interface exposes no per-session
  token counter, and no estimate was made.
