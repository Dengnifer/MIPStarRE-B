# QPBT-026 / LPR-016 semantic-union integration scout A22

## Verdict

`proceed only through a resolved immutable integration candidate and fresh review`.

The exact LPR-016 candidate can be integrated over checkpoint
`3686315526fab8704745df6ad69d60e1bd72fa3a`, but it is not a mechanical
candidate-tree merge. The supported three-argument `git merge-tree` preview has
one real textual conflict: one marker triplet in `protocols/CHANGELOG.md`.
`protocols/review.md` is changed on both sides and the textual merge currently
has no conflict marker, but it still creates combined semantics that neither
candidate review covered. A fresh independent read-only reviewer must approve
an exact immutable resolved commit/tree and exact file manifest before that tree
is activated as the LPR-016 integration.

The smallest resolution is:

1. concatenate, without rewriting, the complete QPBT-027 changelog entry and
   the complete QPBT-026 dated entries;
2. accept the clean review-protocol merge only after proving it retains both
   QPBT-026's fail-closed disclosure/offline-isolation rules and QPBT-027's
   immutable, append-only, current-head confirmation rules; and
3. preserve the candidate code/test blobs, the five identical report blobs,
   and all first-parent-only state/evidence blobs exactly.

Choosing either protocol side wholesale is invalid. Taking `ours` would omit
the disclosure boundary; taking `theirs` would omit the finding-confirmation
contract already activated by QPBT-027.

## Authenticated inputs

- Detached clean scout HEAD:
  `3686315526fab8704745df6ad69d60e1bd72fa3a`.
- Scout tree: `5f076ec1171b80dd0aa9a0e459ef4788897ea2a9`.
- Exact approved LPR-016 candidate:
  `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.
- Candidate tree: `88b1b6076aa8890376cf4f8b56c3da2bd372367d`.
- Candidate direct parent:
  `f3f49388f7058a9f9b997798417e4ae08435f523`.
- Declared PR base and exact merge base:
  `ea584e9e894391773e09ddad2ce4d082497c7913`.
- Base tree: `5c338d37641ea02d8bcc41c38d87a0a97e7947c4`.

All three revisions authenticated as commit objects. `git merge-base --all`
returned the declared PR base and no other commit. The scout worktree was
detached and porcelain-clean. The checkpoint changes 46 paths from the base;
the candidate changes 9; 7 paths occur in both sets, for a 48-path union.

This authentication is a checkpoint, not authority to merge from a later main
without another preview. Canonical A22 evidence may advance main. Immediately
before constructing the integration candidate, bind the actual clean first
parent, require this same merge base, and rerun the same three-argument preview.

## Complete path classification

### One actual conflict

`protocols/CHANGELOG.md` is `changed in both` and has exactly one conflict-marker
triplet in the preview.

| role | blob |
| --- | --- |
| base | `224a0ef6a92be7f15d4fc5a4884d0e62ee2b9812` |
| first-parent side | `f5fcf6d0511c889fc35e97ae551f8fcc98c13bfc` |
| candidate side | `86c1432768f51464f97d2ef65f5882096ad68a2c` |

### One clean overlapping change requiring semantic review

`protocols/review.md` is `changed in both`, but its preview contains no conflict
marker. The candidate rewrites the execution/disclosure sections while the
first-parent side adds the later findings-ledger rules.

| role | blob |
| --- | --- |
| base | `98e6590233e8a295e0cd87a72a9acf5e5c0092b5` |
| first-parent side | `84b5c607426f661ce3defb6b525be99d839f14f9` |
| candidate side | `6582dadc95c1d7c0bb091ceb2cfa6642646982d1` |

The traditional three-argument preview does not publish a result object, so no
result blob is claimed here. The eventual immutable integration commit must
bind and report it.

### Two candidate-only clean changes

The checkpoint side equals the PR base for both paths. `merge-tree` reports the
exact candidate blob as the clean result:

| path | base/checkpoint blob | candidate/result blob |
| --- | --- | --- |
| `scripts/local_agent.py` | `6805faca67b89a6d6c61bd90caf7652f350cb940` | `25a5198e9b3c7e3ace8c6365b7064e8aa55dc506` |
| `tests/test_local_agent.py` | `ce7fbc4596a63be2246fc7a125d3b7365fb3e801` | `f8b51e87f2e1d7ac5fc40d55b0c415b95cebf824` |

### Five byte-identical both-added reports

These paths have the same blob on the checkpoint and candidate sides. They
need no content resolution and must retain these identities:

| path | blob |
| --- | --- |
| `workflow/reviews/qpbt-026-capability-schema-a19.md` | `80d15f96cc97594236bc6d7d55879b2bead3c0a5` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a01.md` | `2923e68d180243053e80bc56f48fac9053499d4e` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a05.md` | `0ccf818f3a274a2fd649086a6919cc71a997cb59` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a11.md` | `da1e5c1cf6d8fec19a8c21d508c5efbd6f5baabc` |
| `workflow/reviews/qpbt-026-offline-isolation-a17.md` | `ea20399f6dceeea1e7d7ac04e90acd46f45935ce` |

### Thirty-nine first-parent-only paths

These paths are unchanged by the candidate from its PR base and therefore must
remain the exact first-parent versions:

```text
research/metrics/incidents.jsonl
research/metrics/sessions.jsonl
research/report.md
scripts/workflow.py
tests/test_workflow.py
workflow/events.jsonl
workflow/reviews/qpbt-018-021-closure-evidence-a18.md
workflow/reviews/qpbt-026-canonical-checkpoint-a13-r2.md
workflow/reviews/qpbt-026-canonical-checkpoint-a13.md
workflow/reviews/qpbt-026-integration-preview-a09.md
workflow/reviews/qpbt-026-pr016-bind-a02.md
workflow/reviews/qpbt-026-review-a03-pr016-immutable.md
workflow/reviews/qpbt-026-review-a04-supplemental.md
workflow/reviews/qpbt-026-review-a08-pr016-immutable.md
workflow/reviews/qpbt-026-review-a14-pr016-immutable.md
workflow/reviews/qpbt-026-review-a18-pr016-immutable.md
workflow/reviews/qpbt-026-review-a20-pr016-immutable.md
workflow/reviews/qpbt-026-scope-token-design-a10.md
workflow/reviews/qpbt-026-scout-a06-transport-compat.md
workflow/reviews/qpbt-026-scout-a07-credential-paths.md
workflow/reviews/qpbt-026-stage2-critical-path-a15.md
workflow/reviews/qpbt-026-stage2-readiness-a12.md
workflow/reviews/qpbt-027-final-merge-a13.md
workflow/reviews/qpbt-027-finding-reconfirm-a01.md
workflow/reviews/qpbt-027-postreview-ledger-a10.md
workflow/reviews/qpbt-027-pr017-bind-a03.md
workflow/reviews/qpbt-027-pr017-integration-preflight-a09.md
workflow/reviews/qpbt-027-reconfirm-contract-a02.md
workflow/reviews/qpbt-027-recovery-merge-a12.md
workflow/reviews/qpbt-027-review-a04-pr017-immutable.md
workflow/reviews/qpbt-027-review-a08-pr017-immutable.md
workflow/reviews/qpbt-027-review-a11-pr017-immutable.md
workflow/reviews/qpbt-027-stale-append-contract-a06.md
workflow/reviews/qpbt-027-stale-append-fix-a05.md
workflow/reviews/qpbt-stage2-integration-order-a07.md
workflow/state/issues.json
workflow/state/prs.json
workflow/state/sessions.json
workflow/state/stages.json
```

The load-bearing QPBT-027 first-parent blobs at this checkpoint are
`scripts/workflow.py` =
`6b5271bc995066641319c4ee0fe880e37d74490e`,
`tests/test_workflow.py` =
`ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe`, and
`workflow/state/prs.json` =
`2e5bc98daffb47a2afd797e8b8bdf02529eefede`.
The candidate has the old PR-base versions of those files, so any integration
result that regresses them is invalid.

## Exact semantic resolution

### `protocols/CHANGELOG.md`

Resolve the one top-of-file conflict by keeping the title once and then, in
order:

1. the complete `## 0.1.8 candidate (QPBT-027) - 2026-09-01` block from the
   first-parent blob, unchanged;
2. the complete `## 2026-09-01` QPBT-026 A17/A11/A05 block from the candidate
   blob, unchanged; and
3. the existing `## 0.1.7 candidate (QPBT-021) - 2026-08-31` and all following
   history.

Also retain the candidate's QPBT-026 bullet under the later
`## 2026-08-31` heading; that separate insertion already merges without a
marker. Remove only the three conflict-marker lines. Do not coalesce, summarize,
renumber, or duplicate either entry: exact concatenation is the smallest
sufficient resolution and preserves the already reviewed provenance text.

### `protocols/review.md`

The no-marker preview is the intended minimum only if the resulting immutable
file retains all of the following candidate rules:

- transport trust is separate from content-disclosure authorization;
- version-1 changed-path authorization is not production-launch authority;
- production review fails before task/context reads, capability or persistence
  probes, evidence/output construction, lease claim, command construction, or
  runner invocation until exact-content authorization and enforceable host read
  isolation exist;
- omitted transport profiles never inherit an implicit local destination;
- credential-path screening and rename-endpoint coverage remain fail-closed;
- offline mode requires an injected non-`codex` runner and validated capability
  record, uses a fresh repository with no source objects or remote, binds exact
  bytes/objects/modes/sizes/SHA-256, and does not claim host isolation;
- all Git inspection/harness operations and the injected runner use the fixed
  minimal environment; and
- no replayable global preflight token or independently callable production
  helper is reintroduced, and uncommitted external dispatch remains disabled.

It must simultaneously retain the first-parent QPBT-027 findings-ledger text:

- resolved status, disposition, evidence, and resolution review are immutable;
- `confirmation_review_ids` is optional, unique, chronological, same-PR,
  independent, terminal, approving, and append-only;
- the PR review list and each confirmation list are append-only;
- `approved`/`merged` requires a current exact base/head resolution or
  confirmation for every resolved finding; and
- stale confirmations cannot approve a later head, while a
  `request_changes` review cannot serve as an approving reconfirmation.

Do not preserve the superseded base wording that describes the Stage 1 profile
as authorization to dispatch externally. The candidate intentionally replaces
that claim with a fail-closed offline-only boundary. Conversely, do not replace
the findings-ledger section with the candidate's older base text.

## Integration and immutable-review gate

Construct a true two-parent integration candidate in its owned writable
worktree. Its ordered parents must be `(actual-main-before-integration,
5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a)`, and the exact candidate must be an
ancestor. Resolve only the changelog conflict as specified; inspect rather than
manually rewrite the clean `protocols/review.md` result.

Relative to the actual first parent, the expected content delta is exactly four
modified paths and no additions, deletions, or renames:

```text
protocols/CHANGELOG.md
protocols/review.md
scripts/local_agent.py
tests/test_local_agent.py
```

The five candidate report additions are already byte-identical in the first
parent, so they should disappear from that first-parent delta while remaining
authenticated in the merge tree.

Freeze the resulting commit SHA, tree SHA, ordered parents, four-path
first-parent manifest, all relevant blob identities above, and validation logs.
Then dispatch a fresh independent read-only reviewer who is neither the
candidate implementer, orchestrator, nor integration resolver. The reviewer
must review that exact immutable combined commit and exact manifest, not an
uncommitted worktree or a prose reconstruction. It must lead with findings and
specifically check both protocol contracts, the candidate code/test identity,
the QPBT-027 workflow/test identity, report identity, ancestry, and validation
results. Any byte change after review invalidates approval and requires another
fresh review.

Do not transition LPR-016 to `merged`, close QPBT-026, or advance canonical main
to the combined tree before this review approves it. If integration is formed
temporarily on main, treat it as unactivated and do not publish merged/done
state until approval; an owned integration branch/worktree avoids that
ambiguity.

## Required post-resolution gates

Run these against the exact immutable integration candidate, recording observed
counts and durations rather than carrying historical counts forward:

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPYCACHEPREFIX=/tmp/qpbt-stage2-integration-pycache python3 -m compileall -q scripts tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py
make -C blueprint test check graph
git diff --check ACTUAL_FIRST_PARENT..INTEGRATION
git status --porcelain
```

Also require:

- clean pre-integration and post-validation worktrees;
- exact ordered parents, merge-base, candidate ancestry, and tree identity;
- a repeated three-argument merge preview from the actual first parent;
- exactly the four-path first-parent content manifest above;
- exact candidate blobs for `scripts/local_agent.py` and
  `tests/test_local_agent.py`;
- exact first-parent blobs for `scripts/workflow.py` and
  `tests/test_workflow.py`;
- the five exact shared report blobs above; and
- no conflict markers or rejected hunks in either protocol file.

No Lean source, declaration list, pin file, or build recipe changes in this
integration. Lean, Lake, full project build, and hot-main-cache work are not
required by this path unless an independently discovered repository gate says
otherwise. The Python aggregate and blueprint synchronization gates remain
mandatory.

## Residual risk and metrics

The preview is bound to checkpoint `368631552...`; later canonical evidence can
change the first parent and therefore requires a final preview. A no-marker
textual merge of `protocols/review.md` is not itself proof that the two security
contracts compose. The candidate approval covers tree `88b1b607...`, not the
new combined protocol blobs, which is why the immutable combined-tree review is
mandatory.

- Stable session: `i026-scout-a22-semantic-union`.
- Topology: one bounded read-only scout; subagents: 0.
- Repository edits, Git writes, refs, commits, branches, merges, checkouts, and
  canonical state/metrics writes: 0.
- Tests, compilation, Lean, Lake, builds, hot-cache actions, network, endpoint,
  GitHub, credential access, Codex CLI, and external review launches: 0.
- Findings: one textual conflict; one clean semantic-overlap review boundary;
  no candidate-code conflict; five identical add/add reports.
- Token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session token accounting, so no estimate was made.
- End-to-end elapsed time: `null`.
- Elapsed availability reason: no canonical per-agent session timer was exposed
  before the first action, so no estimate was made.
- Report artifact: only `/tmp/qpbt-026-semantic-union-a22.md`; its SHA-256 is
  reported externally after the bytes are frozen.
