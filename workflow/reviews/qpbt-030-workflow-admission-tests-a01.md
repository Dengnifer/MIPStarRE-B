# GitHub Cutover Admission Test Lane A01

- Session: `i030-tester-a01-workflow-admission`
- Collaboration task: `/root/i030_tester_a01_workflow_admission`
- Canonical issue: GitHub #30
- Model requested: `gpt-5.6-sol`
- Owned path: `tests/test_workflow.py`
- Subagents: 0
- Point timing and token usage: unavailable from the collaboration backend
- Lean/Lake builds: 0
- GitHub operations: 0
- Admission note: retrospective cutover repair dispatched while the accepted
  blocker was the absence of any lawful planned-session enqueue; it is recorded
  as an actual attempt, not as governed launch evidence

The lane replaced the accidental always-present test manifest with an explicit
valid cutover fixture and added regressions for manifest-bound migrated and
GitHub-only enqueue, byte-exact identity rejection, state-path aliases,
irreversible missing-config failure, ready-to-blocked drift at lock acquisition,
and GitHub-only formalization orchestrator admission.

Validation: workflow tests `112/112` and diff hygiene passed.
