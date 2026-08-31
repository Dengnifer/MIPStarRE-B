# QPBT-024 post-warm closure matrix (a08)

## Verdict

**HOLD: the failure branch is active.** The root coordinator reported that the
one changed-hypothesis warm failed closed after the build phase with exact
error `Lake package verification command failed with exit code 1`. This scout
did not inspect the live or retained runtime evidence; the classification must
be confirmed from the terminal envelope, but the reported phase and error
match INC-044. No integration SHA or lifecycle transition is authorized, and
the exact 9c9/9b6 hypothesis must not be retried unchanged.

Canonical `main` is the already integrated exact LPR-014 head
`9c9b49548fabdd6b01916787d7dc17a4bca36513`. LPR-014 is `approved`, QPBT-024 is
`review`, LPR-013 and LPR-012 are `approved` with their physical integration
SHAs still unrecorded, and QPBT-018/QPBT-021 remain `review`. These holds are
intentional.

The success branch below is a counterfactual closure matrix for a future newly
reviewed changed hypothesis; it is not authorization to reinterpret or retry
this failed attempt. No closure transition is authorized unless a permitted
one changed-hypothesis warm is terminally successful for exact key
`9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36`,
post-warm status is `hit` for exact main `9c9b495...`, READY equals the manifest
SHA-256, and independent deep inventory recomputation equals the manifest.
Failure of the warm, status, READY binding, or deep inventory is the failure
branch even if compilation itself completed.

This scout did not inspect the live process, lock, cache key, runtime tree,
warm output, or warm metrics. The root must bind the result to a separately
imported immutable evidence report before applying this matrix.

## Current ledger facts

| Item | Current state | Physical fact | Immediate disposition |
|---|---|---|---|
| LPR-014 | `approved`; `integration_sha: null` | main equals head `9c9b495...` | hold until verified warm |
| QPBT-024 | `review` | all pre-integration checks and independent review passed | hold until verified warm |
| LPR-013 | `approved`; `integration_sha: null` | physically present at `c0de090...` | hold until verified warm |
| QPBT-018 | `review` | EXDEV repair is physically present | hold until verified warm |
| LPR-012 | `approved`; `integration_sha: null` | physically present through `c5a0fec...` | hold until verified warm |
| QPBT-021 | `review` | local Mathlib repair is physically present | hold until verified warm |
| QPBT-004 | `planned` | depends on QPBT-003 and QPBT-024 | remain held after cache success because QPBT-003 is `blocked` |
| INC-044 | `mitigating`, count 1 | old c0de/dba1 failure retained | resolve only on full success; increment on same-class failure |
| STAGE-04A | `in_progress` | contains other incomplete issues | remain `in_progress` on either branch |

The immutable physical integration SHAs are:

- LPR-014: `9c9b49548fabdd6b01916787d7dc17a4bca36513`.
- LPR-013: `c0de0900a01724c2a515311424dcbe5e7526ebd4`.
- LPR-012: `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`.

## Evidence gate before either branch

Import one root-owned post-warm report and record its SHA-256 out of band. The
report must preserve the exact command and environment and include:

1. Exact main SHA and cache key, authenticated archive paths and recomputed
   archive/pin hashes, start/end timestamps, exit code, terminal result, and
   stdout/stderr or build-log path.
2. The before/after line count and exact single new record from
   `.workflow-runtime/metrics/hot-main.jsonl`, including elected/hit result,
   build count, lock wait, build duration, and total elapsed time.
3. Post-warm status JSON bound to `9c9b495...`/`9b6ccb7...` and reporting `hit`.
4. Snapshot, `manifest.json`, `READY`, and `build.log` identities; READY content
   equal to the manifest SHA-256; `is_ready(deep=True)` or its exact equivalent;
   and recomputed artifact inventory byte-for-byte equal to the manifest.
5. Pre-build and post-build package-verification success, source evidence,
   Mathlib commit/tree/pack evidence, and the generated package artifacts that
   demonstrate the repaired source/build-output boundary.
6. Confirmation that exactly one changed-hypothesis warm was issued, no second
   attempt occurred, no builder remained afterward, and the prior dba1 failure
   envelope/log remained retained and unchanged.

The report path and digest below are placeholders that must be replaced with
the actual imported root-owned evidence. Do not enter a success branch using a
prescription/scout report in place of observed warm evidence.

```bash
QPBT_WARM_REPORT='workflow/reviews/<observed-postwarm-report>.md'
QPBT_WARM_REPORT_SHA256='<64-lowercase-hex>'
QPBT_WARM_METRIC_SHA256='<64-lowercase-hex-of-the-single-new-metric-line>'
```

`workflow/events.jsonl` must be extended only by the supported `workflow.py`
mutations below. The root must not hand-edit or reorder prior events. Session
metrics remain one append-only record per issued session in
`research/metrics/sessions.jsonl`.

## Success branch

### Required predicates

All evidence-gate items above pass; the report and its digest exist; the warm
command exited zero; terminal warm result is `built`, or an authoritative
same-key `hit`/`hit_after_wait` proves another elected invocation supplied the
only build; build count is exactly one; status is `hit`; READY/manifest and deep
inventory checks pass; and no failure envelope exists for the new key.

### Monotonic evidence records

Before transitioning a PR to `merged`, attach a set-once
`post_integration_evidence` object. Do not append the warm as a PR `checks`
entry: an approving review predates the warm, and adding a current-head check
after review would violate the ledger's review/check chronology validation.
The evidence object must contain at least:

```json
{
  "main_sha": "9c9b49548fabdd6b01916787d7dc17a4bca36513",
  "cache_key": "9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36",
  "warm_result": "built",
  "post_status": "hit",
  "builds": 1,
  "ready_manifest_sha256_equal": true,
  "deep_inventory_verified": true,
  "report_path": "workflow/reviews/<observed-postwarm-report>.md",
  "report_sha256": "<64-lowercase-hex>",
  "metric_line_sha256": "<64-lowercase-hex>"
}
```

If the accepted terminal result is an authoritative `hit` or
`hit_after_wait`, record that literal result and the elected invocation's
identity instead of falsely writing `built`.

Monotonically extend the unique INC-044 record in place, preserving every
existing identity/evidence field: set `status` to `resolved`; add
`resolution_at`; add `resolution_evidence` naming the observed report and
digest, exact 9c9/9b6 identity, verified READY, and deep inventory; and retain
the old dba1 failure paths. `incidents.jsonl` requires unique IDs, so appending a
second `INC-044` line is invalid.

### Smallest valid ordered workflow commands

Construct `QPBT_POST_INTEGRATION_JSON` from the observed values above. Then run
the following state batch exactly in this order. Each update must succeed
before its following transition.

```bash
python3 scripts/workflow.py validate

python3 scripts/workflow.py update pr LPR-014 \
  --set 'integration_sha="9c9b49548fabdd6b01916787d7dc17a4bca36513"' \
  --set "post_integration_evidence=$QPBT_POST_INTEGRATION_JSON"
python3 scripts/workflow.py transition pr LPR-014 merged
python3 scripts/workflow.py update issue QPBT-024 \
  --set "completion_evidence=$QPBT_POST_INTEGRATION_JSON"
python3 scripts/workflow.py transition issue QPBT-024 done

python3 scripts/workflow.py update pr LPR-013 \
  --set 'integration_sha="c0de0900a01724c2a515311424dcbe5e7526ebd4"' \
  --set "post_integration_evidence=$QPBT_POST_INTEGRATION_JSON"
python3 scripts/workflow.py transition pr LPR-013 merged
python3 scripts/workflow.py update issue QPBT-018 \
  --set "completion_evidence=$QPBT_POST_INTEGRATION_JSON"
python3 scripts/workflow.py transition issue QPBT-018 done

python3 scripts/workflow.py update pr LPR-012 \
  --set 'integration_sha="c5a0fecc26eb18452219cf0df31ce2a9113e45f1"' \
  --set "post_integration_evidence=$QPBT_POST_INTEGRATION_JSON"
python3 scripts/workflow.py transition pr LPR-012 merged
python3 scripts/workflow.py update issue QPBT-021 \
  --set "completion_evidence=$QPBT_POST_INTEGRATION_JSON"
python3 scripts/workflow.py transition issue QPBT-021 done

python3 scripts/workflow.py update issue QPBT-004 \
  --set 'blocked_reason="The authenticated 9c9b495/9b6ccb7 singleton warm, status-ready check, and deep inventory gate succeeded; the remaining dependency QPBT-003 is blocked."' \
  --set 'unblock_condition="Complete QPBT-003, then reconcile QPBT-004 own acceptance gates before transitioning planned to ready."' \
  --set "cache_acceptance_evidence=$QPBT_POST_INTEGRATION_JSON"

python3 scripts/workflow.py validate
```

Then run the aggregate checker required to reconcile the monotonic INC-044 and
session-metrics edits. The final event suffix must show the three PR updates
before their `merged` transitions and the three issue evidence updates before
their `done` transitions.

### Items that remain held after success

- QPBT-004 remains `planned`; QPBT-003 is still `blocked`, so no `planned ->
  ready` transition is legal as a dependency-ready claim.
- STAGE-04A remains `in_progress`; QPBT-000 remains `in_progress`.
- LPR-005 and its resolved findings remain untouched.
- The old a582 and dba1 failure envelopes/logs remain immutable historical
  evidence. Success does not erase or rewrite them.
- No QPBT-004-dependent formalization session may be dispatched until the
  issue DAG and QPBT-004's remaining gates permit it.

## Failure branch

### Trigger

Any nonzero warm exit, absent or ambiguous terminal result, extra warm attempt,
wrong main/key, wrong input identity, more than one build, failed post-status,
missing/invalid READY, manifest mismatch, deep inventory mismatch, missing
metric evidence, or a new failure envelope triggers this branch.

### Immediate lifecycle disposition

Run no PR or issue transition and record no integration SHA. In particular:

- LPR-014 stays `approved`, `integration_sha: null`, `merged_at: null`;
  QPBT-024 stays `review`.
- LPR-013 stays `approved`, `integration_sha: null`, `merged_at: null`;
  QPBT-018 stays `review`.
- LPR-012 stays `approved`, `integration_sha: null`, `merged_at: null`;
  QPBT-021 stays `review`.
- QPBT-004 stays `planned`; STAGE-04A stays `in_progress`.
- Do not issue another warm. Physical presence of all three PRs on main does
  not authorize ledger closure.

The reported failure changes QPBT-004's blocker text. After the root-owned
failure report and digest exist, make only this evidence update:

```bash
python3 scripts/workflow.py validate
python3 scripts/workflow.py update issue QPBT-004 \
  --set 'blocked_reason="The exact 9c9b495/9b6ccb7 changed-hypothesis warm failed closed during post-build package verification: Lake package verification command failed with exit code 1; QPBT-024 remains the cache-acceptance blocker, and QPBT-003 remains incomplete."' \
  --set 'unblock_condition="Retain the failure envelope, diagnose the classified failure, obtain fresh immutable review for changed evidence, and require one newly authorized changed-hypothesis warm plus completion of QPBT-003; do not retry 9c9b495/9b6ccb7 unchanged."' \
  --set "last_cache_failure_evidence=$QPBT_FAILURE_EVIDENCE_JSON"
python3 scripts/workflow.py validate
```

Do not transition QPBT-024 from `review` merely to record a terminal warm
failure. A later repair session may make the separately justified lifecycle
transition after ownership and scope are established.

### Incident/evidence disposition

For the coordinator-reported post-build package-verification failure,
provisionally classify the occurrence as the same INC-044 class. Monotonically
extend the existing unique INC-044 object: increment `count` from 1 to 2;
append the actual occurrence session ID to `occurrence_session_ids`; preserve
old evidence and append the new failure report/envelope/log/metric identities;
keep `status: mitigating`; update mitigation to forbid an unchanged retry; and
add the latest occurrence timestamp. Do not append a duplicate INC-044 line.

For an existing different class, extend that class's incident and leave
INC-044 `mitigating` because QPBT-024's success gate was not completed. For a
genuinely new class, allocate a fresh unique incident ID and, if it is an
acceptance blocker, a new issue/dependency before writable repair work. Do not
misclassify it as INC-044 merely to avoid opening the required issue.

Every failure branch must preserve exact argv/environment, timestamps, exit
code, error, the single appended metric, failure envelope and build-log hashes,
absence of the new-key READY publication, status/deep-check output if safely
available after termination, and proof that no automatic retry occurred.

## State-machine rationale

The commands above follow the implemented transitions: PR `approved -> merged`
requires `integration_sha` first, and issue `review -> done` is direct. PR
records cannot be updated after `merged`, which is why post-integration evidence
is attached before each transition. QPBT-004 cannot close because its two
dependencies are distinct; success completes QPBT-024 but not blocked QPBT-003.
A stage can complete only after its whole stage scope is complete, which is not
the case here.

## Session accounting

- Logical session: `i024-scout-a08-postwarm-closure`.
- Topology: read-only scout under root coordinator; 0 subagents; depth 1.
- Canonical start: `2026-08-31T17:01:48.398775Z`.
- Evidence cutoff/end: `2026-08-31T17:11:30.070014045Z`.
- Exact elapsed: `581.671239045` seconds.
- Base revision: `9c9b49548fabdd6b01916787d7dc17a4bca36513`.
- Repository edits, Git writes, tests, builds, warm, seed, status, Lean, Lake,
  network, process/lock/cache/runtime inspection, and canonical state mutation:
  0 each.
- Authored artifact: `/tmp/qpbt-024-postwarm-closure-a08.md` only.
- Token usage: JSON `null`; availability reason: collaboration backend does
  not expose per-agent token usage. No estimate was made.

Read-only commands used: `cat AGENTS.md`; `date --iso-8601=ns`; `wc -c` on the
specified state/event/incident/review files; `git rev-parse HEAD`; `python3
scripts/workflow.py --help`, `show --help`, `update --help`, and `transition
--help`; scoped `jq` projections of issues, PRs, sessions, stages, events, and
incidents; `tail -n 80 workflow/events.jsonl`; scoped `rg -n` searches of
workflow code, reviews, state, protocols, events, and metrics; and scoped
`sed -n` reads of workflow implementation and comparable closure reports.
Final report self-checks used read-only `rg -n` and `wc -l -c`; exact elapsed
was computed from two GNU `date` nanosecond values with Bash integer
arithmetic. No validation command was executed.

Report SHA-256 is supplied out of band after finalization because embedding it
would change the digest.
