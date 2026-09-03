# QPBT-051 metric rollback repair evidence

Session: `i051-fixer-a09-cache-metric`
Issue/review: `QPBT-051` / `LPR-034`

## Verdict

Finding `F051-A03-003` is resolved. `_append_metric` now records the metric
file length while holding the metrics lock, checks that the complete JSONL
record was written, and fsyncs the append. Any write, short-write, or fsync
failure truncates the file back to the checkpoint and fsyncs the compensating
rollback before propagating the original failure. Seed and prepare therefore
cannot leave a persisted `result:"seeded"` record when their replacement
transaction rolls back.

## Regression coverage

- `test_seed_metric_fsync_failure_rolls_back_metric_and_replaced_seed` injects
  a failure at the real `os.fsync` seam after a complete metric line reaches
  the file, then verifies the original `.lake` and metric prefix remain.
- `test_seed_metric_short_write_rolls_back_metric_and_replaced_seed` injects a
  deterministic short `os.write`, then verifies no partial JSONL line or false
  `result:"seeded"` remains and the original `.lake` is restored.

Both tests retain the pre-existing warm metric, proving rollback preserves
prior records while removing only the failed append.

## Validation and accounting

No Lean/Lake/full build, network, endpoint, GitHub, credential, canonical
state/metrics, or unrelated path was touched. Nested agents: 0. Token usage:
`null` (collaboration backend does not expose per-session token usage).

| Gate | Result |
| --- | --- |
| Python compile | pass |
| Focused metric regressions | 2/2 pass in 0.729s |
| Full `test_hot_main_cache.py` | 82/82 pass in 36.997s |
| `git diff --check` | pass |

The final candidate commit/tree/parent and patch/report hashes are supplied to
the root coordinator out of band because the report cannot contain its own
final digest.

## Residual risk

If the filesystem fails during the compensating truncate or its fsync, the
append raises an explicit rollback-failed error; retained metric bytes are
never reported as a successful operation by this process, but external crash
recovery still depends on filesystem durability guarantees.
