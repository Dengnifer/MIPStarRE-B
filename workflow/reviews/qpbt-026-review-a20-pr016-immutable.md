# QPBT-026 / LPR-016 immutable review A20

## Findings

No findings. I found no safety, correctness, source/contract-fidelity, or test
regression in the exact immutable range. No `F-LPR016-009` issue is proposed.

Mathematical truth and paper-source fidelity are not applicable: the range
changes workflow protocol, a Python launcher and tests, and implementation
evidence reports only. It changes no paper-labelled theorem, Lean declaration,
blueprint statement, or mathematical source.

## Verdict

`approve`. `F-LPR016-008` is resolved, and `F-LPR016-001` through
`F-LPR016-007` remain resolved at this exact head. Production external review
remains intentionally disabled.

## F-LPR016-008 disposition

Resolved. `scripts/local_agent.py:2271-2341` defines the complete accepted
11-field allowlist: four required fields and the producer's seven optional
detail fields. It rejects unknown fields, enforces exact string, integer, and
boolean types (so `bool` cannot pass as `int`), validates nullable fields and
positive timeouts, and performs strict JSON serialization with NaN disabled.

The sole production producer, `inspect_codex_review_capability` at
`scripts/local_agent.py:2172-2257`, returns all 11 fields on both its normal and
timeout branches. Its complete records pass unchanged. Short injected fixtures
with the four required fields remain supported; nullable return-code and signal
fields are accepted with their documented types.

Every injected-record consumer was traced. `run_review` validates at
`scripts/local_agent.py:3094-3099` before a lease claim; `_run_review_unbound`
validates at `scripts/local_agent.py:3042-3046`; and `_run_offline_review`
revalidates at `scripts/local_agent.py:3165-3169` before the first repository
inspection. Thus malformed data cannot reach a real capability probe,
repository inspection, harness/output creation, lease claim, command
construction, runner invocation, or result serialization. The new regression
exercises the public and private early boundaries with zero observed calls or
filesystem creation. A separate pure-validator matrix accepted three valid
short/complete/nullable records and rejected seven adversarial records,
including unknown, NaN, bool-as-int, integer-as-bool, malformed digest, and
empty-signal cases.

## Prior finding reconfirmation

- `F-LPR016-001`: resolved. Raw/normalized authorization mappings remain
  internal to validation and are not echoed into evidence or result envelopes.
- `F-LPR016-002`: resolved. Missing production profiles fail before review
  work, and no replayable global preflight token or post-persistence production
  helper exists.
- `F-LPR016-003`: resolved. Immutable committed target, exact base/head,
  first-parent, ancestry, tree, cleanliness, and path checks precede any bound
  production lease claim.
- `F-LPR016-004`: resolved. Canonical full-path credential screening and
  no-renames changed-path handling remain intact; no credential content was
  inspected during this review.
- `F-LPR016-005`: resolved. All production version-1 entry paths fail closed
  before packet/context/persistence/capability/evidence/harness/output/lease/
  command/runner effects. Exact-content authorization and OS read isolation
  remain prerequisites for enabling production review.
- `F-LPR016-006`: resolved. Empty, missing, and malformed injected capability
  records fail without falling back to the live capability probe.
- `F-LPR016-007`: resolved. Git subprocesses and the injected runner retain the
  fixed minimal environment; ambient Git/Codex/credential selectors are not
  inherited.

Standing trust in official OpenAI transport and
`https://api.finite-dimensional.space` remains transport trust only. It does
not confer exact-content authorization or host-read isolation. The A19 delta is
confined to capability validation, its tests, and its report; it does not alter
the previously reviewed production security surfaces.

## Immutable identity

- Base: `ea584e9e894391773e09ddad2ce4d082497c7913`.
- Head: `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.
- Head tree: `88b1b6076aa8890376cf4f8b56c3da2bd372367d`.
- Direct parent: `f3f49388f7058a9f9b997798417e4ae08435f523`.
- Merge base: the exact declared base; base ancestry passed.
- Commit count: exactly 5 in `BASE..HEAD`.
- State: detached and clean at initial authentication and evidence freeze.
- Exact no-renames manifest: 9 paths and no others:
  `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/local_agent.py`, `tests/test_local_agent.py`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a01.md`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a05.md`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a11.md`,
  `workflow/reviews/qpbt-026-offline-isolation-a17.md`, and
  `workflow/reviews/qpbt-026-capability-schema-a19.md`.
- A19 report SHA-256:
  `518f5c4e133b8bd0eb7ef4303ee3a4953e30113ef5e510960e41c9e9657a089f`.
- Prior A18 immutable review SHA-256:
  `0b203f02ade092400fdc524cb36ec5ee54ab190f3d460392d27f4dde09053cfe`.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p
  'test_local_agent.py'`: passed 63/63 in 5.208 seconds; 5.37 seconds command
  wall time.
- `PYTHONPYCACHEPREFIX=/tmp/qpbt-026-review-a20-pycache python3 -m compileall
  -q scripts/local_agent.py tests/test_local_agent.py`: passed; 0.22 seconds.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate`: passed with
  `valid=true`; 27 issues, 15 pull requests, 308 issued sessions, and 7 stages;
  0.11 seconds.
- Exact-range `git diff --check`: passed at authentication and evidence freeze.
- Head/tree/parent, merge-base, ancestry, revision count, detached state, exact
  name-status manifest, report digests, and clean state all passed.

Evidence cutoff: `2026-09-01T04:46:47.228264002Z`. Whole-session start time and
elapsed time were not exposed before the first tool action, so neither was
estimated. The final report SHA-256 is reported externally after the bytes are
frozen because embedding a file's own digest would change that digest.

## Metrics and residual risk

- Exposed token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session token accounting; no estimate was made.
- Subagents: 0; topology was one fresh independent read-only reviewer.
- Prescribed unit/compile/workflow attempts: 1/1/1. Diff-hygiene attempts: 2.
  Pure-validator adversarial attempts: 2 (the first had an import-path setup
  error before validation; the corrected attempt passed 3 valid and 7 invalid
  cases). Review findings: 0; implementation retries: 0; incidents: 0.
- Repository edits, canonical state/metrics writes, commits, branches, and Git
  writes: 0. The only report artifact is this assigned `/tmp` file; compile
  cache output is confined to `/tmp/qpbt-026-review-a20-pycache`.
- Codex CLI launches/real probes: 0/0. Endpoint/network requests: 0/0. GitHub
  reads/writes: 0/0. Credential files or contents inspected/used: 0/0.
- Lean/Lake/project build/full build/hot-cache actions: 0/0/0/0/0.

Residual risk is unchanged and explicit: the offline runner is a trusted
in-process test double, not an OS isolation primitive; credential screening is
name-based rather than content scanning; and production review must remain
disabled until exact-content authorization and enforceable host read isolation
are implemented and independently reviewed.
