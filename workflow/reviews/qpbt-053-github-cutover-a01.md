# GitHub Canonical Cutover Evidence A01

## Authority

- Repository: `Dengnifer/MIPStarRE-B`
- Repository database ID: `1352436168`
- Repository node ID: `R_kgDOUJyJyA`
- Explicit integration base: `main`
- Cutover and current main before this candidate:
  `4a6683795a71712d6a5c52b7539c2f532fd39f71`
- Server default branch: `from-monorepo`
- Canonical cutover issue: #1, migrated marker `QPBT-053`
- Third-occurrence live-contract issue: #28, with no legacy marker
- Remote: `git@github.com:Dengnifer/MIPStarRE-B.git`

The configured `main` base is independent of the server default. Changing the
default requires repository-administration permission which the current token
does not have; the attempted settings request failed with HTTP 403. This does
not block the cutover because every PR and adapter check names `main`
explicitly. No umbrella-repository operation was performed.

## Migration Inventory

The cutover created or bound 25 manifest issues: 24 still-open legacy issues
and cutover issue #1. Twenty-nine completed issues remain only in the frozen
archive so the migration does not fabricate history. It also published the
exact heads for two still-open local candidates and opened GitHub PRs #26 and
#27 against explicit `main`.

Native GitHub graph reconciliation wrote 21 parent relationships and 13
blocked-by relationships. Relationships to completed pre-cutover objects stay
as archive provenance rather than invented GitHub issues. Thirteen scoped
labels cover domain, workflow kind/status, migration, and review transport.

After three live fixture-shape failures of one class, root opened GitHub-only
issue #28 under native parent #1 and blocked it by #1. It is deliberately absent
from the immutable migration manifest. Its live preflight reports
`legacy_id: null`, proving that post-cutover objects need no shadow local issue.

Frozen legacy archive SHA-256 values:

```text
f43d77ee8e928161cb0053c7548392235108865a153a37829f71b02212c7f122  workflow/state/issues.json
3b411467e473974b69ec6340de6bec3c4a389a461ee0fd774ac0a2971a65a2c5  workflow/state/prs.json
```

Authority input SHA-256 values:

```text
18771388469e578a7ef47c1eb3f86a0a401a61c58b0174fe12e8ea8330a75e30  workflow/github.json
caeae3403d85134a3c970b10496e70e45cd05531821f76392cc6c5a4b7daca4f  workflow/github-cutover.json
```

## Live Verification

The dependency-free adapter and its tests are bound by:

```text
2a883e5f26da3a79e2d7a9540c9b06d702858e24772f8df23cb88b9cb097dadc  scripts/github_workflow.py
20df6c7cb0812a67a99395adeb4678c24c0484087c9a71caaffefe10062a6cda  tests/test_github_workflow.py
```

Four sequential live preflights failed closed before the complete pass:

1. an `identical` comparison omitted `head_commit`;
2. open issue `stateReason` differed as exact CLI `""` versus REST `null`;
3. `blockedBy` used a `{nodes,totalCount}` connection;
4. `subIssues` used the same connection.

Each resulted in a smallest-sufficient parser rule and negative regression,
with a fresh child review after the final byte change. No failed preflight made
a write. The complete GET-only gate then validated exact repository identity,
`main`, all 25 manifest issues, the native graph, and both PR base/head pairs.
An additional selected-object gate validated GitHub-only issue #28.

The live gate separately found and root corrected three label-set defects:
issue #1 lacked its manifest-required migration label and carried a PR-only
review label, while PR #26 carried two mutually exclusive review labels. No
body, ref, commit, graph edge, or historical record changed in those repairs.

## Local Execution Layer

`workflow/state/issues.json` and `workflow/state/prs.json` are frozen archive
or compatibility inputs. Their legacy mutation commands fail closed after the
committed GitHub config appears. Dispatch requires that exact config and a live
selected-issue projection. GitHub-only sessions retain `issue_id: null`, a
positive `github_issue_number`, and an explicit local stage; tests prove no
issue row is persisted.

Local sessions, metrics, event history, reviewer artifacts, and the singleton
hot-main cache remain local authorities for execution evidence. Exact child
task paths are preserved separately from stable session names, and unavailable
token or timing data is recorded as JSON `null` with a reason.

## Validation And Review

- Adapter tests: 31/31 passed.
- Workflow tests: 83/83 passed after GitHub-only dispatch support.
- Research/workflow checker: passed.
- Offline manifest: 25 issues and two PRs passed.
- Complete and selected-object live preflights: passed.
- Python compilation and diff hygiene: passed.
- Lean/Lake builds for this cutover: 0.
- Shared writable build outputs: 0.
- Credentials recorded or transmitted in evidence: 0.

The adapter child reviewer approved its exact two-file hash manifest with no
findings. A fresh whole-candidate review, exact GitHub PR comment identity, and
guarded PR integration remain required before protocol revision 0.2.0 becomes
active.
