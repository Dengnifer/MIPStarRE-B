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

## One orchestrator per issue

The coordinator dispatches exactly one orchestrator for each implementation
issue. The initial prompt contains the full issue record, protocol revision,
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
