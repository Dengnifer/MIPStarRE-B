# QPBT-026 canonical checkpoint audit A13

## Identity and scope

- Logical session: `i026-auditor-a13-canonical-checkpoint`
- Role: fresh read-only canonical checkpoint auditor
- Repository: `/home/drx/MIPStarRE-auto`
- Main commit: `e8ba9e4a1f94ac99118e3724d8af507f50235374`
- Main tree: `87d267c61ea9aaf379add57a91f219014c2b0248`
- Audit start: `2026-09-01T03:16:40.634102169Z`
- Audit end: `2026-09-01T03:20:58.211758581Z`
- Measured elapsed: `257.578` seconds
- Verdict: `request_changes` for one metrics/accounting mismatch; no security-state, provenance, or candidate-integration defect found in this checkpoint

The audited tracked diff has SHA-256
`23b17e4c5af5e459ed2b656f9367d03e135e059d4d219cf37a5478e02d72543e`
when rendered by `git diff --binary` over the five requested tracked paths.
The complete main worktree delta is exactly those five tracked ledger files and
the three requested untracked evidence reports. No implementation, protocol,
test, Lean, blueprint, or reference-source path is modified on main.

## Finding

### A13-001 (medium): A10 records ten mapped channels, but its immutable evidence enumerates eleven

`workflow/state/sessions.json:15685` and
`research/metrics/sessions.jsonl:317` both record
`"outbound_channels_mapped": 10`. The immutable A10 report's table at
`workflow/reviews/qpbt-026-scope-token-design-a10.md:95` through line 105 has
eleven data rows: prompt authority, prompt request, prompt path metadata, base
checkout, synthetic head, Git object database, Git-derived diff/patch,
model-directed reads, child environment, capability/parser probe, and
command/tool output.

This does not weaken A10's repair design or the two open blockers, but it makes
the research/session counter factually inconsistent with its bound evidence.
Because the report bytes and hashes are already exact, the smallest correction
is to change the session check and the corresponding metric check from `10` to
`11`, with the normal root-owned state event. Do not rewrite the report.

## Evidence consistency

All three canonical reports are byte-identical to their `/tmp` source reports,
and their observed SHA-256 values match every recorded source/canonical/report
hash:

| Report | SHA-256 |
| --- | --- |
| `workflow/reviews/qpbt-026-review-a08-pr016-immutable.md` | `6d1452b08f1fdfc89f66bfdd77eeeb69ba1086ec960aefa1a7c2d920c555f5eb` |
| `workflow/reviews/qpbt-026-integration-preview-a09.md` | `3affc5d1cf5f51c9e3b60f9145587f844dcbdfbc6a945e210acdadc713ffcd40` |
| `workflow/reviews/qpbt-026-scope-token-design-a10.md` | `58e030e52f67982ab039d6927db340b86ad8868cbd7dff69ff0446ae6c37c79e` |

For A08, A09, and A10, session state and the single corresponding JSONL metric
row agree on issue, PR, role, backend, external ID, coordinator-measured elapsed
time, timing quality, agent-measured elapsed time, outcome, checks, notes, and
token-unavailability reason. There are no duplicate metric rows. Their runtime
intervals round to the recorded `531.616`, `513.347`, and `647.84` seconds,
respectively. Each session has an ordered running/update/finished/archived event
sequence and is terminal with both `status` and `archive_status` equal to
`archived`.

LPR-016 remains correctly blocked:

- status is `changes_requested`;
- immutable base/head are `ea584e9e894391773e09ddad2ce4d082497c7913`
  and `94c0e630b5f2697f678c400da082f108bde89471`;
- A08 is the third formal round, has verdict `request_changes`, and lists exactly
  its newly introduced `F-LPR016-005` as required by the schema;
- `F-LPR016-001`, `F-LPR016-003`, and `F-LPR016-004` are resolved by A08;
- `F-LPR016-002` and `F-LPR016-005` remain open/pending;
- `integration_sha` and `merged_at` remain null and the independent approval gate
  remains unexecuted.

A09's no-conflict result is explicitly frozen to old head `94c0e630...` and main
`e8ba9e4...`; its canonical notes correctly mark the preview advisory after A08
requested changes and require a rerun for the next approved head. Read-only Git
identity checks reproduced its base/head/tree, two-commit/six-path candidate
range, merge base, branch target, and absence of predicted conflict tokens.

STAGE-02 moves coherently from 73 to 76 issued subagents: the event delta adds
A09, A10, and the running A11 fixer. Its output count moves from 14 to 17 by
adding the A08, A09, and A10 reports; every listed output exists. A11 is still
running, so its report, metric row, and stage output are correctly absent rather
than missing canonical evidence.

## Validation and counters

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate --json`:
  passed with `valid=true`, 27 issues, 16 PRs, 319 issued sessions, and 7 stages.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py --skip-tests`:
  passed with `workflow state: valid`.
- `git diff --check`: passed.
- JSON syntax gates: all three requested JSON files and both requested JSONL
  ledgers parsed successfully with `jq`.
- Source/canonical report hash comparisons: 3/3 exact.
- Session/metric structural comparisons: 3/3 exact apart from A13-001, which is
  identically repeated in both ledgers but disagrees with source evidence.
- Stage outputs present: 17/17.
- Candidate implementation paths integrated into main: 0.
- Tests, Python compile attempts, Lean commands, Lake commands, builds, cache
  actions, subagents, network requests, endpoint contacts, GitHub operations,
  credential reads/uses, repository edits, and Git writes: 0.
- Files written: only `/tmp/qpbt-026-canonical-checkpoint-a13.md`.

Residual risk is limited to the semantic review already recorded by A08 and A10:
this audit checked canonical consistency and immutable evidence, not the pending
A11 implementation or the truth of its future fix.
