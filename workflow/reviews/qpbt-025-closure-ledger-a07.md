# QPBT-025 closure-ledger audit (A07)

## Verdict

No warm, integration, approval, or source-evidence blocker remains in the
authorized scope. Local `HEAD` and `main` are both exact
`d73cce44d5f9f37d38ee8d916811719408818c03`; its tree is
`8a8985252eb019282ab6ef1842ce1b9178a58c07`, its sole parent is exact
`45d2fe657af587e8e10952aced2e156d349fd65e`, and old LPR-014 head
`9c9b49548fabdd6b01916787d7dc17a4bca36513` is an ancestor. The success
report records the only authorized recipe-v5 warm as `built` / `hit` for key
`5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266`,
with READY/manifest and deep inventory verified and no matching failure
envelope.

Canonical closure has not yet happened in the inspected snapshot:
LPR-014/LPR-015 are `approved` with null `integration_sha`/`merged_at`,
QPBT-025/QPBT-024 are `review`, QPBT-004 is `planned` with dependencies
`[QPBT-003, QPBT-024]`, and INC-044 remains `mitigating` with count 2.

## Exact monotone order

Before terminal transitions, terminally import and archive the orchestrator,
reviewer, and integration-session accounting, append the successful warm
evidence, and validate. The exact safe physical order is:

1. For LPR-014, set `integration_sha` once to
   `9c9b49548fabdd6b01916787d7dc17a4bca36513`, add the shared structured
   `post_integration_evidence`, then transition `approved -> merged`. Preserve
   the existing `unexecuted_gate` as historical pre-warm state; the new evidence
   records its later discharge. The transition creates `merged_at` and refreshes
   `updated_at`.
2. For LPR-015, set `integration_sha` once to
   `d73cce44d5f9f37d38ee8d916811719408818c03`, add the same
   `post_integration_evidence`, preserve its historical `unexecuted_gate`, then
   transition `approved -> merged`. The transition creates `merged_at` and
   refreshes `updated_at`.
3. Attach the same object as QPBT-025 `completion_evidence`, retain
   `blocked_reason: null`, then transition `review -> done`; `updated_at` is
   automatic. A06 does not direct a rewrite of `unblock_condition`.
4. Reconcile INC-044 monotonically to resolved before parent closure. Preserve
   all two-occurrence failure history and add separate resolution evidence.
5. Only after steps 1-4, attach the same object as QPBT-024
   `completion_evidence`, clear `blocked_reason`, and transition `review ->
   done`. A06 does not direct a rewrite of `unblock_condition`.
6. Leave QPBT-004 `planned` and preserve `dependency_ids` exactly as
   `[QPBT-003, QPBT-024]`. Update only its blocker/unblock text so QPBT-003 is
   identified as the sole unfinished dependency, add the shared object as
   `cache_acceptance_evidence`, and retain its old failure evidence. Completed
   QPBT-024 remains a durable graph/provenance edge but is no longer a blocker.

This freezes both required partial orders: both PRs are merged before either
issue closes, and child QPBT-025 is done before parent QPBT-024 is done.
LPR-014 precedes LPR-015 as frozen by A17/A05. Incident reconciliation is put
before parent closure because A17 makes it a QPBT-024 close predicate; the
later success report's numbered list places it afterward, which is a source
ordering inconsistency. The stricter order above satisfies the close
predicate without weakening the PR/issue order.

## Fields and evidence

Validator-required PR terminal fields are `status: merged`, a syntactically
valid non-null `integration_sha`, non-null `merged_at`, current passed checks,
an identified implementer, a current approving review, and no unresolved
findings. Existing immutable base/head/check/review/finding evidence already
satisfies these predicates. `integration_sha` must be set before transition;
the CLI makes it immutable once non-null and makes merged records uneditable.
Therefore `post_integration_evidence` must be recorded before `merged`. Do not
replace or delete `unexecuted_gate`: A06's exact commands leave it intact as
historical pre-warm state, and the new structured field records discharge. Do
not add a late PR check.

The issue validator requires no `closed_at` or named completion-evidence field.
For `done`, it requires only the ordinary issue schema and all declared
dependencies done; the transition writes `status` and `updated_at`. Governance,
not schema, requires QPBT-025/QPBT-024 to attach the A06-prescribed structured
warm-evidence object, which itself binds the corrected success report, before
closure. The validators ignore unknown fields, so these requirements come from
the reviewed runbook. The object must bind at least:

- corrected report
  `workflow/reviews/qpbt-025-postintegration-warm-success-537.md`, SHA-256
  `940f18e7bbd60b7e440860bbcc6ce8b851b6515c983c0ff45da97dafb0070cbb`;
- main SHA/key, `result: built`, `status: hit`, miss/build count 1, zero retry,
  lock wait 0/0.0, build seconds `551.877742`, and exact build command
  `["lake","--packages=.lake/package-overrides.json","build"]`;
- manifest/READY digest
  `f41716f8a1213bd1fbff2939723c739653c360d6b797d93be69cb5a42f5ad234`;
- warm metric SHA-256
  `5022a23bf7a4a686588a5bba912e136051b743328a640c7dcb3b6185de1cb919`;
- inventory SHA-256
  `321e2813533a93c8218eefb277bd3425d3b55a59d978a233fc9b4795de42df60`,
  counts 124925 files / 4147 directories / 3 symlinks, deep equality true;
- failure-envelope absence, sidecar absence, retained target, and retained
  proofwidgets `.lake/build`.

Do not add new PR `source_refs` fields or rewrite issue `source_refs` during
closure. A06's exact commands add `post_integration_evidence` to both PRs,
`completion_evidence` to QPBT-025/QPBT-024, and
`cache_acceptance_evidence` to QPBT-004; that shared object already binds the
corrected success-report path and digest. A06 is imported through its own
session/report/metric evidence. There is no direct authority to add A06 or the
success report to `source_refs`, so preserving those lists is the narrower
monotone operation.

For INC-044, preserve `count: 2`, both `occurrence_keys`, the occurrence
session list, `evidence`, `latest_*` failure fields, report/log/metric hashes,
related incidents, protocol effect, and `unchanged_retry_allowed: false`.
Change only the lifecycle status monotonically and append distinct resolution
fields binding the successful head/key/report/hashes and resolution timestamp.
Do not overwrite `latest_*` with success data: those fields describe the last
failure occurrence.

## Validator hazards

- QPBT-024 is `kind: workflow`, not `kind: tracking`; the validator's
  child-before-parent rule applies only to done tracking issues. It will not
  enforce QPBT-025-before-QPBT-024.
- No validator links issue `done` to a merged PR, acceptance evidence, cleared
  blocker text, or the successful warm. Additional evidence fields are ignored.
- PR `integration_sha` is checked only as 40/64 lowercase hex. It is not
  required to equal `head_sha`, be reachable from main, or match physical
  integration. The exact values above are a governance guard.
- Validation checks snapshots, not lifecycle history. Direct JSON edits can
  bypass transition order; use checked CLI updates/transitions. Issue
  `source_refs` and `dependency_ids` are not append-only in the CLI. This makes
  preserving QPBT-004's frozen edges and all existing source references an
  explicit governance requirement.
- PR checks/reviews/implementers are append-only, findings are
  disposition-aware, and `integration_sha` is set-once. A merged PR cannot be
  updated, so evidence/disposition ordering matters.
- `workflow.py validate` does not validate research JSONL ledgers.
  `check_workflow.py --skip-tests` does, but incident validation checks only
  unique nonempty IDs and references; it does not validate incident status,
  resolution fields, or append-only history.
- Appending a second JSONL row with id `INC-044` fails the uniqueness check.
  Literal row-append-only resolution is therefore unsupported. The available
  source-faithful operation is a monotone extension of the existing INC-044
  object (status plus new resolution fields) while retaining every historical
  field; this schema limitation should remain explicit.
- A17 says INC-044 reconciliation is a QPBT-024 close predicate, while the
  success report lists incident resolution after QPBT-024. The safe order above
  resolves the inconsistency conservatively.
- Terminal session metrics are a stated close predicate and
  `check_workflow.py` rejects terminal issued sessions lacking a metric. Their
  presence was not inspectable under this scout's exact file scope, so root
  must verify them before step 1. This is an unverified prerequisite, not an
  observed failure.

Run root-owned `python3 scripts/workflow.py validate` before and after the state
mutation sequence, then the A06-prescribed aggregate
`python3 scripts/check_workflow.py`. Each CLI mutation validates the resulting
state, but a final aggregate validation remains required.

## Audit accounting

Inspected commands were read-only: `cat AGENTS.md`; `jq` projections of the
three named issues, two named PRs, and INC-044; `cat`/`nl`/`sed`/`rg` over the
three authorized reports and relevant validator regions; `git rev-parse`,
`git merge-base --is-ancestor`, and `git status`; `sha256sum`; and `date`.
The initial `.prs[]` query failed harmlessly because the schema key is
`pull_requests`; the corrected query was used. No test, build, Lean, Lake,
workflow validation, warm, seed, operational cache status, network, Git write,
runtime/cache access, repository mutation, or canonical-state write was run.

Repository/canonical edits by this scout: zero. Subagents: zero. The only
authored file is this `/tmp` report. First captured timestamp:
`2026-09-01T04:18:08.212750770+08:00`; cutoff:
`2026-09-01T04:20:36.234225708+08:00`; exactly measured captured interval:
`148.021474938` seconds. Earlier uncaptured instruction/read setup is excluded
rather than estimated. Token usage: JSON `null`; per-session usage was not
exposed. The report SHA-256 is supplied out of band because embedding it would
change the digest.

## Follow-up correction

Root requested a narrow correction after A06 was imported and the success
report was amended. Reinspection confirmed A17 freezes
`QPBT-004.dependency_ids` as `[QPBT-003, QPBT-024]`; A06 F1 explicitly rejects
deleting QPBT-024, and the corrected success report preserves both edges.
Completed dependencies remain graph history but do not count as unfinished
blockers. This revision also records the A06-directed treatment of
`unexecuted_gate`, structured evidence, and unchanged `source_refs`.

Follow-up first captured timestamp: `2026-09-01T04:24:03.729982831+08:00`;
cutoff: `2026-09-01T04:26:23.826066445+08:00`; exactly measured follow-up
interval: `140.096083614` seconds.
