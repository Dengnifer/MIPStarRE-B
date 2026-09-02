# Orchestration

## Canonical GitHub issue lifecycle

GitHub issue numbers in `Dengnifer/MIPStarRE-B` are the canonical issue IDs.
Migrated issue bodies retain their stable `QPBT-NNN` marker and carry
`migration:local-v1`, but that marker is compatibility provenance rather than
an identifier for new work. Only manifest-bound migration may add that marker
or label; post-cutover issue creation uses only the GitHub number.

Every open issue has exactly one status label: `status:planned`, `status:ready`,
`status:in-progress`, `status:review`, or `status:blocked`, plus its
`kind:<legacy kind>` label. An issue may enter `status:ready` only when every
separately listed dependency issue is closed as completed. It may enter
`status:in-progress` only after an orchestrator session is issued.
`status:blocked` requires a concrete blocker and unblock condition.

Completion requires every acceptance gate and linked GitHub PR to be complete.
The root coordinator then removes the active status label and closes the issue
with the completed reason. Cancellation closes with the not-planned reason and
does not count as completion. A tracker closes leaf-up only if it has at least
one child and every child was closed as completed. Parent/sub-issue
relationships describe grouping; explicit dependency references describe
ordering. Never infer one from the other.

GitHub's native parent/sub-issue and blocked-by relationships are the canonical
machine-readable graph whenever both objects exist. Migrated prose links are
human-readable provenance, not a second graph. When a completed pre-cutover
parent or dependency was intentionally retained only in the frozen archive,
the issue body names that archive reference and no replacement GitHub object is
invented.

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

Only the root coordinator creates, edits, labels, comments on, reopens, or
closes issues. Before each mutation, it runs the repository adapter's read-only
preflight against the canonical GitHub object and expected transition. The
adapter commands are:

```bash
python3 scripts/github_workflow.py --config workflow/github.json validate
python3 scripts/github_workflow.py --config workflow/github.json preflight
```

`validate` is offline; `preflight` is a live GET-only check. The committed
`workflow/github.json` binds the exact repository identity, explicit
base ref, and immutable migration manifest; it contains no credential. The optional
`preflight --repository-only` check is insufficient for an object mutation.
Every writing `gh` command explicitly includes
`--repo Dengnifer/MIPStarRE-B`. Issue bodies and comments must not contain
credentials or unredacted runtime transcripts.

`workflow/state/issues.json` is retained only as legacy history or a derived
compatibility projection. Before dispatch, the root preflights the canonical
GitHub issue, its exact status label, its parent and dependency references, and
dependency completion. A stale or disagreeing projection fails closed and must
be refreshed; `workflow.py ready` and hand edits to local issue JSON do not
authorize work.

Post-cutover session evidence carries the positive canonical
`github_issue_number` and optional `github_pull_request_number`. Migrated work
may also retain its legacy `issue_id` for compatibility. Work created only on
GitHub uses `issue_id: null` and an explicit known local `stage_id`; no shadow
issue row is created. Dispatch plans these rows from a live, in-memory
canonical-number projection and never persists that projection as issue state.
Repository visibility is not workflow authority: the repository may be public,
but exact repository IDs, the explicit `main` base, and scoped root-only writes
remain mandatory.

The root creates post-cutover planned rows only through
`python3 scripts/workflow.py add planned-session --json ...`. That guarded
transaction holds the workflow lock, loads the exact adjacent config and
immutable cutover manifest, materializes the canonical number for migrated
work, rejects GitHub-only shadows of migrated issues or PRs, binds every
PR-bound session to exact base/head refs and SHAs, rejects records that cannot
materialize as issued sessions and duplicate orchestrators, validates the
complete state, and rolls back exact session/event bytes on any publication
failure.
Planning does not perform a live status check and grants no launch authority;
the dispatch gate performs that check immediately before admission. The
cutover manifest is irreversible: a missing config fails closed, and canonical
state may be addressed only through its real, non-aliased `workflow/state`
path.

Each mutating dispatch performs its final live GitHub issue and selected-PR
reads while holding the same exclusive lock used for local publication. The
resulting projection binds issue status, dependencies, kind, and execution
category, plus each selected PR's open state and exact base/head identity.
Every non-orchestrator
formalization delegate, including read-only scouts and reviewers, is admitted
only after exactly one active writable orchestrator is bound to the same
canonical issue; the orchestrator itself must be dispatched first.

For `codex-collaboration` session admission, use the following spawn-first,
confirm-at-dispatch sequence. The workflow CLI has no collaboration-tool access
and must never pretend that it launched or independently verified an external
thread.

1. After the GitHub adapter preflight succeeds, run
   `python3 scripts/workflow.py dispatch --github-config workflow/github.json
   --dry-run --capacity N` with an exact stage and `--session-id`. For
   collaboration work, preflight exactly one
   session at a time. The result is a deterministic local-session eligibility,
   ownership, and slot check; it writes neither session state nor events and
   cannot change or supersede the GitHub issue.
2. Ask the collaboration backend to create that one thread with a bootstrap-only
   prompt. The bootstrap may acknowledge and become idle, but it must not read
   project files, run tools, or receive the task packet yet. If backend creation
   is rejected, do not run the confirmation command. The planned row and exact
   authoritative local session/event bytes consequently remain unchanged;
   retry the same preflight after a live slot is released.
3. Copy the immutable thread identity returned by that successful backend call
   exactly into `dispatch --confirm-launched SESSION_ID=EXTERNAL_ID`, repeating
   the same GitHub config, capacity, stage, ID, and materialization authority. Collaboration
   callers of the legacy single-session wrapper use
   `--launched-external-id EXTERNAL_ID`. A generic `external_id` override is not
   launch confirmation. The coordinator attests
   that the value came from the just-completed backend call; the CLI validates
   shape, uniqueness, admission, and immutability but cannot prove backend
   existence. Never invent an ID.
4. The confirmation transaction rechecks the derived dependency snapshot,
   stage membership, active non-coordinator sessions, writable ownership, and
   the sorted capacity prefix under the workflow lock. It atomically moves the
   planned row to `issued` and appends identity-bound events. If capacity or
   authority drifted, it writes nothing; immediately interrupt and retire the
   still-bootstrap-only external thread, then retry from step 1.
5. Only after local launch confirmation may the coordinator deliver the full
   task packet and move the session through the launch lease to `running`.

Every collaboration session newly issued through the dispatcher requires a
confirmed, non-empty immutable external thread identity. Active collaboration
rows enforce that invariant at schema validation too. Confirm one collaboration
launch before attempting the next, so the ledger catches up with live occupancy
between backend calls.
Nested launches follow the same boundary: the root coordinator preflights the
planned child, the parent creates only its bootstrap thread and returns the
external ID, the root confirms it, and only then does the parent send the child
task. Every active parent and child other than the root coordinator consumes
one aggregate slot; nesting does not create free capacity.

Governed `codex-cli` launch retains its distinct issue-first lease. Capacity,
dependency, stage, and ownership checks first issue the CLI row with
`external_id: null` and no launch confirmation. The governed launcher then
claims that exact authority, revalidates its worktree, runs Codex, and imports
the real external ID returned in the terminal envelope. The import sets the ID
once and rejects a conflict. Never pass an invented prelaunch ID merely to make
a CLI row dispatchable.

The dispatcher holds the workflow lock for each confirmation transaction. The
explicit capacity is an aggregate ceiling across all backends in the selected
local scope. Candidate IDs are sorted; capacity exhaustion is reported as a
queued result and dependency or ownership failures as blocked results. A
capacity-only wave can atomically confirm the sorted available prefix and leave
the remainder planned, but collaboration callers use the single-ID sequence
above. Any blocked selected member leaves the requested batch untouched.
Cross-candidate materialization conflicts are checked for the admitted prefix,
queued rows are revalidated on a later attempt, and ownership conflicts are
checked across the whole selected set. The result's `request_atomic` and
`blocked_batch_unchanged` fields identify the transaction boundary explicitly.
Any `BaseException` during sessions publication, an issuance or summary event,
or the post-publication audit restores the exact pre-dispatch sessions/event
bytes and is re-raised. A retry therefore observes the same deterministic plan.
`backend_scope: all` is one local-service ceiling: active sessions are summed
across every backend, never multiplied by backend count. An unknown capacity is
rejected after deterministic dependency and ownership diagnostics, without a
ledger or event write. The stage ledger's `max_concurrency` is an observed
metric, not admission authority. Backend rejection is the authoritative live
capacity signal; a caller-supplied ceiling cannot guarantee backend admission.

Dispatch capacity does not relax the hot-main cache singleton: Lean/Lake work
still waits for the one elected builder for a cache key.

## One orchestrator per issue

The coordinator dispatches exactly one orchestrator for each canonical GitHub
implementation issue. Admission rejects a second planned or active orchestrator
for the same GitHub issue number, including while the issue is still
`status:planned`; terminal attempts remain retry provenance. The initial prompt
contains the repository name, GitHub issue number and frozen body/label
snapshot, protocol revision, base SHA, worktree, owned paths, source anchors,
acceptance gates, cache key, prior attempts, and expected result-envelope path.

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

1. **Plan:** add an expected role to `sessions.json:planned`. After GitHub
   cutover, use only the guarded `workflow.py add planned-session` command; do
   not hand-edit the ledger. No agent exists and no work is authorized.
2. **Issue:** create the immutable issued-attempt record and launch the agent.
3. **Run:** write raw JSONL and outputs to `.workflow-runtime/runs/<name>/`.
4. **Inspect:** verify owned paths, diff, commands, result, metrics, and handoff.
5. **Finish:** import a compact record into authoritative local session state
   and research metrics.
6. **Archive:** run `codex archive <external-id>` when the backend provides a
   persistent Codex session, then mark the local record archived. Collaboration
   backends without a CLI session are retired locally with the limitation noted.

Never estimate token use. Import input/output/cache/reasoning token fields when
the Codex JSON stream exposes them; otherwise store `null` plus the reason.
The exact registered validation command must be executed; a paraphrase or a
nearby test command is not completion evidence. Issued authority fields are
immutable, and lifecycle events must reconcile with the issued record.

## Canonical GitHub PR lifecycle

GitHub PR numbers in `Dengnifer/MIPStarRE-B` are canonical. A migrated PR body
retains its stable `LPR-NNN` marker and carries `migration:local-v1`; new PRs use
only their GitHub number and never receive migration metadata. Native
draft/open/closed/merged state is canonical, and every open PR has exactly one
of `review:required`, `review:approved`, or `review:changes-requested`.
A review label records transported workflow state; it is never sufficient
approval evidence without the exact identity-bearing report comment bound by
the integration preflight.

Only the root coordinator pushes to GitHub or creates, edits, labels, comments
on, closes, reopens, or merges a PR. It runs the repository adapter's
read-only preflight before every mutation. Every writing `gh` command includes
`--repo Dengnifer/MIPStarRE-B`. Until the default branch is fixed, every PR
creation also includes explicit `--base main`; an ambient default is never
accepted, and adapter preflight rejects a PR whose base is not `main`.
Before every push, the root verifies that its explicit destination is exactly
`Dengnifer/MIPStarRE-B`; `LionSR/MIPStarRE`, umbrella repositories, and every
other repository are read-only and out of scope. Credentials and raw private
runtime logs never enter a commit, PR body, comment, or command output.

1. Create a branch and issue worktree from a verified `main` SHA. The root opens
   the draft GitHub PR against explicit base `main` and applies
   `review:required` after a coherent checkpoint is committed and pushed.
2. Implement only the linked canonical issue scope. The PR body records the
   exact base/head SHAs, changed paths, motivation, description, validation, and
   `Closes #NNN` or a non-closing issue link.
3. Record scoped checks and warm/seed the cache through the cache protocol.
4. Freeze the head SHA and run the full local gate. A changed head immediately
   returns the PR to `review:required` and invalidates prior approval.
5. If the gate passes, the root moves the linked issue to `status:review` after
   adapter preflight, then dispatches fresh code and blueprint reviewers. Each
   round binds the PR number, base SHA, head SHA, stable reviewer session name,
   and immutable external reviewer identity.
6. Reviewers remain read-only and perform no GitHub action. The root posts each
   returned report byte-for-byte, without paraphrase or identity substitution,
   and applies the matching `review:approved` or
   `review:changes-requested` label. The root's GitHub account is transport
   identity, not reviewer identity.
7. On findings, preserve their exact report and disposition history, change the
   head, run the full gate, and dispatch a fresh review round. Never reuse an
   approval across head SHAs.
8. The root integrates only a `review:approved`, unchanged head. Run the main
   build after merge, reconcile the linked GitHub issue, post exact terminal
   status, and archive local sessions.

PR titles use `type(scope): description`. `workflow/state/prs.json` is legacy
history or a derived compatibility projection only and never authorizes review
or merge.

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
