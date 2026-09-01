# QPBT-045 / LPR-024 immutable review A08

## Findings

### F-LPR024-001 - resolved - root/intermediate directory substitution

The candidate binds the project, `MIPStarRE`, `QPBT`, and recursive child
directories with `O_DIRECTORY|O_NOFOLLOW` descriptors and checks the lexical
incarnation before binding, before/after scanning, and after recursion
(`scripts/hot_main_cache.py:455-765`). File and directory entries are then
resolved relative to the held descriptor. The six targeted end-to-end tests
passed, including root and nested replacement. Each replacement raised at
`before_materialization`, left the external sentinel unchanged, created no
snapshot or `READY`, and left no `READY` in retained failure state.

Disposition: **resolved** by the exact changed head. No residual finding.

### F-LPR024-002 - resolved - hard-linked authored file

`_authored_file_facts` rejects non-regular and `st_nlink != 1` files at name
inspection, descriptor binding, descriptor post-read, and final name
inspection, and includes link count in the strong identity
(`scripts/hot_main_cache.py:599-653`). The helper and complete-warm hard-link
regressions passed. The complete warm rejected the linked file at
`after_build`, published no snapshot or `READY`, and retained no `READY`.

Disposition: **resolved** by the exact changed head. No residual finding.

### F-LPR024-003 - resolved - scan errors and Git diagnostics

Every authored `scandir`, stat, open, read, and recheck `OSError` is converted
to `CacheError` (`scripts/hot_main_cache.py:668-721`). `git_source_changes`
rejects nonempty stderr even when Git exits zero (`scripts/hot_main_cache.py:904-927`).
The unreadable generated-subtree and exit-zero Git-warning full-warm tests
passed; each raised at the expected phase, published no snapshot or `READY`,
and retained no `READY`.

Disposition: **resolved** by the exact changed head. No residual finding for
the requested scan/diagnostic contract.

### F-LPR024-004 - resolved - deterministic authored inventory ordering

`authored_tree_facts_on_disk` now sorts records by complete relative path before
digesting (`scripts/hot_main_cache.py:767-770`), matching
`authored_tree_facts_at_commit` (`scripts/hot_main_cache.py:442-447`). An
independent temporary Git fixture containing `Game.lean` and
`Game/Types.lean` produced equal committed/on-disk facts (2 files, 11 bytes,
digest `9e4e1015dd7f1fb79a206b888775a6b8445e49b3d888216001f2571f6fd83407`).
The durable complete-warm same-stem regression passed and deep readiness was
true.

Disposition: **resolved** by the exact changed head. No residual finding.

### F-LPR024-005 - Medium residual, pre-existing and out of scope

`git_source_changes` invokes `git status` without the existing
`_trusted_git_environment` (`scripts/hot_main_cache.py:915`), so ambient or
repository `core.fsmonitor` configuration can execute a hook. A bounded probe
with only `GIT_CONFIG_GLOBAL` pointing to a hook touched an external marker;
an identity-isolated preserving-recipe warm still built and published a ready
cache. The same
behavior is present on the formal base and is unchanged by A07. A07's accepted
scope is authored descriptor/link/scan integrity, successful-Git diagnostic
fail-closed handling, inventory ordering, and the corresponding durable
regressions; it does not change Git environment isolation. This is a real
follow-up hardening item, but it is not a new LPR-024 regression and does not
invalidate the four requested dispositions.

Disposition: **non-blocking residual**; track separately from LPR-024. The
probe did not bypass any authored inventory check or create a cache under an
authored failure. The implementation should use `_trusted_git_environment`
for this status call in a future security repair.

## Verdict and integration gate

**APPROVE** the exact head `39c9ee0d74c929cbd4a1fc98be970f4d6c6c8a16` for
guarded integration. F-LPR024-001 through F-LPR024-004 are resolved. The
non-blocking F-LPR024-005 residual is pre-existing and out of scope for this
candidate. Integration must preserve the authenticated base/head/tree and run
exactly one lock-elected current-main recipe-v7 warm; do not retry the older
recipe-v5 path. No real warm, seed, build, or publication was performed in
this review.

The warm path independently verifies authored inventory at all five boundaries
(`before_materialization`, `after_materialization`,
`after_dependency_retrieval`, `after_build`, `before_publication`), records the
recipe-v7 inventory/phases in the manifest, and binds `READY` to manifest bytes.
The canonical materializer command includes `--replace-existing`; the
materializer remains identity-bound through the versioned command and pin
inputs. Failure paths retain diagnostics and remove staging without leaving a
`READY` marker.

## Authentication

| Item | Authenticated value |
| --- | --- |
| Formal base commit | `f4b00c7616b8710220a4f8480cfb23412914d151` |
| Formal base tree | `f120a82f74df4d32bfb6b0491636546c7651b64a` |
| Changed head commit | `39c9ee0d74c929cbd4a1fc98be970f4d6c6c8a16` |
| Changed head tree | `105854b569b76a6c2103ac2c22e512454afe0c53` |
| Changed-head parent | `3c3f0c15aef87920d0668cc18d1fd03bc0274b7f` |
| Required three-path manifest SHA-256 | `11ee7fbec15a1bda08bcfc94da37232a191f48ac19a94f29af1c8299bc006c6b` |
| A06 report SHA-256 | `d400d0653cd15a987c3ccc4b942d0bce3222b9e95f43f94833134bb18757c7a3` |
| A07 report SHA-256 | `3dbca3c82dd9e5131c69823529e0b44b1f4b9b50b70ccb262e1c60acf831e13f` |
| Detached worktree | clean, detached at changed head |

The full base-to-head diff contains exactly the seven expected paths:

```text
protocols/CHANGELOG.md
protocols/local-development.md
scripts/hot_main_cache.py
tests/test_hot_main_cache.py
workflow/reviews/qpbt-045-hot-main-preservation-a01.md
workflow/reviews/qpbt-045-hot-main-preservation-a05.md
workflow/reviews/qpbt-045-hot-main-preservation-a07.md
```

## Validation and counters

| Check | Result | Measured time |
| --- | --- | ---: |
| `python3 tests/test_hot_main_cache.py` | 60/60 passed | 12.813 s |
| `python3 tests/test_mipstarre_materialization.py` | 11/11 passed | 0.577 s |
| Six exact full-warm adversarial tests | 6/6 passed | 0.606 s |
| Same-stem independent inventory probe | equal facts | 0.3 s |
| `python3 -m compileall -q scripts tests` | passed | 0.088 s |
| `python3 scripts/workflow.py validate --json` | valid: 48 issues, 23 PRs, 392 issued sessions, 7 stages | <0.1 s |
| `python3 scripts/check_workflow.py --skip-tests` | valid | <0.1 s |
| `python3 tests/test_check_workflow.py` | 3/3 passed | 0.004 s |
| `git diff --check BASE..HEAD` | passed | <0.1 s |

Aggregate workflow suite: **0 attempts** in A08 (A07's single 358/358 result
was not rerun). Real warm/seed/build/cache publication: 0. Lean/Lake: 0.
Network, endpoint, GitHub, credentials: 0. Nested agents: 0. Candidate or
canonical repository edits: 0. Review report writes: 1.

Reviewer session started at `2026-09-01T18:01:16.675641Z`; evidence cutoff
`2026-09-01T18:14:09.863559Z`; measured elapsed `773.188` s. Requested model:
`gpt-5.6-sol`. Token usage is JSON `null`; the collaboration backend does not
expose per-agent token usage, so no estimate was made. Topology is root
coordinator -> one fresh read-only reviewer, with zero nested sessions.

## Integration checklist

- [x] Exact base/head/tree/parent and three-path manifest authenticated.
- [x] F-LPR024-001 root and nested substitution fail closed with sentinels and no `READY`.
- [x] F-LPR024-002 hard-link identity rejects helper and full-warm cases.
- [x] F-LPR024-003 scan errors and exit-zero Git diagnostics fail closed.
- [x] F-LPR024-004 same-stem committed/on-disk ordering is deterministic.
- [x] Five authored verification phases, recipe-v7 identity, materializer binding, and `READY` manifest binding inspected.
- [x] Focused, materializer, compile, workflow, checker, test-checker, and diff gates passed.
- [ ] One guarded singleton current-main recipe-v7 warm after integration (root gate).
