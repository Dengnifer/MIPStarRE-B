# QPBT-025 post-warm closure audit (a06)

## Findings

### F1 - Medium - correct the draft success report before canonical closure

`workflow/reviews/qpbt-025-postintegration-warm-success-537.md:158` says to
remove completed QPBT-024 from `QPBT-004.dependency_ids`. That conflicts with
the frozen topology in `workflow/reviews/qpbt-024-repair-topology-a17.md:31`
and `:42-43`, which keeps QPBT-024 as QPBT-004's single cache-acceptance
dependency. A completed dependency is no longer an unfinished blocker; it does
not need to be erased from the issue graph.

Before hashing or attaching the draft success report as canonical evidence,
root should replace that consequence with: preserve
`dependency_ids: ["QPBT-003", "QPBT-024"]`, retain QPBT-004 as `planned`, and
update only its blocker text and cache-acceptance evidence so QPBT-003 is the
sole unfinished blocker. The currently observed draft digest
`9d0ba1e1c1a017f20065a8821d9835834bf83b3e2dadd9fa79692c95cfd43f06`
must not be recorded as the final report digest after that correction.

### No technical closure blocker

Subject to the F1 documentation correction and terminal import/archive of this
A06 session, the success closure is authorized. The exact approved main/key
has one and only one successful built warm metric, shallow status is a hit,
READY binds the manifest, the independently recomputed deep inventory matches,
the trusted sidecar is absent, required build output remains, and there is no
matching failure envelope. No retry, second warm, or seed is authorized.

## Exact live facts

### Integrated identity

| Fact | Value |
|---|---|
| branch / HEAD | `main` / `d73cce44d5f9f37d38ee8d916811719408818c03` |
| HEAD tree | `8a8985252eb019282ab6ef1842ce1b9178a58c07` |
| sole parent | `45d2fe657af587e8e10952aced2e156d349fd65e` |
| cache key | `5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266` |
| recipe schema / version | `3` / `5` |
| verifier argv | `python3 scripts/materialize_lake_packages.py verify --remove-validated-generated-sidecars` |

The operational status call ran from
`2026-09-01T04:07:21.531873747+08:00` through
`2026-09-01T04:07:21.648942052+08:00` and returned this exact head/key with
`status: "hit"`.

### Unique warm metric

Exactly one line in `.workflow-runtime/metrics/hot-main.jsonl` matches the
cache key. Its raw-line SHA-256 is
`5022a23bf7a4a686588a5bba912e136051b743328a640c7dcb3b6185de1cb919`.

| Metric field | Value |
|---|---:|
| timestamp | `2026-08-31T20:02:45.006319Z` |
| result / status | `built` / `hit` |
| cache hit / miss | `0` / `1` |
| builds | `1` |
| lock waited / seconds | `0` / `0.0` |
| materialize seconds | `3.038161` |
| package materialize seconds | `17.847069` |
| package verify seconds | `16.824722` |
| dependency cache seconds | `39.60957` |
| build seconds | `551.877742` |
| elapsed seconds | `655.003154` |
| elected owner | PID `2`, host `GHZ` |
| build command | `["lake","--packages=.lake/package-overrides.json","build"]` |

### READY and deep inventory

| Fact | Value |
|---|---|
| manifest SHA-256 / READY content | `f41716f8a1213bd1fbff2939723c739653c360d6b797d93be69cb5a42f5ad234` |
| READY file SHA-256 | `06720bffaa45dfc2fe92f5816caf9e31178d52bd4a95bcb4fdf70eceae4aa80a` |
| inventory SHA-256 | `321e2813533a93c8218eefb277bd3425d3b55a59d978a233fc9b4795de42df60` |
| files / directories / symlinks | `124925` / `4147` / `3` |
| bytes | `10097592794` |

The full inventory was independently recomputed over the published `.lake`
from `2026-09-01T04:08:24.586680265+08:00` through
`2026-09-01T04:08:38.599077620+08:00`. It equaled the complete manifest
inventory. The READY content equaled the independently hashed manifest.

The exact target
`.lake/packages/proofwidgets/widget/package-lock.json` is a regular
172140-byte file. Its `.hash` sidecar is absent. Both
`.lake/packages/proofwidgets/.lake/build` and root `.lake/build` are real
directories. There are zero failure directories matching the new key and no
active warm/seed/Lake/Lean process or kernel-reported target lock holder.

### Current lifecycle state

| Record | Current state | Required terminal fact |
|---|---|---|
| LPR-014 | `approved`, integration null | merge at `9c9b49548fabdd6b01916787d7dc17a4bca36513` |
| LPR-015 | `approved`, integration null | merge at `d73cce44d5f9f37d38ee8d916811719408818c03` |
| QPBT-025 | `review` | done after both PR predicates and warm evidence |
| QPBT-024 | `review` | done after QPBT-025 and INC-044 reconciliation |
| QPBT-004 | `planned` | remain planned; only QPBT-003 is unfinished |
| INC-044 | `mitigating`, count `2` | resolve without changing historical occurrences |

QPBT-004 currently and correctly has
`dependency_ids: ["QPBT-003", "QPBT-024"]`. QPBT-003 is `blocked` and
QPBT-024 is not yet done. The issue/PR counters are already reconciled to 26
and 16. STAGE-04A contains QPBT-024 and QPBT-025 and remains `in_progress`.

The QPBT-025 orchestrator, immutable reviewer, and A05 integration-readiness
scout are archived, each with exactly one imported session metric. A06 is the
only non-coordinator running session and must be terminally imported and
archived before issue closure. Current workflow validation passes with 26
issues, 15 PRs, 302 issued sessions, and 7 stages.

## Evidence object

After correcting the success report, recompute its SHA-256 and construct one
structured `QPBT_POST_INTEGRATION_JSON` used unchanged by both PRs and both
issues. It should contain at least:

```json
{
  "report_path": "workflow/reviews/qpbt-025-postintegration-warm-success-537.md",
  "report_sha256": "<final digest after F1 correction>",
  "main_sha": "d73cce44d5f9f37d38ee8d916811719408818c03",
  "cache_key": "5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266",
  "warm_result": "built",
  "post_status": "hit",
  "cache_hit": 0,
  "cache_miss": 1,
  "builds": 1,
  "lock_waited": 0,
  "lock_wait_seconds": 0.0,
  "build_seconds": 551.877742,
  "package_verify_seconds": 16.824722,
  "elapsed_seconds": 655.003154,
  "command": ["lake", "--packages=.lake/package-overrides.json", "build"],
  "metric_line_sha256": "5022a23bf7a4a686588a5bba912e136051b743328a640c7dcb3b6185de1cb919",
  "manifest_sha256": "f41716f8a1213bd1fbff2939723c739653c360d6b797d93be69cb5a42f5ad234",
  "ready_manifest_sha256_equal": true,
  "deep_inventory_verified": true,
  "artifact_inventory": {
    "schema_version": 1,
    "sha256": "321e2813533a93c8218eefb277bd3425d3b55a59d978a233fc9b4795de42df60",
    "files": 124925,
    "directories": 4147,
    "symlinks": 3,
    "bytes": 10097592794
  },
  "trusted_sidecar_absent": true,
  "proofwidgets_build_present": true,
  "matching_failure_envelopes": 0
}
```

Do not append a late PR check. This is post-integration evidence, not a new
check in the already approved review chronology.

## Exact monotone closure order

1. Finish A06, copy/import this report under the canonical review path, append
   exactly one A06 metric row with unavailable token usage recorded as null,
   update the issued-session evidence, and archive A06. Inspect its report and
   digest.
2. Correct F1 in the root-owned warm-success report and hash the final bytes.
   Build the evidence object above with that final digest.
3. Run the required pre-change validation:

```bash
python3 scripts/workflow.py validate
```

4. Bind and merge LPR-014 first. Its integration SHA is its already physical
   head, not the later repair head:

```bash
python3 scripts/workflow.py update pr LPR-014 \
  --set 'integration_sha="9c9b49548fabdd6b01916787d7dc17a4bca36513"' \
  --set "post_integration_evidence=$QPBT_POST_INTEGRATION_JSON"
python3 scripts/workflow.py transition pr LPR-014 merged
```

5. Bind and merge LPR-015 at the exact integrated head:

```bash
python3 scripts/workflow.py update pr LPR-015 \
  --set 'integration_sha="d73cce44d5f9f37d38ee8d916811719408818c03"' \
  --set "post_integration_evidence=$QPBT_POST_INTEGRATION_JSON"
python3 scripts/workflow.py transition pr LPR-015 merged
```

Each update must precede its transition because `integration_sha` is set-once
and PR records cannot be updated after `merged`; the transition alone assigns
`merged_at`.

6. Attach the same evidence to the child and close it:

```bash
python3 scripts/workflow.py update issue QPBT-025 \
  --set "completion_evidence=$QPBT_POST_INTEGRATION_JSON" \
  --set 'blocked_reason=null'
python3 scripts/workflow.py transition issue QPBT-025 done
```

7. Reconcile the unique INC-044 object before closing its owning parent. This
   is a root-only in-place monotone edit to the existing JSONL object, not a
   second `INC-044` line:

- preserve `id`, class, severity, `count: 2`, both `occurrence_keys`, every old
  failure path/hash, `latest_*` failure fields, cause, and protocol effect;
- set `status: "resolved"`;
- add `resolution_at` using the actual UTC edit timestamp;
- add `resolution_evidence` naming the corrected success report and its final
  SHA-256, successful d73/537 identity, result built/status hit, metric-line
  digest, READY/manifest digest, and deep-inventory digest/counts;
- optionally add separate structured `resolution_main_commit`,
  `resolution_cache_key`, `resolution_metric_line_sha256`, and
  `resolution_inventory_sha256` fields, but do not overwrite historical
  `latest_main_commit`, `latest_cache_key`, `latest_metric_line_sha256`, or
  `latest_status`, which describe the second failed occurrence;
- do not increment `count`: the success is a resolution, not occurrence 3.

8. Attach child/warm/incident completion evidence to QPBT-024, then close the
   parent:

```bash
python3 scripts/workflow.py update issue QPBT-024 \
  --set "completion_evidence=$QPBT_POST_INTEGRATION_JSON" \
  --set 'blocked_reason=null'
python3 scripts/workflow.py transition issue QPBT-024 done
```

9. Update QPBT-004 only after QPBT-024 is done. Preserve its status and exact
   dependency list:

```bash
python3 scripts/workflow.py update issue QPBT-004 \
  --set 'blocked_reason="QPBT-003 remains incomplete. QPBT-024 and its QPBT-025 child are done after the successful authenticated recipe-v5 warm, READY check, and deep inventory verification."' \
  --set 'unblock_condition="Complete QPBT-003, then reconcile QPBT-004 own pin, provenance, empty-project build, and local-cache acceptance gates before transitioning planned to ready."' \
  --set "cache_acceptance_evidence=$QPBT_POST_INTEGRATION_JSON"
```

Do not set `dependency_ids` in this command. QPBT-004 remains `planned` with
`["QPBT-003", "QPBT-024"]`; only QPBT-003 remains unfinished.

10. Run post-change validation and the aggregate workflow/research checker,
    inspect the event suffix and final records, and only then commit the
    root-owned closure evidence:

```bash
python3 scripts/workflow.py validate
python3 scripts/check_workflow.py
```

The final event suffix must show each PR update before its merged transition,
QPBT-025 evidence before its done transition, and QPBT-024 evidence after the
child is done but before the parent's done transition. STAGE-04A and QPBT-000
remain in progress. Do not run another warm, seed, build, Lean, or Lake command.

## Source and state reconciliation

- A17 SHA-256:
  `00e423bb55defd985154224c2a4b714ffe366b682f3e391f60b4887d303f871f`.
- A05 SHA-256:
  `3d2b079b081aff095118b925c17b6d096dffb8843734f07b24445e27a37f912e`.
- Live issues state SHA-256 at cutoff:
  `30dd593b0e6fe0e1a0cc15f9412620d4b659a07d0252b3d3b4c72b7b235cff26`.
- Live PR state SHA-256 at cutoff:
  `4e0990fdab109e482439c976884fdd47445cb9d7d92dd1a6287538cbeb896ec4`.
- Live incidents ledger SHA-256 at cutoff:
  `4d4e6b079ed00d8feab474d7c7141e4ff351c7aac5f1fe52e2129533791209ec`.

## Session accounting

- Logical session: `i025-scout-a06-postwarm-closure`.
- Role/topology: fresh read-only closure scout under root coordinator;
  subagents `0`; depth `1`.
- Canonical start: `2026-08-31T20:05:38.033444Z`.
- Evidence/report cutoff: `2026-08-31T20:13:10.252458198Z`
  (`2026-09-01T04:13:10.254330344+08:00`).
- Captured elapsed: `452.219014168` seconds.
- Token usage: JSON `null`.
- Token availability reason: the collaboration backend does not expose
  per-session token usage; no estimate was made.
- Operational status calls: `1`; full deep-inventory recomputations: `1`;
  workflow validation calls: `1`.
- Cache warms, seeds, tests, compile attempts, builds, Lean commands, Lake
  commands, and network operations by this session: `0`.
- Git writes, repository/canonical edits, runtime/cache mutations, and child
  agents: `0`.
- Authored output: `/tmp/qpbt-025-postwarm-closure-a06.md` only.

The report SHA-256 is supplied out of band because embedding it would change
the digest.
