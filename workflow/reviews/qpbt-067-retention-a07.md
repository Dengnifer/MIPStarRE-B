# QPBT-067 retention and immediate space-saving scout

Session: `i067-scout-a07-retention` (attempt 7), role `scout`, read-only.
Observed 2026-09-03 (Asia/Shanghai). Current repository checkpoint:

- `HEAD`/main commit: `77db485f56d9c93d5b52f3cb77625852742242cf`
- main tree: `fee57b584ef2ee033ecfad5692009cb1de907cef`
- commit time: `2026-09-03T18:19:46+08:00`
- `github/main...main`: `0 97` (main ahead 97, behind 0)
- local branches: 58; registered worktrees: 132; detached worktrees: 79
- at the first status probe the worktree was already dirty in coordinator-owned
  files (`research/report.md`, `workflow/events.jsonl`, `workflow/state/sessions.json`,
  `workflow/state/stages.json`); later concurrent coordinator activity may add
  status entries. No repository files were changed by this scout.

## Source and packet authentication

The prescribed scout packets were read and their exact SHA-256 values matched:

| packet | SHA-256 |
|---|---|
| `/tmp/i067-scout-a03-storage-architecture.md` | `6491530bd54285b3722e50ed7e9f9739d30ff62fc465e32aa405e1e0b7d7bf09` |
| `/tmp/i067-scout-a04-worktree-topology.md` | `44de7772a2f7e6c4dab750a4cc5bd13b2b7ad216bc7534ec33b966f5e3606283` |
| `/tmp/i067-scout-a05-reflink-capability.md` | `57b230feea5463ea5106f843379455f27dae0a2699a2c32ac5d6089e7492f586` |
| `/tmp/i067-scout-a06-migration-cost.md` | `47985916c0be639dc83b0084c1c6814957068bba5430f3539e55ac6c07d65823` |

Relevant contracts are `protocols/local-development.md:16-27,39-44,64-82`
(content-addressed snapshots, singleton lock, deep seed verification, private
`.lake`, explicit cleanup), and `protocols/orchestration.md:129-182`
(lease/worktree identity, interruption recovery, archive lifecycle). QPBT-067
is in review and blocked by two open findings at
`workflow/state/issues.json:3399-3415`; QPBT-068 is planned and explicitly
requires preserving existing bytes at `workflow/state/issues.json:3420-3465`.

## Current ownership and liveness evidence

`workflow/state/sessions.json` contains 515 issued rows: 512 archived and three
running. The running rows are the root coordinator (`i001-coordinator-a01-bootstrap`,
writable main), `i051-reviewer-a12-cache-cleanup` (read-only), and this scout
(read-only). No running session row records a cache key. A recursive scan found
14 cache keys in session checks, all associated only with archived rows. This is
evidence of ledger state, not proof that an archived worktree or cache is unused.

`workflow/state/prs.json` contains 34 PR rows: 29 merged, three
`changes_requested` (LPR-018, LPR-025, LPR-034), and two closed. None of the
three open/changes-requested heads has a `.lake` tree in its registered
worktree. Several `.lake`-holding branches are unmerged or correspond to blocked
issues (for example `issue/qpbt-004`, `issue/qpbt-004-lean-foundations-a01`,
`issue/qpbt-038-types-a02`, and `issue/qpbt-057-f06a-a01`); they must not be
treated as reclaimable from branch age or archived session status.

Git worktree/session reconciliation found 132 registered worktrees, 117 with at
least one session row and 15 with no session row. The 15 unregistered paths are:

```
.workflow-runtime/worktrees/qpbt-031-pr29-review-a01
.workflow-runtime/worktrees/qpbt-031-pr29-review-a02
.workflow-runtime/worktrees/qpbt-031-review-repairs-a01
.workflow-runtime/worktrees/qpbt-031-review-repairs-a02
.workflow-runtime/worktrees/qpbt-031-review-repairs-a04
.workflow-runtime/worktrees/qpbt-032-f04-contract-a01
.workflow-runtime/worktrees/qpbt-036-guarded-integration-a04
.workflow-runtime/worktrees/qpbt-053-github-canonical-a01
.workflow-runtime/worktrees/qpbt-062-branch-lifecycle-a01
/tmp/qpbt-026-final-activation
/tmp/qpbt-026-final-activation-a27-target
/tmp/qpbt-031-pr29-review-a07
/tmp/qpbt-052-candidate-a03
/tmp/qpbt-second-rehearsal-920e
/tmp/qpbt020-integration-cc5d
```

All 75 repository worktree directories and all 56 `/tmp` worktree directories
listed by Git currently exist. Unregistered means “no ledger owner,” not “dead”;
each requires coordinator disposition and a path/HEAD/cleanliness audit before
any move.

## Footprint observed

The current read-only scan found 18 repository issue-worktree `.lake` trees and
two `/tmp` `.lake` trees. `du -sx -B1` measured 17 session-mapped archived
repository trees totaling `147,082,665,984` bytes and one unregistered
repository tree (`qpbt-036-guarded-integration-a04`) of `10,503,192,576`
bytes. The two `/tmp` trees were `/tmp/qpbt-023-lean-api-a03` at
`10,497,339,392` bytes (archived read-only scout `i023-scout-a03-lean-api`) and
`/tmp/qpbt-031-pr020-review-a01` at `8,192` bytes (archived read-only reviewer).
These are physical `du` values from this scan; they are not deletion
recommendations.

The prior authenticated QPBT-067 audit remains the evidence of record for the
larger aggregate: 13 `cache/main` snapshots, `136,463,261,696` physical bytes;
18 issue-worktree trees, `158,283,636,736` physical bytes; 14 retained failure
directories; 45 metric records; and no observed file link count greater than
one. It measured package/build totals of `95,852,466,176`/`40,590,970,880`
bytes in snapshots and `112,684,318,720`/`44,877,463,552` bytes in issue trees.
The current scan found 13 snapshot directories and 13 `READY` files (each 65
bytes). The current main key from `python3 scripts/hot_main_cache.py status`
is `b331ba76785c88651dacca64832f348ccfdbd3958865f47efa0a7edd33eacdfc`; its
status is `miss`, so no current-main snapshot is available to reclaim.

The runtime has 22 `hot-main-*` lock files and 15 `seed-*` lock files. They are
zero-byte metadata files. `lslocks` showed no holder for these paths during the
scan, but absence of a holder at one instant is not a lease proof; deleting
locks while a process races to open one can break singleton semantics.

The issue-worktree `.lake` scan found 49 symlinks. Most are package-internal
relative links; `qpbt-037-pauli-a01/.lake/packages/mathlib` is an absolute link
to `/home/drx/.cache/mipstarre-dev/hot-main/repo/.lake/packages/mathlib`.
At this observation its resolved package directory mode was `0555`, while
ancestors under `/home/drx/.cache/mipstarre-dev` include mode `0775`. The
supplied independent review records the same external target as writable at its
observation (finding F-067-A02-001). Therefore the external link remains an
isolation/quarantine finding regardless of its current mode; no seed is safe to
reuse until QPBT-068's fail-closed policy is implemented.

## Safe immediate actions (metadata/dry-run only)

1. **Create an inventory/index, do not remove bytes.** Record for every cache
   key and registered worktree: canonical path and realpath, Git HEAD/tree and
   branch/detached state, session/PR rows, manifest and `READY` digests,
   `.lake` symlink targets and modes, `st_dev:st_ino:st_nlink`, apparent size,
   and physical blocks. Repeat the scan and require identical values. A key or
   worktree is a *candidate* only after this index finds no active session,
   open PR, seed/warm journal, lock holder, or unexpired reference.
2. **Metadata-only lock hygiene under a dedicated lock.** The 37 zero-byte
   lock files are the only immediately visible low-value metadata. A future
   cleanup command may report them and remove only entries proven unheld by a
   lock-held, atomic check; this has negligible byte impact and must fail closed
   on races. Do not manually unlink them now.
3. **Separate no-Lake roles for new attempts.** New read-only scouts,
   reviewers, auditors, and source/blueprint agents should use detached trees
   without `.lake` unless their exact validation command requires Lean. This
   avoids allocating a ~10.5 GB seed per read-only lane. Existing trees are not
   deleted or rewritten; migrate only after terminal evidence, path/HEAD checks,
   and an archived result envelope are bound to the tree.
4. **Quarantine before any deletion.** For an inventory candidate, emit a
   dry-run record containing key, owner/lease evidence, manifest/READY status,
   symlink findings, physical/apparent bytes, and earliest eligible time. After
   two observations separated by the policy grace period (30 days for
   successful snapshots; at least seven days and terminal attempt for failure
   diagnostics), atomically rename to
   `.workflow-runtime/cache/quarantine/<key>/<timestamp>/` or a separately
   approved worktree quarantine. Never repair mismatched `READY` in place.
5. **Retain reversible evidence.** Keep all unmerged branches, blocked-issue
   worktrees, open-PR heads, external-symlink trees, failure logs, and any tree
   with missing provenance. Preserve old snapshots until a lease/reference
   index and authenticated deep inventory establish reachability. Deletion,
   when eventually authorized, is a separate reviewed operation after the
   quarantine grace period and final manifest/READY/deep-inventory check.

No observed value authorizes immediate cache/worktree deletion. Apparent age,
archived session status, zero current lock holders, or a branch being reachable
from `main` is insufficient without explicit lease/reference and provenance
evidence.

## Session accounting

Repository/state/metrics/protocol/cache/worktree/build/network/Git writes: 0
(the requested report is the only output, `/tmp/i067-scout-a07-retention.md`).
Nested agents: 0. The status command and read-only filesystem scans took about
`1.3 s` (cache status), `0.032463 s` (Git worktree list scan), `7.9 s` (issue
`.lake` size scan), and `12.8 s` (runtime directory `du`); timing is command
level only and excludes orchestration. Exposed token usage is `null` because
the collaboration backend does not expose per-agent token data; no estimate was
made. Session elapsed wall time is unavailable from the backend.
