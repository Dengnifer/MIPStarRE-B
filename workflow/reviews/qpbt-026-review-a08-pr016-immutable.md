# QPBT-026 / LPR-016 immutable review A08

- Logical session: `i026-reviewer-a08-pr016-immutable`
- Verdict: `request_changes`
- Review start: `2026-09-01T02:55:35Z`
- Review end: `2026-09-01T03:01:38Z`
- Measured elapsed: 363 seconds
- Model family: `GPT-5`
- Exact deployed model identifier: `null`
- Model availability reason: the session identifies only the model family, not an exact deployment identifier
- Token usage: `null`
- Token availability reason: the collaboration/runtime tools expose command output and wall time but no per-session model token accounting; no estimate was made
- Subagents: 0; topology was one fresh read-only reviewer

## Findings

### F-LPR016-002 remains unresolved (blocker): the offline token can be replayed into the production helper

`scripts/local_agent.py:828` enters offline mode without resolving or validating a
target, destination, or authorization and returns the same module-global singleton
token at `scripts/local_agent.py:833` that an authorized external preflight returns
at `scripts/local_agent.py:846`. The post-persistence helper checks only singleton
identity at `scripts/local_agent.py:2887`; the token carries no mode, target,
revision, model, profile, or authorization binding. Its independently supplied
`offline_test_mode` can therefore be false and its `transport_profile` can be
`None`. In that state the helper selects the real `codex` executable at
`scripts/local_agent.py:3012`, and `scripts/local_agent.py:3020` simply omits
transport overrides.

Consequently an internal library caller can mint the token through the offline
branch using an injected runner, then replay it into
`_run_review_after_persistence_probe` with `offline_test_mode=False`, the real
subprocess runner, an injected capability record, a different committed target,
and no profile or authorization. The singleton is also directly reachable as a
module attribute. Normal `run_review` and CLI call paths do not perform this
replay, and there is no offline CLI flag, but the protocol specifically claims the
token prevents internal-helper bypass (`protocols/review.md:84`). It does not.
The existing regression at `tests/test_local_agent.py:1502` checks only a missing
token, not offline-to-production or cross-target replay.

Smallest sufficient fix: make the consumed capability bind the validated mode,
resolved base/head/tree, model, and transport profile, reject any mismatch in the
helper, and ensure an offline capability can only select the offline executable
with the same injected runner/capability constraints. Add a regression that mints
an offline capability and attempts to consume it in production mode.

### F-LPR016-005 (new blocker): the changed-path authorization does not bound transmitted or accessible repository content

`scripts/local_agent.py:812` computes `private_file_paths` solely from
`git diff --no-renames --name-only -z BASE HEAD`, so authorization covers only
changed paths. Actual launch scope is broader in two independently concrete ways.

First, `scripts/local_agent.py:2079` loads complete contents for every unchanged
base authority file found in `REVIEW_AUTHORITY_PATHS`. Those contents are copied
into the prompt at `scripts/local_agent.py:1193` and serialized at
`scripts/local_agent.py:1229`; the prompt is then passed to Codex at
`scripts/local_agent.py:3095`. Thus unchanged private repository files are
definitely transmitted even though they are absent from `private_file_paths`.
The successful production-shaped test demonstrates the mismatch: its
authorization lists only `code.txt` at `tests/test_local_agent.py:858`, while the
fixture base also contains `AGENTS.md`, `workflow/prompts/reviewer.md`, and
`protocols/review.md` at `tests/test_local_agent.py:87`.

Second, `scripts/local_agent.py:2195` clones the complete private Git repository
and reachable object database into the harness. The committed harness checks out
the base and creates a synthetic commit from the complete head tree at
`scripts/local_agent.py:2476` and `scripts/local_agent.py:2492`. The outbound
reviewer is expressly told to use `git show` for head-side surrounding files at
`scripts/local_agent.py:1238`. It can therefore read and transmit unchanged base
files and any blob reachable through the cloned repository, not merely the
authorized changed paths.

This violates QPBT-026's requirement that authorization bind the exact private
file paths whose contents may be transmitted, and contradicts the exact-scope
claims at `protocols/review.md:38`, `protocols/review.md:51`, and
`protocols/CHANGELOG.md:22`. Standing transport trust cannot supply the missing
content permission.

Smallest sufficient fix: bind authorization to every repository file whose bytes
are embedded in the prompt or made readable in the evidence harness, including
trusted authority files. Either authorize and screen a complete immutable
accessible-file manifest, or construct a minimal evidence repository/object
database containing only authorized material and prevent access to the source or
unlisted objects. Add a regression with an unchanged sentinel file and prove its
path/content is neither in the outbound prompt nor readable from the launched
harness unless it appears in the authorization.

## Prior finding dispositions

- `F-LPR016-001`: resolved on its stated authorization-echo surface.
  Validation returns no mapping, callers pass only the internal token, and the
  authorization object is no longer added to the target, prompt, envelope,
  persisted result, or event log. Focused tests inspect all four artifacts.
  Independently required transport/model fields still appear through the
  transport profile and command; that is not an echo of the authorization
  mapping. F-LPR016-005 is a separate unauthorized-content problem.
- `F-LPR016-002`: unresolved. Production entry points reject a missing profile or
  authorization before persistence/evidence/lease side effects; normal offline
  mode has no CLI switch, requires injected runner and capability data, rejects
  transport/authorization data, and substitutes a non-`codex` executable.
  However, its unbound singleton capability can be replayed into the production
  helper as described above.
- `F-LPR016-003`: resolved on bound, unbound, and CLI paths. Commit target,
  declared head, and first-parent base resolution share
  `_resolve_committed_review_target`; mismatches fail during preflight before a
  bound lease claim. Capture repeats the same resolver. Direct-helper replay is
  instead covered by unresolved F-LPR016-002.
- `F-LPR016-004`: resolved for the changed-path classifier itself. Paths are
  canonical POSIX repository-relative values, screening case-folds the full path,
  and `--no-renames` preserves rename sources. Required denials include
  `keys/id_rsa`, `.ssh/authorized_keys`, `private/private_key.pem`,
  `certs/client.pem`, `.aws/config`, and `credentials/config`; `.crt`/`.cer` and
  ordinary `keys`, `auth`, `tokenizer`, `passwordless`, and `secretary` names
  remain allowed. End-to-end credential exclusion is nevertheless incomplete
  because F-LPR016-005 leaves unchanged/unlisted repository material readable.

## Protocol truth

The standing-trust text for official OpenAI transport and
`https://api.finite-dimensional.space` is transport trust only. The normal
production preflight does not exempt either endpoint from exact per-review
authorization, and arbitrary HTTPS profiles likewise require a matching record.
Version-1 production entry points fail closed for uncommitted targets. These
claims match code.

The claims that an opaque token prevents internal callers from bypassing
preflight and that the changed-path list is the exact transmitted evidence scope
do not match code, for F-LPR016-002 and F-LPR016-005 respectively. Accordingly,
the A05 fixer report's conclusion that every external review has an exact
immutable content manifest is not established.

## Immutable identity and scope

- Base: `ea584e9e894391773e09ddad2ce4d082497c7913`
- Head: `94c0e630b5f2697f678c400da082f108bde89471`
- Head tree: `4188a6d959cb145b945c9618789f96cd98165d02`
- Direct fix parent: `5d6164e949a32c906557a136c7e49558ea13d7ae`
- Base is an ancestor of head: yes
- Commit count in `BASE..HEAD`: 2
- Worktree: detached and clean at start, after validation, and at final identity check
- Exact `--no-renames` changed-path manifest: six paths and no others:
  `protocols/CHANGELOG.md`, `protocols/review.md`, `scripts/local_agent.py`,
  `tests/test_local_agent.py`,
  `workflow/reviews/qpbt-026-disclosure-preflight-a01.md`, and
  `workflow/reviews/qpbt-026-disclosure-preflight-a05.md`.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'`:
  passed 58/58 in 4.686 seconds (4.772 seconds command wall time).
- `PYTHONPYCACHEPREFIX=/tmp/qpbt-026-a08-pycache python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py`:
  passed (0.112 seconds command wall time).
- `python3 scripts/workflow.py validate --json`: passed with `valid=true`;
  27 issues, 15 pull requests, 308 issued sessions, and 7 stages
  (0.014 seconds command wall time).
- `git diff --check ea584e9e894391773e09ddad2ce4d082497c7913..94c0e630b5f2697f678c400da082f108bde89471`:
  passed.
- Read-only identity commands verified exact HEAD/tree, ancestry, two-commit
  count, direct parent, six-path `--no-renames` manifest, and clean status.

No Lean, Lake, project build, hot-cache warm/seed, network, Codex CLI, external
endpoint, GitHub, or credential command was run. Counts: external endpoints 0;
network requests 0; GitHub reads/writes 0; credentials inspected/used 0; Codex
launches/probes 0; Lean/Lake/project builds 0; cache operations 0; repository
edits 0. Python test attempts: 1; Python compile attempts: 1; workflow validation
attempts: 1; diff-hygiene attempts: 1.

## Residual risk

The path classifier is intentionally a conservative name-based screen, not a
content scanner; a benign-looking authorized file can still contain a secret.
Pre-existing base-side symlink traversal was not changed by this diff and was not
promoted to a separate finding. The concrete scope defect here is broader and
does not depend on symlinks: ordinary unchanged authority files are embedded in
the prompt, and ordinary unlisted Git objects remain readable in the full clone.
