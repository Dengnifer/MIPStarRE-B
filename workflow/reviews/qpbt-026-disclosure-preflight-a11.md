# QPBT-026 disclosure preflight fixer A11

- Logical session: `i026-fixer-a11-scope-token-repair`
- Role: sole writable fixer for QPBT-026 / LPR-016
- Branch: `issue/qpbt-026-disclosure-a11-fix`
- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-026-disclosure-a11`
- Direct parent SHA: `94c0e630b5f2697f678c400da082f108bde89471`
- Direct parent tree: `4188a6d959cb145b945c9618789f96cd98165d02`
- Session start: `2026-09-01T03:10:39Z`
- Report freeze: `2026-09-01T03:30:10Z`
- Measured elapsed to report freeze: 1,171 seconds
- Owned paths: `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/local_agent.py`, `tests/test_local_agent.py`, and this report

The containing commit SHA and tree are reported separately because a report
cannot embed the SHA of the commit containing its own bytes without a circular
identity dependency. The final inventory is exactly the five owned paths.

## Design evidence and scope decision

The fixer read immutable review A08 and the A10 design report at
`/tmp/qpbt-026-scope-token-design-a10.md`, whose verified SHA-256 was
`58e030e52f67982ab039d6927db340b86ad8868cbd7dff69ff0446ae6c37c79e`.
A10 established that version-1 changed-path authorization cannot bind prompt
bytes, Git objects, tool output, inherited environment, or the host read
surface, and that read-only Codex execution is not read isolation.

The conservative A11 decision is therefore final: production reviewer dispatch
is unavailable until a separately reviewed exact-content authorization schema,
one-time capture, sanitized evidence packet, and enforceable OS filesystem and
environment isolation exist. A matching version-1 record validates its legacy
destination/target/path fields and then fails closed before task/context reads,
persistence or capability probes, harness/output creation, lease claim, command
construction, or runner invocation.

## Finding dispositions

### F-LPR016-002: replayable singleton and helper

Fixed. `_DISCLOSURE_PREFLIGHT_TOKEN` and
`_run_review_after_persistence_probe` no longer exist. Production entry points
cannot obtain or consume an offline capability. The remaining offline
constructor has no mode, transport-profile, or disclosure-token arguments and
always selects `__local_agent_offline_review_test_double__` with an injected
runner and capability record. There is no capability to replay across mode,
target, model, or profile, and duplicate consumption is inapplicable.

Regressions cover direct module attributes, offline-envelope replay into a
bound production call, cross-target/profile/model mismatch through the legacy
validator, and production bound/unbound/CLI ordering. The ordering tests verify
zero packet/task/context reads, persistence and Codex-capability probes,
harness/output preparation, lease claims, transport command construction, or
runner calls.

### F-LPR016-005: names did not bind readable content

Fixed conservatively for production by disabling dispatch before evidence or
lease side effects. The code and protocol no longer claim that version-1 path
names authorize exact transmitted content or that the offline host is isolated.

The deterministic committed offline success path now creates a fresh Git
repository rather than cloning the source. It has no remote, alternates, or Git
objects. Only changed base/head endpoint bytes are copied as inert regular files;
symlink targets and gitlinks cannot become live filesystem links. The manifest
records channel, revision role, path, Git type/mode/object identity,
representation, size, and SHA-256, plus the exact derived patch. Recursive
verification rejects unsafe paths, credentials, live symlinks, missing,
tampered, or unmanifested files, imported objects, alternates, and remotes before
the fake runner.

The offline packet projection additionally binds the inline request, unchanged
base authority blobs, harness manifest, derived evidence, and exact final prompt.
It carries a canonical digest and explicitly says `external_launchable: false`
and `host_isolation: not-enforced`. The success regression proves an unchanged
sentinel is absent, the source head OID is unresolvable, the Git object count is
zero, the exact evidence inventory matches, and a changed symlink is represented
only by inert bytes. This meets the deterministic exact-content test gate without
making an unisolated production launch reachable.

### Preserved A08 dispositions

- F-LPR016-001 remains resolved: raw and normalized authorization mappings do
  not enter a target, prompt, envelope, persisted result, or event log.
- F-LPR016-003 remains resolved: commit target, declared head, first-parent
  base, ancestry, tree, and clean-worktree checks share the committed resolver
  and occur before any lease claim.
- F-LPR016-004 remains resolved: canonical full-path screening, credential
  exclusions, and no-renames endpoint discovery remain in place. The projected
  committed capture applies the same normalization and credential classifier.

## Validation and attempts

Final code-freeze commands:

| Gate | Result | Measured wall time |
| --- | --- | ---: |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'` | pass, 60/60 | 5.49 s (5.316 s unittest) |
| `PYTHONPYCACHEPREFIX=/tmp/qpbt-026-a11-final-pycache python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py` | pass | 0.08 s |
| `python3 scripts/workflow.py validate --json` | pass, `valid=true`; 27 issues, 15 PRs, 308 issued sessions, 7 stages | 0.11 s |
| `git diff --check 94c0e630b5f2697f678c400da082f108bde89471` | pass | below timer resolution |

Focused unit attempts: 11. The baseline passed 58/58. Four intermediate runs
failed: 10 stale production/helper expectations after removing the old seam; 2
status-label expectations; 8 calls after a mistyped credential-classifier name;
and 2 uncommitted paths missing a newly required manifest-size field. Each was
fixed locally. The other seven attempts passed, ending at 60/60.

Python compilation attempts: 7 total, comprising one `py_compile` and six
`compileall` runs; all passed. Workflow validation attempts: 5; all passed.
Precommit diff-hygiene attempts: 8; all passed. No Lean/Lake/project build was
required or run. Cache hits, lock wait, and build duration are not applicable.

## Metrics and safety

- Exposed model token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session model token accounting; no estimate was made.
- Subagents spawned by this fixer: 0.
- Topology: one writable fixer; the coordinator supplied one completed read-only
  A10 design report, which the fixer read and applied directly.
- Reviewer findings addressed: 2 blockers; implementation retry classes: 4;
  incidents or workflow issues opened: 0.
- Protocol revision: QPBT-026 A11 entry dated 2026-09-01.
- External endpoints contacted: 0.
- Network requests: 0.
- Codex CLI launches or probes: 0.
- GitHub reads/writes: 0/0.
- Credentials inspected/used: 0/0.
- Lean commands: 0; Lake commands: 0; project builds: 0.
- Hot-cache warm/seed/status operations: 0/0/0.
- Canonical `workflow/state/` writes: 0.
- `research/metrics/` writes: 0.
- Subagent count: 0.

## Residual risk

Production external review is intentionally unavailable, so exact-content
authorization and OS read isolation remain future work rather than a claimed
property. Offline mode is a deterministic test facility, not a security
boundary against malicious code in the same Python process; it uses only an
injected fake runner and cannot select `codex`. The path classifier remains a
name-based credential screen rather than a content/DLP scanner. Uncommitted
bootstrap construction remains offline-only under its existing freeze contract.
