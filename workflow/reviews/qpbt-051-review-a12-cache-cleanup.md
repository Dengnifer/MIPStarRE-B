# LPR-034 / QPBT-051 immutable cache cleanup review A12

## Findings

No findings. `F051-A03-003` is resolved for the reviewed post-fsync cleanup
seams.

## Verdict

**APPROVE**

The exact candidate head `69b77a6c12865173e204d16867b5390a7589a315` may proceed
past this review gate. In `_append_metric`, the JSONL length is captured while
holding `metrics_lock_path` (`scripts/hot_main_cache.py:2571-2585`). Descriptor
close and both lock teardown operations are inside the outer `BaseException`
boundary (`scripts/hot_main_cache.py:2573-2595`; `ExclusiveLock.__exit__` at
`scripts/hot_main_cache.py:2028-2042`). When any of those operations fails after
the append/fsync, `_rollback_metric_append` reacquires the metrics lock,
truncates to the captured checkpoint, and fsyncs that truncation before the
original error is propagated (`scripts/hot_main_cache.py:2597-2618`).

Both caller transactions retain the replacement state and restore the target
after metric failure (`scripts/hot_main_cache.py:3278-3322` and
`scripts/hot_main_cache.py:3324-3446`), so a failed `seed` or `prepare` cannot
return with the failed `result:"seeded"` append left in the ledger for the
three reviewed cleanup faults.

The added regressions inject descriptor-close, metrics-lock unlock, and
metrics-lock stream-close failures after a complete append and assert both
restoration of the original `.lake` and removal of every `result:"seeded"`
record (`tests/test_hot_main_cache.py:2161-2278`). Existing fsync and short-write
tests cover the earlier append faults (`tests/test_hot_main_cache.py:2097-2159`).
The protocol claims match this ordering: the backup remains rollback-capable
through the success-metric append and cleanup is nonfatal only after commit
(`protocols/local-development.md:83-106`, `protocols/orchestration.md:219-229`,
`protocols/CHANGELOG.md:23-37`).

The compensating rollback still depends on the filesystem allowing lock
reacquisition, truncate, and fsync; if that independent rollback itself fails,
the code raises an explicit rollback-failed error. That is the documented
durability residual in the authenticated A09 evidence, not an unhandled
post-fsync descriptor/lock-cleanup path.

## Authentication and scope

- Review manifest SHA-256: `9338ce735b01a0f1c3cd0f4e9ec4f8b3c9fcda1f29398b908e83e4c2e2d2d577` (exact match).
- Candidate base/head/tree/sole parent: `e8b790a32c230aaf0f17ca2aa389ef41f94867f3` / `69b77a6c12865173e204d16867b5390a7589a315` / `e86475c40c243d0b997431df8db804eca435b87e` / `6f053f79512613f0576245bc9a8cd2a2a8ac7d81`.
- Full binary patch SHA-256: `6ccacbb4338d64a23cde5651eccf6463085572b83758bcc4f7b4c3f46954a537`.
- Repair patch SHA-256: `8e73965e1de438e9d79757ae4069e362d3075f38ab8e6f20fd0b162d70f0d35b`.
- All candidate and canonical-checkpoint blobs listed by the manifest matched
  their locator and declared SHA-256; the two filesystem reports also matched.
- Full changed paths are exactly the seven manifest paths; repair paths are
  exactly `scripts/hot_main_cache.py` and `tests/test_hot_main_cache.py`.
- Authenticated-input preflight, target lock lifetime, publication state, and
  authored-QPBT preservation checks remain present in the inspected candidate.

## Accounting

- Findings: 0 (F051-A03-003 resolved).
- Verdict: `APPROVE`.
- Repository writes: 0; report write: 1 (`/tmp/i051-review-a12-cache-cleanup.md`).
- Tests, compilation, builds, cache/materialization, network, endpoint,
  GitHub, credentials, and nested agents: 0 (prohibited by the review packet).
- Token usage: `null` (collaboration backend does not expose per-session token
  usage; none estimated).
- Elapsed time: unavailable from the backend; no runtime estimate made.
- Report line count: 69 (final file, including this metadata).
- Report SHA-256 (all bytes before this metadata, since a file cannot contain
  its own complete self-hash): `97b41212985a119e17bc8c4905658c6d29df99fcfe75d182f4c7eaadb35ce23f`.
