# QPBT-026 offline isolation fixer A17

- Logical session: `i026-fixer-a17-offline-isolation`
- Role: sole writable fixer for QPBT-026 / LPR-016
- Branch: `issue/qpbt-026-disclosure-a17-fix`
- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-026-disclosure-a17`
- Direct parent: `89862d4b74364d1b2bb488d3ffc8e6820564c9ea`
- Direct-parent tree: `62c3da6b307a6411721469538368a2680e32da01`
- Session measurement start: `2026-09-01T03:56:07.407965933Z`
- Evidence cutoff: `2026-09-01T04:07:36.694132977Z`
- Measured elapsed to cutoff: 689.286167044 seconds
- Requested model: `gpt-5.6-sol`

The containing commit SHA and tree are reported separately because a report
cannot embed the SHA of the commit containing its own bytes without circular
identity. The intended commit inventory is exactly this report plus
`protocols/CHANGELOG.md`, `protocols/review.md`, `scripts/local_agent.py`, and
`tests/test_local_agent.py`.

## Source evidence

The immutable A14 review was read from the canonical repository path and its
SHA-256 verified as
`8a613b59d20b27b9eb709547c7719c8c10e963367c49f9cb14881eeb4b74bb29`.
The A11 implementation report at
`workflow/reviews/qpbt-026-disclosure-preflight-a11.md` was read with SHA-256
`faa33aa7b0d3282afd45113d90b375287c341c1be34dab3761f238839e5c4314`.
No external source, endpoint, credential, or mutable reviewer context was used.

## Finding dispositions

### F-LPR016-006: falsey capability fallback

Fixed. Offline capability evidence is copied directly from the injected mapping;
there is no truthiness fallback and no offline call to
`inspect_codex_review_capability`. Required version, help digest, selector
boolean, and probe-reason fields are validated before repository inspection.
The public entry point performs this validation before a bound session can claim
a lease, and the private constructor repeats it before source, harness, output,
or runner work.

The regression passes `{}` with a mocked real capability probe and mocked
repository, harness, output, and lease functions. It receives the incomplete
record error and observes zero calls to every mock and the injected runner, with
no harness or run directory created.

### F-LPR016-007: inherited Git object and repository selection

Fixed. `_git_environment` no longer copies ambient process state. Every Git
operation receives a fixed environment containing only the system default path,
C locale, disabled system/global configuration and attributes, disabled
prompting, and the local-config override. The deterministic harness commit may
add only fixed author and committer dates; author identity remains command-local.

The fixed environment contains none of:

- `GIT_ALTERNATE_OBJECT_DIRECTORIES`
- `GIT_OBJECT_DIRECTORY`
- `GIT_DIR`
- `GIT_WORK_TREE`
- `GIT_COMMON_DIR`
- `GIT_INDEX_FILE`
- `GIT_NAMESPACE`
- `GIT_REPLACE_REF_BASE`
- `GIT_SHALLOW_FILE`
- `GIT_CEILING_DIRECTORIES`
- `GIT_TEMPLATE_DIR`
- `GIT_DISCOVERY_ACROSS_FILESYSTEM`
- `GIT_QUARANTINE_PATH`

The injected offline runner is handed a copy of the same fixed environment.
The adversarial regression sets every listed selector in the ambient process,
points `GIT_ALTERNATE_OBJECT_DIRECTORIES` at the source fixture's object store,
and also sets count-based and parameter-based Git configuration injection. The
offline review still finishes: the child receives the exact fixed environment,
reports zero local objects and no alternate, and cannot resolve the unmanifested
source head. The ordinary exact committed projection regression also continues
to pass.

Production review behavior is unchanged: version-1 records still fail closed
before packet/context reads, persistence and capability probes, harness/output
creation, lease claim, command construction, or runner invocation. This patch
does not implement external dispatch or claim OS filesystem isolation.

## Validation and attempts

The final code-freeze gates were:

| Gate | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'` | pass, 62/62 in 4.392 seconds against the committed code |
| `PYTHONPYCACHEPREFIX=/tmp/qpbt-026-a17-pycache python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py` | pass |
| `python3 scripts/workflow.py validate --json` | pass, `valid=true`; 27 issues, 15 PRs, 308 issued sessions, 7 stages |
| `git diff --check 89862d4b74364d1b2bb488d3ffc8e6820564c9ea..HEAD` | pass against the committed range |

Test attempts were five. The first targeted invocation used a non-package module
path and failed during discovery with three import errors, so it ran zero tests.
The corrected targeted invocation passed all three selected regressions in 0.391
seconds. The first full-suite run executed 62 tests and failed one existing
bound-review race fixture because it omitted the capability record now required
before lease claim. Supplying the valid injected fixture preserved the intended
race assertion; the second full-suite run passed 62/62 in 4.180 seconds, and a
third full-suite run against the committed code passed 62/62 in 4.392 seconds.
Python compilation took two attempts, workflow validation three, and diff
hygiene four; every attempt passed. Commit construction took two successful
commands: the initial commit and one report-only amendment to freeze these final
metrics. The final path, ancestry, tree, cleanliness, and report digest are
necessarily reported with the containing commit.

No Lean, Lake, project build, or hot-main-cache command was required or run.

## Metrics and safety

- Exposed model token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session model token accounting; no estimate was made.
- Subagents spawned: 0; topology was one writable fixer under the root
  coordinator and one completed immutable A14 review as input evidence.
- Reviewer findings addressed: 2; implementation retry classes: 2; incidents or
  new workflow issues opened: 0.
- External endpoints contacted: 0; network requests: 0.
- Codex CLI launches/probes: 0.
- GitHub reads/writes: 0/0.
- Credentials inspected/used/transmitted: 0/0/0.
- Lean commands: 0; Lake commands: 0; project/full builds: 0/0.
- Hot-cache warm/seed/status operations: 0/0/0.
- Canonical `workflow/state/` writes: 0.
- `research/metrics/` writes: 0.
- Commits before the containing commit: 0.

## Residual risk

The offline runner remains an injected in-process test double and is trusted to
honor the environment argument; this is a deterministic test boundary, not an
OS confinement primitive. Production external review remains intentionally
unavailable until exact-content authorization and enforceable host read
isolation are implemented and independently reviewed.
