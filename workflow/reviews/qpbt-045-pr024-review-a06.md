# QPBT-045 / LPR-024 changed-head immutable review A06

## Findings

### F-LPR024-004 - High - Valid exact authored trees can be rejected because the two inventories hash different orders

`scripts/hot_main_cache.py:442` sorts committed records by their complete
relative path, while `scripts/hot_main_cache.py:767` hashes the on-disk records
in descriptor walk order without a final path sort. Those orders differ for a
normal Lean layout containing both a same-stem module and namespace directory.
For example, the disk walk visits `Game/Types.lean` before `Game.lean`, while
the committed path sort places `Game.lean` before `Game/Types.lean`.

An independent two-file Git fixture reproduced the failure on this exact head.
Both inventories reported 2 files and 51 bytes, but the committed digest was
`c67d9fd193393b892ef2eb67245b778255f9089b2a7b2b84279b5d5990e00970`
and the disk digest was
`d96c8d7e0256b245a1ef21511d8e218b0eda4e69f4ab6ad6f5681f796fa154c1`.
Thus an exact committed source tree is rejected at the first inventory phase,
and the singleton hot-main cache cannot build it. This violates the exact
source-preservation contract of QPBT-045 and is a build blocker, although it
fails closed rather than publishing an unsafe snapshot.

Required change: sort `records` by the complete relative path immediately
before computing the on-disk digest, and add a regression comparing committed
and on-disk facts for an exact `Game.lean` plus `Game/Types.lean` fixture.

### F-LPR024-001 - Medium - The required substitution publication regression remains helper-only

`tests/test_hot_main_cache.py:907` exercises root and nested replacement only by
calling `authored_tree_facts_on_disk`. It never runs `HotMainCache.warm`, so it
cannot assert the formal A04 repair gate's required absence of a snapshot and
`READY` for both replacement cases. The descriptor-bound implementation itself
appears repaired: the focused suite rejected both substitutions, an independent
nested substitution probe raised `CacheError`, and an independent complete fake
warm rejected root substitution while leaving the external sentinel unchanged
and publishing neither a snapshot nor `READY`.

Formal disposition: not resolved. Preserve the helper coverage, but add
identity-isolated complete-warm root and nested substitution regressions that
assert `CacheError`, no snapshot, no `READY`, and no external mutation.

### F-LPR024-003 - Medium - The required Git-diagnostic publication regression remains helper-only

`tests/test_hot_main_cache.py:965` proves only that a direct
`git_source_changes` call rejects exit-zero stderr. The full unreadable-subtree
test at `tests/test_hot_main_cache.py:1017` proves the scan-error publication
path, but no committed test injects successful-Git diagnostics into a complete
warm and proves that publication stays absent. An independent complete fake
warm on this head did reject an exit-zero warning and produced neither a
snapshot nor `READY`, so the production control flow appears correct; the exact
A04 adversarial regression gate is nevertheless not durable.

Formal disposition: not resolved. Add an identity-isolated full-warm Git-warning
regression that reaches the cleanliness boundary and asserts `CacheError`, no
snapshot, and no `READY`.

## Finding dispositions

| Finding | Disposition on changed head | Evidence |
| --- | --- | --- |
| `F-LPR024-001` | open; production repair works, required end-to-end regression incomplete | Root and nested descriptor substitutions reject; root full-warm probe publishes nothing; repository test is helper-only. |
| `F-LPR024-002` | resolved | Single-link enforcement is present at name-before, descriptor-before, descriptor-after, and name-after boundaries; strong identity includes `st_nlink`; focused helper and full-warm tests pass; independent hard-link full warm rejects with no snapshot or `READY`. |
| `F-LPR024-003` | open; production repair works, required Git-warning end-to-end regression incomplete | Scandir/stat/open/recheck injections fail closed; unreadable full-warm test passes; independent Git-warning full warm publishes nothing; repository Git-warning test is helper-only. |
| `F-LPR024-004` | new, open | Exact same-stem file/directory fixture has equal files and bytes but unequal commit/disk digests due solely to record order. |

## Verdict and integration gate

Verdict: **request changes**. LPR-024 must remain `changes_requested`; QPBT-045
and INC-060 must remain open; this head must not be integrated or used for the
real warm. Repair the deterministic inventory order and add the two missing
complete-warm adversarial regressions. The changed head must then pass focused
and aggregate gates, receive a fresh immutable review, and resolve all four
finding dispositions. Only an approval of that exact new head permits guarded
integration, followed by exactly one lock-elected real current-main recipe-v7
warm.

## Immutable authentication

| Item | Independently authenticated value |
| --- | --- |
| Formal base / tree | `f4b00c7616b8710220a4f8480cfb23412914d151` / `f120a82f74df4d32bfb6b0491636546c7651b64a` |
| Changed head / tree | `3c3f0c15aef87920d0668cc18d1fd03bc0274b7f` / `af566d43899a77dc328325eb2f08fd8b786198f2` |
| Changed-head ancestry | sole parent `bc41314fb74baced6f6a043cbc8956a18a2e0003`; that commit's sole parent is the formal base |
| Full PR scope | six expected paths; 1,204 insertions and 8 deletions |
| A05 commit scope | five expected paths; 679 insertions and 97 deletions |
| A05 path-sorted `git ls-tree` manifest SHA-256 | `bab2e635156e4fbb9ac66ebddff6c3c6601e5c892a6f26a593ee4703d58416bb` |
| A05 report SHA-256 | `d4696c054f7d002631e1e6a7ac0505f92c847f22701ededd916be20db79ed894` |
| A04 report SHA-256 | `69aa23141d57e3a69abd9ce331c7dec767f6e82cd4f75e87a817a4535734730d` |
| Registered checks | 14/14 passed; latest completion `2026-09-01T17:24:09.578144Z`, before reviewer start |

The full PR paths are `protocols/CHANGELOG.md`,
`protocols/local-development.md`, `scripts/hot_main_cache.py`,
`tests/test_hot_main_cache.py`, the A01 writer report, and the A05 repair
report. The A05 manifest contains the first four paths plus its repair report.
The detached worktree was clean before review; full-base `git diff --check`
passed.

## Checked scope and validation

The descriptor implementation was inspected through the project, foundation,
authored root, recursive child, and file boundaries, together with the local
authenticated materializer pattern. Directory binds use `O_DIRECTORY` and
`O_NOFOLLOW`, compare name/descriptor identities, and recheck lexical
incarnations. Scans use bound descriptors and propagate enumeration,
inspection, open, read, and recheck errors. File identity includes device,
inode, mode, size, mtime, ctime, and link count; every strong boundary requires
`st_nlink == 1`. Nonempty successful-Git stderr raises `CacheError`.

All five authored phases occur in the warm path. The expected inventory and
phase list are sealed into the manifest, `READY` binds the manifest digest, and
readiness compares recipe, source contract, source evidence, and authored
verification with the exact cache identity. Recipe version 7 is identity
bearing and therefore makes version-6 snapshots unaddressable. Apart from the
ordering defect and incomplete durable regressions above, the changed protocol
claims match the inspected implementation.

| Gate / probe | Result |
| --- | --- |
| `python3 tests/test_hot_main_cache.py` | pass, 56/56; test-reported 12.520 s, real 12.67 s |
| `python3 tests/test_mipstarre_materialization.py` | pass, 11/11; test-reported 0.513 s, real 0.60 s |
| Current authenticated two-file tree | committed and on-disk facts equal: 2 files, 5,319 bytes, digest `0578da860a522b58b69c2c16df366c7eee3abd97c425900401e4e83c992803ed` |
| Same-stem exact-tree probe | reproduced F-LPR024-004: equal counts/bytes, unequal digest |
| Full-warm root substitution | rejected; external unchanged; no snapshot or `READY` |
| Nested substitution | rejected; external unchanged |
| Full-warm exact hard link | rejected; no snapshot or `READY` |
| Full-warm exit-zero Git warning | rejected; no snapshot or `READY` |
| Injected scandir/stat/open/recheck errors | all four rejected with `CacheError` |
| `git diff --check BASE..HEAD` | pass |

No aggregate was rerun. No real cache warm, cache seed, Lean/Lake command,
production build or publication, network or endpoint request, GitHub action,
credential access, repository edit, canonical state/metric edit, Git write, or
nested-agent dispatch occurred. All probes used automatically removed temporary
fixtures.

## Metrics

- Canonical session: `i045-reviewer-a06-pr024-resolution`.
- External collaboration ID: `/root/i045_pr024_review_a06`.
- Topology: root coordinator -> one fresh read-only reviewer; nested agents: 0.
- Durable start: `2026-09-01T17:27:23.425022Z`.
- Evidence freeze: `2026-09-01T17:39:25.083251Z`.
- Reviewer elapsed through evidence freeze: `721.658229` seconds.
- Token usage: JSON `null`; availability reason: collaboration backend does
  not expose per-agent token usage. No estimate was made.
- Focused suite attempts: 2, both passed; 67 tests total.
- Independent adversarial probe commands: 4; nine bounded outcomes (one
  ordering mismatch, eight expected fail-closed rejections). Positive current
  tree comparison commands: 1.
- Aggregate, Lean/Lake, real warm/seed/build/publication, network, and nested
  session attempts: 0.
- Candidate/repository files edited: 0. Review report files edited: 1.

The exact report SHA-256 and final clean-worktree authentication are returned
out of band to avoid self-reference.
