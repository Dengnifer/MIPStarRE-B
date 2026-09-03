# LPR-034 / QPBT-051 immutable cache transaction review A11

## Findings

### High - F051-A03-003 remains open: post-fsync cleanup can leave a false seeded metric

Locations: `scripts/hot_main_cache.py:2581-2582`,
`scripts/hot_main_cache.py:2028-2032`, with rollback callers at
`scripts/hot_main_cache.py:3275-3281` and `scripts/hot_main_cache.py:3395-3405`.

`_append_metric` checkpoints the JSONL file, checks the complete `os.write`,
and fsyncs the append. However, its `finally` unconditionally calls
`os.close(descriptor)` after a successful fsync. The surrounding metrics
`ExclusiveLock.__exit__` then unconditionally calls `flock(..., LOCK_UN)` and
`stream.close()`. A failure in any of those post-fsync cleanup operations
propagates from `_append_metric`; `seed`/`prepare` catch it and restore the
replaced target `.lake` through `_rollback_seed_transaction`, but no code
reopens/truncates the already durable metric line to the checkpoint. The
metrics ledger can therefore retain `result:"seeded"` for a target operation
that was rolled back, violating the shared rollback boundary claimed by
`protocols/local-development.md:89-91,103-106` and
`protocols/orchestration.md:223-229`.

The repair tests at `tests/test_hot_main_cache.py:2097-2160` inject only the
first metric `os.fsync` failure and a short `os.write`; they do not inject
descriptor-close, lock-unlock, or lock-stream-close failures after a complete
append. The repair evidence in
`workflow/reviews/qpbt-051-metric-rollback-a09.md:8-18,41-50` consequently
overstates resolution and lists only truncate/fsync failure as residual risk.

Smallest sufficient repair: make post-fsync descriptor and metrics-lock
cleanup non-fatal once the metric append is committed, or retain a rollback
guard that can reacquire the metrics lock and durably truncate the captured
checkpoint before target rollback. Add deterministic regressions for each
post-fsync cleanup seam and assert both target restoration and removal of the
failed success metric.

## Verdict

**REQUEST CHANGES**

The exact candidate cannot be approved while a post-fsync close/unlock failure
can produce a durable success metric for a transaction whose target is then
restored.

## Audit summary

- Manifest authenticated before review: SHA-256
  `9d6553bdd9e538eee4c8a5df909e85ddf4a49ceabf4648b319f952d52fa7ab4a`.
- Candidate base/head/tree: `e8b790a32c230aaf0f17ca2aa389ef41f94867f3` /
  `6f053f79512613f0576245bc9a8cd2a2a8ac7d81` /
  `37d243fc391208018277fbd30086779c3598f767`; full patch digest
  `d459ec0af6e1a30e00aa5470abe983808468d2ed3e503fa1124212a49018e73f`.
- Repair range is exactly the declared three paths (`scripts/hot_main_cache.py`,
  `tests/test_hot_main_cache.py`, and the A09 evidence report); the full
  candidate changed-path list matches the manifest declaration.
- Lock/publication ordering, authenticated captured-input handling, authored
  QPBT preservation checks, and replacement state tracking remain present in
  the inspected candidate. No other blocker was found; the cleanup exception
  leaves the transaction contract and protocol claims materially false.
- No tests, compilation, builds, cache/materialization, network, endpoint,
  GitHub, credentials, or repository/state/metrics/protocol writes were run.
  Nested agents: 0. Token usage: `null` (not exposed by the collaboration
  backend).

