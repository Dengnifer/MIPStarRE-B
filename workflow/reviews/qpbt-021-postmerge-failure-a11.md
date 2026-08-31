# LPR-012 / QPBT-021 post-merge failure review (a11)

Verdict: **hold lifecycle closure**. The physical merge is faithful and the
failure is attributable to the pre-existing QPBT-018 detached-clone portability
defect, not to a QPBT-021 regression. Nevertheless, LPR-012 must remain
`approved` and QPBT-021 must remain `review` until QPBT-018 is integrated and
one authenticated singleton warm succeeds and publishes the verified cache.

## Findings

**Blocker - `workflow/reviews/qpbt-021-integration-a10.md:111`.** The registered
post-merge closure rule says not to mark LPR-012 merged until every listed
command passes; the singleton warm at lines 122-130 is explicitly the required
full-main build. The Python/workflow gates passed, but the warm for exact key
`a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0`
failed. Therefore the transitions shown at lines 137-140 are not authorized.
The current ledger correctly retains `integration_sha: null` and
`merged_at: null` (`workflow/state/prs.json:3458`) and QPBT-021 remains
`review` (`workflow/state/issues.json:675`).

This is a lifecycle blocker, not a code finding against LPR-012. No new
QPBT-021 finding was identified.

## Merge identity and content

- Canonical merge: `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`.
- First parent: `08f4418e5763e9d49137134a8ff61d83c37943c8`.
- Second parent: approved candidate
  `6303aab63eeed144fe176969ca7c87f5a852b967`.
- The merge is a two-parent commit in exactly that order.
- All five LPR-012 owned paths are byte-identical to the approved candidate.
  The merge and candidate have the same blob IDs for:
  `protocols/CHANGELOG.md` (`224a0ef6...`),
  `protocols/orchestration.md` (`66898c89...`),
  `scripts/hot_main_cache.py` (`70df1582...`),
  `tests/test_hot_main_cache.py` (`9ee53433...`), and
  `workflow/README.md` (`33ee5bfe...`). The scoped candidate-to-merge diff is
  empty.
- Relative to first parent, the merge changes exactly those five registered
  paths, with 1849 insertions and 10 deletions. SHA-bound diff hygiene passes.

## Registered review and gates

LPR-012 is correctly recorded `approved` at `workflow/state/prs.json:3281`.
The exact approved head has six passed registered checks
(`workflow/state/prs.json:3356-3413`) and a fresh independent approval
(`workflow/state/prs.json:3431-3439`). The only earlier blocker,
`F-LPR012-A08-001`, is recorded resolved/fixed at
`workflow/state/prs.json:3442-3455`; it concerned the stale changelog count,
not runtime behavior.

The measured final merge gates inspected for `c5a0fec` are:

- focused hot-cache suite: 42/42, 10.14 s;
- full serial unittest discovery: 299/299, 81.91 s;
- workflow checker: 299/299, 71.58 s;
- Python compileall: passed;
- workflow validation: passed;
- first-parent-to-merge diff hygiene: passed.

These results rule out a Python/workflow merge regression in the integrated
five-path payload, but they do not substitute for the mandatory warm.

## Failure attribution

The retained failure envelope binds exact key
`a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0`
to exact main commit `c5a0fec` at
`.workflow-runtime/cache/failures/a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0-20260831T220839-2/failure.json:3-4`.
It records a cache miss, one elected build, no lock wait, and failure after
0.014599 s at the detached-clone step. No cache snapshot or `READY` artifact
was published.

The log fails on `git clone --local` while hard-linking a Git object:
`Invalid cross-device link`
(`.workflow-runtime/cache/failures/a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0-20260831T220839-2/build.log:2`).
The integrated implementation invokes that local clone at
`scripts/hot_main_cache.py:1894` and aborts at line 1900, before detached
checkout, Mathlib binding, archive authentication, package materialization,
dependency cache, or Lake build. The envelope's `mathlib_source: null` is thus
a consequence of the earlier clone abort, not a rejection of QPBT-021's local
Mathlib source.

This is exactly QPBT-018's owned failure class: its acceptance gates require a
bounded object-copy fallback for local-clone EXDEV and a successful singleton
warm (`workflow/state/issues.json:589-593`). The pre-integration cache scout
also warned that QPBT-021 does not eliminate this historical failure
(`workflow/reviews/stage-04a-cache-postintegration-a53.md:289-296`). The failure
therefore reveals no QPBT-021 regression. It does leave QPBT-021's real
authenticated warm path unexecuted on integrated main.

## Exact lifecycle recommendation

1. Make no LPR-012 or QPBT-021 lifecycle transition now. Keep LPR-012
   `approved`, `integration_sha: null`, and `merged_at: null`; keep QPBT-021
   `review`.
2. Complete current-main QPBT-018 implementation and fresh immutable review,
   preserving its separate ownership and failure evidence. Integrate the
   bounded EXDEV fallback without altering the already merged LPR-012 blobs
   except where the reviewed QPBT-018 patch necessarily touches the cache
   script/tests.
3. Run exactly one elected authenticated singleton warm on the resulting
   combined current-main commit. Require a successful build, verified
   publication, `status` ready for that commit's new exact cache key, and
   recorded lock/build/cache metrics. Retain the failed `a58247f0...` envelope.
4. Only after that successful warm, record LPR-012's physical integration SHA
   as `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`, transition LPR-012 to
   `merged`, transition QPBT-021 to `done`, import the final integration/warm
   evidence, and validate the state before and after the changes.

## Residual risk and accounting

Residual risk is confined but material: because the clone failed first, the
integrated QPBT-021 Mathlib authentication, local URL-map injection,
materialization, dependency-cache, Lake build, and atomic publication path have
not yet executed end to end on canonical main. A successful post-QPBT-018 warm
is the evidence that discharges that risk; Python tests alone cannot.

- Elapsed: approximately 6 minutes.
- Subagents: 0.
- Token usage: `null`; the collaboration backend does not expose per-agent
  token usage, so it was not estimated.
- Commands run by this review: read-only Git/file/state inspection only; no
  tests, workflow validation, Lean, Lake, build, warm, seed, or network action.
