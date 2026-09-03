# QPBT-067 Cache Layout Audit

Session: `i067-orchestrator-a01-cache-layout`
Base: `58980655263b581b0fa8751bed09440ee1b0141a`
Observed: 2026-09-03 (read-only audit; no cache, worktree, source, or state mutation)

## Scope and sources

The layout is governed by `protocols/local-development.md`: the runtime root is
`.workflow-runtime` below the primary non-bare worktree (lines 16-27), warm is
lock-elected and publishes an atomic key directory only after a successful build
(lines 39-44), `READY` authenticates the manifest and deep verification is done
by `seed` (lines 64-67), and issue worktrees must receive private writable
copies with hard-linked `.lake/build` forbidden (lines 73-78). The implementation
places `cache/main/<key>/.lake`, `manifest.json`, `READY`, and per-key locks at
`scripts/hot_main_cache.py:1973-1981`; `is_ready` checks the READY digest and
identity fields before optional deep artifact inventory at `:2179-2229`.

## Inventory evidence

Commands were read-only (`du -x -B1`, `du --apparent-size`, `git worktree list
--porcelain`, `find`, `stat`, `jq`, `sha256sum`, and `df`). Values are decimal
bytes unless noted.

| Area | Entries | Physical (`du`) | Apparent | Notes |
|---|---:|---:|---:|---|
| `.workflow-runtime/cache` | 13 READY snapshots + failures | 136,463,532,032 | 131,520,672,692 | `cache/main` accounts for 136,463,261,696 / 131,520,471,782 |
| `.workflow-runtime/cache/main` | 13 snapshots | 136.46 GB | 131.52 GB | 10 recipe-v7, 3 legacy recipe-v5 |
| Runtime issue-worktree `.lake` | 18 trees | 158,283,636,736 | 152,472,023,838 | 17 issue trees plus one tiny/partial tree |
| All Git-registered `.lake` (including primary and `/tmp`) | 20 trees | 158,573,428,736 | 152,830,198,162 | includes primary worktree and `/tmp/qpbt-023-lean-api-a03` |

The filesystem is ext4 (`findmnt`: `ext4 rw,nosuid,nodev,relatime,stripe=96`),
4-KB blocks, with 185 GB free and 97% used (`df -h`). Inode pressure is low
(11% used). No file under the 18 runtime issue `.lake` trees has link count
greater than one. Representative files have distinct device/inode pairs across
all snapshots and seeds. Thus no hard-link sharing is present for the examined
files, especially `.lake/build`; this does not establish whole-`.lake`
isolation when symlinks resolve outside the destination. The live registered
worktree `.workflow-runtime/worktrees/qpbt-037-pauli-a01/.lake/packages/mathlib`
was observed as an absolute symlink to
`/home/drx/.cache/mipstarre-dev/hot-main/repo/.lake/packages/mathlib`; the
resolved target was mode `775` and writable at review time. Consequently,
package-target ownership/read-only and realpath containment checks are still
required before claiming a seed is private. Existing seed
metrics (45 JSONL records in `metrics/hot-main.jsonl`) report
`copy.files=124925`, approximately 10.10 GB per full seed, and
`reflinked=0,copied=124925`; this volume is using the conservative byte-copy
fallback rather than reflinks.

One complete v7 snapshot (`1d815f...`) is 10,496,942,080 physical / 10,116,933,597
apparent bytes. Its `.lake/packages` is 7,373,111,296 physical (7,001,090,850
apparent), of which `packages/mathlib` is 7,011,647,488; `.lake/build` is
3,122,368,512 physical (3,114,417,343 apparent). Across all 13 snapshots,
packages account for 95,852,466,176 physical bytes and builds 40,590,970,880.
Across the 18 runtime issue trees, packages account for 112,684,318,720 and
builds 44,877,463,552 physical bytes. These are measurements, not a claim that
all bytes can be reclaimed safely.

### Authenticated identity grouping

Every main directory has both `manifest.json` and `READY`; all 13 READY files
equal the SHA-256 of their manifest. Manifest `artifact_inventory.sha256` values
are 13/13 distinct. Grouping by recipe and authored-source identity gives:

| Recipe / authored QPBT inventory | Snapshots | Artifact inventories |
|---|---:|---:|
| v5 / empty (`e3b0c4...`) | 3 | 3 distinct |
| v7 / `0578da...` | 5 | 5 distinct |
| v7 / `54fdca...`, `88f054...`, `c74492...`, `d65435...`, `f6b585...` | 1 each | each distinct |

The upstream source inventory (`d8d9e763...`) is common, but cache identity also
binds main commit, all key-input hashes, and the exact recipe. The five v7
snapshots sharing authored hash still have different main commits and artifact
hashes, so they are not duplicates. Full artifact-hash deduplication would
reclaim 0 bytes on this inventory. Recipe-v5 snapshots must remain addressable
only for audit history: the protocol explicitly invalidates v6 and forbids
retrying v5 after authored QPBT sources exist (local-development.md:60-62).

## Leases, references, and crash state

The runtime currently has 22 `hot-main-*.lock` files, 15 `seed-*.lock` files,
one metrics lock, and one workflow-state lock (all zero-byte lock files), plus
14 retained failure directories under `cache/failures`. Failure records contain
`failure.json` and `build.log`, and none contains `READY`; this matches the
failed-staging rule (local-development.md:69-71 and hot_main_cache.py:2669-2682).
There is no durable reference-count/lease manifest tying a published key to
registered worktrees; lock files only serialize an operation and do not express
retention ownership. A future cleanup tool therefore must treat every live
registered worktree and any in-flight lock/metric record as an implicit lease,
and should add an explicit append-only reference record before reclaiming.

## Layout options and recommendation

| Option | Soundness against singleton compilation / private writable output | Space and portability assessment |
|---|---|---|
| Immutable shared snapshot, copy on seed | Preserves one lock-elected build and authenticated READY; inspected build files have no hard links. Whole-`.lake` privacy is not established until symlink targets are contained/owned and non-writable. | Current behavior; safe everywhere once the target policy is enforced, but byte-copy costs about 10 GB per seed on ext4. |
| Reflink copy-on-write seed | Same semantics if destination inode/link checks and deep inventory remain; writes diverge by extent. | Preferred optimization when `FICLONE` succeeds. Must record `reflinked`/`copied` counts and retain byte-copy fallback; filesystem-dependent. |
| Hard links to `.lake/build` | Violates protocol: Lean can mutate artifacts and cross-worktree writes become visible. | Prohibited regardless of apparent savings; test link counts and reject. |
| Overlayfs / CoW delta over immutable package+build layers | Could share read-only package bytes and isolate writable deltas; singleton warm still required. | Requires privileged/mount support, careful lowerdir authentication, whiteout handling, and portability fallback; not justified until measured on this host. |
| Package/build separation | A read-only authenticated package layer (~7 GB) plus per-issue build layer (~1.7–3.1 GB) targets the dominant duplication. | Promising design, but package materialization and sidecar verification must be independently authenticated; no savings claim until prototype measurements. |
| Singleton compilation with private byte copies (fallback) | Current conservative baseline; one elected builder, private destination, rollback on seed failure. | Portable and auditable; retain as mandatory fallback when reflink/overlay is unavailable or errors. |

Recommended migration is incremental: (1) add a read-only inventory/reference
scanner and dry-run quarantine report; (2) add explicit snapshot reference
records and lease expiry rules; (3) trial reflink seeding on a disposable test
filesystem while asserting no hard links; (4) only then consider package-layer
separation or overlayfs; (5) keep singleton warm + private byte-copy as the
rollback path. Do not delete or rewrite existing snapshots during migration.

## Retention, quarantine, and recovery contract

Use a separate `cache/quarantine/<key>/<timestamp>/` namespace for invalid or
superseded snapshots. A dry-run command must report candidate key, reason,
manifest/READY digest status, physical/apparent bytes, active references, and
the earliest eligible deletion time without changing bytes. Retain failed
staging diagnostics for at least 7 days (and until its corresponding issue
attempt is terminal); retain successful snapshots while referenced, then for a
30-day grace period. Quarantine deletion requires two observations separated by
the grace interval, no active lease, valid lock-state audit, and a final
manifest/READY check; move to quarantine before any irreversible deletion.

The implemented live-process path is exception rollback: staging directories
without `READY` are never addressable; a snapshot with a mismatched READY digest
is quarantined, never repaired in place; and seed replacement uses the existing
private backup and restores it when post-publication validation fails
(local-development.md:77-78). This rollback path does not prove process-crash
recovery. In `scripts/hot_main_cache.py:2841-2846`, a SIGKILL between the rename
of the old `.lake` to `.lake.backup-*` and the rename of the staged tree can
leave the target without `.lake`; no automatic recovery guarantee is currently
implemented. Treat that state as an observed risk requiring a future
lock-serialized recovery implementation and subprocess SIGKILL tests. Do not
claim that interruption between copy and publication currently preserves either
the old destination or a complete validated destination.

## Measurable acceptance tests

1. **Identity/authentication:** enumerate all snapshots; require exactly one
   manifest and READY per published key, matching digest, schema/key/main/input/
   recipe fields, and deep artifact inventory. Group by
   `(recipe.version, source_contract.authored_qpbt_sha256,
   artifact_inventory.sha256)` and assert no unverified duplicate is treated as
   equivalent.
2. **Isolation:** seed a fixture on filesystems with and without reflink;
   assert destination inode differs, all build files have `st_nlink == 1`,
   writes to destination do not alter source, and fallback reports
   `reflinked=0` with exact copied file/byte counts. Existing regression
   `tests/test_hot_main_cache.py:600-624` covers private writable behavior.
3. **Singleton/leases:** run concurrent warms for one key; assert one build,
   one READY publication, waiter hit metrics, and no staging READY. Register two
   seeds, then run dry-run cleanup; referenced key must not be a candidate.
4. **Crash/rollback:** inject interruption at staging, READY publication, and
   seed replacement; assert no partial published tree, old destination restored,
   and quarantine/failure record contains reason without READY. Existing failure
   regressions cover no-READY behavior (`tests/test_hot_main_cache.py:545-598`).
5. **Capacity guard:** on a filesystem with <10 GB free, dry-run must refuse
   byte-copy seeding before mutation and report required/apparent/physical bytes;
   reflink mode may proceed only after an explicit CoW capability check.
6. **Migration equivalence:** for package-layer or overlay prototype, compare
   deep artifact inventory and all five authored-QPBT verification phases before
   and after migration; require byte-identical Lean outputs and a measured
   physical-block reduction over at least three independent seeds. Do not claim
   savings from apparent size alone.

## Metrics and protocol implications

This attempt made no source or protocol edits and dispatched no child agents.
Observed protocol revision is the current `local-development.md` contract
(recipe v7). The audit exposes a capacity risk rather than an implementation
bug: 97% volume utilization leaves roughly 185 GB, while one full byte-copy
seed is about 10.5 GB physical. Add reference/lease accounting and dry-run
quarantine reporting before enabling automated cleanup. If the same ext4
fallback pressure recurs in three independent sessions, open a protocol issue
for a measured package-layer/reflink rollout; until then, preserve the current
portable fallback and make any savings claim contingent on measured physical
blocks and authenticated inventory equality.
