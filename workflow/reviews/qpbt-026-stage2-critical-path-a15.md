# QPBT-026 Stage 2 critical-path audit A15

## Identity and verdict

- Logical session: `i026-scout-a15-stage2-critical-path`
- Role: fresh read-only critical-path scout
- Canonical session start: `2026-09-01T03:49:00.474309Z`
- Agent-observed start: `2026-09-01T03:49:24.413676883Z`
- Agent-observed report freeze: `2026-09-01T04:01:14.080851245Z`
- Agent-measured elapsed to report freeze: `709.667174` seconds
- Evidence cutoff: `2026-09-01T03:58:35.257121568Z`
- Cutoff main commit: `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`
- Cutoff main tree: `10f8da1ebb8b3fd7ce92dafee19d61fafe2cf8e2`
- Verdict: **stop LPR-016 integration; continue with two bounded repairs in the
  order below. QPBT-010 cannot yet close without either a completed governed
  endpoint review or an explicit disposition of that supplemental gate.**

## Findings

### Blocker 1: A14 is not clean and LPR-016 remains changes requested

Fresh immutable review A14 returned `request_changes` on exact base
`ea584e9e894391773e09ddad2ce4d082497c7913`, head
`89862d4b74364d1b2bb488d3ffc8e6820564c9ea`, and tree
`62c3da6b307a6411721469538368a2680e32da01`. Its report SHA-256 is
`8a613b59d20b27b9eb709547c7719c8c10e963367c49f9cb14881eeb4b74bb29`.

- F-LPR016-006 is a blocker: an empty injected offline capability mapping takes
  the truthiness fallback to the real Codex capability probe.
- F-LPR016-007 is high: inherited Git repository/object-selection environment,
  especially `GIT_ALTERNATE_OBJECT_DIRECTORIES`, makes source objects readable
  from the projected harness despite its empty local object inventory.

A14 confirms F-LPR016-002 on its original replay surface and F-LPR016-005 for
production fail-closed behavior, while introducing the two narrower defects.
The canonical PR now records F001-F005 resolved and F006-F007 open. Therefore
no PR status or integration transition is justified before a changed-head fix
and another fresh immutable review.

### Blocker 2: the current finding ledger makes later LPR-016 approval impossible

This blocker is independent of F006/F007. `scripts/workflow.py:692-710`
requires every resolved finding on an `approved` or `merged` PR to have its
resolution review bound to the PR's current base/head. At the same time,
`scripts/workflow.py:2380-2401` makes every resolved finding disposition,
including `resolved_by_review_id`, immutable.

LPR-016 is already in the contradictory state:

| Findings | Immutable resolution review | Resolution head | Current head |
| --- | --- | --- | --- |
| F001, F003, F004 | A08 | `94c0e630...` | `89862d4b...` |
| F002, F005 | A14 | `89862d4b...` | `89862d4b...` |
| F006, F007 | open | none | `89862d4b...` |

F006/F007 require another changed head. A later approving reviewer could
confirm every prior disposition, but the ledger has no append-only field in
which to record that confirmation, and it forbids rebinding F001/F003/F004.
Thus `changes_requested -> ready` is mechanically possible after checks, but
`ready -> approved` will fail validation even after a mathematically clean
review. Integration must not work around this invariant.

The smallest numbered repair is **QPBT-027: Permit append-only current-head
reconfirmation of resolved PR findings**. It should preserve the original
finding, disposition, evidence, and resolution review byte-for-byte; add only
append-only fresh-review confirmations; require each confirmation to be later,
independent, and bound to the current base/head; and let approval accept the
original current-head resolution or such a current-head confirmation. Tests
must cover a head advance after partial resolution, a later new finding, stale
or non-approving confirmation rejection, mutation/removal rejection, and final
approval only after every resolved finding is reconfirmed. The change needs its
own protocol/changelog evidence and immutable review. A read-only design can
run beside the active F006/F007 fixer; writable work must respect its
protocol/changelog ownership.

A fresh replacement PR is a valid fallback if QPBT-027 is rejected: close
LPR-016 as superseded only after importing all A14 evidence, create a new PR
over the complete `ea584e9e...` to final-head range, rerun all checks, and have
one new reviewer inspect the full range. Do not delete, rewrite, or transplant
the closed PR's review history.

### Blocker 3: standing transport trust is not content authorization

The direct user instruction establishes that
`https://api.finite-dimensional.space` is trusted transport equivalent to the
official OpenAI endpoint for this repository, with preferred model
`gpt-5.6-sol`. It does not identify or authorize the exact bytes of a particular
review packet. The canonical `QPBT-010.standing_transport_trust` record makes
this explicit with:

- `credentials_authorized: false`;
- `unrelated_private_content_authorized: false`;
- `exact_immutable_file_manifest_required: true`; and
- `separate_content_scope_authorization_required: true`.

That reading is corroborated by `protocols/review.md:33-40`, INC-045, A08's
blocked endpoint report, A10's eleven-channel disclosure audit, the candidate
A11 protocol, and A14. An exact immutable manifest is necessary evidence of
scope; its existence is not itself consent to transmit the listed bytes.
Endpoint/model selection, exact content authorization, and OS-enforced host
read isolation are three separate gates.

A11 deliberately leaves production review unavailable. It validates legacy
version-1 destination/target/path structure, then fails before task/context
reads, probes, harness/output creation, lease claim, command construction, or
runner invocation. Its projected harness is an offline test facility and, per
A14, still needs the capability and Git-environment repairs. It does not create
a production authorization or isolation boundary.

### High: intrinsic QPBT-010 acceptance is complete, but its supplemental gate remains open

The four acceptance gates written on QPBT-010 are evidenced as complete:
bounded checksum verification, REST/codeload fallback, offline fallback tests,
and three bounded pinned acquisitions. LPR-001 head `e93d949d...` received the
independent local A04 approval with all three findings resolved and was
physically integrated at `65315213d047d9181804ad74d573f533c904ef4f`.
The approved head, integration commit, LPR-002 head, and LPR-004 head are all
ancestors of the cutoff main; the approved LPR-001 and LPR-002 path bytes are
unchanged.

Nevertheless A09 and the combined Stage 2/3 report explicitly retain the
later, user-requested endpoint review as a supplemental closure gate, satisfied
only by a governed endpoint verdict or an explicit disposition. Existing local
approval is not silently interchangeable with that gate. Therefore:

- intrinsic issue evidence would support `QPBT-010 review -> done` without an
  endpoint request if the supplemental endpoint gate were explicitly disposed;
- current recorded requirements do not permit the coordinator to infer that
  disposition from standing transport trust; and
- the latest instruction is not content authorization and is not a waiver.

## Exact transition and integration sequence

### Current QPBT-026 sequence

1. Keep QPBT-026 `in_progress` and LPR-016 `changes_requested`. Preserve A14 as
   the disposition of F002/F005 and introduction of F006/F007.
2. Fix F006/F007 on one owned changed head: reject every falsey/incomplete
   offline capability before any probe or side effect, and scrub or fail closed
   on all Git repository/object/template/replacement selectors for harness Git
   commands and the injected child runner. Add the two adversarial regressions.
3. In parallel where ownership permits, implement and independently review
   QPBT-027. Do not attempt to approve LPR-016 until its current-head
   reconfirmation mechanism is integrated and validated.
4. Rebind LPR-016 to the final changed head, append current checks, and issue a
   fresh read-only reviewer over the complete immutable base-to-head range. The
   reviewer must explicitly reconfirm F001-F005 and dispose F006/F007.
5. Import and archive that reviewer, record all finding confirmations, then
   transition LPR-016 `changes_requested -> ready -> approved` and QPBT-026
   `in_progress -> review`. Validate after each state batch.
6. From a clean canonical checkpoint, recompute merge base and `merge-tree`.
   Integrate with a true non-fast-forward merge whose second parent is the exact
   approved candidate head. Do not cherry-pick or copy paths: the immutable
   reviewed head must become an ancestor. Preserve the full PR-range inventory
   separately from the expected four implementation/protocol/test paths in the
   first-parent merge delta when candidate reports are already byte-identical on
   main.
7. Run the exact focused tests, compileall, full dependency-free workflow gate,
   workflow validation, staged diff hygiene, parent/tree/ancestry, and clean
   worktree checks. No Lean/Lake/cache build belongs to this Python/protocol PR.
8. Record the merge SHA and post-integration evidence while the PR is approved,
   transition LPR-016 `approved -> merged`, attach QPBT-026 completion evidence,
   and transition QPBT-026 `review -> done` in a separate validated closure
   change.

QPBT-026 closure alone unlocks no issue: no issue has a dependency edge to it.
It establishes safe fail-closed behavior, not production external review.

### Production external-review follow-up

After allocating QPBT-027 to the ledger repair, the smallest production issue
is **QPBT-028: Enable content-bound, OS-isolated production external review**,
dependent on QPBT-026. Its acceptance must include:

1. a version-2 authorization binding endpoint/model/wire/base/head/tree and
   path, channel, revision role, mode/type/object ID, size, and SHA-256 for every
   Git, authority, request/context, derived-patch, prompt, and tool-readable
   content unit;
2. guarded one-time capture and an evidence-only projection with no source
   objects, refs, remotes, alternates, live symlinks, or host paths;
3. an enforceable OS filesystem/environment/tool-egress boundary, with
   production fail-closed when unavailable and a real sentinel-denial test;
4. explicit rejection of credentials and unrelated content, plus the complete
   A10 adversarial matrix; and
5. a fresh immutable security review.

QPBT-028 can build the mechanism without contacting the endpoint. A production
LPR-001 reviewer then still needs an explicit user authorization for the final
exact version-2 manifest. The alternative is an explicit user disposition
waiving the supplemental endpoint review. These are the only two evidence-based
routes to QPBT-010 closure; the coordinator cannot manufacture either.

### Stage 2/3 dependency sequence after QPBT-010

The source and blueprint implementation, local reviews, physical integrations,
and strict integrated acceptance gate are already complete. No merge replay or
new second commit is needed. Once the endpoint condition is satisfied or
explicitly disposed, use this dependency order:

| Closure | Newly eligible work |
| --- | --- |
| QPBT-026 | None; it has no reverse dependency edge. |
| QPBT-010 | QPBT-002 becomes dependency-complete but must be explicitly moved from `blocked`. |
| QPBT-002 | QPBT-009 becomes dependency-complete but must be explicitly moved from `blocked`. |
| QPBT-009 | QPBT-003 becomes dependency-complete but must be explicitly moved from `blocked`. |
| QPBT-003 | Planned QPBT-004 becomes strictly dependency-ready because QPBT-024 is done; blocked QPBT-023 becomes eligible for explicit unblocking. Run them in parallel. |
| QPBT-004 | Tracking QPBT-005 and planned QPBT-017 become dependency-ready; QPBT-013 is ready only if QPBT-023 is also done. |
| QPBT-023 and QPBT-004 | QPBT-013 becomes ready, followed sequentially by QPBT-014, QPBT-015, and QPBT-016. |

For QPBT-002, QPBT-009, and QPBT-003, use the legal issue path
`blocked -> ready -> in_progress -> review -> done`, attaching existing
immutable approval and integration evidence before closure. QPBT-002 has A20
approval at `63037ddc...`; QPBT-009's thirteen source-gap dispositions are
accepted; QPBT-003 has A30 approval at `3f4d4b30...`; and the strict integrated
gate at `fcd1aa92...` passed. STAGE-02 can complete after QPBT-010, QPBT-002,
QPBT-012, and QPBT-026 are done. STAGE-03 remains open through QPBT-023.

## Evidence inventory

At the cutoff, canonical state hashes were:

```text
56df709b77e1dc68aadb8daec88569384551ffb4431add49be8acf7c3aad0ee0  workflow/state/issues.json
94bf60c0825f1abfac244fc1c3d3424011569b8ba7c0f81bb1a9e28fccb945fc  workflow/state/prs.json
ef8927847935ebe97b0e627ef2f2f2ade635da9ac808fcd5529d50dd65918fde  workflow/state/sessions.json
c9bf8479cb3debad8bedfd533f5cafa2ac275b97aa6bc6590b264c6efbd9c1b4  workflow/state/stages.json
a1dff24b3a5846850a7b9452f460256372573a6e777ca939f5a99a189ded1a57  workflow/events.jsonl
23a9ad2e94c78345e9869a218ad6569cbd629062f500d19ab043a06496cc4f1f  protocols/review.md
```

Relevant immutable report hashes:

```text
fc6d9ad2984d836aa04ac547ed5a44a9d471cd3f9ce286520c5a679457371b5e  qpbt-010-endpoint-review-a06.md
50cfd5708da680e4186489ce3ff706c87cac5d05a09ef801d8023fed921f449c  qpbt-010-endpoint-review-a08.md
715c4d9e89fb18addded6df6389b3c05f29baf52bc02c6fbbbe47173873df51d  qpbt-010-endpoint-retry-a08.md
2bdd7f6a0c4c15f6118e29b15a35a191d310487a36ae1e51f0d6c9c4b4621fea  qpbt-010-integration-reconciliation-a09.md
b974b915046351321d32df2a6df0a2e78e050f0a3a3caeabac83139faa171c6e  qpbt-010-combined-gate-a10.md
64c9c11959b9a22ecd025a5ee47873aef14d8c24788494ea14f0d5e494415b84  stage-02-03-postintegration-acceptance-fcd1aa9.md
83ddc7d2ac6adc50eacb973c57869defb77c8246c1c73d12f1fa3f674ec1abc9  qpbt-002-reference-split.md (A20 ledger result)
5cefffe759413907ad752f73a20dab1451c949894730482ecbf0d9115a3d2c8c  blueprint/README.md (A30 ledger result)
6c569f7bcc227821d9f55487fa31b1a2fcc9a749ba812543931bea336139eead  stage-03-blueprint-lean-recon.md
faa33aa7b0d3282afd45113d90b375287c341c1be34dab3761f238839e5c4314  qpbt-026-disclosure-preflight-a11.md
8a613b59d20b27b9eb709547c7719c8c10e963367c49f9cb14881eeb4b74bb29  qpbt-026-review-a14-pr016-immutable.md
d3aa6e88e5c25124150a3d6478a32d658e8193b9ab01127faf83a40496388603  qpbt-026-stage2-readiness-a12.md
```

`python3 scripts/workflow.py validate --json` passed at the stable cutoff with
27 issues, 16 PRs, zero planned sessions, 325 issued sessions, and seven stages.
`python3 scripts/check_workflow.py --skip-tests` passed with `workflow state:
valid`. A prior check correctly observed the transient interval between A14's
terminal transition and metric import; it was rerun only after the root finished
that atomic evidence batch.

Read-only ancestry checks passed for integration `65315213...`, LPR-001 head
`e93d949d...`, LPR-002 head `63037ddc...`, and LPR-004 head `3f4d4b30...`
against cutoff main. Candidate `89862d4b...` is not yet an ancestor of main;
its merge base with main is exact PR base `ea584e9e...`, and its seven-path
base-to-head diff passes `git diff --check`.

## Metrics and safety

- Exposed token usage: `null`.
- Token availability reason: the collaboration backend does not expose
  per-agent token accounting; no estimate was made.
- Subagents spawned: 0; topology was one read-only scout.
- Repository/canonical/runtime/Git writes: 0.
- Authored output: only `/tmp/qpbt-026-stage2-critical-path-a15.md`.
- Tests, compile attempts, Lean/Lake commands, project builds, and hot-cache
  warm/seed/status operations: 0.
- Codex launches/probes, endpoint requests, network requests, GitHub reads or
  writes, and credentials inspected/used/transmitted: 0.
- No acceptance gate was weakened, rewritten, or silently disposed.
