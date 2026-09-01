# QPBT-018 / QPBT-021 closure-evidence audit (A18)

## Findings

### Medium - acceptance is complete, but both PR/issue lifecycles are stale

No technical, review, ancestry, build, cache-publication, provenance, or
dependency blocker remains for either issue. The only missing gates are the
root-owned ledger updates and terminal transitions:

- QPBT-018 remains `review` despite all five acceptance gates being discharged
  (`workflow/state/issues.json:707-738`). LPR-013 remains `approved` with
  `integration_sha: null`, `merged_at: null`, and no post-integration evidence
  (`workflow/state/prs.json:3484-3496`, `:3559-3574`, `:3591`).
- QPBT-021 remains `review` despite all four acceptance gates being discharged
  (`workflow/state/issues.json:806-835`). LPR-012 remains `approved` with
  `integration_sha: null`, `merged_at: null`, and no post-integration evidence
  (`workflow/state/prs.json:3281-3295`, `:3433-3461`). Its sole historical
  blocker is already recorded resolved/fixed (`workflow/state/prs.json:3444-3458`).

This is stale bookkeeping, not a reason to re-review either unchanged head.
The workflow permits `approved -> merged` and `review -> done`
(`scripts/workflow.py:132-146`); a merged PR requires a set-once integration
SHA before transition (`scripts/workflow.py:726-734`, `:2403-2417`).

## QPBT-018 evidence

Recommended transition: **QPBT-018 may transition from `review` to `done` now,
after LPR-013 receives its physical integration SHA/evidence and transitions to
`merged`.**

Acceptance mapping:

1. The immutable A13 review approved exact base/head
   `c5a0fecc26eb18452219cf0df31ce2a9113e45f1` /
   `c0de0900a01724c2a515311424dcbe5e7526ebd4`, tree
   `8b3d2caee539921fe4bcbcc456f0fc00ae2bbe17`, and exactly the two registered
   paths (`workflow/reviews/qpbt-018-review-a13-pr013.md:7-29`). It found no
   findings and verified 46/46 focused tests, 303/303 full tests, the checker,
   compileall, workflow validation, and SHA-bound diff hygiene
   (`workflow/reviews/qpbt-018-review-a13-pr013.md:89-108`). The canonical
   report SHA-256 is
   `2ea34832fb3903bf8f622c572d83eb34280785276c3b98e069d1537badfbcab7`,
   matching the archived reviewer record and current bytes.
2. Git independently confirms c0de090 is the sole-child commit of c5a0fec and
   has the reviewed tree. Its exact diff is only
   `scripts/hot_main_cache.py` and `tests/test_hot_main_cache.py`. c0de090 is
   an ancestor of both warm head d73cce4 and audit-cutoff main 506ac7a.
3. The later recipe-v5 build log directly exercises the repair: the local clone
   encounters `Invalid cross-device link`, emits the bounded EXDEV fallback
   marker, retries by object copy, and checks out exact d73cce4
   (`.workflow-runtime/cache/main/5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266/build.log:1-5`).
   It then completes 8,992 jobs successfully and verifies the package projection
   (`.workflow-runtime/cache/main/5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266/build.log:406-407`).
4. The original A13 review named the successful singleton warm as the only
   remaining gate (`workflow/reviews/qpbt-018-review-a13-pr013.md:110-116`).
   The later A17 disposition froze c0de090 as the eventual LPR-013 integration
   SHA and explicitly authorized LPR-013/QPBT-018 closure after one later
   changed-hypothesis warm succeeds
   (`workflow/reviews/qpbt-018-failure-disposition-a17.md:110-132`, `:150-166`).
   That success now exists.

## QPBT-021 evidence

Recommended transition: **QPBT-021 may transition from `review` to `done` now,
after LPR-012 receives its physical integration SHA/evidence and transitions to
`merged`.**

Acceptance mapping:

1. The immutable A09 review approved exact base/head
   `7669f70be786a53ba1a0a92c1d347f5fe7544681` /
   `6303aab63eeed144fe176969ca7c87f5a852b967`, tree
   `def685a69b3aee904b6ef6c2d711d63c75211efe`, and exactly the five registered
   paths (`workflow/reviews/qpbt-021-pr012-review-a09.md:3-26`). It independently
   checked the exact local Mathlib source/archive contract
   (`workflow/reviews/qpbt-021-pr012-review-a09.md:28-60`) and passed 42/42
   focused tests, 185/185 aggregate tests, checker, compileall, workflow
   validation, and SHA-bound diff hygiene
   (`workflow/reviews/qpbt-021-pr012-review-a09.md:69-87`). The current report
   SHA-256 is
   `99ae57f41cbd96eee10fa9b1bff34b372f062a3365140916338f5fce8facd431`.
2. Git independently confirms physical integration commit c5a0fec has first
   parent `08f4418e5763e9d49137134a8ff61d83c37943c8` and second parent exact approved
   head 6303aab. All five registered candidate paths are byte-identical at the
   merge, consistent with the prior post-merge audit
   (`workflow/reviews/qpbt-021-postmerge-failure-a11.md:24-40`). The approved
   head is an ancestor of c5a0fec, warm head d73cce4, and cutoff main 506ac7a.
3. The successful warm metric authenticates Mathlib exact commit
   `81a5d257c8e410db227a6665ed08f64fea08e997`, tree
   `5ea66b811b8461daae82f14d356fed2a287d7c40`, archive SHA-256
   `c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`,
   and local-archive mode (`.workflow-runtime/metrics/hot-main.jsonl:7`). The
   build log shows a local `file://.../mathlib-source` clone and exact revision
   checkout
   (`.workflow-runtime/cache/main/5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266/build.log:22-23`),
   then the successful 8,992-job build.
4. The earlier post-merge audit identified a later successful authenticated
   singleton warm as the only lifecycle blocker and prescribed integration SHA
   c5a0fec followed by LPR-012/QPBT-021 closure
   (`workflow/reviews/qpbt-021-postmerge-failure-a11.md:92-109`). The later A17
   disposition repeats that authorization (`workflow/reviews/qpbt-018-failure-disposition-a17.md:159-166`).

## Post-warm evidence verification

The QPBT-024/QPBT-025 repair chain is terminal and supplies the deferred shared
evidence:

- QPBT-024 and QPBT-025 are `done`, each binding the same recipe-v5 completion
  object (`workflow/state/issues.json:904-1039`, `:1042-1098`). LPR-014 and
  LPR-015 are `merged` with post-integration evidence. The event ledger records
  PR evidence before each merge, child QPBT-025 closure before parent QPBT-024,
  and completion evidence before each issue transition
  (`workflow/events.jsonl:1927-1934`). INC-044 is resolved while preserving its
  two historical failure keys (`research/metrics/incidents.jsonl:44`).
- The canonical success report, independent post-warm audit, and independent
  ledger audit hashes are respectively
  `940f18e7bbd60b7e440860bbcc6ce8b851b6515c983c0ff45da97dafb0070cbb`,
  `38b31d20168bbd06521874a2002b246a67c894167d8969a51b3f9d6ac9b360a2`,
  and `791259a3399b964476067a3cc92cecc917657410c18920814d13d58eb61d3172`.
  They match current files, QPBT-024/QPBT-025 completion objects, LPR-014/LPR-015
  post-integration objects, and archived session evidence
  (`research/metrics/sessions.jsonl:301`, `:303`).
- Exactly one runtime metric line matches cache key
  `5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266`.
  Its raw-line SHA-256 is
  `5022a23bf7a4a686588a5bba912e136051b743328a640c7dcb3b6185de1cb919`;
  it records main d73cce4, result `built`, status `hit`, one miss, one build,
  zero retry/lock wait, recipe version 5, and the local Mathlib identity
  (`.workflow-runtime/metrics/hot-main.jsonl:7`).
- Direct read-only hashes match the ledger: manifest
  `f41716f8a1213bd1fbff2939723c739653c360d6b797d93be69cb5a42f5ad234`,
  READY file `06720bffaa45dfc2fe92f5816caf9e31178d52bd4a95bcb4fdf70eceae4aa80a`,
  and build log
  `4737436c617f7072fd7bfb6d0fd65f900e8713fb7bfd722eb98e22e0c58b7b5c`.
  READY content equals the manifest hash. The manifest binds inventory SHA-256
  `321e2813533a93c8218eefb277bd3425d3b55a59d978a233fc9b4795de42df60`
  with 124925 files, 4147 directories, 3 symlinks, and 10097592794 bytes.
  The trusted sidecar is absent, its 172140-byte target is a regular file, both
  required build directories exist, and no matching failure envelope exists.
  A06 already independently recomputed the complete inventory
  (`workflow/reviews/qpbt-025-postwarm-closure-a06.md:49-91`). This audit did not
  repeat that 10 GB scan.

## Exact root changes

Use the already canonical QPBT-024 completion object unchanged. Preserve every
base/head/check/review/finding record, all issue dependencies/source references,
and LPR-013's historical `unexecuted_gate`. Add no late PR check and do not
re-review either unchanged head.

```bash
python3 scripts/workflow.py validate

qpbt_closure_evidence=$(jq -c '.issues[] | select(.id == "QPBT-024") | .completion_evidence' workflow/state/issues.json)
test "$qpbt_closure_evidence" != null

python3 scripts/workflow.py update pr LPR-013 \
  --set 'integration_sha="c0de0900a01724c2a515311424dcbe5e7526ebd4"' \
  --set "post_integration_evidence=$qpbt_closure_evidence"
python3 scripts/workflow.py transition pr LPR-013 merged
python3 scripts/workflow.py update issue QPBT-018 \
  --set "completion_evidence=$qpbt_closure_evidence"
python3 scripts/workflow.py transition issue QPBT-018 done

python3 scripts/workflow.py update pr LPR-012 \
  --set 'integration_sha="c5a0fecc26eb18452219cf0df31ce2a9113e45f1"' \
  --set "post_integration_evidence=$qpbt_closure_evidence"
python3 scripts/workflow.py transition pr LPR-012 merged
python3 scripts/workflow.py update issue QPBT-021 \
  --set "completion_evidence=$qpbt_closure_evidence"
python3 scripts/workflow.py transition issue QPBT-021 done

python3 scripts/workflow.py validate
python3 scripts/check_workflow.py --skip-tests
```

Expected automatic fields are `merged_at` and `updated_at`. The final event
suffix must show each evidence update before its terminal transition. No code,
protocol, source, metric, incident, stage, dependency, or cache change is
needed.

## Audit identity and validation

- Audit cutoff main: commit
  `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`, tree
  `10f8da1ebb8b3fd7ce92dafee19d61fafe2cf8e2`. Read-only
  `git merge-base --is-ancestor` checks returned exit 0 for 6303aab, c0de090,
  and d73cce4 against this main.
- Cutoff state hashes: issues
  `02ce5a4222763bf455c2ec1fd1f6403dde47fef5ac28887dfb441c44b8bda7dc`;
  PRs `e347b9cc9753627b1d614a97e1166d72a32221a1140257cd3208fe77dbbd19f6`;
  events `3d7c9960672bbc36d7cf46e66185fa6019e955daed15f9d8d2262efdabcae1b1`;
  sessions `c3c479a430b82f034e1f747f3266757a73d2188b09bf7ddbecab01b8ed61eae7`;
  session metrics
  `bf47dffc676cc309f798d911e09512e639f8da8838293fe97b11aa41b2b733da`;
  incidents
  `390a1641845be8fc73f66fa4230edb2291eb6e39d55374e9c1d6ce16dca2b8c7`.
- `python3 scripts/workflow.py validate --json`: exit 0, valid, 27 issues,
  16 PRs, 0 planned sessions, 322 issued sessions, 7 stages.
- `python3 scripts/check_workflow.py --skip-tests`: exit 0, `workflow state: valid`.
- Git identity/ancestry, exact range paths, candidate-to-integration path equality,
  report SHA-256, runtime metric count/hash, manifest/READY/build-log hashes,
  target/sidecar/build-directory existence, and failure-envelope absence all
  passed read-only checks.
- One exploratory snapshot lookup used the wrong `cache/snapshots` directory and
  failed read-only before the metric-provided `cache/main` path was used. One
  mistaken direct manifest-path invocation returned exit 126 because the
  read-only JSON file is non-executable. Neither attempt mutated any file or
  cache state.

## Accounting

- Logical session: `i018-auditor-a18-closure-evidence`.
- Start: `2026-09-01T03:32:14.939984591Z`.
- Evidence/report cutoff: `2026-09-01T03:39:22.186299378Z`.
- Measured elapsed to cutoff: `427.246314787` seconds.
- Token usage: JSON `null`; the collaboration backend does not expose
  per-session token usage, so no estimate was made.
- Subagents: 0.
- Tests: 0. Compile attempts: 0. Lean commands: 0. Lake commands: 0. Builds: 0.
- Cache warms/seeds/status calls: 0/0/0. Deep-inventory recomputations: 0.
- Repository edits: 0. Canonical state/metric edits: 0. Git writes: 0.
- Runtime/cache mutations: 0. Network/GitHub/endpoint/credential actions: 0.
- Only authored output: `/tmp/qpbt-018-021-closure-evidence-a18.md`.

The report SHA-256 is supplied out of band because embedding it would change
the digest.
