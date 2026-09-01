# QPBT-026 / LPR-016 immutable review A14

## Findings

### F-LPR016-006 (blocker): an empty injected capability record invokes the real Codex probe in offline mode

`scripts/local_agent.py:2928` and `scripts/local_agent.py:3046` reject only a
`None` capability. An empty mapping therefore enters the offline implementation,
where `scripts/local_agent.py:3097` evaluates
`codex_capability or inspect_codex_review_capability()`. The fallback invokes the
real `codex` executable for version, help, and parser probes at
`scripts/local_agent.py:2148`, `scripts/local_agent.py:2154`, and
`scripts/local_agent.py:2180`. This occurs even for an offline dry run and before
the supplied record is rejected as incomplete.

This contradicts `protocols/review.md:78`, which requires an injected capability
record, and the offline-only/non-transmitting claims at
`protocols/review.md:79-80` and `protocols/review.md:102-104`. It also leaves a
direct offline entry path to Codex after the replayable production helper was
removed. I reproduced the control flow without launching Codex by mocking
`inspect_codex_review_capability`, passing `{}` as the injected capability, and
running a committed offline dry run: the probe mock was called exactly once and
the call otherwise returned a dry-run envelope.

Smallest sufficient fix: never use truthiness fallback after offline injection.
Copy the supplied mapping directly, then validate its exact required fields; an
empty or otherwise incomplete mapping must fail before any probe, harness,
output, or runner action. Add a regression that passes `{}`, mocks the real
probe, and asserts the probe and runner are both untouched.

### F-LPR016-007 (high): inherited Git object configuration defeats the projected-only harness

`scripts/local_agent.py:1831-1854` copies the ambient environment and removes
only selected config-injection variables. It retains repository/object selectors
such as `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_OBJECT_DIRECTORY`, `GIT_DIR`,
`GIT_WORK_TREE`, and `GIT_TEMPLATE_DIR`. The allegedly fresh repository is
initialized through that environment at `scripts/local_agent.py:2595-2596`.
Verification then checks only an on-disk `.git/objects/info/alternates` file and
files physically under the local object directory at
`scripts/local_agent.py:2415-2418`; it does not reject inherited object stores.
The injected runner is also called without a scrubbed environment at
`scripts/local_agent.py:1771`.

A safe local reproduction set `GIT_ALTERNATE_OBJECT_DIRECTORIES` to the source
fixture's `.git/objects` and used only the injected fake runner. The offline run
finished, the harness had no alternates file and reported zero local objects,
but `git cat-file -e <source-head>` in the harness succeeded; `git count-objects
-v` reported the source object directory as an alternate. No Codex process,
network, endpoint, credential, or GitHub operation was used. Consequently the
source object database is readable despite being absent from the evidence
manifest. This refutes the no-source-objects and exact projected-content claims
at `protocols/review.md:81-90` and `protocols/CHANGELOG.md:13-20`.

Smallest sufficient fix: use an explicit minimal environment for every harness
Git command and for the child/test runner, or fail closed before the runner when
any repository-, object-, replacement-, template-, or alternate-selection
variable is inherited. Add an adversarial regression with a source-object
alternate and require rejection before the runner or prove that the source head
remains unresolvable and no alternate appears in `count-objects -v`.

## Verdict and prior finding dispositions

Verdict: `request_changes`. F-LPR016-006 is a blocker and F-LPR016-007 is a high
protocol/scope defect, so this immutable head cannot be approved.

- F-LPR016-001 remains resolved. Production never constructs a target, prompt,
  result envelope, or event log, and offline mode rejects any authorization
  mapping; the raw or normalized record is not copied into those surfaces.
- F-LPR016-002 is resolved on its stated replay surface. The module-global token
  and independently callable post-persistence production helper are absent, and
  every production `run_review` path fails before runner construction. The new
  falsey-capability fallback is recorded separately as F-LPR016-006 because it
  reaches a Codex capability probe without replaying production authority.
- F-LPR016-003 remains resolved. Base/commit identity, declared head, first
  parent, ancestry, tree, and clean-worktree checks share the committed resolver,
  and production failures occur before any bound lease claim.
- F-LPR016-004 remains resolved for the name classifier. Paths are canonical and
  full-path screened, and `--no-renames` retains both rename endpoints. The
  inherited object-store path in F-LPR016-007 bypasses the projected harness
  inventory rather than the classifier itself.
- F-LPR016-005 is resolved for production disclosure: version 1 always fails
  before task/context loading, persistence/capability probes, harness/output
  creation, lease claim, transport command construction, or runner invocation.
  The broader A11 claim that the offline success proves an exact evidence-only
  repository is not confirmed because F-LPR016-007 leaves unmanifested source
  objects readable.

## Protocol and implementation checks

Production bound, unbound, dry-run, and CLI review paths all enter
`_preflight_external_disclosure` and fail closed after structural version-1
validation. CLI packet/task/context loading is downstream of the unconditional
failure. No production path reached persistence probing, capability probing,
evidence/output creation, lease claim, Codex command construction, or a runner
during review. The endpoint/model standing-trust text remains transport trust
only and does not claim content permission. The protocol truthfully records that
host isolation is not enforced and that production exact-content authorization
remains future work.

Committed offline construction no longer clones the source, checks out a source
tree, configures a source remote, or materializes live changed symlinks. Its
ordinary-environment manifest records base/head object metadata and bytes plus
the derived patch, and its packet projection hashes the request, final prompt,
authority, manifest, and evidence. These properties do not cure the inherited
probe and Git-object paths above.

Mathematical and paper-source fidelity were not applicable: the seven-path range
contains workflow protocol, Python launcher/tests, and evidence reports only.

## Immutable identity and validation

- Review start: `2026-09-01T03:42:26.722741524Z`.
- Review freeze: `2026-09-01T03:51:37.257657Z`.
- Measured elapsed to freeze: `550.534916` seconds (start truncated to
  microseconds only for arithmetic).
- Base: `ea584e9e894391773e09ddad2ce4d082497c7913`.
- Head: `89862d4b74364d1b2bb488d3ffc8e6820564c9ea`.
- Head tree: `62c3da6b307a6411721469538368a2680e32da01`.
- Direct parent: `94c0e630b5f2697f678c400da082f108bde89471`.
- The exact base is the merge base; `BASE..HEAD` contains three commits.
- The worktree was detached and clean at start, after validation, and at the
  final identity check.
- The exact no-renames range contains seven paths and no others:
  `protocols/CHANGELOG.md`, `protocols/review.md`, `scripts/local_agent.py`,
  `tests/test_local_agent.py`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a01.md`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a05.md`, and
  `workflow/reviews/qpbt-026-disclosure-preflight-a11.md`.

Validation results:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p
  'test_local_agent.py'`: passed 60/60 in 4.932 seconds (5.10 seconds command
  wall time).
- `PYTHONPYCACHEPREFIX=/tmp/qpbt-026-a14-pycache python3 -m compileall -q
  scripts/local_agent.py tests/test_local_agent.py`: passed (0.21 seconds
  command wall time).
- `python3 scripts/workflow.py validate --json`: passed with `valid=true`, 27
  issues, 15 pull requests, 308 issued sessions, and 7 stages (0.11 seconds
  command wall time).
- Exact range `git diff --check`, head/tree/parent, ancestry, commit-count,
  no-renames name-status, detached-state, and clean-state checks passed.
- Prescribed unit-test attempts: 1. Python compilation attempts: 1. Workflow
  validation attempts: 1. Diff-hygiene attempts: 2. Additional safe adversarial
  reproductions: 2 (empty capability with mocked probe; inherited Git alternate
  with fake runner).

## Metrics and prohibited-action counters

- Requested reviewer model: `gpt-5.6-sol`.
- Token usage: `null`.
- Token availability reason: the collaboration/runtime tools expose no
  per-session token accounting; no estimate was made.
- Subagents spawned: 0; topology was one fresh read-only reviewer.
- Candidate repository edits/writes: 0; commits: 0; state/metrics writes: 0.
- Codex CLI launches/probes: 0; external endpoint contacts: 0; network requests:
  0; GitHub reads/writes: 0/0; credentials inspected/used: 0/0.
- Lean commands: 0; Lake commands: 0; project/full builds: 0; hot-cache
  warm/seed/status actions: 0/0/0.

## Residual risk

Production external review remains intentionally unavailable, so a future
content-authorization schema and enforced OS read boundary still require their
own implementation and independent review. After F-LPR016-006 and
F-LPR016-007 are fixed, the exact head must receive a fresh immutable review;
the passing unit suite cannot substitute for those adversarial cases.
