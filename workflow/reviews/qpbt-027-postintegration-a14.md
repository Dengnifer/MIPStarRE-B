# QPBT-027 / LPR-017 post-integration review A14

## Findings

None.

## Verdict

`approve` for post-integration activation.

The exact merge commit
`3686315526fab8704745df6ad69d60e1bd72fa3a` preserves the approved first-parent
state and integrates exactly the four candidate workflow files. The integrated
blobs are byte-identical to approved candidate
`2c6b1f1d0be89d09bad2f60e074cf106be99fd46`. The focused workflow tests and both
required state checks pass. No blocker, high, medium, or low behavioral finding
was found.

This review does not itself change `LPR-017` from `approved` to `merged`.
Recording `integration_sha`, the coordinator-owned aggregate gate, and the
subsequent canonical state transitions remain coordinator actions.

## Immutable merge identity

- Review worktree: `/tmp/qpbt-027-postmerge-review-a14`.
- Detached HEAD: `3686315526fab8704745df6ad69d60e1bd72fa3a`.
- Merge tree: `5f076ec1171b80dd0aa9a0e459ef4788897ea2a9`.
- Ordered first parent:
  `3a90910de7921e43fd40db44271c528bbca7301d`.
- Ordered second parent:
  `2c6b1f1d0be89d09bad2f60e074cf106be99fd46`.
- `git show -s --format='%H %P'` has exactly three fields: the merge and exactly
  those two parents in that order.
- The second parent is an ancestor of the merge (`git merge-base
  --is-ancestor` exit 0).
- Final detached worktree porcelain is empty.
- `git diff --check FIRST_PARENT..HEAD` is empty.

The first-parent diff contains exactly four modified paths. Its sorted,
newline-delimited manifest has SHA-256
`cb8e72c6b794d9f4b466fbce802f61cf8ec33ef6b4b594f9ca410b08b061f59e`:

```text
protocols/CHANGELOG.md
protocols/review.md
scripts/workflow.py
tests/test_workflow.py
```

No repository path outside those four differs from the first parent. An
explicit diff over the canonical evidence scopes (`research/metrics/`,
`research/report.md`, `workflow/events.jsonl`, `workflow/reviews/`, and the four
canonical workflow state documents) exits 0. This preserves the A13 scout
report and the approved LPR-017/A11 state introduced before the merge.

## Integrated blob authentication

| Path | Merge/candidate Git blob | Content SHA-256 |
| --- | --- | --- |
| `protocols/CHANGELOG.md` | `f5fcf6d0511c889fc35e97ae551f8fcc98c13bfc` | `c667bcbdcb5c139242fe7ce6d936209a7a6d0d45c487ac22ae4d0f938023afd5` |
| `protocols/review.md` | `84b5c607426f661ce3defb6b525be99d839f14f9` | `4638e12e9d82d4a2d2bde3e2074068b468368bedaa21c623432f16ec090634ae` |
| `scripts/workflow.py` | `6b5271bc995066641319c4ee0fe880e37d74490e` | `a23110e0b65843525cc51443ef1c0aa8be1ad21df715c4b3c0b8e20b17e61eca` |
| `tests/test_workflow.py` | `ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe` | `89713c6d0dc2bbed1df1cd90977c7257dc3b67cde91321d6e57923751f96eabd` |

The two candidate paths shared with the first parent also preserve their exact
approved blobs and bytes:

| Path | Git blob at first parent, candidate, and merge | Content SHA-256 |
| --- | --- | --- |
| `workflow/reviews/qpbt-027-finding-reconfirm-a01.md` | `06e0c36a4b376ec309463b2a3ccd19d8eff054a2` | `1885c02167279996773fe29d31cf3665d225d02ffd494b02d743fe2437134e73` |
| `workflow/reviews/qpbt-027-stale-append-fix-a05.md` | `815939ceb85a606cb134a6010b8e9a49c6b17df0` | `a442bc60c86ccae962c956ebe024f1b822792a9e9afbb9d81722458e954d5e61` |

## Behavioral review

The integrated change is workflow-only; it changes no Lean declaration,
blueprint statement, paper-labelled theorem, source pin, build recipe, or cache
path. Mathematical and paper-source fidelity are therefore not implicated.

The finding ledger remains append-only. Existing finding identity and
introduction fields remain immutable, and a resolved disposition can change
only by appending an exact prefix-preserving `confirmation_review_ids` suffix
(`scripts/workflow.py:2462-2500`). New suffix entries are checked against the
complete candidate assembled after every public assignment. Each must name an
existing candidate review, be unique, differ from the resolution review, have
valid increasing chronology, approve, and bind the candidate's exact PR base
and head (`scripts/workflow.py:2503-2580`). This closes the previously reported
assignment-order stale-append path.

Complete static validation independently requires the referenced reviewer's
terminal read-only reviewer role, same-PR binding, persistent external identity,
and independence from implementers and issue owners. It also requires passing
checks for every reviewed immutable base/head and chronological review issuance
(`scripts/workflow.py:492-571`, `scripts/workflow.py:695-735`). Approval and
merge require a current approving review, all findings resolved, and a current
resolution or approving confirmation for every finding
(`scripts/workflow.py:747-790`). Open findings cannot carry confirmations, and
unknown, duplicate, malformed, non-approving, stale-head, wrong-PR, and
non-reviewer evidence fails closed.

I inspected the public `update pr` path as well as the helpers. It builds a deep
copy, applies all assignments, invokes the guard once on that complete
candidate, and only then replaces the in-memory record. Full cross-document
validation occurs before persistence (`scripts/workflow.py:2920-2968`,
`scripts/workflow.py:1739-1755`). Existing exact-current confirmations may later
become an immutable historical prefix after a head advance, but such a stale
prefix cannot authorize `approved` or `merged` on the new head. That distinction
matches the protocol text in `protocols/review.md:124-148`.

The first-parent LPR ledger retains the formal A11 approval on exact PR base
`506ac7a7b57a2318e0764acfc2558dc62f9e50f0` and exact candidate head
`2c6b1f1d0be89d09bad2f60e074cf106be99fd46`. Its sole high finding,
`F-LPR017-001`, is resolved as fixed by A11. The A11 report hash recomputes to
`2d8296adc252e0c3fe39a889fad9e9143bf9e194d365077e67fbef2f5ca21331`,
matching the PR ledger.

## Validation

| Gate | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py` | pass, 70/70 in 0.719 s |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate` | pass: 29 issues, 17 PRs, 0 planned sessions, 341 issued sessions, 7 stages |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_workflow.py --skip-tests` | pass |
| Exact commit, tree, parent order, ancestry, first-parent manifest, blob, evidence-preservation, diff-check, and clean-worktree checks | pass |

The aggregate dependency-free suite was deliberately not duplicated because
the root coordinator owns that test lane. Lean, Lake, full builds, and the hot
main cache are not applicable to this workflow-only four-file integration.

## Residual risk

Static validation cannot prove that an already stored historical confirmation
was current at its original append time; that temporal property is enforced
prospectively by the guarded public update path. Direct out-of-band JSON edits
remain outside that temporal guarantee, although complete validation still
prevents stale evidence from authorizing current approval or merge.

The canonical PR record at this reviewed commit is intentionally still
`approved`, with `integration_sha: null`. The coordinator must not transition it
to `merged` until its separately owned aggregate test gate passes, this report is
hashed and imported, and exact integration evidence is recorded.

## Actions and metrics

- New findings: 0.
- Repository edits, canonical state writes, canonical metric writes, Git writes,
  issue creation, and PR mutation: 0.
- Report files written: 1, this `/tmp` artifact only.
- Required focused tests: 70, all passed.
- Required workflow validation/check commands: 2, both passed.
- Aggregate tests: 0 by this reviewer; root coordinator owns that lane.
- Subagents: 0. Topology: root coordinator -> this fresh read-only reviewer.
- Network requests, endpoint calls, GitHub operations, credential access, Codex
  CLI launches, Lean commands, Lake commands, cache actions, and builds: 0.
- Session elapsed: `null`; availability reason: the collaboration backend does
  not expose a canonical per-agent duration.
- Token usage: input `null`, output `null`, total `null`; availability reason:
  per-agent token usage is not exposed by the collaboration backend.
- Incidents: 0. Protocol revisions made by this review: 0.

This report's SHA-256 is recorded externally after the file is closed; a file
cannot embed its own final digest.
