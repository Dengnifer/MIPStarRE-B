# Local Orchestration

## Issue lifecycle

Issue IDs are stable (`QPBT-NNN`). Statuses are `planned`, `ready`,
`in_progress`, `review`, `blocked`, `done`, and `cancelled`.

An issue may enter `ready` only when all dependency issues are `done`. It may
enter `in_progress` only after an orchestrator session is issued. `blocked`
requires a concrete blocker and unblock condition. `done` requires every
acceptance gate and linked local PR to be complete. A tracker closes leaf-up
only if it has at least one child and every child is `done`; cancellation does
not count as completion.

Issue creation has a high bar. One genuine follow-up remains flat. Two or more
coherent follow-ups may receive a tracking parent. A new issue must name the
mathematical or operational result, not merely "cleanup", "phase", or
"follow-up". Formalization issues include:

- paper path, section, line/label, and a precise paraphrase;
- blueprint path/label and current Lean-link status;
- intended Lean declaration and file;
- dependencies and known blockers;
- statement-integrity expectations; and
- exact validation and acceptance gates.

Run `python3 scripts/workflow.py ready` to compute dispatchable work rather than
inferring readiness from list order.

For session admission, use `python3 scripts/workflow.py dispatch` with an
explicit capacity. The legacy `issue-session` command is a single-session
wrapper around this planner and also requires that capacity; it cannot bypass
the admission checks. The dispatcher holds the workflow lock while it checks issue
dependencies, stage membership, active non-coordinator sessions, and writable
path ownership. The explicit capacity is an aggregate ceiling across all
backends in the selected local scope. Candidate IDs are sorted; capacity
exhaustion is reported as a queued result and dependency or ownership failures
as blocked results. A capacity-only wave atomically issues the sorted available
prefix and leaves the remainder planned; any blocked selected member leaves the
requested batch untouched. `--dry-run` performs the same checks without writing
state. Cross-candidate materialization conflicts are checked for the admitted
prefix and queued rows are revalidated on a later attempt; ownership conflicts
are checked across the whole selected set. The result's `request_atomic` and
`blocked_batch_unchanged` fields identify the transaction boundary explicitly.
`backend_scope: all` is a single local-service ceiling: active sessions are
summed across every backend, and `--capacity N` is never interpreted as N slots
per backend or multiplied by the number of backends.
An unknown capacity is rejected only after dependency and ownership diagnostics
are collected; the deterministic diagnostics are carried in the fail-closed
error and no ledger or event is written.
The stage
ledger's `max_concurrency` field is an observed metric, not a substitute for the
explicit dispatch capacity.
Dispatch capacity does not relax the hot-main cache singleton: Lean/Lake work
still waits for the one elected builder for a cache key. The currently observed
four collaboration slots are an environment fact, not a universal default;
pass the measured limit for the active backend and fail closed when it is not
known.

## One orchestrator per issue

The coordinator dispatches exactly one orchestrator for each implementation
issue. Admission rejects a second planned or active orchestrator for the same
issue, including while the issue is still `planned`; terminal attempts remain
retry provenance. The initial prompt contains the full issue record, protocol revision,
base SHA, worktree, owned paths, source anchors, acceptance gates, cache key,
prior attempts, and expected result-envelope path.

The orchestrator may delegate:

- `scout`: read-only Mathlib or source search with exact search questions;
- `blueprint`: source-to-declaration mapping without Lean implementation;
- `prover`: one named proof family or file with a compile command;
- `reviewer`: fresh and read-only after validation;
- `simplifier`: behavior-preserving reduction after proofs pass; and
- `auditor`: fresh end-of-session comparison of goal, diff, checks, and debt.

Fan out only when tasks are independent and all boundaries are known. If the
next task depends on a previous mathematical result, dispatch sequentially.
Every child prompt is self-contained. Child reports are evidence, not accepted
changes; the orchestrator checks the result and diff.

### Issued session launch lease

Coordinator launchers must call the local session lease API while holding the
WorkflowStore lock. The API compares session id, immutable base revision,
registered worktree, ownership claims, and read-only mode, then verifies that
the actual clean Git repository root, `HEAD`, and tree match that base before
recording `issued -> running`. Git-unavailable, dirty, moved, or mismatched
worktrees fail closed; a null base is valid only for an unborn repository. A
terminal envelope is imported once using its canonical digest and the issued
`result_envelope_path`; traversal, symlink, and external paths are rejected.
Identical retries are harmless and a conflicting retry is rejected. Parent
interruption is recovered by recording a failed session with an explicit,
archiveable recovery envelope at that same result path. Recovery never invokes
the child again, and state/event/artifact writes roll back on any exception or
interrupt.
Governed `run` and `review` calls pass `--session-id` plus the complete packet
authority; both modes use the lease. Omitting `--session-id` is retained only
for explicitly ungoverned local experiments and does not mutate workflow state.
Immediately before either child process is spawned, the launcher repeats the
canonical worktree-path, clean-status, `HEAD`, and tree checks from the claim;
replacement or drift in that interval fails the lease and triggers recovery.
Archive retries return the existing matching envelope without invoking Codex;
conflicting archive identities fail closed. Reuse additionally compares each
recorded stdout/stderr byte count and SHA-256 digest with the current log bytes.
Terminal result publication is part
of the import transaction, so an event-append failure rolls back lifecycle
state and the result artifact before interruption recovery writes its envelope.
Archive aliases are published by atomic directory rename under the runtime root;
runtime and alias paths are no-follow, complete envelopes are validated before
reuse, and per-alias locking handles concurrent retries without clobbering
evidence. All Git identity/status probes clear inherited configuration and
override repository-local hooks/fsmonitor settings so claims cannot execute
untrusted callbacks.

## Session lifecycle

Use `i<issue-number>-<role>-a<two-digit-attempt>-<slug>`, for example
`i005-prover-a02-pauli-linearity`. The stable name, external Codex thread ID,
and parent session ID are separate fields.

1. **Plan:** add an expected role to `sessions.json:planned`. No agent exists.
2. **Issue:** create the immutable issued-attempt record and launch the agent.
3. **Run:** write raw JSONL and outputs to `.workflow-runtime/runs/<name>/`.
4. **Inspect:** verify owned paths, diff, commands, result, metrics, and handoff.
5. **Finish:** import a compact record into canonical state/research metrics.
6. **Archive:** run `codex archive <external-id>` when the backend provides a
   persistent Codex session, then mark the local record archived. Collaboration
   backends without a CLI session are retired locally with the limitation noted.

Never estimate token use. Import input/output/cache/reasoning token fields when
the Codex JSON stream exposes them; otherwise store `null` plus the reason.
The exact registered validation command must be executed; a paraphrase or a
nearby test command is not completion evidence. Issued authority fields are
immutable, and lifecycle events must reconcile with the issued record.

## Local PR lifecycle

Local PR IDs are stable (`LPR-NNN`). One record names issue IDs, base branch and
SHA, head branch and SHA, changed paths, motivation, precise description,
validation, review rounds, findings, dispositions, and final integration SHA.

Statuses are `draft`, `ready`, `changes_requested`, `approved`, `merged`, and
`closed`.

1. Create a branch/worktree from verified main and open a draft record.
2. Implement only the linked issue scope.
3. Record scoped checks; warm/seed the cache through the cache protocol.
4. Freeze the head SHA and run the full local gate.
5. If the gate passes, dispatch fresh code and blueprint reviewers.
6. On findings, record dispositions, change the head, invalidate approval, and
   run a new review round.
7. Integrate only an approved, unchanged head. Run the main build after merge.
8. Reconcile issue status and genuine follow-ups, then archive sessions.

PR titles use `type(scope): description`. The record body contains Motivation,
Description, Testing, and `Addresses QPBT-NNN` or `Closes QPBT-NNN`.

## Local Mathlib hot-cache input

The canonical hot-main recipe is pinned to Mathlib commit
`81a5d257c8e410db227a6665ed08f64fea08e997` (tree
`5ea66b811b8461daae82f14d356fed2a287d7c40`). A warm must receive exactly one
of these absolute paths:

```bash
MATHLIB_SOURCE=/absolute/path/to/mathlib
MATHLIB_ARCHIVE=/absolute/path/to/mathlib-81a5d257-shallow-repo.tar.gz
```

`MATHLIB_SOURCE` must name a standalone, clean, non-bare Git worktree. The
cache checks `HEAD`, the root tree, local `git fsck --full`, the shallow
boundary when present, absence of alternates and submodules, and regular
one-link object packs. Its `.git` tree must contain no symlink, special entry,
external common directory, replacement reference, or index visibility flag.
Before any Git command against the supplied Mathlib repository, the cache
parses local config without includes and permits only a narrow set of inert core,
origin, branch, and user
identity settings. Repository Git commands also discard inherited `GIT_*` values,
disable system/global config and pagers, and override executable fsmonitor,
hook, credential-helper, and external-protocol settings. `MATHLIB_ARCHIVE` is
authenticated before extraction by the exact compressed size/digest
(`51,938,317` bytes,
`c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`) and
decompressed tar size/digest (`147,712,000` bytes,
`ad9a60b01736070112fbc1008ea98c67e68fa045c5b69e66873e0b9444ddd3ba`). Its
Git pack is `27,574,578` bytes with SHA-256
`4659f2a0cabfec474474f5e83ea3d495e711b735418742dd3d642328adcada02`.

The elected builder reads the detached project's root `lake-manifest.json` to
derive Mathlib's URL and revision, then checks both against this authenticated
contract (the known tree binds the revision to the exact source identity).
The manifest is never rewritten to point at the local path.

The elected builder performs this authentication in its staging directory,
then serializes `LAKE_PKG_URL_MAP` as a sorted JSON object with the `mathlib`
entry set to the validated `file://` URL. Existing entries for other packages
are preserved; a conflicting `mathlib` entry fails closed. The project
manifest's HTTPS URL and revision are never rewritten, and the source path and
archive location are excluded from the cache identity. The source is checked
again immediately before publication, including its object-pack evidence, and
an archive extraction is removed before `.lake` is atomically published. A warm
validates the local input even
when it would otherwise be a cache hit, so a missing, dirty, or mismatched
source cannot be hidden by `READY`.

This URL map only controls where Lake obtains the Mathlib Git package. The
canonical dependency command, `lake --packages=.lake/package-overrides.json
exe cache get`, may still request compiled artifacts from Reservoir. A local
Mathlib source therefore does not promise an offline warm: use a permitted
Reservoir/cache endpoint or a separately provisioned artifact cache, and treat
that command's nonzero result as a build failure with no `READY` publication.
