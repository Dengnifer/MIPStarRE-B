# dba1 one-shot warm failure disposition (a17)

Logical session: `i018-scout-a17-failure-disposition`
Audited canonical HEAD: `c0de0900a01724c2a515311424dcbe5e7526ebd4`
Verdict: **hold every pending closure; open a new bounded package/cache repair
issue under QPBT-004 provenance; do not retry the unchanged warm.**

## Provenance finding

The retained failure is not another EXDEV failure and is not a QPBT-021 local
Mathlib failure.

- Cache key `dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276`
  is bound to exact integrated main `c0de0900a01724c2a515311424dcbe5e7526ebd4`.
- The first local clone failed with `Invalid cross-device link`, the reviewed
  QPBT-018 fallback emitted its marker, the single `--no-local` clone succeeded,
  and detached HEAD became exactly `c0de090...`. This is positive operational
  evidence for LPR-013's changed path.
- The MIPStarRE archive, all eight Lake package archives, and the pinned local
  Mathlib archive were authenticated. Mathlib was cloned from the staged local
  `file://` source. This is positive operational evidence for LPR-012's changed
  path; the log contains no QPBT-021 GitHub-fetch failure.
- Dependency cache retrieval completed, then `lake ... build` completed all
  `8992` jobs. The retained metric records `build_seconds: 611.282074` and
  `elapsed_seconds: 617.697424`.
- The post-build command `scripts/materialize_lake_packages.py verify` then
  failed with `materialized archive tree differs for plausible`. The failure
  envelope records `Lake package verification command failed with exit code
  1`. Publication did not reach manifest/READY rename; the transaction failed
  closed.

Primary evidence:

- `.workflow-runtime/cache/failures/dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276-20260831T232823-2/failure.json`
- the sibling retained `build.log`
- `.workflow-runtime/metrics/hot-main.jsonl`, final record at
  `2026-08-31T15:28:29.503476Z`

The actual warm was a root-coordinator operation following the authorization
prepared by `i018-scout-a14-integration-warm`. Do not attribute the build to
A14: its imported metric explicitly records `cache_warms: 0`, `lake_builds: 0`,
and says it only prescribed the later singleton command.

## Repair ownership

The defect domain is **QPBT-004**, specifically the package materialization and
post-build publication contract introduced by LPR-005. It is not within
QPBT-018's bounded detached-clone portability scope and not within QPBT-021's
authenticated local-Mathlib scope. Both later changes demonstrably advanced
past their formerly failing boundaries.

Do not reopen or rewrite merged LPR-005, and do not reopen
`F-LPR005-001`. That finding said build-time package mutation could be
published because no post-build verifier existed. Its resolution remains true:
the verifier exists and prevented publication. The real warm has exposed a new
contract defect: the verifier does not yet distinguish an authorized,
deterministic Lake mutation from unauthorized package-source drift. The old
finding and its resolution remain immutable provenance for the new work.

QPBT-004 itself is still `planned` and dependency-blocked by QPBT-003. Therefore
the root should not evade the issue DAG by issuing a writable QPBT-004 session
directly. Open the next numbered bounded workflow issue (currently
**QPBT-024**) as the dispatch owner, linked explicitly as the package/cache
acceptance blocker for QPBT-004, with only already-complete workflow
dependencies. Open a successor PR (currently **LPR-014**) from exact current
main after the issue is valid and ready. This preserves semantic ownership in
QPBT-004 while giving the repair one issuable orchestrator and one nonoverlapping
worktree.

The new issue must be scoped from the A15/A16 diagnosis, not guessed from the
error string. Its minimum gates are:

1. identify the exact post-build `plausible` path and producer;
2. define the weakest deterministic distinction between immutable archive
   source and permitted build-generated state;
3. retain rejection of arbitrary package-source drift and no-READY behavior;
4. add regressions for the observed legitimate mutation and for an unauthorized
   mutation at the same boundary;
5. pass exact focused package/hot-cache tests, full serial aggregate, workflow
   checker/validation, compile check, and SHA-bound diff hygiene;
6. receive a fresh independent immutable review of the new head and, if the
   normative package-verification rule changes, a separate protocol review plus
   changelog/protocol-change evidence.

No candidate warm is authorized. The real warm remains a post-integration main
gate.

## Incident disposition

Create **INC-044**, severity `high`, count `1`, owned by the new QPBT-004-linked
workflow issue, with a class such as
`hot-cache-postbuild-verifier-build-induced-package-drift`.

This is a **new incident class**, not another occurrence of INC-031 and not a
fourth EXDEV occurrence under INC-043:

- INC-031 records absence of post-build package verification plus an unrelated
  lock-incarnation defect. Here the mitigation is present and fails closed; the
  new cause is its incomplete model of expected Lake mutations.
- INC-043 records local-clone EXDEV. Here the bounded fallback succeeded and
  the full build ran.
- INC-036/QPBT-021 records Mathlib network fetch. Here the authenticated local
  Mathlib input was accepted and used.

Reference INC-031, F-LPR005-001, and the retained dba1 envelope as causal
provenance, but do not increment or rewrite their historical occurrence data.
If the repaired verifier later fails again for the same build-induced drift
class, increment INC-044; do not spend an automatic second warm.

## Lifecycle holds

Until a changed-hypothesis warm succeeds:

- keep LPR-012 `approved`, `integration_sha: null`, `merged_at: null`;
- keep QPBT-021 `review`;
- keep LPR-013 `approved`, `integration_sha: null`, `merged_at: null`;
- keep QPBT-018 `review`;
- keep LPR-005 `merged` and both F-LPR005 findings `resolved`; do not falsify
  immutable history;
- keep QPBT-004 `planned` while QPBT-003 is not done, but replace its stale
  blocked reason/unblock condition with the dba1 failure and the new numbered
  repair dependency;
- keep the dba1 cache outcome failed/miss, retain its envelope/log, and claim no
  READY, seed, or accepted main build;
- keep all QPBT-004-dependent formalization dispatch held under the issue DAG
  and the protocol stop condition for a failed/unverified hot-main publication.

Physical integration does not authorize ledger closure. LPR-012 is physically
present through merge `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`; LPR-013 is
physically present through fast-forward `c0de0900a01724c2a515311424dcbe5e7526ebd4`.
Those SHAs remain the eventual integration SHAs; a later repair commit does not
rewrite either reviewed PR head.

## Exact authorization sequence

1. Import and inspect all three A15/A16/A17 read-only reports. Record INC-044,
   reconcile QPBT-004's stale blocker, create QPBT-024 with exact source anchors
   and gates, and validate canonical state before and after each state batch.
2. Issue one QPBT-024 orchestrator in a private exact-`c0de090...` worktree with
   explicit owned paths. Freeze its head and open LPR-014; never append the fix
   to LPR-012 or LPR-013 and never mutate LPR-005 history.
3. Run and record every deterministic gate on the exact LPR-014 base/head.
   Scan for overlapping writable sessions. If code or protocol bytes change,
   dispatch fresh independent read-only review(s); the implementer and
   orchestrator cannot approve.
4. Only after approval, physically integrate the unchanged LPR-014 head onto
   canonical main. Keep LPR-014 `approved` and its issue not done while the
   post-integration gate is pending, mirroring the existing LPR-012/LPR-013
   hold.
5. Re-authenticate the exact MIPStarRE, eight Lake package, and Mathlib archive
   inputs; verify no live builder/lock holder; then authorize **exactly one**
   elected warm from the reviewed script on the new canonical main SHA and its
   new cache key. This is permitted because the reviewed repair and new main
   identity are a changed hypothesis. An unchanged c0de/dba1 retry is forbidden.
6. Require terminal success, verified READY binding, status-ready, and deep
   inventory evidence before any closure. On the same-class failure, retain the
   envelope, increment INC-044, hold every status, and return to diagnosis and
   fresh review; do not retry automatically.
7. On success, first record LPR-014's physical integration SHA and transition
   LPR-014/QPBT-024 to `merged`/`done`. Then record LPR-013 integration SHA
   `c0de090...` and LPR-012 integration SHA `c5a0fec...`, transition both PRs to
   `merged`, and transition QPBT-018 and QPBT-021 to `done`. Resolve/mitigate the
   corresponding incidents with the successful evidence. QPBT-004 still may
   not become `done` until QPBT-003 is done and all of QPBT-004's own gates are
   reconciled; record the successful cache/build evidence without bypassing
   that dependency.

## Accounting

- Audit interval: `2026-08-31T15:33:26.731194Z` through
  `2026-08-31T15:38:20.567739024Z` (`293.837` seconds through report drafting).
- Canonical inventory observed: 24 issues, 13 PRs, 43 incident records.
- Scope inspected: 3 named issues; LPR-005/LPR-007/LPR-010/LPR-012/LPR-013
  provenance; F-LPR005-001/002; INC-031/032/035/036/043; current issue, PR,
  session, event, review, metric, and protocol records.
- Subagents: `0`.
- Token usage: `null`; the collaboration backend does not expose per-agent
  token usage, so no estimate was made.
- Tests, workflow validations, Lean commands, Lake commands, builds, warm,
  seed, status, network, Git writes, canonical edits, runtime edits, cache
  edits, ref edits, and worktree edits performed by this audit: `0` each.
- Retained runtime artifacts were read only; the sole authored artifact is this
  `/tmp` report.
