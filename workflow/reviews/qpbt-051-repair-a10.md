Issue: QPBT-051
PR: LPR-034
Session: i051-fixer-a10-cache-cleanup
Worktree: /home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-051-metric-rollback-a09

Outcome: Implemented rollback for metric append failures occurring during
post-fsync descriptor close, metrics-lock unlock, or metrics-lock stream close.
ExclusiveLock now attempts both teardown operations and preserves the first
cleanup error. Added deterministic seed regressions for all three seams; each
asserts replacement target restoration and removal of result:"seeded".

Changed paths:
- scripts/hot_main_cache.py
- tests/test_hot_main_cache.py

Validation:
- python3 -m py_compile scripts/hot_main_cache.py tests/test_hot_main_cache.py: PASS
- PYTHONPATH=tests python3 -m unittest test_hot_main_cache test_check_workflow test_focused_command: 90 tests, PASS (35.293s)
- git diff --check: PASS
- authored-QPBT/forbidden-assumption scan in owned paths: PASS (no matches)

Hashes:
- base commit: 6f053f79512613f0576245bc9a8cd2a2a8ac7d81
- base tree: 37d243fc391208018277fbd30086779c3598f767
- base parent: 7ed086c834f41525cff78d1fc42ee22bcd7852e2
- working-tree binary patch: 8e73965e1de438e9d79757ae4069e362d3075f38ab8e6f20fd0b162d70f0d35b
- commit after coordinator reconciliation: `69b77a6c12865173e204d16867b5390a7589a315`
- commit tree: `e86475c40c243d0b997431df8db804eca435b87e`
- sole parent: `6f053f79512613f0576245bc9a8cd2a2a8ac7d81`
- coordinator commit note: the agent could not write the managed worktree index; the coordinator created this exact two-path commit with approved local Git escalation

Elapsed time: approximately 7 minutes
Token usage: null (not exposed by collaboration backend)
Commit reconciled by coordinator from the unchanged clean handoff; assigned worktree is clean at the exact commit above.

