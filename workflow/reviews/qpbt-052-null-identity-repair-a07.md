# QPBT-052 Null-Identity Release Repair A07

Outcome: the changed candidate repairs the null-identity bypass reported as
`F-LPR025-A06-001`. It also addresses the remaining null-identity cases behind
`F-LPR025-A04-001` and `F-LPR025-A04-002`. No prior finding is marked resolved
by this implementation report; the candidate awaits a fresh independent review.

## Finding Disposition

### F-LPR025-A06-001: repaired in candidate, pending independent verification

Every `session.issued` payload containing `release_contract` now requires both
the corresponding issued-session `external_id` and the issuance `external_id`
to be non-empty strings. The two values must also remain equal. For a supported
contract on the `codex-collaboration` backend, release enforcement now depends
only on the marker, backend, and lifecycle progression. A null identity can no
longer disable the release requirement or its terminal/archive ordering checks.

Full-store regressions cover missing and null issuance identity copies against
a null issued-session identity for `finished`, `failed`, and `archived` rows.
They cover no release, release after terminal/archive, ordinary timestamps, and
equal timestamps with event-line ordering. A markerless archived collaboration
history with a null identity remains valid, preserving the legacy compatibility
boundary exactly.

## Reproduction

Before editing, an independent temporary full-store probe authenticated the A05
head and constructed an archived `codex-collaboration` row with
`external_id: null`, a marked issuance lacking `external_id`, a terminal event,
an archive event, and no release. Both `validate_documents` and
`WorkflowStore.validate()` unexpectedly accepted it.

The first focused regression run failed in all ten hostile subcases while its
markerless legacy control passed. This reproduced the missing/null identity
bypass for all three terminal statuses and the late-release ordering bypass at
ordinary and equal timestamps.

## Authentication

- Formal PR base: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`
  (authenticated commit and ancestor of the candidate).
- Dispatched repair base and sole candidate parent:
  `2310617ed6df56730f1fa267a9b19aec47be6e37`.
- Candidate head: `9d3b81b4c431d4b8e095d8dc94a8363c2ff07d84`.
- Candidate tree: `3bb25c9933326774ec07d23cb97071e0c61aec5c`.
- Commit subject: `fix(workflow): reject marked null identities`.
- Exact candidate changed paths: `scripts/workflow.py`,
  `tests/test_workflow.py`.
- Sorted newline-delimited two-path manifest SHA-256:
  `ed1d478437c5e52e80e2828ca3439138c7483235b51c49ffbff7f24a30cb8184`.
- `scripts/workflow.py` SHA-256:
  `340c350048be479259274cdbb95b9b7d4f9e87d2760ee0aaa52b30a0c55b3857`.
- `tests/test_workflow.py` SHA-256:
  `d90f48ebb54eda92974f0ebbbda12d25225302ef16141fdb8bdf0c90a85d6855`.
- A06 review SHA-256:
  `e450b2d2f8782bdf5975fbf1b4443d80857bff60ee54e81abd0cf977a8a20347`.
- A05 repair report SHA-256:
  `fb5aec95306545c793bae05449b36c14c8585136c51860ef9dcd6e012863ccd8`.

This report is intentionally outside the candidate commit so it can
authenticate the immutable head and tree. Its SHA-256 is supplied out of band
after these bytes are frozen.

## Validation

| Command | Result | Wall time |
| --- | --- | ---: |
| Pre-repair focused full-store regressions | expected red: 10 hostile subcases accepted; markerless control passed | 0.14 s |
| First post-repair focused run (six test methods) | 6/6 passed | 0.13 s |
| Refined focused run (six test methods) | 6/6 passed | 0.16 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py` | 87/87 passed | 6.50 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_local_agent.py` | 65/65 passed | 16.90 s |
| `PYTHONPYCACHEPREFIX=/tmp/qpbt-052-a07-pycache python3 -m compileall -q scripts/workflow.py scripts/local_agent.py tests/test_workflow.py tests/test_local_agent.py` | passed | 0.22 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py --root . --skip-tests` | `workflow state: valid` | 0.16 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py --root . validate` | valid: 52 issues, 24 PRs, 407 issued sessions, 7 stages | 0.13 s |
| `git diff --check` | passed | 0.03 s |
| Post-commit ancestry, tree, path-manifest, file-hash, and clean tracked-state authentication | passed | not separately instrumented |

The two full suites ran concurrently in isolated temporary directories. No
repository build output or shared writable cache was involved.

## Scope And Metrics

- Candidate edits: `scripts/workflow.py` and `tests/test_workflow.py` only.
- External report:
  `workflow/reviews/qpbt-052-null-identity-repair-a07.md`.
- Canonical workflow state, metrics, event-log, and protocol edits: 0.
- Nested agents: 0; topology was one implementation orchestrator only.
- Token usage: `null`; per-agent token counters are not exposed by the
  collaboration runtime.
- Session elapsed seconds: `null`; a stable external session-start timestamp is
  not exposed to this agent. Individually measured command wall times are above.
- Focused regression attempts: 3 (one expected red, two green).
- Full-suite attempts: 1 per suite; retries: 0.
- Python compileall attempts: 1, passed; retries: 0.
- Lean/Lake compile or build attempts: 0.
- Cache actions and duplicate builders: 0.
- Network, endpoint, GitHub, credential, and push actions: 0.
- Local staging attempts: 1; local commit attempts: 1; both passed.
- Incidents: 0. Protocol revisions: 0.

## Residual Risk

Markerless collaboration histories deliberately retain their legacy behavior,
including terminal archived rows with null identity and no release. This is the
documented compatibility boundary, not a newly marked lifecycle. The candidate
has not been reviewed by an independent session, so integration remains blocked
until a fresh reviewer authenticates this exact head and disposes the open
findings. No Lean build was run because this repair is Python-only and the task
explicitly excluded Lean, Lake, and cache work.
