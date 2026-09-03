# QPBT-067 Cache Layout Audit

Session: `i067-orchestrator-a01-cache-layout`
Base: `58980655263b581b0fa8751bed09440ee1b0141a`
Observed: 2026-09-03 (read-only audit; no cache, worktree, source, or state mutation)

## Scope and sources

The layout is governed by the Worktree isolation and Hot-main cache sections of
`protocols/local-development.md`: the runtime root is `.workflow-runtime` below
the primary non-bare worktree, warm is lock-elected and publishes an atomic key
directory only after a successful build, `READY` authenticates the manifest and
deep verification is done by `seed`, and issue worktrees must receive private
writable copies with hard-linked `.lake/build` forbidden. In the QPBT-068 A10
candidate, `HotMainCache.__init__` places `cache/main/<key>/.lake`,
`manifest.json`, `READY`, and per-key locks at
`scripts/hot_main_cache.py:2661`; `HotMainCache.is_ready` checks the READY
digest and identity fields before optional deep artifact inventory at
`scripts/hot_main_cache.py:3106`. Transaction anchors are
`HotMainCache._write_seed_journal` at `:3933`,
`HotMainCache._recover_interrupted_seed` at `:4081`,
`HotMainCache._publish_seed_locked` at `:4393`, and
`HotMainCache._retain_seed_backup` at `:4562`. These line and symbol anchors are
for the A10 pre-commit candidate and must be rebound to its frozen commit in the
terminal report and independent review.

### Source provenance

| Source | Commit / tree / blob | Byte evidence | Disposition |
|---|---|---|---|
| Original QPBT-067 report | commit `4c4612b5f77800c3b549b60585e0ee21762e7d30`; tree `812749f12d268f84fc1802ce7af7c821d6a2af05`; blob `09df9dac0f3687f2a69baad90887d16d7af10781` | SHA-256 `afa401e27cb8e5e8a2a83501f3813c4e56fe58a26a692dd1fdc14a3a64e7ef97` | Authenticated from Git. |
| `workflow/reviews/qpbt-062-branch-lifecycle-a01.md` | commit `889e7f8f16b09e5c6de23b3348508a48c2bc14c6`; tree `04cad9b46835ab529b849510c853a07b2c8bce27`; blob `fb4990be9374d38944d62007cbf3bceaf649def1` | 7,398 bytes; SHA-256 `fc8c515d300b2bfe7d7c3f171afd56df8cd599f2fcd9de91f49d1773c84e2795` | Authenticated from the reachable Git object. The A20 and A21 immutable review manifests included and independently authenticated these exact bytes, satisfying the deferred evidence-inclusion gate. |

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
the QPBT-068 candidate rejects every external first hop or final target rather
than treating mode bits as durable immutability evidence. That candidate still
requires fresh immutable approval before this audit may rely on the policy.
Existing seed
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
only for audit history: the Hot-main cache protocol explicitly invalidates v6
and forbids retrying v5 after authored QPBT sources exist.

## Leases, references, and crash state

The runtime currently has 22 `hot-main-*.lock` files, 15 `seed-*.lock` files,
one metrics lock, and one workflow-state lock (all zero-byte lock files), plus
14 retained failure directories under `cache/failures`. Failure records contain
`failure.json` and `build.log`, and none contains `READY`; this matches the
failed-staging rule in the Hot-main cache protocol and
`HotMainCache._retain_failure` in `scripts/hot_main_cache.py`.
There is no durable reference-count/lease manifest tying a published key to
registered worktrees; lock files only serialize an operation and do not express
retention ownership. A future cleanup tool therefore must treat every live
registered worktree and any in-flight lock/metric record as an implicit lease,
and should add an explicit append-only reference record before reclaiming.

## Layout options and recommendation

| Option | Soundness against singleton compilation / private writable output | Space and portability assessment |
|---|---|---|
| Immutable shared snapshot, copy on seed | Preserves one lock-elected build and authenticated READY; inspected build files have no hard links. Whole-`.lake` privacy requires rejecting every link that leaves the private destination. | Current baseline plus the preliminary QPBT-068 policy; byte-copy costs about 10 GB per seed on ext4. |
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

The implemented cache-readiness path is fail-closed:
`HotMainCache.is_ready` returns false for a mismatched `READY` digest; no
current command moves that snapshot to quarantine. The quarantine rules above
remain a proposed cleanup contract. Synchronous seed failures atomically
exchange a continuously bound displaced tree back before the metric commit
point. The repaired QPBT-068 A22 candidate publishes a diagnostic digest-bound
journal before exchange, but does not treat that journal or its adjacent
digest/commit marker as persistent ownership authority. A later process rejects
all fixed journal/active staging state unchanged for manual disposition. The
live transaction binds every target ancestor and the transaction objects by
descriptors and permanent event monitors, publishes with atomic exchange or
no-replace, and retains rather than deletes the journal, staging root, and
authenticated old tree after commit. The journal runtime ancestors are created
and held descriptor-relatively; output children receive move monitors before
their handoff; and displaced trees are recursively byte/inode-inventoried before
and after retention. These are candidate behaviors, not
approved live guarantees, until a fresh immutable review approves the final
head. Its foundation materializer separately keeps `MIPStarRE/` continuously
present during replacement with one descriptor-bound exchange and retains the
whole live materialization transaction instead of deleting it. Cleanup
quarantine remains separate from live exception rollback and manual crash
disposition.

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
   `HotMainCacheTests.test_warm_hits_then_seed_is_private_and_writable`
   (`tests/test_hot_main_cache.py:879`) covers private writable behavior.
3. **Singleton/leases:** run concurrent warms for one key; assert one build,
   one READY publication, waiter hit metrics, and no staging READY. Register two
   seeds, then run dry-run cleanup; referenced key must not be a candidate.
4. **Crash/rollback:** inject interruption at staging, READY publication, and
   seed replacement; assert the destination is always the complete old or new
   tree, displaced and ambiguous objects remain intact, and no success metric
   escapes a precommit failure. Candidate regressions begin at
   `HotMainCacheTests.test_seed_rejects_unowned_backup_decoys_without_mutation`
   (`tests/test_hot_main_cache.py:3732`), atomic replacement is covered by
   `HotMainCacheTests.test_seed_atomic_exchange_never_has_absent_destination`
   (`:4028`), and ancestor ABA is covered symmetrically by
   `HotMainCacheTests.test_seed_and_prepare_reject_ancestor_swap_restore`
   (`:5197`). Existing failed-build retention is
   covered by `HotMainCacheTests.test_failed_build_is_retained_but_never_published`
   (`:3526`).
5. **Capacity guard:** on a filesystem with <10 GB free, dry-run must refuse
   byte-copy seeding before mutation and report required/apparent/physical bytes;
   reflink mode may proceed only after an explicit CoW capability check.
6. **Migration equivalence:** for package-layer or overlay prototype, compare
   deep artifact inventory and all five authored-QPBT verification phases before
   and after migration; require byte-identical Lean outputs and a measured
   physical-block reduction over at least three independent seeds. Do not claim
   savings from apparent size alone.

## Metrics and protocol implications

The original audit attempt made no source or protocol edits and dispatched no
child agents. Its authenticated lifecycle and timing records are
`workflow/state/sessions.json` SHA-256
`ae17e1b2c93ef6d120058c4402383370f71cb532b9736504ef11dc0a8e5c1bcc`
and `research/metrics/sessions.jsonl` SHA-256
`6b1c2c1e2141f6bbbaf626a6303c572350c8ff01b4ca4f710858fc4870d16a5e`.

| Audit metric | Authenticated value | Availability |
|---|---:|---|
| `audit_started_at` | `2026-09-03T09:10:15.289700Z` | Runtime measured. |
| `audit_stopped_at` | `2026-09-03T09:25:32.007492Z` | Runtime measured. |
| `elapsed_seconds` | `916.718` | Runtime measured. |
| Focused cache tests | `62/62 passed` | Result recorded; per-command elapsed latency was not recorded and is unavailable. |
| Inventory command latencies | `null` | No per-command timing evidence was recorded; not estimated. |
| `measured_max_parallel_lanes` | `4` non-coordinator sessions | Interval sweep over authenticated `started_at`/`ended_at` fields. From `2026-09-03T09:15:01.976868Z` through `09:24:47.060258Z`, the audit overlapped `i051-fixer-a09-cache-metric`, `i060-orchestrator-a02-integration`, and `i057-scout-a06-resource-selection`. The continuously running root coordinator is excluded from lane occupancy. |
| Protocol revision | recipe v7 at audit base `58980655263b581b0fa8751bed09440ee1b0141a` | Authenticated by the session record. |

QPBT-067 was created at `2026-09-03T09:12:00Z`. QPBT-068 was created at
`2026-09-03T09:42:00Z` while QPBT-067 was still in review. No authenticated
authorization for an exception is recorded. The acceptance gate requiring
these metrics and approval before opening an implementation issue was therefore
violated and cannot be repaired retroactively. QPBT-067 remains unapproved;
this correction records the missing values and ordering failure rather than
claiming an exception.

The audit exposes a capacity risk rather than an implementation
bug: 97% volume utilization leaves roughly 185 GB, while one full byte-copy
seed is about 10.5 GB physical. Add reference/lease accounting and dry-run
quarantine reporting before enabling automated cleanup. If the same ext4
fallback pressure recurs in three independent sessions, open a protocol issue
for a measured package-layer/reflink rollout; until then, preserve the current
portable fallback and make any savings claim contingent on measured physical
blocks and authenticated inventory equality.
