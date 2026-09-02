# QPBT-052 Release Contract Repair A05

Outcome: both A04 blocker findings are repaired in a changed candidate head.
The candidate remains unapproved and requires a fresh independent immutable
review before integration.

## Finding Dispositions

### F-LPR025-A04-001: fixed in candidate, pending independent verification

Marked `post-confirmation-v1` histories now require release before every
terminal and archive event. Ordering uses `(timestamp, event line)`, so a
terminal or archive event earlier in the log is rejected even when its
timestamp equals the release timestamp. Focused regressions cover ordinary
time, equal-time, terminal-before-release, archive-before-release, and the
valid release-first order.

### F-LPR025-A04-002: fixed in candidate, pending independent verification

The presence of a `release_contract` field on `session.issued` is now a
non-downgradable marker. The validator rejects an unsupported contract, a
non-collaboration session backend, or an issuance `external_id` that does not
equal the immutable issued-session identity. Markerless legacy histories
remain valid. Hostile regressions cover wrong and missing identities, wrong
backend, unsupported contract, and a markerless compatibility control.

## Authentication

- Dispatched base: `40d3e565426f74a0e3c60798ec7e2b5f7e35cfbf`
- Candidate head: `2310617ed6df56730f1fa267a9b19aec47be6e37`
- Candidate tree: `d8a0402804ed6066b4c7143285446815925ce267`
- Candidate parent: `40d3e565426f74a0e3c60798ec7e2b5f7e35cfbf`
- Formal PR base: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`
- Commit: `fix(workflow): bind marked release lifecycles`
- Candidate changed paths: `scripts/workflow.py`, `tests/test_workflow.py`
- Sorted newline-delimited changed-path manifest SHA-256:
  `ed1d478437c5e52e80e2828ca3439138c7483235b51c49ffbff7f24a30cb8184`
- `scripts/workflow.py` SHA-256:
  `ada39132d3c837e86aa1e4d5849b277dd111976dd88d2560c15a2b660882aa1d`
- `tests/test_workflow.py` SHA-256:
  `1cd151ffd44b02a0bf03a49dc826dc1e0d194fa08c0b12cf810f78cc25832e5a`
- A04 review SHA-256:
  `e4d2cafe70963d59ebb68ba4854a60d31bdeefbb43ee49f43cf354c7ae7e7036`
- Prior candidate path-manifest SHA-256 authenticated against the supplied
  value: `9c8a5a2e835d5afd3363d708be5298a8141a64aac52b3652083754aef1e57e6e`

This report is intentionally outside the candidate commit so it can
authenticate the exact head and tree without a self-reference.

## Validation

| Command | Result | Duration |
| --- | --- | ---: |
| Focused two-test red probe before validator repair | expected failure in all 8 hostile subcases | 0.13 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py EventLogTests.test_marked_release_precedes_terminal_and_archive_events EventLogTests.test_marked_issuance_identity_backend_and_contract_are_checked EventLogTests.test_legacy_collaboration_history_without_release_contract_remains_valid EventLogTests.test_equal_timestamp_release_order_uses_event_line_sequence EventLogTests.test_release_identity_and_backend_scope_are_checked` | 5 passed | 0.13 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py` | 84 passed | 1.40 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_local_agent.py` | 65 passed | 5.39 s |
| `PYTHONPYCACHEPREFIX=/tmp/qpbt-052-a05-pycache python3 -m compileall -q scripts/workflow.py scripts/local_agent.py tests/test_workflow.py tests/test_local_agent.py` | passed | 0.26 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py --root . validate` | valid: 52 issues, 24 PRs, 407 issued sessions, 7 stages | 0.14 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py --root . --skip-tests` | `workflow state: valid` | 0.15 s |
| `git diff --check` | passed | 0.03 s |

The full workflow suite includes the previously accepted lock-held transaction
rollback regressions. `tests/test_local_agent.py` was executed read-only.

## Scope And Metrics

- Stage-1 implementation edits: `scripts/workflow.py` and
  `tests/test_workflow.py` only.
- External report: `workflow/reviews/qpbt-052-release-contract-repair-a05.md`.
- Canonical state/metrics edits: 0.
- Lean/Lake/build/cache actions: 0.
- Network, GitHub, credential, or other external operations: 0.
- Nested agents: 0; topology was one orchestrator only.
- Token usage: `null`; per-agent token counters are not exposed by the
  collaboration runtime.
- Session elapsed seconds: `null`; a stable external session start timestamp
  is not exposed by the collaboration runtime.
- Python compileall attempts: 1, passed.
- Focused regression attempts: 2, expected red then green.
- Full-suite retries: 0.
- Local Git commits: 1.
- Incident: the first local `git add` encountered the managed read-only index;
  the exact two-path staging and commit completed through approved scoped Git
  metadata access.
- Protocol revision: unchanged; no protocol files were in the repair lease.
- Review status: fresh independent review required; no approval is claimed.
