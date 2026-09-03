# LPR-034 / QPBT-051 immutable cache transaction review A10

## Findings

### High - F051-A03-003 remains open: post-fsync metric cleanup errors bypass metric rollback

Location: `scripts/hot_main_cache.py:2581`

`_append_metric` checkpoints the metrics file and correctly compensates short
writes and fsync failures by truncating and fsyncing the prefix. However, the
`finally` block calls `os.close(descriptor)` after that successful fsync, and
the enclosing `ExclusiveLock` context releases its lock and closes its stream
after the body returns. An `os.close`, lock-unlock, or lock-stream-close
failure therefore propagates after the metric bytes are durable, without
reopening/truncating to `checkpoint`. `seed` and `prepare` catch that failure
and restore the replaced `.lake`, leaving a durable `result:"seeded"` record
for an operation whose target was rolled back. This violates the protocol's
claim that publication, validation, and success-metric append share one
rollback boundary (`protocols/local-development.md:89-91`,
`protocols/orchestration.md:226-229`).

The candidate regressions cover injected short writes and fsync failures at
`tests/test_hot_main_cache.py:2097` and `:2128`, but do not inject descriptor
close or metrics-lock cleanup failures after a complete append. Add
deterministic seam tests for both cleanup paths, and either make post-commit
cleanup non-fatal after a successful fsync or retain a rollback guard that can
reacquire the metrics lock and truncate the captured checkpoint before the
target transaction is rolled back.

## Verdict

**REQUEST CHANGES**

F051-A03-003 is not disposed: short-write and fsync compensation is present,
but a fallible cleanup path can still publish a false success metric when seed
or prepare restores the target. No approval is possible until the metric
append commit/cleanup contract is made atomic and regression-tested.

## Positive checks and residual risk

- The candidate keeps one target-operation lock from admission through seed,
  authenticated module/pin loading, foundation materialization, final authored
  and cache checks, and success-metric append.
- `_SeedReplacement` distinguishes `old_moved` and `new_published`; failed
  first renames do not withdraw an untouched destination, and ordinary
  publication/validation/metric failures restore the prior `.lake`.
- `_append_metric` uses a locked checkpoint, detects short writes, fsyncs the
  append, and performs compensating truncate/fsync on write or fsync failure.
  Its documented residual risk remains filesystem failure during that
  compensating rollback; the cleanup gap above is additional.
- Authenticated captured-byte adapters, post-verifier authored-QPBT checks,
  mandatory foundation replacement, and the declared five-path repair scope
  are preserved. No authored QPBT files are changed by the candidate paths.

## Authentication and scope

- Review manifest SHA-256 matched the packet: `8110664963ad502b1835c1cc96e8350283552c7adf2d76bf455aef07e94d971a`.
- Candidate code/protocol/review inputs matched all listed hashes for the
  seven candidate paths and seven external reports. The three
  canonical-checkpoint state files in the mutable worktree did not match
  their manifest hashes and were treated as untrusted runtime state, not as
  evidence for this verdict.
- Candidate range and repair range were inspected from the authenticated
  worktree packet: base `e8b790a32c230aaf0f17ca2aa389ef41f94867f3`, head
  `6f053f79512613f0576245bc9a8cd2a2a8ac7d81`, head tree
  `37d243fc391208018277fbd30086779c3598f767`, full patch SHA
  `d459ec0af6e1a30e00aa5470abe983808468d2ed3e503fa1124212a49018e73f`, and
  repair patch SHA
  `81f6943945765efe3b87e5114c58ab1f1205671af17825ea0ab358f072518cca`.
- Changed paths are exactly the seven manifest-declared candidate paths;
  repair paths are exactly the three declared repair paths. No repository,
  Git, state, metrics, protocol, cache, worktree, or authored-source writes
  were made.

## Validation and accounting

No tests, compilation, Lean/Lake commands, builds, cache/materialization
operations, network, endpoint, GitHub, or credential operations were run;
the review packet explicitly prohibits them. Static source and test inspection
covered the required transaction ordering and exception paths.

- Reviewer session: `i051-reviewer-a10-cache-transaction`.
- Nested agents: 0.
- Token usage: `null` (not exposed by the collaboration backend).
- Output is limited to this report at `/tmp/i051-review-a10.md`.


