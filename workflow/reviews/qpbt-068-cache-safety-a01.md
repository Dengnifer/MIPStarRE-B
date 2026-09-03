# QPBT-068 Cache Safety Transaction Repair Report

Current session: `i068-orchestrator-a16-retention-monitor`
Repair parent/tree: `913766cf3f69b2c5f4135827ec9a7ab31e6c8fba` /
`6f34fbef431400a71b21ceecff1d55686cef4ea4`
Owned worktree: `.workflow-runtime/worktrees/qpbt-068-cache-safety-a04`

## Scope and authenticated inputs

A16 repairs the A14 materializer/cache security findings and A15 regression and
protocol findings while reauditing every earlier closure. The repair remains in
the assigned seven-path ownership envelope and does not edit `protocols/CHANGELOG.md`;
that remains a sequential binder obligation before integration.

The two required A16 review artifacts authenticated before implementation:

- A14: `/tmp/i068-reviewer-a14-materializer-transaction.md`, SHA-256
  `aa34a96601db9afd5b631d202c011598bc853cc81c8c17ad1060ffa41d4b549e`.
- A15: `/tmp/i068-reviewer-a15-regression.md`, SHA-256
  `d82f2cff9dad418bd2162db5d51963d9644b6d6f42b36f4e7b5cf5ffa8508214`.

Two bounded read-only A16 scouts independently audited the live repair. A17's
cache-event report authenticated as
`94aa8cacce3bd371e0bb4ee4f8475816950601b57bfb7703f858169861be179a`;
A18's materializer/descriptor report authenticated as
`6ce078488171daba72726a2bfd44f47748fed5eaa9dc9903f8d8e953323ccd7a`.
A19's final non-approving regression/security audit authenticated as
`87e9c4756090f5dfb36e17c2404b3b300a5540f9abb2af241b706c70cb28fc9c`.

## Transaction contract

Seed and prepare now require Linux `renameat2`, inotify, descriptor-relative
operations, a conservatively approved local filesystem, and a successful
same-device semantic probe before input/cache admission or target mutation.
The uniquely named probe tree is retained instead of recursively deleted.
Non-replacement publication is one `RENAME_NOREPLACE`; replacement
is one `RENAME_EXCHANGE`, so a crash cannot expose an absent destination and a
concurrent destination is never replaced. There is no ordinary-rename
fallback.

The target monitor binds every ancestor root-to-leaf, installs each parent
watch before opening its child, holds all descriptors, and remains poisoned by
any protected rename, substitution, invalidation, malformed/unknown event, or
ABA. Live Git registration and the initially captured worktree `HEAD` are
rechecked before publication, around metric commit and finalization, and before
return. Rollback, old-tree retention, journal retention, failed-tree retention,
and empty-staging finalization use continuously held object descriptors plus
atomic exchange/no-replace. Seed/prepare never recursively delete transaction
objects and no longer unlink or `rmdir` live journal/staging names; successful
finalization moves them to unique retained evidence names. The journal files,
outer staging root, and staged `.lake` child cross exact create/open/drain
handoffs before their first write. Derived failed and retained destinations are
added to the responsible monitor before rename, so both move events are
consumed. Cache descendants are created and copied through held parent/file
descriptors with no-follow handoffs for both reflink and byte-copy operation.
Readable journal descriptors, exact retained bytes, `IN_MODIFY`, the journal's
own move event, and final drains bind the diagnostic evidence through
finalization. A last-instant substitution can therefore only be preserved or
moved intact before failure.

The authenticated foundation materializer now applies the same contract to
`MIPStarRE/`: existing output is replaced by one descriptor-bound
`RENAME_EXCHANGE`, absent output is published by `RENAME_NOREPLACE`, and
rollback reverses the exchange or retains the failed new tree. Stage,
destination, transaction, marker, and backup have exact event/content accounting
and held descriptors. Archive extraction and authored copy create every
descendant descriptor-relatively with no-follow directory handoffs;
authored-source monitors remain live through copying. Completion moves the
active transaction no-replace to unique evidence, then rechecks its exact
transaction/stage inventories and bindings immediately before success. Its held
transaction inode identity and exact control-object inventory cross the module
return boundary, so `prepare` rejects a real-directory decoy as well as a
symlink. There is no recursive deletion or ordinary-rename publication,
rollback, or cleanup path; ambiguous objects remain preserved.

Every fixed seed journal, backup, or active staging object on a later invocation
causes refusal before cache/input admission. The dead seed-journal recovery
parser was removed. Prepare likewise rejects a materializer transaction or
cleanup tombstone before archive/cache admission and immediately before
invocation. Dry-run executes the same non-mutating materializer-state, archive,
target-module, pin, validation, and interface sequence before delegated dry
seed. The bound adapter never delegates to the legacy persisted recovery
routine, refuses a module missing any required private fail-closed operation,
and provides no lexical target fallback. Live `/proc/self/fd` evidence is
authenticated by a held no-follow descriptor chain and rewritten to the stable
worktree display path before the target binding closes.

Dry-run seed and prepare now bind without checking cache-key inputs, prove the
atomic capability set, then rebind with input checks and prove capabilities
again. The capability gate therefore precedes identity, archive, and cache
admission on dry and live paths.

## Finding dispositions

| Finding | A16 disposition |
|---|---|
| F068-A08-001 | Resolved: materializer recovery state is refused before admission and again before invocation; adapted `_recover` never parses or delegates persisted recovery. |
| F068-A08-002 / A09 atomic-publication blocker | Resolved: capability-gated `RENAME_NOREPLACE` and `RENAME_EXCHANGE`, with no ordinary fallback and crash/collision regressions for seed and prepare. |
| F068-A08-003 / A09 live-cleanup blocker | Resolved conservatively: rollback and retention are descriptor-bound object-preserving atomic moves; journal and staging finalization retain instead of deleting. Substitution/collision/ABA preserves every candidate. |
| F068-A08-004 / A09 Git blocker | Resolved: `_assert_seed_target_registered` performs a fresh eligibility/Git query and compares project, worktree, parent, and initial `HEAD` bindings at every live barrier. |
| F068-A08-005 | Resolved: the QPBT-067 report uses final A16 symbol/line anchors and labels them pre-commit until the terminal identity envelope. |
| A09 ancestor-ABA blocker | Resolved: root-to-leaf held-descriptor inotify construction observes setup-time and live ancestor changes; poison is permanent. |
| A09 materializer-fallback blocker | Resolved: incomplete materializers fail before seed allocation/publication for both replace modes; no lexical fallback is reachable. |
| A09 regression-evidence high | Resolved: the hostile matrix is symmetric where applicable, metadata snapshots include root/entries, type, link text, mode, size, device, inode, link count, digest, and payload, and exact metric bytes remain separately checked. |
| F068-A11-001 | Resolved: live foundation publication, rollback, and transaction retention use held descriptors, exact permanent name monitors, and atomic exchange/no-replace only; cleanup is preserve-only. |
| F068-A12-001 | Resolved: dry-run gates capabilities before identity, archive, cache-status, or cache-key admission; the regression covers seed/prepare and dry/live combinations. |
| F068-A14-001 | Resolved: all outer and inner staging/journal creations use exact event batches, immediate descriptors, binding checks, and post-open drains; all live mutation sites consume exact batches. |
| F068-A14-002 | Resolved: archive and authored descendants are created through held parent descriptors and no-follow child opens; substitution regressions prove external targets receive no bytes. |
| F068-A14-003 | Resolved: `prepare` authenticates the three-component evidence chain descriptor-relatively and returns the stable registered-worktree spelling after target teardown. |
| F068-A15-001 | Resolved: retained transaction, marker, backup, stage, and stage slot state is revalidated immediately before success; tracked current-name rollback and queued substitution/ABA regressions preserve ambiguity. |
| F068-A15-002 | Resolved: dry-run and live `prepare` share the same non-mutating materializer admission helper before dry seed or live publication, with state/interface/order regressions. |
| F068-A15-003 | Resolved: exactly five stale QPBT-067 test anchors now name their final symbols and lines. |
| A17 inner-handoff high | Resolved: staged `.lake` and both journal files are monitored before creation and authenticated before content writes. |
| A17 destination-event high | Resolved: failed and retained target names enter the appropriate monitor before atomic rename; source and destination events are consumed exactly. |
| A18 evidence-path medium | Resolved: evidence normalization authenticates a held no-follow chain before returning the stable worktree spelling. |
| A18 source-snapshot medium | Resolved: authored directory monitors remain live through destination copying and final namespace rebinding. |
| A18 retained-proof medium | Resolved: wildcard retained monitors plus exact marker content and transaction/stage inventories reject contamination. |
| A19 cache-descendant high | Resolved: source and destination recursion is descriptor-relative; child directories and files use no-follow create/open/drain handoffs, and reflink/fallback writes use held file descriptors. |
| A19 evidence-continuity medium | Resolved: the materializer returns the retained inode identity and exact transaction control-object inventory captured under live monitors; `prepare` requires both. |
| A19 journal-integrity medium | Resolved: readable held descriptors, expected bytes, `IN_MODIFY`, exact self-move consumption, post-retention rebinding, content verification, and final drains cover journal finalization. |
| A19 transaction-document medium | Resolved: the wildcard transaction monitor precedes `transaction.json` creation and consumes exact create/modify events around the first write. |
| A19 validation-timing low | Resolved: the validation table separates suite-reported duration from measured process wall time. |

### A14-A19 regression mapping

| Finding | Deterministic regression evidence |
|---|---|
| F068-A14-001 | `test_seed_and_prepare_reject_created_staging_and_journal_substitution`; `test_seed_and_prepare_reject_inner_staging_and_journal_file_handoffs` |
| F068-A14-002 | `test_archive_descendant_substitution_cannot_receive_output_bytes`; `test_authored_descendant_substitution_cannot_receive_output_bytes` |
| F068-A14-003 | `test_prepare_returns_stable_materializer_evidence_after_target_close`; `test_prepare_evidence_normalization_rejects_descendant_symlink_swap` |
| F068-A15-001 | `test_queued_stage_substitution_after_retention_prevents_success`; `test_queued_stage_slot_aba_after_retention_prevents_success` |
| F068-A15-002 | `test_dry_prepare_runs_materializer_admission_before_delegated_seed`; `test_dry_prepare_refuses_materializer_state_and_interface_before_seed` |
| F068-A15-003 | Exact `rg -n` anchor audit for the five QPBT-067 references. |
| A17 inner handoffs | `test_seed_and_prepare_reject_inner_staging_and_journal_file_handoffs` |
| A17 move destinations | `test_seed_interruption_immediately_after_publication_restores_original`; `test_committed_backup_swap_restore_aba_fails_before_retention` |
| A18 evidence path | `test_prepare_returns_stable_materializer_evidence_after_target_close`; `test_prepare_evidence_normalization_rejects_descendant_symlink_swap` |
| A18 source snapshot | `test_authored_source_namespace_substitution_prevents_publication` |
| A18 retained proof | `test_retained_marker_and_unexpected_stage_child_prevent_success`; both queued post-retention regressions above. |
| A19 cache descendants | `test_seed_copy_rejects_descendant_symlink_before_external_write` |
| A19 evidence continuity | `test_prepare_evidence_normalization_rejects_real_directory_replacement` |
| A19 journal integrity | `test_retained_journal_modification_prevents_success` (journal and commit-marker subtests) |
| A19 transaction document | `test_transaction_document_creation_aba_is_detected_before_write` |

## Validation

| Command | Result (suite-reported time) | Process wall time |
|---|---|---:|
| `python3 tests/test_mipstarre_materialization.py` | 26/26 passed (3.195 s) | 3.32 s |
| `python3 tests/test_hot_main_cache.py` | 131/131 passed (65.295 s) | 65.48 s |
| `python3 tests/test_workflow.py` | 77/77 passed (1.224 s) | 1.35 s |
| `python3 tests/test_check_workflow.py` | 3/3 passed (0.009 s) | 0.08 s |
| `python3 scripts/check_workflow.py --skip-tests` | workflow state valid | 0.19 s |
| `python3 -m compileall -q scripts tests` | passed | 0.03 s |
| `python3 scripts/workflow.py validate` | valid: 69 issues, 34 PRs, 541 issued sessions, 7 stages | 0.21 s |
| `git diff --check` and seven-path scope check | passed | below timer resolution |

No aggregate suite was needed: both complete owned suites and the complete
workflow/checker unit suites passed. Commit/tree/patch/report identities are
recorded in the terminal A16 orchestration report after this canonical report
is frozen. Retained evidence growth and dependence on the admitted Linux
rename/inotify semantics remain explicit non-blocking risks.

No Lean/Lake/full build, real cache warm/seed/prepare, network, GitHub,
credential, endpoint, canonical workflow-state, or research-metric action ran.

## Capacity and remaining gates

A coordinator read-only check on 2026-09-04 observed 97% filesystem utilization
with 164 GB free. Archived QPBT-040 and active QPBT-069 each hold a separate
approximately 9.8 GB `.lake` after reflink was unsupported. A13 created no
cache copy; A16 likewise creates no real cache copy and deletes neither tree.
QPBT-069 remains an active lease. After
independent review, a separately authorized reclamation pass may dry-run the
archived QPBT-040 tree, but only after proving terminal session state, no Git
registration, no live lock/reference/lease, and an authenticated source cache;
quarantine plus the configured grace interval and a repeated final check must
precede deletion.

This A16 candidate still requires a fresh immutable security/regression review,
the existing QPBT-062 evidence inclusion gate, and the sequential
`protocols/CHANGELOG.md` binder. It is not integration-ready until those gates
are recorded against the frozen A16 commit.
