# QPBT-045 / LPR-024 immutable review A03

## Findings

### F-LPR024-001 - High - Authored-tree traversal can follow a replaced directory

`scripts/hot_main_cache.py:519` starts `os.walk` on the lexical `QPBT` path
after only an earlier `lstat`-style check at `scripts/hot_main_cache.py:506`.
Files are then reopened by full lexical path at `scripts/hot_main_cache.py:530`;
the `O_NOFOLLOW` at `scripts/hot_main_cache.py:456` protects only the final
component.  Neither the root nor intermediate directories are descriptor-bound,
and no directory inode/incarnation is checked before and after traversal.

A deterministic read-only probe replaced `MIPStarRE/QPBT` with a symlink to an
external, byte-identical tree after the root check and before `os.walk`.  The
function accepted the symlinked external tree and returned exactly the baseline
file count, byte count, and digest while `QPBT.is_symlink()` was true.  The same
gap exists for an intermediate directory replaced between `os.walk`'s link
test and its later scan/open.  Therefore the docstring's "without following
links" claim and the five-boundary source-confinement gate are false under the
explicit concurrent-substitution threat model.

The established pattern at `scripts/materialize_lake_packages.py:434` binds
child directories with `O_DIRECTORY | O_NOFOLLOW` and `dir_fd`; its
`BoundDirectory` also checks lexical incarnation at
`scripts/materialize_lake_packages.py:458`.  The new inventory needs equivalent
descriptor-anchored recursion, including fail-closed scan errors and root and
child incarnation checks.  Add deterministic regressions for root and nested
directory replacement.  The lexical walker in `materialize_mipstarre.py` does
not compensate for this independent verifier gap.

### F-LPR024-002 - High - Exact hard-linked authored files publish as READY

`scripts/hot_main_cache.py:462` accepts any regular file, and the identity at
`scripts/hot_main_cache.py:474` omits `st_nlink`.  A two-link file containing
the exact committed bytes therefore has the expected inventory.  This differs
from the existing authenticated materializer pattern, which requires
`st_nlink == 1` before and after reads at
`scripts/materialize_lake_packages.py:687` and
`scripts/materialize_lake_packages.py:698`.

The reviewer ran the complete identity-isolated fake warm: immediately after
the fake build, `Owned.lean` was replaced by a hard link to an external file
with the exact committed bytes.  Git reported the checkout clean; every
authored inventory/source-evidence check passed; `warm()` returned `built`;
`is_ready(deep=True)` returned true; and the snapshot was published.  This
directly contradicts the claims that any linked source fails closed in
`protocols/CHANGELOG.md:21` and `protocols/local-development.md:52`.

Require a single-link regular file, include link count (and the existing strong
file identity fields) in both before/after identity checks, and add a full-warm
hard-link regression proving no snapshot and no `READY`.

### F-LPR024-003 - Medium - Unreadable generated subtrees are silently omitted

`scripts/hot_main_cache.py:519` supplies no `onerror` callback to `os.walk`, so
a nested `scandir` failure is silently skipped.  The surrounding cleanliness
check at `scripts/hot_main_cache.py:680` also discards Git stderr whenever Git
exits zero.  A deterministic probe added `QPBT/Hidden/Generated.lean`, removed
all permissions from `Hidden`, and observed the exact baseline authored
inventory.  `git status --porcelain=v1 --untracked-files=all` then exited zero
with empty stdout and only a permission-denied warning on stderr, so
`git_source_changes()` would also report no drift.

This violates the acceptance gate for added, untracked, and generated QPBT
source.  Descriptor-anchored traversal must fail on every scan/stat/open error;
the cleanliness check must also fail closed on diagnostics that mean the tree
was not completely inspected.  Add a regression covering an unreadable nested
generated source and no `READY` publication.

## Verdict and gate

Verdict: **request changes**.  LPR-024 must not be approved, integrated, or
used for the guarded real warm until all three findings are repaired on a new
immutable head and a fresh review authenticates that head.  In particular,
INC-060 remains open and QPBT-045 remains a Lean-build blocker.

## Authentication

| Item | Authenticated value |
| --- | --- |
| Formal base / tree | `f4b00c7616b8710220a4f8480cfb23412914d151` / `f120a82f74df4d32bfb6b0491636546c7651b64a` |
| Reviewed head / tree | `bc41314fb74baced6f6a043cbc8956a18a2e0003` / `c71eb62b31004c1b219f93e25475d5f1aa7356b7` |
| Head parent | sole parent `f4b00c7616b8710220a4f8480cfb23412914d151` |
| Exact changed paths | five: both protocol files, cache implementation/test, and A01 report |
| Path-sorted `git ls-tree` manifest SHA-256 | `2707b1097d9d3cc4ba2588f54b88ea8ac159ce8c6d0d3e3ec08d91ea0b38fd26` |
| A01 report SHA-256 | `738890e5eaa16e9d29efda6e1b1153a555744380aab2c5e20093adae073e15e5` |
| Diff size | 5 files, 621 insertions, 7 deletions |

The detached worktree was clean before and after review.  `git diff --check`
passed.

## Validation and inspected behavior

| Gate | Result |
| --- | --- |
| `python3 tests/test_hot_main_cache.py` | pass, 51/51; test-reported 11.732 s |
| `python3 tests/test_mipstarre_materialization.py` | pass, 11/11; test-reported 0.555 s |
| `python3 scripts/workflow.py validate --json` | pass; 48 issues, 23 PRs, 0 planned sessions, 392 issued sessions, 7 stages |
| `python3 scripts/check_workflow.py --skip-tests` | pass |
| `git diff --check BASE..HEAD` | pass |
| Root-symlink substitution probe | fail: byte-identical external tree accepted through replaced root |
| Hard-link helper probe | fail: two-link regular file accepted as exact inventory |
| Full fake warm with hard-linked `Owned.lean` | fail: `built`, deep-ready true, snapshot published |
| Unreadable generated-subtree probe | fail: inventory unchanged; Git exits zero with warning only on discarded stderr |

The candidate does correctly bump the recipe to v6, binds the changed argv into
identity, includes `--replace-existing`, places calls at all five named
boundaries, and binds the declared inventory/phase list into manifest readiness.
The focused tests also demonstrate ordinary missing/altered/untracked/static
symlink/generated failures and materializer replacement/rollback behavior.
Those positive checks do not close the adversarial traversal and hard-link
gaps above.

No second aggregate was run, as instructed; A01's aggregate evidence was
inspected but treated as untrusted.  No real cache warm, seed, build,
publication, Lean/Lake command, network or endpoint request, GitHub operation,
credential access, repository write, Git write, or nested-agent dispatch
occurred.  Probe publication existed only inside an automatically cleaned
temporary fixture.

## Metrics and residual risk

- Canonical reviewer: `i045-reviewer-a03-pr024-immutable`
- External collaboration ID: `/root/i045_pr024_review_a03`
- Topology: root coordinator -> one fresh read-only reviewer; nested agents: 0
- Physical start: `2026-09-01T16:42:48.906801Z`
- Evidence freeze: `2026-09-01T16:50:28.909983Z`
- Reviewer-measured elapsed through evidence freeze: 460.003182 s
- Token usage: JSON `null`; availability reason: collaboration backend does
  not expose per-agent token usage.  No estimate was made.
- Focused suite attempts: 2, both passed; workflow/checker attempts: 2, both
  passed; adversarial probes: 4 (root substitution, hard-link helper, full
  hard-link warm, unreadable subtree), all reproduced their target gap.
- Aggregate, Lean/Lake, production cache, network, and nested-session attempts:
  0.

Residual risk after these findings is repaired includes the real pinned-input
materialization/build path and filesystem-specific behavior of the eventual
descriptor walker.  Those remain for the post-repair immutable review and the
single lock-elected post-integration warm; they are not reasons to weaken the
current request-changes verdict.
