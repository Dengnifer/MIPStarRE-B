# QPBT-081 collaboration rate-limit protocol evidence (A01)

## Result

This candidate adds a documentation-only collaboration admission protocol. It
serializes preflight, bootstrap, confirmation, and task release through one
root-owned launch-class lane; applies a 5-second minimum request stagger; and
bounds a 429 episode to three same-session retries with 10/20/40-second
exponential base delays, deterministic `[0, 5)`-second jitter, and a 120-second
deadline. Terminal exhaustion stops automatic transport and requires root
accounting. Admitted work remains parallel at the existing capacity.

No collaboration traffic was sent to reconstruct or validate the incident. No
active session, canonical workflow state, research metric, code, Lean source,
build output, cache, network resource, or GitHub state was mutated.

## Immutable scope

| Field | Value |
|---|---|
| Stable session | `i081-orchestrator-a01-rate-limit-retries` |
| Branch | `issue/qpbt-081-rate-limit-a01` |
| Base commit | `32e4d20704de440f6f25d058939880e61849681d` |
| Base tree | `0f7febe78b43d4c385192f1bb196452d51fc232a` |
| Owned repository paths | `protocols/orchestration.md`; `protocols/CHANGELOG.md`; `workflow/reviews/qpbt-081-rate-limit-retries-a01.md` |
| Canonical writes | none under `workflow/state/` or `research/metrics/` |

## Canonical incident reconstruction

`research/metrics/incidents.jsonl#INC-087` is the canonical incident. It records
nine HTTP 429 retry-limit failures across seven `gpt-5.6-sol` stable sessions,
attributes the failure class to concurrent root/nested capacity filling without
a shared launch stagger or backoff boundary, and records same-session reuse as
the successful mitigation.

The five implicated issued rows expose these exact lifecycle times and retry
counts:

| Stable session | Issuance event (UTC) | Canonical `started_at` (UTC) | Canonical end (UTC) | 429 retries |
|---|---:|---:|---:|---:|
| `i075-orchestrator-a01-classical-ldt` | `2026-09-03T23:19:33.133779Z` | `2026-09-03T23:19:33.748617Z` | `2026-09-04T00:57:34.975137Z` | 1 |
| `i043-scout-a08-source-boundary` | `2026-09-03T23:23:59.577135Z` | `2026-09-03T23:24:00.200266Z` | `2026-09-04T00:23:27.619130Z` | 1 |
| `i068-orchestrator-a28-boundary-repair` | `2026-09-04T00:16:50.556989Z` | `2026-09-04T00:16:51.160053Z` | `2026-09-04T03:42:32.007320Z` | 3 |
| `i080-orchestrator-a01-detyping-boundary` | `2026-09-04T00:49:46.328321Z` | `2026-09-04T00:50:24.427159Z` | `2026-09-04T01:25:05.022472Z` | 1 |
| `i080-orchestrator-a06-review-repair` | `2026-09-04T02:01:54.918415Z` | `2026-09-04T02:02:16.387562Z` | `null` at evidence base | 1 |

These rows account for seven failures. The QPBT-075 result report at
`/tmp/i075-orchestrator-a01-classical-ldt.md` authenticates the other two: both
parallel children, `i075-scout-a02-source-fidelity` and
`i075-scout-a03-api-precedents`, received HTTP 429 on their first work turn and
were resumed under their existing names. Their retrospective canonical planned
rows have `started_at`, `ended_at`, and `external_id` unavailable, so no exact
child request timing is claimed.

The three source-ref sessions named in QPBT-081 did not have simultaneous
canonical running transitions: their exact `started_at` values span
3,437.411436 seconds. Those values timestamp eventual running admission, not
the preceding rejected calls. INC-087's concurrency diagnosis and the QPBT-075
parallel-child report establish a burst, but neither source exposes exact 429
request timestamps. This candidate therefore does not infer simultaneity,
provider window length, or request-ID-to-session mappings that the evidence
does not contain.

The A28 handoff records `transport_429_interruptions: 2`, while the later
canonical session row and INC-087 record three failures for that identity: the
initial launch and two later resumes. The canonical count is used for the
incident total; the earlier handoff discrepancy remains visible rather than
being silently normalized.

## Decision and bounds

| Requirement | Candidate rule | Reason |
|---|---|---|
| Sequential admission | One root-owned lane covers single-session dry-run, bootstrap-only creation, confirmation, and task release; no launch/resume interleaving | Closes the root/nested burst boundary identified by INC-087 while retaining existing confirmation semantics |
| Minimum stagger | At least 5 seconds from return of one launch-class request to issuance of the next | Small initial control for a proven zero-stagger defect; not presented as a provider-window estimate |
| Backoff | For retry `r = 1..3`, `10 * 2^(r-1)` seconds plus deterministic SHA-256-derived jitter in `[0, 5)` seconds | Exponential spacing avoids immediate retries; stable-name/action/ordinal jitter disperses different sessions without network or hidden randomness |
| Retry bound | At most three retries after the initial 429 and no retry at or after 120 seconds from the initial 429 return | Cumulative planned wait is below 85 seconds and cannot become an unbounded retry loop |
| Identity | Same planned name before creation; same external thread, worktree, ownership, and task after creation | Preserves edits, reports, attempt provenance, and the successful INC-087 mitigation |
| Terminal action | Stop automation, preserve bytes/thread, keep all sibling launch-class traffic quiet through the 120-second deadline, record exact exposed transport facts, and escalate to root; any later bounded episode requires explicit authorization and the same identity | Makes exhaustion visible and prevents replacement-session multiplication |
| Parallelism | Release the lane after success, or after terminal escalation and the remaining quiet window; running work remains parallel at unchanged capacity | Limits only admission/resume traffic, not useful computation |

The deterministic jitter for stable name `S`, action kind `A`, and retry
ordinal `r` is the first eight hexadecimal digits of
`SHA-256(UTF-8(S + ":" + A + ":" + r))`, interpreted in base 16 and reduced
modulo 5000 milliseconds. It is bounded and auditable. Keeping the lane through
the episode prevents sibling retries from synchronizing even if callers reach a
429 together outside this protocol.

## Enforcement boundary

The existing repository tooling enforces exact dry-run eligibility, Git
identity, aggregate capacity, explicit backend-returned confirmation, canonical
transaction rollback, and unchanged bytes after a rejected pre-confirmation
launch. It does not own the collaboration backend calls that create a thread or
start/resume a turn. It therefore cannot observe a 429, hold a cross-parent
transport mutex, measure a launch interval, or delay a resume.

No concrete local code point covers all implicated actions. A timer in
`scripts/workflow.py` confirmation would execute after bootstrap creation, miss
task release and resume calls, and create a false mechanical guarantee. The
smallest sufficient current change is consequently the coordinator procedure
in `protocols/orchestration.md`, with no production code or focused test. If a
future repository-owned collaboration launcher wraps creation, task release,
and resume, it should implement this lane with a process-shared lock and
monotonic timestamps and add exact no-call-before-deadline tests.

## Validation and review status

Before editing, `python3 scripts/workflow.py validate` passed in 0.24 seconds:
83 issues, 40 local PRs, 9 planned sessions, 664 issued sessions, and 7 stages.
The first `python3 scripts/check_workflow.py` run executed all 418 deterministic
tests in 214.023 seconds; 416 passed and two socket-fixture cases errored because
the managed sandbox rejected Unix-domain socket binding with `EPERM`. This is
an environmental baseline failure unrelated to the documentation diff. The
post-edit validator passed in 0.25 seconds with the same ledger counts. The
required unrestricted replay then passed all 418 tests in 202.059 seconds
(`202.33` seconds command wall time), including both socket cases. It used only
the local deterministic workflow test command and performed no Lean, Lake,
cache, external network, or GitHub operation.

`git diff --check` passed. The ownership check found exactly the two modified
tracked protocol files and the one untracked owned evidence report, with no
path under `workflow/state/` or `research/metrics/`. Final committed identity
and report digest are recorded in the terminal handoff.

Independent review is still required before the candidate is activated or
integrated. The reviewer should verify the arithmetic bounds, immutable retry
semantics, root/nested lane coverage, terminal accounting, and the claim that
no current repository hook covers all collaboration transport actions.

## Metrics at evidence draft

```json
{
  "session_name": "i081-orchestrator-a01-rate-limit-retries",
  "elapsed_seconds": null,
  "elapsed_availability_reason": "The collaboration runtime exposes no authoritative per-session elapsed timer.",
  "token_usage": null,
  "token_usage_availability_reason": "The collaboration runtime exposes no per-session token counter; no estimate was made.",
  "subagent_count": 0,
  "subagent_topology": "single orchestrator; no child sessions",
  "compile_attempts": 0,
  "lean_attempts": 0,
  "lake_attempts": 0,
  "cache_attempts": 0,
  "build_attempts": 0,
  "network_attempts": 0,
  "github_attempts": 0,
  "collaboration_test_traffic_attempts": 0,
  "workflow_validation_attempts_before_edit": 1,
  "workflow_validation_attempts_after_edit": 1,
  "workflow_check_attempts_before_edit": 1,
  "workflow_check_environmental_errors_before_edit": 2,
  "workflow_check_attempts_after_edit": 1,
  "workflow_check_tests_passed_after_edit": 418,
  "workflow_check_unrestricted_replays": 1,
  "diff_check_attempts": 1,
  "ownership_check_attempts": 1,
  "repository_files_written": 3
}
```
