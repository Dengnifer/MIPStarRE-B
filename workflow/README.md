# Local Execution State

GitHub Issues and pull requests in exactly `Dengnifer/MIPStarRE-B` are canonical
for work planning, dependency status, integration, and review threads. This
directory provides the complementary local authority for agent execution,
stages, protocol evidence, and compatibility projections.

## Authority split

- GitHub Issues: canonical issue numbers, hierarchy, dependencies, acceptance
  gates, `kind:<legacy kind>`, and `status:*` labels.
- GitHub PRs: canonical PR numbers, base/head revisions, checks, exact review
  reports, findings, and `review:*` labels.
- `state/issues.json` and `state/prs.json`: legacy history or derived
  compatibility projections only; neither independently authorizes work.
- `state/sessions.json`: authoritative local planned roles and issued attempts.
- `state/stages.json`: authoritative local stage measurements and outputs.
- `state/protocols.json`: active local protocol revision and evolution history.
- `events.jsonl`: append-only local lifecycle and compatibility events.
- `prompts/`: trusted role contracts passed to fresh Codex sessions.

Raw Codex JSONL, prompts assembled for a specific issue, build logs, cache data,
and result envelopes live under ignored `.workflow-runtime/`. Only the root
coordinator imports compact, inspected evidence into authoritative local files.
Only the root writes GitHub. Before each mutation it runs the repository
adapter's read-only preflight; every writing `gh` command explicitly includes
`--repo Dengnifer/MIPStarRE-B`, and every PR creation also includes explicit
`--base main` until the default branch is fixed. No prompt, log, status, or
comment may expose credentials.

Launches of issued sessions are lease-bound: authority is checked under the
WorkflowStore lock, the session is marked running before child invocation, and
terminal evidence is imported exactly once. Interrupted sessions are explicitly
failed and are never silently relaunched.
The `run` and `review` commands accept `--session-id` to select this governed
path. Calls without it are explicitly ungoverned compatibility operations and
cannot update canonical session state.

## Commands

```bash
python3 scripts/github_workflow.py --config workflow/github.json validate
python3 scripts/github_workflow.py --config workflow/github.json preflight
python3 scripts/workflow.py validate
python3 scripts/workflow.py issue-session --help
python3 scripts/workflow.py dispatch --help
python3 scripts/hot_main_cache.py status
python3 scripts/local_agent.py --help
python3 scripts/bootstrap_manifest.py --help
```

The GitHub adapter's `validate` command is offline. Its `preflight` command is a
live GET-only check and must bind the intended object and transition before a
write; `preflight --repository-only` is not sufficient for an object mutation.
The committed `workflow/github.json` contains only the exact repository/base
identity and the migration-manifest path; it never contains credentials.

Commands such as `ready`, `add`, `update`, and `transition` that target local
issue/PR records are legacy compatibility operations. They do not create or
transition canonical work and are disabled after cutover. They cannot be used
to bypass GitHub or the adapter preflight.

Run validation before dispatch, after any local state/projection edit, before
review, and after integration. The aggregate gate also reconciles local event
lifecycles, incident references, protocol-change evidence, and terminal-session
metrics. State writes are locked and atomically renamed. Do not hand-edit
authoritative local JSON or compatibility projections while another coordinator
command is active.

Terminal artifact publication and lifecycle import are one rollback-safe
transaction. Archive directories are confined beneath `.workflow-runtime`,
published by atomic alias rename, and reused only after strict envelope and log
validation. Git claim/status probes run with isolated configuration and disabled
repository hooks/fsmonitor callbacks.

`dispatch` is the capacity-aware local-session batch entry point. It consumes
only a fresh compatibility projection after the canonical GitHub issue and
dependency state pass adapter preflight; it cannot edit GitHub or make stale
local status authoritative. The legacy `issue-session` command is a
single-session wrapper around the same planner and also requires an explicit
capacity. On success it preserves its historical JSON shape by
returning the issued session record; queued or blocked attempts return the
planner envelope with a status and reason. Dispatch requires an explicit
non-negative `--capacity`; an omitted or unknown limit fails closed. The command
also requires `--github-config workflow/github.json` after cutover and performs
the selected-issue GET-only preflight itself. GitHub-only session evidence uses
a canonical issue number; the planner consumes its live canonical-number
projection without creating a local issue row. The command
counts active `issued`/`running` sessions other than `coordinator` across all
backends (the explicit limit is an aggregate local ceiling), scoped
to `--stage` when requested, and sorts planned session IDs before classifying
them as `dispatchable`, `queued`, or `blocked`. Capacity-only queueing issues the
available prefix atomically and leaves the remainder planned; a batch containing
any blocked candidate is left unchanged. Cross-candidate materialization
conflicts are checked for the admitted prefix; queued rows are revalidated when
they are admitted. Ownership conflicts are checked across the whole selected
set. `backend_scope: all` is one local-service ceiling: counts are summed across
backends and `--capacity N` is never multiplied into per-backend quotas. The
result's `request_atomic` and `blocked_batch_unchanged` fields make the
transaction and rollback semantics explicit. Use `--dry-run` to inspect that
plan. When capacity is unknown, projected dependency and ownership analysis
still runs and its deterministic diagnostics are included in the fail-closed
error; no state or event is written.
Stage `max_concurrency` remains historical observation data and is not an
admission limit.

An issued launch lease also binds the live worktree: the launcher must observe
a clean Git repository at the registered root with the exact issued `HEAD` and
tree (or an unborn repository when the base is null), and repeats that identity
check immediately before spawning the child. Terminal imports must use
the normalized, in-root `result_envelope_path` from the issued row. An
interrupted lease writes a deterministic failed recovery envelope at that path;
the recovery and its subsequent archive transition are retried only by
reusing the recorded evidence.

The planner reserves one orchestrator slot per canonical GitHub issue number: a
second planned or active orchestrator is blocked at admission, including for an
issue still labelled `status:planned`. Terminal attempts remain provenance for
a later retry. Dispatch override objects must use one shape (single record,
keyed map, or ID-bearing list); a single record mixed with keyed entries is
rejected.

## Local Mathlib hot cache

The canonical warm uses the authenticated Mathlib revision
`81a5d257c8e410db227a6665ed08f64fea08e997` (tree
`5ea66b811b8461daae82f14d356fed2a287d7c40`). Provide one local source or the
audited shallow-repository archive; paths must be absolute and free of symlink
components:

```bash
export MATHLIB_SOURCE=/srv/sources/mathlib
# or: export MATHLIB_ARCHIVE=/srv/archives/mathlib-81a5d257-shallow-repo.tar.gz
python3 scripts/hot_main_cache.py warm
```

The source must be clean and authenticate to the pinned commit/tree. The
validator rejects external or special `.git` metadata, executable local Git
configuration, inherited Git configuration, and index flags that hide changes.
Repository Git commands run with isolated system/global config and inert
command-scope overrides. The archive is accepted only at compressed SHA-256
`c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7` and
`51,938,317` bytes. The builder derives a canonical sorted
`LAKE_PKG_URL_MAP` for Mathlib inside the elected staging transaction; source
paths do not enter the cache key or manifest identity. It derives the URL and
revision from the detached root Lake manifest and rejects a pin outside the
authenticated contract. A warm rechecks this input on cache hits as well as
misses.

`lake ... exe cache get` can still contact Reservoir for compiled artifacts.
The local source map directs Lake's Mathlib package lookup to the validated
local `file://` URL, but it does not by itself make the warm offline; provision
the permitted artifact cache or endpoint and retain the failure when Reservoir
returns a nonzero status.
