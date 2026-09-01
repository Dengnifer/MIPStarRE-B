# QPBT Stage 2/3 closure-disposition audit A11

## Frozen scope

- Logical session: `i010-reviewer-a11-closure-disposition`
- Audited commit: `1cbcd4efe79f1bacfb2deffdb47d75bdf15516ac`
- Audited tree: `d31d767eda1504b393616cc6de03048eec04abb4`
- Checkout: detached, clean `/tmp/qpbt-stage23-closure-a11`
- Role: fresh read-only closure auditor

## Findings

1. **Low, nonblocking: the QPBT-009 blocker carries a stale exact count.**
   `workflow/state/issues.json:382` says that thirteen source-gap dispositions
   are accepted, while the approved final metadata now records `G01` through
   `G15` (`blueprint/metadata/gaps.json:5`,
   `blueprint/metadata/gaps.json:145`). The source map itself enumerates twelve
   initial discrepancies (`references/2001.04383v3/QPBT_SOURCE_MAP.md:127`).
   This is bookkeeping drift, not an omitted disposition: all map entries and
   the additional fidelity findings have explicit source, affected nodes,
   disposition, public effect, and QPBT-009 ownership. Replace the count with
   count-free completion wording when recording closure.

No blocking finding was found.

## Verdict

**Approve the explicit closure disposition.** The direct user rule disposes
the later endpoint-backed LPR-001 review as supplemental work without waiving
any written issue acceptance gate.

The canonical closure discipline says that after a stage gate passes, only a
failed acceptance test, a concrete safety issue, or a direct user requirement
may change the delivered surface, and all other improvements move to a numbered
issue (`protocols/meta.md:46`, `protocols/CHANGELOG.md:250`). QPBT-010's
canonical acceptance list contains exactly bounded checksum verification,
REST/codeload fallback, an offline fallback test, and three bounded acquisitions
(`workflow/state/issues.json:400`). It contains no endpoint-backed second-review
gate. The endpoint review is separately recorded as a requested external review,
while an approved local immutable review is also recorded (`workflow/state/prs.json:149`,
`workflow/state/prs.json:217`). Therefore the user's rule is an explicit
disposition of that supplemental request, not a waiver or deletion of an
acceptance criterion.

This disposition must not be recorded as endpoint approval or disclosure.
Canonical state still says no endpoint request or repository evidence was sent
(`workflow/state/issues.json:432`) and requires exact immutable manifests while
excluding credentials and unrelated private content
(`workflow/state/issues.json:452`). Preserve those facts.

## Intrinsic acceptance

### QPBT-010

All four written gates are satisfied on immutable LPR-001 head
`e93d949d06af2a7f4407d198a37aad315deac6aa`:

- The three acquisitions are checksum-pinned and bounded, including actual
  Git-to-REST-to-codeload fallback evidence
  (`workflow/reviews/qpbt-010-reference-transport.md:55`).
- Forty-nine offline tests cover fallback decisions, exact URLs, drift,
  process cleanup, credentials, byte bounds, checksums, and publication races
  (`workflow/reviews/qpbt-010-reference-transport.md:111`).
- Focused, aggregate, compile, state, and diff gates passed
  (`workflow/reviews/qpbt-010-reference-transport.md:129`).
- Fresh immutable reviewer A04 approved the exact base/head with no findings;
  all earlier findings are resolved (`workflow/state/prs.json:149`,
  `workflow/state/prs.json:160`). LPR-001 is merged at integration
  `65315213d047d9181804ad74d573f533c904ef4f`
  (`workflow/state/prs.json:204`).

The delivery itself classifies additional locking/resume/dirfd and HTTP
hardening as optional and unnecessary for the written gates
(`workflow/reviews/qpbt-010-reference-transport.md:169`). This independently
supports deferral rather than keeping QPBT-010 open.

### QPBT-002

All five written source gates are satisfied:

- The exact arXiv archive and member pins are recorded
  (`workflow/reviews/qpbt-002-reference-split.md:16`).
- The deterministic manifest covers all 34 safe split outputs and 646 label
  occurrences (`workflow/reviews/qpbt-002-reference-split.md:42`).
- Exact materialization and independent verification reproduce 39 files and
  646 labels with the pinned inventory (`workflow/reviews/qpbt-002-reference-split.md:72`).
- Rights and ignored-source provenance are explicit
  (`references/2001.04383v3/QPBT_SOURCE_MAP.md:21`,
  `references/2001.04383v3/QPBT_SOURCE_MAP.md:162`).
- Fresh immutable A20 approved exact LPR-002 head
  `63037ddceada7a88436f9afa9ed1ef4d74319098` with no findings, and the sole
  formal finding is resolved (`workflow/state/prs.json:421`,
  `workflow/state/prs.json:432`). LPR-002 is merged at the same integration
  commit (`workflow/state/prs.json:448`).

Its canonical blocker already says the local implementation and formal review
are complete and explicitly permits a user disposition of the endpoint
condition (`workflow/state/issues.json:103`).

### QPBT-009

The source-facing blueprint gates are satisfied in their Stage 3 meaning:

- The source map requires explicit decisions rather than silent normalization
  (`references/2001.04383v3/QPBT_SOURCE_MAP.md:127`), and final gap metadata
  records all fifteen source/fidelity decisions with explicit classes and
  public effects (`blueprint/metadata/gaps.json:5`).
- Typographical/domain normalization is distinguished from false statements,
  missing proofs, and mathematical repairs, for example G04 versus G05/G09
  (`blueprint/metadata/gaps.json:35`, `blueprint/metadata/gaps.json:45`,
  `blueprint/metadata/gaps.json:85`).
- The norm mismatch is represented by named Lean theorem contracts
  `normExtraction_ofSquared` and `qpbtRobustness_reparameterize`; its boundary
  explicitly says it is a theorem and never an input to public soundness
  (`blueprint/src/generated/chapter-11-entries.tex:19`). At blueprint stage,
  this satisfies the written "named proved statement" gate by fixing a theorem
  obligation rather than adding a public assumption. It does not claim that the
  later Lean proof-complete stage has already happened.
- External versions and trust/exclusion treatments are pinned
  (`blueprint/metadata/external-sources.json:5`,
  `blueprint/metadata/external-sources.json:68`).
- The full source-facing blueprint was independently approved on exact LPR-004
  head `3f4d4b302b96b74dffaf595c11ff01db4e6c7fbd`
  (`workflow/state/prs.json:1027`).

QPBT-009 is blocked only by QPBT-002 according to its dependency edge and
canonical disposition (`workflow/state/issues.json:356`).

### QPBT-003

The full immutable blueprint head passed the 48-node/12-chapter graph,
source-anchor, 26-test, 45-page/109-identifier PDF, compile, and diff gates
(`workflow/state/prs.json:961`, `workflow/state/prs.json:971`,
`workflow/state/prs.json:981`, `workflow/state/prs.json:991`). A30 approved that
exact head with no findings (`workflow/state/prs.json:1027`), and LPR-004 is
merged at `65315213d047d9181804ad74d573f533c904ef4f`
(`workflow/state/prs.json:1054`).

The terminal disposable post-integration gate at
`fcd1aa928ac0263f83de37143dc8dc5f4d937210` passed source, graph,
reachability/generated-output, PDF, aggregate, compile, state, diff, and clean
tracked-status checks (`workflow/reviews/stage-02-03-postintegration-acceptance-fcd1aa9.md:30`,
`workflow/reviews/stage-02-03-postintegration-acceptance-fcd1aa9.md:38`,
`workflow/reviews/stage-02-03-postintegration-acceptance-fcd1aa9.md:55`,
`workflow/reviews/stage-02-03-postintegration-acceptance-fcd1aa9.md:65`). That
report also identifies `65315213...` as the requested second milestone commit
in substance and history (`workflow/reviews/stage-02-03-postintegration-acceptance-fcd1aa9.md:82`).
Its earlier statement that endpoint review was still required is precisely the
supplemental condition now explicitly disposed, not new evidence against its
recorded combined-gate pass (`workflow/reviews/stage-02-03-postintegration-acceptance-fcd1aa9.md:7`).

Git independently confirms that all three approved heads, integration commit
`65315213...`, and acceptance snapshot `fcd1aa9...` are ancestors of the audited
HEAD. Each LPR-001, LPR-002, and LPR-004 changed-path set is byte-identical at
its reviewed head and audited HEAD. The acceptance report SHA-256 remains
`64c9c11959b9a22ecd025a5ee47873aef14d8c24788494ea14f0d5e494415b84`.

## Supplemental security work remains open

Closure does not approve, cancel, or bypass production external-review
security. QPBT-028 remains active with exact content, projection, OS isolation,
pre-request validation, adversarial tests, and independent security-review gates
(`workflow/state/issues.json:1329`). QPBT-029 separately owns the one-time
content capture and projection coordinator (`workflow/state/issues.json:1367`),
and QPBT-030 separately owns digest-pinned Docker isolation and the credential
broker (`workflow/state/issues.json:1410`). None is a dependency of QPBT-010,
QPBT-002, QPBT-009, QPBT-003, QPBT-004, or QPBT-023. STAGE-02 therefore remains
open for this supplemental lane even after the intrinsic source closures.

## Legal transition and immediate dispatch order

The workflow permits `review -> done` and requires blocked issues to traverse
`blocked -> ready -> in_progress -> review -> done`
(`scripts/workflow.py:132`). Dependency validation requires every dependency to
be exactly `done` before an issue may be ready or active
(`scripts/workflow.py:918`). The legal order is therefore:

1. Record the explicit supplemental-review disposition and transition QPBT-010
   `review -> done`.
2. Transition QPBT-002
   `blocked -> ready -> in_progress -> review -> done` using LPR-002/A20 and
   integrated acceptance evidence.
3. Transition QPBT-009 through the same path using the accepted gap metadata
   and A30 source-facing review.
4. Transition QPBT-003 through the same path using LPR-004/A30,
   `65315213...`, and the `fcd1aa9...` integrated gate.
5. Validate before and after each canonical state batch. Do not replay or
   modify any merged PR.

After QPBT-003 is done, **QPBT-004 and QPBT-023 may start immediately and in
parallel**, provided each receives one nonoverlapping owned worktree and exact
path scope. QPBT-004 then has both dependencies done because QPBT-024 is already
done (`workflow/state/issues.json:138`, `workflow/state/issues.json:1016`), so it
may move `planned -> ready` and begin current-main pin/cache/foundation
reconciliation. QPBT-023's sole dependency is QPBT-003
(`workflow/state/issues.json:982`), so it may move `blocked -> ready` and begin
the F01/F03/F04 signature and self-dual-basis contract work. The workflow's
ready selector is based only on explicit dependency edges, not stage completion
or parent edges (`scripts/workflow.py:1885`).

No endpoint/network request, Git write, Lean/Lake/cache command, or repository
edit was performed in this audit.
