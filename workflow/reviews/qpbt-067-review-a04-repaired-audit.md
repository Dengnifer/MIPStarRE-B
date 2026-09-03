# QPBT-067 Fresh Immutable Repaired Audit (A04)

Review session: `i067-reviewer-a04-repaired-audit`
Issue: `QPBT-067`
Candidate commit: `e1cf001915bd8463ca3b5b1555d912b08085c0af`
Candidate tree: `765f626bd25596ab92521a235a255ed2fb6c9ceb`
Repair commit recorded by the issue: `be115acbdcab7d2020fec694357eb64671b09238`
Repair-source commit/tree recorded by the issue: `b2368ddbd72bda81c4fae325b5809115b968f054` /
`97b724312e2b0f440da6f469f3771f4cd7174a55`

## Findings

### High: the report claims an implemented READY-quarantine path that does not exist

`workflow/reviews/qpbt-067-cache-layout-a01.md:122-126` calls the
mismatched-`READY` quarantine behavior part of the “implemented live-process
path.” In the candidate implementation, `HotMainCache.is_ready` only returns
false after digest/identity/deep-inventory failure (`scripts/hot_main_cache.py:2497-2549`),
and no quarantine operation exists in `scripts/hot_main_cache.py`. The protocol
only says failed staging is retained/logged and that cleanup is explicit
(`protocols/local-development.md:79-81,108-110`). Quarantine is a proposed
retention design at `workflow/reviews/qpbt-067-cache-layout-a01.md:112-120`,
not implemented behavior. This is a source-fidelity/implementation claim and
must be rewritten as a future requirement before approval; it is independent of
the QPBT-068 implementation.

### Medium: source anchors are materially stale or point at unrelated code

The repair report says source anchors are unchanged, but several anchors in the
canonical report cannot reproduce the claims. For example,
`workflow/reviews/qpbt-067-cache-layout-a01.md:15-17` cites
`scripts/hot_main_cache.py:1973-1981` for cache-path construction and `is_ready`;
those lines are `_walk_without_following`/`make_read_only`, while the path fields
are at `scripts/hot_main_cache.py:2076-2084` and `is_ready` is at
`scripts/hot_main_cache.py:2497-2549`. The same paragraph cites
`protocols/local-development.md:39-44,64-67,73-78` for lock publication,
`READY`/seed verification, and private-copy restrictions, but those contracts
are at `protocols/local-development.md:49-54,74-77,83-91`. The report's
`scripts/hot_main_cache.py:2841-2846` citation for the seed replacement window
(`:127-131`) is also the `warm` metric base; the two renames are at
`scripts/hot_main_cache.py:3216-3224`. These are not cosmetic line drift: the
source-anchored audit cannot be independently checked until the citations are
corrected (or a stable symbol/commit anchor is supplied).

### High: acceptance metrics are incomplete and the ordering gate is not evidenced

The issue requires the independent review to record measured disk,
duplicate-identity, parallel-lane, timing, and protocol-evolution metrics before
an implementation issue is opened (`workflow/state/issues.json:3406-3410`).
The report has disk and identity measurements and names recipe v7, but its
metrics section (`workflow/reviews/qpbt-067-cache-layout-a01.md:164-175`) has no
parallel-lane count/measurement and no audit timing or latency distribution; the
statement that no child agents were dispatched is not a parallelism metric.
QPBT-068 is already `in_progress` (`workflow/state/issues.json:3453-3477`), so
the required pre-opening evidence is not present in this candidate. Add the
missing metrics with source packet hashes and explain the ordering exception, or
keep QPBT-067 unapproved.

### Medium: the issue's QPBT-062 source reference is unauthenticated in this candidate

`workflow/state/issues.json:3412-3418` lists
`workflow/reviews/qpbt-062-branch-lifecycle-a01.md` as a QPBT-067 source, but
that file is absent from `workflow/reviews/` at candidate tree
`765f626bd25596ab92521a235a255ed2fb6c9ceb` (QPBT-062 is still in progress).
The report therefore cannot claim that all issue source references were
authenticated. Either publish the cited artifact before review or explicitly
mark this source dependency as unavailable and defer approval.

## Prior findings disposition

F-067-A02-001 is honestly corrected: the report now records the external,
writable `packages/mathlib` symlink and limits the hard-link observation rather
than claiming whole-`.lake` privacy (`workflow/reviews/qpbt-067-cache-layout-a01.md:34-44,94-101`).
F-067-A02-002 is honestly corrected: it distinguishes synchronous exception
rollback from the uncovered SIGKILL two-rename window and calls recovery a
future requirement (`workflow/reviews/qpbt-067-cache-layout-a01.md:122-133`).
No QPBT-068 code was treated as evidence for QPBT-067.

## Recomputed provenance

SHA-256 values in the immutable candidate:

| File | SHA-256 |
|---|---|
| `AGENTS.md` | `3df95336eaf3b504a7e537b04703e66c0daf6311e511e9dca3b49b1a67b3e339` |
| `workflow/state/issues.json` | `e36e7beef513422635e2c0b1131bb9f7dfc4fcd4dab500d4cab745683a47339a` |
| `workflow/reviews/qpbt-067-cache-layout-a01.md` | `32896b492d90f96eb107790b6b999d4fea40085f6f7b2c8200853939cff36df0` |
| `workflow/reviews/qpbt-067-cache-layout-review-a02.md` | `7b1aef4a5c7d053f180e591e2bfa506004243e19450204ddad150fb8962af9dd` |
| `workflow/reviews/qpbt-067-report-repair-a02.md` | `1639adb10dfed370a524eaa7af1fa903ed2ffc7a6aa9b612cc491bb508ff84f5` |
| `protocols/local-development.md` | `3816bec3d1903e2c26d1940aff2c2c9ce64fddcb9cffd5ee0af1dc14c4c2a8bf` |
| `protocols/orchestration.md` | `c017d8add3277267fa97fa57b598b1c5bda334c805d28fe120afc19f00d45701` |
| `scripts/hot_main_cache.py` | `24bb0016881ae0118df9e33f638af6c9be09b57c69b3e4f702cd7ed00fd10f13` |
| `tests/test_hot_main_cache.py` | `5f5871c3a5a6fcede9ff6582fcefb3375c1833bca33f131f2fa933413400e853` |

The issue's recorded repair-report SHA-256 matches the recomputed value. The
repair commit is an ancestor of the candidate; its recorded repair-source
commit is a divergent same-change commit whose tree matches the issue's
`repair_tree`, so both identities must remain explicit in any follow-up.
All four authenticated `/tmp` scout packet hashes recorded by the retention
scout were recomputed and matched. The cited QPBT-062 report remains missing.

## Checks and counters

No tests, builds, Lean/Lake commands, cache warm/seed/materialization, network,
GitHub, credential, worktree, repository, state, metrics, or protocol writes
were run. Repository/worktree writes: `0`; cache/build/materialization writes:
`0`; Git ref/network/GitHub/credential actions: `0`; child agents: `0`.
Token usage: `null` (collaboration backend exposes no token counters). Elapsed
wall time: `null` (review harness exposes no per-agent start/stop clock).

## Verdict

**REQUEST_CHANGES**. The two repaired findings are substantively corrected,
but the false quarantine implementation claim, stale source anchors, missing
acceptance metrics, and unauthenticated QPBT-062 source reference prevent an
immutable approval.
