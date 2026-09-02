# GitHub Dispatcher Provisional Review A03

## Identity

- Canonical issue: GitHub #1 (`QPBT-053` compatibility marker)
- Stable reviewer session: `i001-reviewer-a03-github-dispatcher-retry`
- Collaboration task: `/root/i053_reviewer_a03_dispatcher_retry`
- Role: fresh read-only reviewer
- Verdict: `request_changes`
- Completed no later than: `2026-09-02T06:43:07Z`
- Point start, elapsed time, and token usage: unavailable because the
  collaboration backend exposed none
- Nested topology: one direct read-only security scout and one interrupted
  nested path-race scout; neither edited files
- Lean/Lake builds: 0
- GitHub writes: 0

## Reviewed Snapshot

```text
d297e95ce620ee25a31de20ca4a5d7199bdbba383e415a90e26fae81f3d53fc4  scripts/workflow.py
89a5ece752d8cf6fbc6b7a1f79299d2302cf1cacbbc581f4dc87a26db4117ad4  scripts/local_agent.py
363b93f99dfaf97edb8633bf2617f1ad3dcaa8dfdd567d57b7f6fb0d15251d84  tests/test_workflow.py
2d8f575383cf3888e690439a3f7d4103e88d36b97516407d3d4a5d5f1444a810  tests/test_local_agent.py
f459e081fcfb96cfe349f1a060cc7a9db06c0585a2c927f20a1959fb2331e678  workflow/reviews/qpbt-053-github-cutover-a01.md
18771388469e578a7ef47c1eb3f86a0a401a61c58b0174fe12e8ea8330a75e30  workflow/github.json
caeae3403d85134a3c970b10496e70e45cd05531821f76392cc6c5a4b7daca4f  workflow/github-cutover.json
```

## Findings

1. High, `scripts/workflow.py`: cutover blocked every generic sessions mutation,
   including the only planned-session enqueue path. No lawful future GitHub-only
   dispatch row could be created.
2. High, `scripts/workflow.py`: authority derived from a lexical state path and
   mutable config presence. A symlinked state alias could miss canonical mode,
   and a new store could reopen legacy mutation after config removal despite the
   retained manifest.
3. High, `scripts/workflow.py`: the final live GitHub preflight completed before
   the exclusive publication lock. A ready-to-blocked remote change on lock
   acquisition could still issue the row.
4. High, `scripts/workflow.py`: the canonical projection omitted issue kind and
   execution category. A writable GitHub-only formalization prover could dispatch
   without the required active orchestrator.
5. Medium, `scripts/local_agent.py`: a migrated claim checked only the caller's
   supplied identity. A stored `(QPBT-002, #999)` pair could reach `running` when
   claimed through the legacy half.
6. Medium, `scripts/local_agent.py`: an identical terminal import returned before
   artifact verification, so deleting the registered result and retrying could
   report success while leaving the artifact absent.
7. Low, `workflow/reviews/qpbt-053-github-cutover-a01.md`: validation evidence
   still reported workflow `91/91` while the reviewed snapshot passed `105/105`.

The reviewer also confirmed that the prior migrated-launch and generic
publication-boundary rollback findings were fixed. Its observed gates passed:
workflow `105/105`, local agent `68/68`, adapter `31/31`, workflow validation,
and diff hygiene.

## Disposition

All six behavioral findings were accepted. GitHub issue #30 records their
release gates. The subsequent repair adds manifest-bound enqueue, real-path and
irreversible cutover checks, a locked final live read, live category/orchestrator
admission, full migrated identity verification through publication, and exact
terminal artifact restoration. The stale-count finding is corrected in the
cutover evidence. Fresh review of the changed head is still required; this
provisional report is not approval evidence for PR #29.
