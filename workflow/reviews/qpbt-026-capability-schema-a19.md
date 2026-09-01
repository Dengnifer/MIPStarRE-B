# QPBT-026 capability schema fixer A19

- Logical session: `i026-fixer-a19-capability-schema`
- Role: sole writable fixer for QPBT-026 / LPR-016 attempt A19
- Branch: `issue/qpbt-026-disclosure-a19-fix`
- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-026-disclosure-a19`
- Required direct parent: `f3f49388f7058a9f9b997798417e4ae08435f523`
- Required-parent tree: `631264163b80c81db945fc88d0f9de5a61ab9228`
- Evidence cutoff: `2026-09-01T04:34:45.621447588Z`
- Requested model: `gpt-5.6-sol`

The containing commit SHA and tree are reported separately because a report
cannot embed the SHA of the commit containing its own bytes without circular
identity. The intended commit inventory is exactly this report,
`scripts/local_agent.py`, and `tests/test_local_agent.py`.

## Source evidence and trace

The immutable A18 review was read from
`/home/drx/MIPStarRE-auto/workflow/reviews/qpbt-026-review-a18-pr016-immutable.md`.
Its SHA-256 was verified as
`0b203f02ade092400fdc524cb36ec5ee54ab190f3d460392d27f4dde09053cfe`.
No external source, endpoint, credential, or mutable reviewer context was used.

`inspect_codex_review_capability` is the sole production producer. Both its
ordinary and timeout returns contain the same 11 fields. Four fields were
already required by offline fixtures: `version`, `review_help_sha256`,
`selector_with_prompt_supported`, and `probe_reason`. The remaining seven
producer fields are optional for injected fixtures: `probe_returncode`,
`probe_output_sha256`, `probe_timeout_seconds`,
`version_help_timeout_seconds`, `probe_timed_out`,
`probe_termination_signal`, and `probe_termination_escalated`.

The injected record has three validation consumers. `run_review` validates it
before a bound lease claim; `_run_review_unbound` validates it before entering
the private constructor; and `_run_offline_review` repeats validation before
repository inspection. After validation, the selector boolean alone chooses
the offline command shape. The complete copied mapping is retained unchanged in
dry-run and terminal envelopes and is serialized into `result.json`; there are
no other capability-field consumers.

## Finding disposition

### F-LPR016-008: malformed extra capability reaches side effects

Fixed. `_validate_offline_codex_capability` now rejects every unexpected field
and validates every present accepted field. Strings and digests have exact
string types and their existing content constraints; booleans use exact boolean
types; return codes use nullable exact integers; timeout values use positive
exact integers; and the termination signal uses a nullable nonempty exact
string. A final strict JSON encoding check confirms the accepted copied mapping
is JSON-safe. A legitimate complete record returned by the mocked production
producer round-trips through the validator unchanged. Existing shorter
injected fixtures remain valid because all seven probe-detail fields are
optional.

The adversarial regression starts from valid required fields and covers an
unserializable unexpected value plus malformed values for every optional field
type. Each case is exercised through both the public bound `run_review` entry
and the private `_run_offline_review` boundary. The real capability probe,
repository probe, both harness constructors, output constructor, and lease
claim are mocked and observed at zero calls. The injected runner has zero calls,
and neither the nonexistent repository path nor any runtime, harness, or output
directory is created.

Production version-1 fail-closed ordering, the A17 no-fallback rule, the fixed
Git/runner environment, and exact offline projection behavior are unchanged.
Production external review remains disabled.

## Validation and attempts

| Attempt | Command or check | Result |
| --- | --- | --- |
| 1 | `python3 scripts/workflow.py validate` before edits | pass, `valid=true`; 27 issues, 15 PRs, 308 issued sessions, 7 stages; 0.11 seconds |
| 1 | Three focused capability tests after the initial edit | pass, 3/3 in 0.052 seconds; 0.21 seconds command wall time |
| 2 | The same three focused tests after the final assertion edit | pass, 3/3 in 0.055 seconds; 0.19 seconds command wall time |
| 1 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'` | pass, 63/63 in 4.066 seconds; 4.23 seconds command wall time |
| 1 | `PYTHONPYCACHEPREFIX=/tmp/qpbt-026-a19-pycache python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py` | pass; 0.22 seconds command wall time |
| 1 | Pre-report diff hygiene and bytecode inventory | pass; timing was not separately exposed by the composed read-only command |
| 2 | `python3 scripts/workflow.py validate` after edits | pass, `valid=true`; 27 issues, 15 PRs, 308 issued sessions, 7 stages; 0.10 seconds |
| 1 | Stage the three owned paths inside the managed sandbox | failed before mutation because the shared worktree index was read-only; 0.1 seconds |
| 2 | Stage the same three paths with approved Git-index access | pass; 4.4 seconds including approval handling and staged-payload checks |

There were no failed test, compile, workflow-validation, or file-edit attempts
before the evidence cutoff. The sole operational failure was the non-mutating
sandbox staging attempt recorded above. Committed-range hygiene, path, parent,
tree, branch, ancestry, commit-count, cleanliness, and report-digest checks are
reported with the containing commit.

The session start timestamp and therefore whole-session elapsed time were not
exposed before the first tool action; neither value was estimated. No Lean,
Lake, project build, or hot-main-cache command was required or run.

## Metrics and safety

- Exposed model token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session model token accounting; no estimate was made.
- Subagents spawned: 0; topology was one writable fixer under the root
  coordinator with the completed immutable A18 review as input evidence.
- Reviewer findings addressed: 1; implementation retry classes: 0; incidents
  or new workflow issues opened: 0.
- External endpoints contacted: 0; network requests: 0.
- Codex CLI launches and real capability probes: 0/0.
- GitHub reads/writes: 0/0.
- Credentials inspected/used/transmitted: 0/0/0.
- Lean commands: 0; Lake commands: 0; project/full builds: 0/0.
- Hot-cache warm/seed/status operations: 0/0/0.
- Canonical `workflow/state/` writes: 0.
- `research/metrics/` writes: 0.
- Subagent count: 0.

## Residual risk

The offline runner remains an injected in-process test double and is trusted to
honor the supplied fixed environment; it is not an OS isolation primitive.
Production external review remains intentionally unavailable until
exact-content authorization and enforceable host read isolation are implemented
and independently reviewed.
