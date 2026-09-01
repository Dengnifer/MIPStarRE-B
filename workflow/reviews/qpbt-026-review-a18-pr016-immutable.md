# QPBT-026 / LPR-016 immutable review A18

## Finding

### F-LPR016-008 (high): unexpected capability fields reach runner side effects before failing

`scripts/local_agent.py:2277` requires only a subset of capability keys and
`scripts/local_agent.py:2293` returns the entire injected mapping without
validating its remaining keys or values. Consequently a record whose four
required fields are valid but which also contains an unserializable value is
accepted before repository inspection. The offline path then creates the
harness at `scripts/local_agent.py:3177`, creates output at
`scripts/local_agent.py:3315`, and invokes the injected runner at
`scripts/local_agent.py:3321`; only the final JSON write at
`scripts/local_agent.py:3419` rejects the malformed extra value.

I reproduced this locally with a disposable `/tmp` repository, the existing
fake runner, a valid capability fixture, and `{"unexpected": object()}`. The
call ended with `TypeError: Object of type object is not JSON serializable`, but
the runner had been called once and the harness parent, run directory, and
`prompt.md` had already been created. No Codex executable, capability probe,
network, endpoint, or credential was used.

This violates the assigned gate that malformed injected capability records
fail before real probe, harness, output, or runner actions. It also makes the
general field-validation claim in `protocols/CHANGELOG.md:5` incomplete; the
focused regression at `tests/test_local_agent.py:1523` covers `{}` only.

Smallest sufficient fix: define and validate the complete accepted capability
schema (including types for every optional probe field), reject unexpected
fields, or canonicalize the record to a fully validated known-field mapping.
Add a regression containing valid required fields plus malformed unexpected or
optional data and assert zero repository/probe/harness/output/lease/runner
calls. Validation must happen at both current early validation sites.

## Verdict

`request_changes`. Production external review remains fail-closed, but the
current head does not meet the explicit malformed-offline-record ordering gate.

Mathematical truth and paper-source fidelity are not applicable: the immutable
range changes only workflow protocol, Python launcher/tests, and implementation
evidence reports; it changes no paper-labelled theorem, Lean declaration,
blueprint statement, or mathematical source.

## Prior finding dispositions

- `F-LPR016-001`: resolved at the current head. Raw and normalized
  authorization mappings remain internal to validation; production cannot
  construct a target/prompt/envelope, and offline mode rejects authorization
  data. The focused artifact checks remain consistent with the implementation.
- `F-LPR016-002`: resolved on its original missing-profile and replay surfaces.
  Missing profiles fail before authorization/task/context/persistence/lease
  work. The module-global token and independently callable post-persistence
  production helper are absent, so offline state cannot be replayed into a
  production helper.
- `F-LPR016-003`: resolved. Commit target, declared head, first parent, exact
  base, clean source, ancestry, and tree resolution share the committed target
  resolver and fail before a bound production lease claim.
- `F-LPR016-004`: resolved for the changed-path classifier. Paths are canonical
  POSIX repository-relative names, the full case-folded path is screened, and
  `--no-renames` retains both rename endpoints. The required sensitive examples
  are rejected while `.crt`, `.cer`, and ordinary `keys`/`auth` names remain
  allowed.
- `F-LPR016-005`: resolved for production disclosure. Every production entry
  point rejects version 1 before packet/task/context reads, persistence or
  capability probes, evidence/harness/output creation, lease claim, Codex
  command construction, or runner invocation. The offline projection is
  explicitly non-launchable and does not claim OS isolation.
- `F-LPR016-006`: resolved on its stated empty/falsey fallback surface. `{}` and
  invalid required-field values are rejected before repository inspection, and
  no offline path falls back to `inspect_codex_review_capability`. The broader
  malformed-extra-field defect is separately recorded as F-LPR016-008 rather
  than reopening the original falsey-fallback finding.
- `F-LPR016-007`: resolved. All Git subprocesses route through `_git_bytes` and
  receive the fixed whitelist environment; the deterministic commit adds only
  its two fixed date values. The injected runner receives a fresh copy of the
  same base mapping. Ambient repository/object/alternate/namespace/replacement,
  shallow/discovery/quarantine/ceiling/template and count/parameter config
  selectors, plus host/Codex secret selectors, are absent. The planted source
  alternate cannot resolve the source head from the harness, and the harness
  reports no alternate and zero local objects.

## Protocol and safety checks

The CLI validates a complete transport profile and legacy authorization before
calling `_packet_from_arguments`; bound and unbound library production paths
enter the same unconditional isolation failure before persistence, capability,
evidence, output, lease, command, or runner effects. Uncommitted production
targets are also unreachable. No production path invokes Codex.

Standing trust for official OpenAI transport and
`https://api.finite-dimensional.space` is correctly described as transport
trust only. It grants neither exact-content authorization nor OS read
isolation. The protocol truthfully states that version 1 is not launch authority
and that the injected in-process offline runner is not an isolation primitive.
The A17 Git-environment and production fail-closed claims match current code and
tests. Its capability statement is accurate for the four required fields and
empty records, but not for malformed additional data as F-LPR016-008 shows.

The current head was inspected together with the A03, A04, A08, and A14
immutable reviews and the A17 fixer report. Surrounding callers, the CLI,
private offline constructor, Git wrappers, harness verification, output
serialization, and focused tests were examined. No regression beyond
F-LPR016-008 was found.

## Immutable identity

- Base: `ea584e9e894391773e09ddad2ce4d082497c7913`.
- Head: `f3f49388f7058a9f9b997798417e4ae08435f523`.
- Head tree: `631264163b80c81db945fc88d0f9de5a61ab9228`.
- Direct parent: `89862d4b74364d1b2bb488d3ffc8e6820564c9ea`.
- Exact merge base: the declared base.
- Base ancestry: passed; `BASE..HEAD` contains exactly 4 commits.
- Worktree: detached and clean at start and evidence freeze.
- Exact no-renames manifest: 8 paths and no others:
  `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/local_agent.py`, `tests/test_local_agent.py`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a01.md`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a05.md`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a11.md`, and
  `workflow/reviews/qpbt-026-offline-isolation-a17.md`.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p
  'test_local_agent.py'`: passed 62/62 in 4.254 seconds; 4.47 seconds command
  wall time.
- `PYTHONPYCACHEPREFIX=/tmp/qpbt-026-a18-pycache python3 -m compileall -q
  scripts/local_agent.py tests/test_local_agent.py`: passed in 0.30 seconds.
- `python3 scripts/workflow.py validate`: passed with `valid=true`; 27 issues,
  15 pull requests, 308 issued sessions, and 7 stages; 0.16 seconds.
- Exact range `git diff --check`: passed in 0.01 seconds.
- Exact `git diff --name-status --no-renames`, head/tree/parent, merge-base,
  ancestry, revision-count, detached-state, and clean-state checks passed.

Review start: `2026-09-01T04:16:39Z`. Evidence freeze:
`2026-09-01T04:22:45Z`. Measured elapsed to freeze: 366 seconds.

## Metrics and residual risk

- Requested reviewer model: `gpt-5.6-sol`.
- Exposed token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session token accounting; no estimate was made.
- Subagents: 0; topology was one fresh independent read-only reviewer.
- Prescribed unit/compile/workflow attempts: 1/1/1. Diff-hygiene attempts: 2.
  Additional safe local adversarial scripts: 4; all used only disposable `/tmp`
  repositories or pure validation and injected no-op/fake runners.
- Repository edits, state writes, metric writes, commits, branches, and worktree
  changes: 0. The only persistent review artifact written is this assigned
  `/tmp` report; prescribed compile-cache bytes were confined to
  `/tmp/qpbt-026-a18-pycache`.
- Codex CLI launches/probes: 0. External endpoints/network requests: 0/0.
  GitHub reads/writes: 0/0. Credential files or contents inspected/used: 0/0.
- Lean commands, Lake commands, project/full builds, and hot-cache operations:
  0/0/0/0.

Residual risk remains intentionally explicit: production external review is
disabled pending exact-content authorization and enforceable OS isolation; the
offline runner remains a trusted in-process test double; and credential path
screening is name-based rather than content scanning. After F-LPR016-008 is
fixed, the changed head requires another fresh immutable review.
