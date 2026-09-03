# QPBT-068 Design Scout

## Scope and anchors

- `scripts/hot_main_cache.py:255-312` (`artifact_inventory`) walks without following symlinks and records symlink targets in the authenticated inventory; it does not reject external or writable targets.
- `scripts/hot_main_cache.py:1842-1873` (`reflink_copytree`) recreates every source symlink with `os.symlink(os.readlink(...))`, including package-layer links. This is the direct isolation seam for QPBT-068.
- `scripts/hot_main_cache.py:2759-2774` (`_validate_seeded_destination`) checks only that the destination and `build` are real directories, then compares inventory; add a destination-tree policy check here (or immediately before validation) that rejects symlinked package/layer components and any symlink resolving outside the private `.lake` root. A writable resolved target must fail closed even when the link itself is read-only.
- `scripts/hot_main_cache.py:2821-2890` (`seed`) stages, renames existing `.lake` to `.lake.backup-*`, renames staged `.lake` into place, validates, and rolls back only while the process is alive. SIGKILL between the two `os.replace` calls leaves no `.lake` and a backup that a later invocation does not recover automatically.
- `scripts/hot_main_cache.py:2781-2808` (`_rollback_seed_replacement`) is deterministic exception rollback and should remain the tested path; it cannot prove crash recovery.
- `tests/test_hot_main_cache.py:600-624` (`test_warm_hits_then_seed_is_private_and_writable`) verifies inode separation and writable destination files but does not inspect package symlink targets.
- `tests/test_hot_main_cache.py:2349-2368` (`test_seed_replace_rolls_back_original_on_post_publish_failure`) injects validation failure and verifies backup cleanup; it does not terminate the process in the rename gap.
- Existing symlink admission tests at `tests/test_hot_main_cache.py:2337-2347` cover lexical target-path components only, not links inside `.lake`.

## Minimal implementation/test seams

1. Add a fail-closed validator for a copied `.lake` tree, invoked before/within `_validate_seeded_destination`. Walk with `os.scandir(..., follow_symlinks=False)`; for every symlink, resolve against its lexical parent, require the resolved path to remain beneath the destination root (or an explicitly authenticated immutable package root), require the resolved target to be owned by the private seed or provably read-only, and reject links into external writable trees. Preserve authenticated `READY` and full artifact inventory semantics; do not silently rewrite links.
2. Deterministic tests can construct a fake cache containing `.lake/packages/mathlib -> external/packages/mathlib`, make the external directory writable, and assert `manager.seed(...)` raises before publication. Add a relative in-tree symlink case if policy permits it, plus an absolute external read-only case to make the boundary explicit. Assert no destination, backup, or metric transaction is left on rejection and the published cache's `READY`/inventory remain unchanged.
3. Add a deterministic fault-injection seam around the two replacement renames (a private callback or patched `os.replace`) to verify exception rollback and cleanup without changing production ordering. Keep this separate from crash evidence.
4. Crash recovery requires a subprocess test. Launch a helper that seeds with `replace=True`, pause after `os.replace(destination, backup)` and before `os.replace(staging_lake, destination)`, then send SIGKILL. A subsequent `seed(..., replace=True)` or explicit recovery entry point must detect `.lake.backup-*`, restore or complete atomically, validate deep inventory, and leave no partial destination. Assert the old marker survives and no unauthenticated `READY` is created. Repeat with SIGKILL after staged publication but before validation to exercise withdrawal/backup recovery.

## Gates and constraints

- Preserve singleton `ExclusiveLock` acquisition (`scripts/hot_main_cache.py:2830-2840`), private writable copies, authenticated manifest/READY and deep inventory, and metric append transaction. Recovery must run under the same per-target lock and be idempotent.
- Capability/migration gate: only enable reflink/package-layer sharing when a probe demonstrates no hard links, destination inode independence, and safe symlink policy on the host filesystem. Byte-copy remains mandatory fallback; never assume reflink support.
- No deletion or in-place repair of published snapshots. Quarantine invalid staging or mismatched READY state; retain backups until post-recovery validation, then remove only through existing owner-writable cleanup.
- Deterministic fault injection is sufficient for exception paths; only a killed subprocess can establish the SIGKILL window is recoverable. Do not claim crash safety from mocked exceptions alone.

Observed scout timing: ~5 minutes wall-clock (read-only inspection and report drafting). Token usage: null (collaboration backend exposes no token counters).
