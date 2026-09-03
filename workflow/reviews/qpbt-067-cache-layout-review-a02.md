# QPBT-067 Fresh Immutable Review (A02)

Verdict: REQUEST CHANGES

Review session: `i067-reviewer-a02-cache-layout`
Issue: `QPBT-067`
Candidate commit: `4c4612b5f77800c3b549b60585e0ee21762e7d30`
Candidate tree: `812749f12d268f84fc1802ce7af7c821d6a2af05`
Base: `58980655263b581b0fa8751bed09440ee1b0141a`
Binary patch SHA-256: `9970f433e168d8a827bf60f6e1e7145c227c174e70ef24089cac665e83e7fd67`
Manifest SHA-256: `2fecb5f9fc80527daf41ea603347049ad1293d52943e792669adcb07fe668666`
Candidate report SHA-256: `afa401e27cb8e5e8a2a83501f3813c4e56fe58a26a692dd1fdc14a3a64e7ef97`

## Findings

### F-067-A02-001 (high): private-seed conclusion omits a writable external package symlink

`workflow/reviews/qpbt-067-cache-layout-a01.md:34-40` only checks hard-link
counts and concludes that the seed is private in the option table at `:86-93`.
The live registered worktree
`.workflow-runtime/worktrees/qpbt-037-pauli-a01/.lake/packages/mathlib` is a
symlink to `/home/drx/.cache/mipstarre-dev/hot-main/repo/.lake/packages/mathlib`;
the resolved target is mode `775` and writable.  Thus the worktree can write
through the symlink into an external shared package tree even though no
`.lake/build` hard links exist.  This conflicts with the protocol's private
`.lake` copy requirement (`protocols/local-development.md:73-78`) and makes
the broad “seed remains private” statement inaccurate.  The audit should record
the symlink target and either restrict its conclusion to private build output or
require a target-ownership/read-only check before claiming isolation.

### F-067-A02-002 (medium): crash contract overstates current seed recovery

The report states an interruption-safe, idempotent publication contract at
`workflow/reviews/qpbt-067-cache-layout-a01.md:114-119`, but does not identify
the existing interruption gap.  In `scripts/hot_main_cache.py:2841-2846`, seed
replacement first renames the old `.lake` to a backup and only then renames the
staged tree into place.  A process termination between those two renames leaves
the target without `.lake` (only the backup remains); a subsequent invocation
does not automatically restore that backup.  The tests cover injected
post-publication validation failure (`tests/test_hot_main_cache.py:2349-2368`),
not process interruption in this window.  The audit should distinguish the
exception rollback path from crash recovery and list this as an unresolved
acceptance gap, or provide evidence of an external recovery mechanism.

## Evidence and checks

The supplied manifest and all eight pinned input hashes authenticated exactly.
Read-only live checks reproduced the report's cache/main total (136,463,261,696
physical bytes; 131,520,471,782 apparent), the complete v7 snapshot's physical,
package, and build sizes, 13/13 READY-to-manifest digests, 13 distinct artifact
inventories, 45 metric records, and 14 failure directories with no READY files.
No tests, builds, compilation, cache materialization, Git, network, endpoint,
or state mutations were run, per the review constraints.  Token usage is
unavailable from the collaboration backend and is recorded as null.

Residual risk: the arithmetic and authenticated identity grouping are sound,
but isolation and crash-recovery conclusions need the above qualification before
this audit can be accepted as a cache-layout safety baseline.


