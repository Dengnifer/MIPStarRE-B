# QPBT-018 exact-base LPR-013 binding audit (a12)

## Verdict

PASS. LPR-013 is correctly opened as a new exact-current-base local PR for the
already committed QPBT-018 candidate. Zero content changes by this adoption
session are correct: the candidate is clean, immutable, and already carries the
intended two-file implementation and regression tests. The root coordinator may
bind this session as the LPR-013 implementer/integrator provenance and advance
the draft to the fresh-review gate without rewriting candidate content or any
LPR-007 evidence.

## Immutable identity and scope

- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-018-current-a10`
- Branch: `issue/qpbt-018-current-a10`
- Worktree status: clean (`git status --short --branch` reported only the branch).
- Base: `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`
- Head: `c0de0900a01724c2a515311424dcbe5e7526ebd4`
- Sole parent: `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`
- Head tree: `8b3d2caee539921fe4bcbcc456f0fc00ae2bbe17`
- Commit subject: `fix(cache): retry detached clone across devices`
- Changed paths: exactly `scripts/hot_main_cache.py` and
  `tests/test_hot_main_cache.py`; no other path differs.
- Diff size: 199 insertions and 8 deletions (production 32/8, tests 167/0).
- Production blob: `48e020d7392f2e1974f5983d6737171e034417d2`.
- Test blob: `39dca3d47f3e8c79dd7ac1c07f4f69ae723aed06`.
- SHA-bound diff hygiene is clean.

These values exactly match the immutable contract. `git rev-list --parents -n
1` returned only the specified base after the head, proving this is not a merge
commit or a candidate with an additional parent.

## Canonical LPR evidence

`workflow/state/prs.json` records LPR-013 as draft with the exact base/head,
branch, two changed paths, QPBT-018 address, and `supersedes_pr_id: LPR-007`.
All six registered checks are passed and independently bind the same
`c5a0fecc...` base and `c0de090...` head:

1. focused hot-main tests;
2. full serial unit tests;
3. aggregate workflow checker;
4. Python compile check;
5. workflow validation; and
6. SHA-bound diff hygiene.

Every check points to `workflow/reviews/qpbt-018-current-a10.md`. Its SHA-256 is
`131d9e36813c20e42331d55ae9bff4bf790fc56aa7a230c8b2c630365aca4003`,
identical to `/tmp/qpbt-018-current-a10.md`. The scout report's canonical and
temporary copies likewise match at
`f5f0130abe0f67f574c1c1c6dbdc58af754a632abf4bf06ffa18ce855a3d7fb0`.

LPR-013 currently has an empty `implementer_session_ids` list and no reviews.
That is consistent with this explicit adoption/binding step, not a content
defect. Before requesting review, the root coordinator should register
`i018-integrator-a12-pr013-bind` as the exact-base implementer/integrator and
import this report; the archived orchestrator and scout remain provenance.

## LPR-007 preservation

Opening LPR-013 preserved rather than rewrote LPR-007. LPR-007 remains closed
with its original base `687e182c7ad41520c226a59160c084ab53ad6f38`, head
`e21c9cda11803f7564a500c005fd55882530538d`, four SHA-bound checks, and three
formal review records (including the final approval). It now adds only
`superseded_by_pr_id: LPR-013` and the explicit closure reason that immutable
old-base evidence remains historical evidence. This is the correct provenance
model for a replay onto the QPBT-021-aware base.

## QPBT-021 preservation

The production diff is confined to `_detached_clone`. It retains the exact
initial local clone and exact `checkout --detach <main_commit>`, adding only a
single EXDEV-evidenced `--no-local` fallback with fixed-path cleanup. No
QPBT-021 Mathlib or publication code differs from the base.

The surrounding current-head code still:

- requires authenticated Mathlib input only for the canonical recipe;
- preflights that input before the cache-hit path and again under the elected
  lock;
- checks detached input hashes immediately after checkout;
- prepares and binds the authenticated local Mathlib source before Lake;
- verifies final HEAD, cache-key inputs, clean source, source evidence, and the
  Mathlib source after build; and
- writes `READY` and publishes the snapshot only after every verification gate.

The four appended regressions cover exact command order and partial-checkout
cleanup, stale-log rejection, a single bounded fallback, retained diagnostics,
and no READY/snapshot publication when detached checkout fails. This matches
the archived implementer and scout evidence and introduces no competing source
or identity path.

## Blockers and next gate

No blocker exists to binding LPR-013 or requesting formal review. LPR-013 must
not yet be approved or integrated: its required next gate is a fresh,
independent, read-only immutable review against exactly base `c5a0fecc...` and
head `c0de090...`. The reviewer must not be this session, the writable
orchestrator, or its nested scout. After approval and faithful integration, the
remaining QPBT-018 acceptance gate is exactly one authenticated singleton warm
and verified READY/status result.

## Session metrics and operations

- Elapsed time: 112.870 seconds, measured from the canonical session start
  `2026-08-31T14:44:08.307596Z` to `2026-08-31T14:46:01.177542Z`.
- Subagents: 0.
- Token usage: `null`; the collaboration backend does not expose per-agent
  token usage.
- Repository edits: 0.
- Staging/commits/ref changes: 0.
- Tests: 0.
- Builds/compiles: 0.
- Cache status/warm/seed/shared-cache operations: 0.
- Lean/Lake operations: 0.
- Network/GitHub operations: 0.
- Only authored output: this `/tmp/qpbt-018-pr013-bind-a12.md` report.
