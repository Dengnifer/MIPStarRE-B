# QPBT-068 Fresh Hostile Cache-Safety Review (A02)

Review session: `i068-reviewer-a02-cache-safety`  
External collaboration ID: `/root/i068_reviewer_a02_cache_safety`  
Base: `b37a33c7c280e29fad2ca2cd12c221b6fc38aa07`  
Head: `7f7da8438a8ee9b456e22d441e7d0c3284779f22`  
Tree: `f2eaf03109057bec8dfa46cbf1ecb8315c1742e3`

## Findings

### Critical: recovery trusts a filename glob and can delete an unrelated existing `.lake` without `--replace`

`scripts/hot_main_cache.py:3204` treats every sole real directory matching
`.lake.backup-*` as interrupted transaction state, without a journal, nonce,
owner record, expected destination identity, or authenticated backup identity.
When `.lake` also exists but does not match the current cache,
`scripts/hot_main_cache.py:3222` withdraws that existing tree, installs the
unowned backup-shaped directory, and the `finally` block at line 3235 deletes
the withdrawn tree. This recovery runs before `_publish_seed_locked` enforces
the caller's `replace` flag at line 3316.

A bounded reproducer created an ordinary `.lake/current-user-bytes` and an
ordinary `.lake.backup-manual/decoy-bytes`, then called `seed(target)` without
`--replace`. The call reported "target .lake already exists", but
`current-user-bytes` was gone, `decoy-bytes` had become `.lake`, and the decoy
path was gone. This violates QPBT-068's no-deletion gate and makes recovery
unsafe for pre-existing worktree bytes. Recovery must operate only on durably
authenticated transaction state, and ambiguous/unowned backup-shaped entries
must fail without moving or deleting either tree.

### High: the accepted external-link fallback still reaches owner-mutable shared output

`scripts/hot_main_cache.py:2022` admits an external resolved target after
checking only current mode bits on the target and descendants. Lines 2024-2027
explicitly omit parent-directory writability and ownership. The target bytes are
also absent from the artifact inventory, which records only the symlink text.
The new positive regression at `tests/test_hot_main_cache.py:3231` creates the
external tree beneath the test's writable temporary directory and accepts it
after `chmod 0555/0444`.

A bounded reproducer seeded that accepted link, then its owner changed the modes
back and rewrote the external marker; the seeded `.lake` immediately read the
new bytes. A writable parent can likewise replace the supposedly read-only
target pathname. Therefore the protocol claim at
`protocols/local-development.md:92` that this prevents a private seed from
reaching shared writable output, and the implementation report's claim at
`workflow/reviews/qpbt-068-cache-safety-a01.md:14`, are false. Either external
links must be rejected, or immutability and target identity need a durable
mechanism stronger than a point-in-time mode check.

### High: cache validation precedes recovery, so a genuine sole backup can remain stranded

Both `seed` and `prepare` require the shared cache to pass deep verification
before calling recovery (`scripts/hot_main_cache.py:3402` versus line 3407, and
line 3450 versus line 3455). After reproducing the actual first-rename crash
state and invalidating `READY`, a bounded call failed with "hot-main cache is
missing or failed deep artifact verification" while `.lake` remained absent and
the sole genuine backup remained stranded. Restoration of prior worktree bytes
does not require a usable source cache and must happen under the target lock
before cache admission. The happy-path SIGKILL test at
`tests/test_hot_main_cache.py:3307` leaves the cache valid and misses this
ordering failure.

### High: metric rollback can truncate another process's committed append

On append or cleanup failure, `_append_metric` exits the metrics-lock context
before invoking rollback (`scripts/hot_main_cache.py:2642`). Rollback then
reacquires the lock at line 2656 and truncates to the old checkpoint at line
2661. A different process can append successfully in that unlocked interval;
the first process then deletes that committed record.

A bounded two-writer reproducer delayed the failing writer immediately before
rollback, committed a second writer's record, and resumed rollback. The second
record disappeared and the JSONL returned exactly to the pre-test bytes. The
single-writer cleanup tests around `tests/test_hot_main_cache.py:2098` do not
exercise this serialization gap. Rollback must occur while continuously holding
the original metrics lock (including short-write/fsync handling), without a
release/reacquire window.

### High: QPBT-067 still falsely reports READY quarantine as implemented

`workflow/reviews/qpbt-067-cache-layout-a01.md:124` still labels the behavior an
"implemented live-process path" and line 126 still says a mismatched `READY`
snapshot "is quarantined". `HotMainCache.is_ready` only returns false, and this
candidate adds no quarantine implementation. This is exactly F-067-A04-001 and
remains unresolved. It also contradicts the "No open implementation finding"
claim at `workflow/reviews/qpbt-068-cache-safety-a01.md:47`.

### High: QPBT-067 still omits required lane/timing evidence and the ordering exception

`workflow/reviews/qpbt-067-cache-layout-a01.md:163` still records no measured
parallel-lane count, audit start/stop time, elapsed time, or latency evidence.
Saying no child agents were dispatched is not the required parallel-lane
measurement. It also does not explain the acceptance-gate ordering exception
under which QPBT-068 was opened before QPBT-067 approval. F-067-A04-003 remains
unresolved.

### Medium: QPBT-067 implementation anchors remain stale and unrelated

`workflow/reviews/qpbt-067-cache-layout-a01.md:9` still anchors lock publication
to protocol lines 39-44, which now describe input preflight; lock publication is
at lines 49-54. Lines 15-17 still anchor cache fields to
`scripts/hot_main_cache.py:1973-1981` (tree walking) and `is_ready` to
`:2179-2229` (Mathlib setup); the actual fields start at line 2132 and
`is_ready` at line 2553. F-067-A04-002 remains unresolved.

### Medium: QPBT-062 provenance is still not authenticated

The authenticated `workflow/state/issues.json` still lists
`workflow/reviews/qpbt-062-branch-lifecycle-a01.md` as a QPBT-067 source, but
that source is not among the manifest-authenticated inputs and the repaired
QPBT-067 report supplies no hash or availability/disposition record for it.
Under the packet's read-only allowlist I did not open the unlisted path.
F-067-A04-004 therefore remains unresolved: existence outside the packet would
not establish the provenance the review requires.

## Claim audit

The changelog's writable-mode rejection and the two tested rename-state
behaviors exist, but its broad lock-serialized/idempotent recovery claim is not
safe because recovery state is unauthenticated and restoration is cache-gated.
The local-development claims of private external targets, no unauthenticated
partial publication, and reliable interrupted-state recovery are contradicted
by the reproducers above. The implementation report's 91/91 focused-test claim
was independently reproduced; its 77/77 workflow, 3/3 check-workflow, and
69-issue ledger claims had no authenticated raw logs in this packet and were
not rerun because those test/program inputs were not manifest-listed.

## Authentication and checks

Manifest SHA-256 matched
`3c7e8c4b00d4e378c8dd8e477f28cfef79c42ed70d2d794a5312c65563b3dd07`.
Twenty-four immutable authentication checks passed: exact review worktree,
inside-worktree state, detached and clean status, head/parent/base/tree,
canonical/base trees, ancestry, six-path changed set, patch SHA-256
`baab726903faed1eb2e903c3116752b6a39b00f389c320f15ff6a05c0573b094`,
and all eleven listed file hashes. `git diff --check` passed.

Focused tests: 91 run, 91 passed, 0 failed, in 19.985 seconds. Adversarial
reproducers: 4 run; 4 reproduced the unsafe behavior described above.
Lean/Lake/full builds: 0. Network/endpoint/GitHub/credential actions: 0.
Repository/Git/state/metric/protocol/candidate writes: 0. Output-report writes:
1 (`/tmp/i068-review-a02-cache-safety.md`). Child/nested agents: 0. Cleanup,
quarantine, cache warm against the real repository, and seed against a real
worktree: 0.

Review start: `2026-09-03T20:36:36.985641344+08:00`. Evidence cutoff:
`2026-09-03T20:42:17.753067643+08:00`. Elapsed wall time:
`340.767426299` seconds. Token usage: `null` (the collaboration backend exposes
no per-session token counters).

## Verdict

**REQUEST_CHANGES**. The candidate does not close the external-link or
crash-recovery safety gaps, introduces a reproducible no-`--replace` deletion
path, preserves a cross-writer metric data-loss race, and leaves all four
QPBT-067 A04 report/provenance findings unresolved. Residual risk includes
untested power-loss durability of directory renames and the unavoidable TOCTOU
surface of path-based external-link validation; rejecting external links is the
smallest defensible policy unless an authenticated immutable-store contract is
introduced.
