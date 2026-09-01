# QPBT-026 / LPR-016 semantic-union integration A23

## Verdict

An immutable two-parent integration candidate was constructed and passed every
scoped gate. Its commit is
`8ee49bcca504ccb02ffcb4852f63ca2d2f8fbbd4` and its tree is
`d1651f29f41d555859838a088726f03ac869d541`.

This resolver does not approve or activate its own work. The exact commit,
tree, ordered parents, and four-path manifest below still require a fresh
independent read-only review before LPR-016 can be integrated into canonical
main or transitioned to `merged`.

## Authenticated inputs

- Owned worktree: `/tmp/qpbt-026-integration-a23`.
- Initial state: detached and porcelain-clean at
  `710cfafd586172d3658499f3552c2ae5e27fe512`.
- First-parent tree:
  `1f30c34c056e7eb5bcb693d80176cdcfdbbc5f0b`.
- Exact approved LPR-016 candidate:
  `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.
- Candidate tree: `88b1b6076aa8890376cf4f8b56c3da2bd372367d`.
- Declared PR base and unique merge base:
  `ea584e9e894391773e09ddad2ce4d082497c7913`.
- Base tree: `5c338d37641ea02d8bcc41c38d87a0a97e7947c4`.

All three input revisions authenticated as commit objects. A repeated supported
three-argument preview

```text
git merge-tree ea584e9e894391773e09ddad2ce4d082497c7913 \
  710cfafd586172d3658499f3552c2ae5e27fe512 \
  5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a
```

reproduced exactly one conflict-marker triplet in
`protocols/CHANGELOG.md`. `protocols/review.md` merged without a marker, and
the two Python paths selected the exact candidate blobs. The real
`git merge --no-ff --no-commit` reproduced exactly that one unresolved path.

The coordinator's earlier blocked dispatch attempt is external coordinator
provenance. It was not an A23 command failure and is not included in A23's
attempt counts.

## Resolution

Only `protocols/CHANGELOG.md` was edited manually. The three conflict-marker
lines were removed while retaining, in order:

1. the title once;
2. the complete QPBT-027 `0.1.8 candidate` block from the first parent;
3. the complete QPBT-026 `2026-09-01` block from the candidate;
4. the complete pre-existing history; and
5. the candidate's separate QPBT-026 insertion under `## 2026-08-31`.

`protocols/review.md` was not hand-rewritten. Its clean auto-merged bytes were
inspected for both contracts and retained unchanged.

### Prefreeze coordinator finding

The first local merge object,
`ebb832f37ad52509f35c8af8afcbe7e4a16d8508`, was created just before a
coordinator message identified that the retained QPBT-027 paragraph ended on
the line immediately before the QPBT-026 heading. It had no separating blank
line. That object was unpublished, unreported as a review target, and never
reviewed.

The finding was fixed by inserting exactly one blank line between
`candidate is activated.` and `## 2026-09-01`. All scoped gates were rerun on
the corrected bytes, and the unpublished object was replaced by the final
amended merge commit below. No other byte changed in that correction.

## Immutable candidate

- Commit: `8ee49bcca504ccb02ffcb4852f63ca2d2f8fbbd4`.
- Tree: `d1651f29f41d555859838a088726f03ac869d541`.
- Ordered parent 1:
  `710cfafd586172d3658499f3552c2ae5e27fe512`.
- Ordered parent 2:
  `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.
- Commit subject:
  `merge(QPBT-026): integrate LPR-016 disclosure isolation`.
- Unique parent merge base:
  `ea584e9e894391773e09ddad2ce4d082497c7913`.
- The exact approved candidate is an ancestor of the integration commit.
- Final worktree status: porcelain-clean, including untracked files.

`git rev-list --parents -n 1` returned exactly:

```text
8ee49bcca504ccb02ffcb4852f63ca2d2f8fbbd4 710cfafd586172d3658499f3552c2ae5e27fe512 5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a
```

## Exact first-parent manifest

The complete content delta from ordered parent 1 contains exactly four
modified paths, with no additions, deletions, renames, mode changes, or other
paths:

| path | mode | integration blob | bytes | first-parent numstat |
| --- | --- | --- | ---: | --- |
| `protocols/CHANGELOG.md` | `100644` | `107c5eb147811e0d3909717c74e2f32eb43d1ac5` | 21,240 | `68 0` |
| `protocols/review.md` | `100644` | `037b625f0f77cfef1997d793aa14d48893d91dc0` | 13,139 | `95 30` |
| `scripts/local_agent.py` | `100644` | `25a5198e9b3c7e3ace8c6365b7064e8aa55dc506` | 160,965 | `740 225` |
| `tests/test_local_agent.py` | `100644` | `f8b51e87f2e1d7ac5fc40d55b0c415b95cebf824` | 114,539 | `934 210` |

The two Python blobs are byte-exact candidate blobs:

| path | candidate blob | result blob | verdict |
| --- | --- | --- | --- |
| `scripts/local_agent.py` | `25a5198e9b3c7e3ace8c6365b7064e8aa55dc506` | `25a5198e9b3c7e3ace8c6365b7064e8aa55dc506` | exact |
| `tests/test_local_agent.py` | `f8b51e87f2e1d7ac5fc40d55b0c415b95cebf824` | `f8b51e87f2e1d7ac5fc40d55b0c415b95cebf824` | exact |

Because the complete first-parent delta is the four paths above, every workflow
state, metric, event, canonical evidence, and QPBT-027 path outside that set
retains its exact first-parent blob. Load-bearing spot checks are:

| preserved path | first-parent/result blob |
| --- | --- |
| `scripts/workflow.py` | `6b5271bc995066641319c4ee0fe880e37d74490e` |
| `tests/test_workflow.py` | `ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe` |
| `workflow/state/prs.json` | `129b7be4a2894f30da48b92dea04f7c81a798551` |

The five shared reports retain one identical blob across parent 1, parent 2,
and the integration result:

| path | blob on all three revisions |
| --- | --- |
| `workflow/reviews/qpbt-026-capability-schema-a19.md` | `80d15f96cc97594236bc6d7d55879b2bead3c0a5` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a01.md` | `2923e68d180243053e80bc56f48fac9053499d4e` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a05.md` | `0ccf818f3a274a2fd649086a6919cc71a997cb59` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a11.md` | `da1e5c1cf6d8fec19a8c21d508c5efbd6f5baabc` |
| `workflow/reviews/qpbt-026-offline-isolation-a17.md` | `ea20399f6dceeea1e7d7ac04e90acd46f45935ce` |

## Contract composition inspection

The auto-merged review protocol retains the QPBT-026 disclosure and isolation
contract:

- transport trust is separate from content-disclosure authorization;
- version 1 is explicitly not production-launch authority and production fails
  before task/context reads, probes, evidence, leases, command construction, or
  invocation without exact-content authorization and enforceable isolation;
- both rename endpoints are preserved and high-signal credential paths fail
  closed without rejecting generic public certificate paths;
- an omitted transport profile never inherits an implicit destination;
- offline mode requires an injected non-`codex` runner and validated copied
  capability record;
- the evidence repository has no source objects or remote and binds path,
  object, mode, size, and SHA-256;
- Git inspection, harness construction, and the injected runner use the fixed
  minimal environment;
- the packet records `external_launchable: false` and
  `host_isolation: not-enforced`; and
- no replayable module-global preflight token or separately callable production
  helper is present.

It simultaneously retains the QPBT-027 findings-ledger contract:

- resolved status, disposition, evidence, and the original resolution review
  are immutable;
- `confirmation_review_ids` is optional, unique, chronological, same-PR,
  independent, terminal, and append-only;
- PR review lists and per-finding confirmation lists are append-only;
- `approved` or `merged` requires an approving exact-current-base/head original
  resolution or confirmation for every finding; and
- historical confirmations do not authorize a later head, while a
  `request_changes` review is not an approving reconfirmation.

The final committed protocol files contain no conflict markers or rejected
hunks. The changelog has the required blank-line-separated top blocks and keeps
the QPBT-026 insertion under the later `## 2026-08-31` heading.

## Validation

All required commands ran in the isolated integration worktree. The final run,
after the coordinator finding was fixed and before the corrected commit was
frozen, observed:

| gate | result | observed duration |
| --- | --- | ---: |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py` | PASS, 70/70 | 0.973 s test time |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'` | PASS, 63/63 | 4.989 s test time |
| `PYTHONPYCACHEPREFIX=/tmp/qpbt-stage2-integration-a23-r2-pycache python3 -m compileall -q scripts tests` | PASS | 0.576 s tool wall |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate` | PASS, 29 issues, 17 PRs, 0 planned, 344 issued, 7 stages | 0.000011 s tool wall |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py --skip-tests` | PASS, `workflow state: valid` | 0.122 s tool wall |
| `git diff --check` and staged/first-parent diff checks | PASS, no output | under 0.001 s tool wall |
| manifest, ancestry, parent-order, object-type, and clean-status probes | PASS | under 0.01 s each |

The superseded prefreeze bytes had also passed workflow 70/70 in 0.705 seconds,
local-agent 63/63 in 4.006 seconds, compileall, workflow validation, checker, and
diff checks. Those results are recorded only as an additional attempt; they do
not stand in for the complete rerun on the final bytes.

Unexpected command failures: 0. The nonzero merge result was the expected
single semantic conflict, and no-match marker searches returned their expected
status. Compileall attempts: 2. Lean/Lake/build/hot-main-cache actions: 0,
because this integration changes no Lean source, declaration list, pin file, or
build recipe.

## Scope and metrics

- Stable session: `i026-integrator-a23-semantic-union`.
- Issue/PR: QPBT-026 / LPR-016.
- Role: one writable integration resolver in one exclusively owned worktree.
- Nested subagents: 0, as required by the bounded assignment.
- Canonical main/state/metrics writes: 0.
- Network, endpoint, GitHub, credentials, Codex, Lean, Lake, and hot-cache
  actions: 0.
- Manual source edits: one conflict-marker resolution plus one coordinator-led
  separator correction, both confined to `protocols/CHANGELOG.md`.
- Commits formed: 2 local object attempts; the first was replaced before review
  and only the final immutable commit is a candidate.
- Token usage: `null`.
- Token availability reason: collaboration and command tools expose no
  per-session token accounting, so no estimate was made.
- End-to-end elapsed time: `null`.
- Elapsed availability reason: no canonical per-agent timer was exposed to this
  resolver before its first action, so no estimate was made.
- Report artifact: only `/tmp/qpbt-026-integration-a23.md`; its SHA-256 is
  reported externally after these bytes are frozen.

