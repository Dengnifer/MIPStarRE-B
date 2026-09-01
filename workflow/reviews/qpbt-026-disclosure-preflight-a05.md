# QPBT-026 disclosure preflight fixer A05

- Logical session: `i026-fixer-a05-disclosure-preflight`
- Role: sole writable fixer under the existing QPBT-026 orchestrator
- Starting/base SHA: `5d6164e949a32c906557a136c7e49558ea13d7ae`
- Starting tree: `7af3fb789c5a4438482599b25e0d42a2088bbba6`
- Branch: `issue/qpbt-026-disclosure-a05-fix`
- Scope: `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/local_agent.py`, `tests/test_local_agent.py`, and this report
- Result: all four A03/A04 findings resolved in the candidate diff

The containing commit and tree are reported separately because a report cannot
embed the SHA of the commit that contains its own bytes without a circular
identity dependency.

## Finding dispositions

### F-LPR016-001: authorization echo

Resolved. Authorization validation now returns no mapping. Successful preflight
produces only a process-local opaque token consumed by the internal dispatch
helper. The raw authorization is no longer passed into evidence preparation,
added to the target, serialized into the trusted prompt, or returned in dry-run
or persisted result envelopes. Regressions inspect the prompt, returned
envelope, persisted `result.json`, and event log for authorization-only keys.

### F-LPR016-002: missing-profile bypass

Resolved. Every production review dispatch requires a complete validated
transport profile and an exact authorization. Missing profile and missing
authorization cases fail before persistence probing, packet/context loading,
evidence preparation, or lease claim across CLI, unbound-library, and
bound-library entry points. The direct post-persistence helper requires the
opaque preflight token.

Legacy deterministic harness tests use an explicit library-only
`offline_test_mode`. It requires injected runner and capability records, rejects
transport/authorization data, substitutes
`__local_agent_offline_review_test_double__` for the executable, and has no CLI
flag. It therefore cannot cause the launcher to execute `codex` or run the Codex
capability probe.

Version-1 authorization remains committed-target-only. An uncommitted Stage 1
bootstrap dispatch now fails closed; a future external bootstrap attempt needs
a separately reviewed immutable-snapshot authorization schema.

The repository treats official OpenAI and
`https://api.finite-dimensional.space` as standing trusted Codex transports.
This is transport trust only. It does not authorize credentials, unrelated
private content, or any repository evidence; every external review still needs
its own exact immutable file manifest and matching disclosure authorization.

### F-LPR016-003: post-lease commit/head mismatch

Resolved. Disclosure preflight and evidence preparation now use the same
committed-target resolver. A supplied commit `head_sha` must resolve exactly to
the commit target, and a supplied base must equal its first parent. The focused
bound regression presents commit A with declared head B and verifies rejection
before lease claim or harness preparation.

### F-LPR016-004: incomplete credential path screening

Resolved. Authorization and Git-derived scope paths must be canonical POSIX
repository-relative paths. Screening uses the full case-folded path and rejects
sensitive directories, established credential artifacts, private-key names,
and certificate/private-container suffixes. Required denials include
`keys/id_rsa`, `.ssh/authorized_keys`, `private/private_key.pem`,
`certs/client.pem`, `.aws/config`, and `credentials/config`. Representative
ordinary paths such as `src/keys/map.py`, `docs/passwordless-auth.md`, and
`src/tokenizer.py` remain allowed. Public certificate paths such as
`certs/ca.crt` and `certs/client.cer` are not rejected merely by extension;
high-signal `.credentials`/`.secrets`/`.gcloud` directories, `.npmrc`, `.pypirc`,
service-account artifacts, and private-container suffixes remain denied.

Changed-path extraction uses `git diff --no-renames --name-only -z`, so both
sides of a rename remain in the authorized scope. A synthetic regression proves
that renaming `.ssh/authorized_keys` to a benign name still exposes the old
sensitive path to the filter. No credential file or credential content was read.

## Acceptance evidence

Final commands at the report candidate:

| Gate | Result | Measured time |
| --- | --- | ---: |
| `python3 -m unittest discover -s tests -p 'test_local_agent.py'` | pass, 58/58 | 4.910 s unittest; 5.04 s wall |
| `python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py` | pass | 0.07 s wall |
| `python3 scripts/workflow.py validate` | pass, `valid=true`; 27 issues, 15 PRs, 308 issued sessions, 7 stages | 0.11 s wall |
| `git diff --check` | pass | 0.02 s wall |

Focused test attempts: eight. The first implementation pass ran 57 tests and
failed two cases in 4.203 seconds: one false positive for `src/keys/map.py` and
one stale uncommitted-bootstrap CLI expectation. After narrowing the component
classifier and making the CLI expectation fail closed, subsequent attempts
passed 57/57 in 4.460 and 4.276 seconds, then 58/58 in 4.223 and 4.331 seconds
after the additional CLI missing-authorization regression. The later exact-head
and false-positive-boundary runs also passed, ending at 58/58 in 4.910 seconds.

Python compile attempts: six; all passed. The final two-file compile command
took 0.07 seconds. No Lean/Lake/build/cache command was run, so cache hit,
cache lock wait, and build duration are not applicable.

## Metrics and safety

- Exposed model token usage: `null`.
- Token availability reason: the collaboration/runtime tools expose command
  output and wall time but no per-session model token accounting; no estimate
  was made.
- Logical-session elapsed time: `null`.
- Elapsed availability reason: the runtime exposes per-command wall times but
  not the logical session start timestamp; no estimate was made.
- Subagents spawned by this fixer: 0.
- Topology: one fixer session; read-only findings from the assigned A03/A04
  reports were verified against surrounding code. Two sibling scout messages
  supplied additional compatibility/path cases; the fixer inspected and
  implemented the accepted cases directly.
- Reviewer findings addressed: 4; retries caused by test failures: 1 focused
  implementation iteration; incidents opened: 0.
- Protocol revision: QPBT-026 A05 entry dated 2026-09-01.
- External endpoints contacted: 0.
- GitHub reads/writes: 0.
- Credentials inspected or used: 0.
- Lean, Lake, full-build, and hot-cache commands: 0.
- Canonical `workflow/state/` and `research/metrics/` writes: 0.

## Residual risk

The version-1 gate intentionally cannot externally dispatch an uncommitted
bootstrap target. Credential exclusion is a conservative path classifier, not
a content scanner; an explicitly authorized benign-looking path containing an
embedded secret is outside this classifier's guarantee. Exact user-authorized
scope remains mandatory. Existing committed-harness symlink behavior was not
changed or broadened by A05; pre-existing base-side symlink traversal remains a
separate review concern.
