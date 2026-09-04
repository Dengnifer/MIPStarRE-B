# QPBT-068 Cache Safety Transaction Repair Report

Current session: `i068-orchestrator-a32-threat-boundary-repair`
Repair parent/tree: `7945323f87d6188127cf2f8a2911a2d111baaa52` /
`c92bc515a1554b606bf976b87963a81b7e8a5b1f`
Owned worktree: `.workflow-runtime/worktrees/qpbt-068-cache-safety-a05`

## Scope and authenticated inputs

A32 accepts the A29 transaction-security and A30 regression/protocol
counterexamples, narrows the operational contract to cooperating repository
agents, and adds detached-file live failure coverage. It remains in the assigned
eight-path ownership envelope and includes the required evidence-bound
`protocols/CHANGELOG.md` entry. Earlier A16, A22, and A28 sections below are
historical evidence; their broader finding language is superseded by the A32
dispositions.

The A29 report authenticated at SHA-256
`ac5174bac58233fe311dad06fe7817f9928045d45e04d5f9efbf54800f0fe9ed`,
the A30 report at
`9b49fbc42ca4406b1529783f32f2a480883fca37b291ed26bf8c3a1e0b6f8a48`,
and the A31 integration plan at
`2ab7c61b836b16169eaff16f5376a4893edf1c611cba8d2158fc452bcdec6ef0`.
All three were authenticated and read completely before editing. Read-only A32
scouts `i068-scout-a33-threat-claim-map` and
`i068-scout-a34-regression-matrix` independently mapped the wording and test
matrix and made zero repository changes.

The A26 report authenticated at SHA-256
`3a73f74fe79a5c46a22c8ecedb94889e5ee800739c48cc433c4b9571ed9060ed`,
the A27 report at
`950ab66eb780baafbe7df8d23fce2b45c2ba4a894f2fd9dc5af6e419c11363fc`,
and the A22 report at
`5d860c2eafd30acf6b23e6b4a89971f83bcb890f285186d7afdc0ae60572e9ec`.
All were authenticated and read in full before implementation. Two bounded
read-only scouts independently analyzed the write boundary and deterministic
regression seams; the orchestrator inspected both results before editing.

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
finalization. The committed tests establish rejection and preservation for
their injected schedules; the monitors do not exclude deliberately timed
same-identity operations between checks.

The authenticated foundation materializer now applies the same contract to
`MIPStarRE/`: existing output is replaced by one descriptor-bound
`RENAME_EXCHANGE`, absent output is published by `RENAME_NOREPLACE`, and
rollback reverses the exchange or retains the failed new tree. Stage,
destination, transaction, marker, and backup have exact event/content accounting
and held descriptors. Archive extraction and authored copy create every
descendant descriptor-relatively with no-follow directory handoffs;
authored-source monitors remain live through copying. Completion moves the
active transaction no-replace to unique evidence, then compares its
transaction/stage traversal records and bindings immediately before success
under the no-concurrent-writer precondition. Its held transaction inode identity
and control-object record cross the module
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
routine, refuses a module missing any required internal fail-closed operation,
and provides no lexical target fallback. Live `/proc/self/fd` evidence is
authenticated by a held no-follow descriptor chain and rewritten to the stable
worktree display path before the target binding closes.

Dry-run seed and prepare now bind without checking cache-key inputs, prove the
descriptor/inotify/filesystem/atomic-rename capability set, then rebind with
input checks and prove those capabilities again. Dry-run does not create an
`O_TMPFILE` or exercise either `linkat` route; it reports that detached-file
publication was not checked. Live failure remains fail-closed and retains
partial evidence.

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
| F068-A14-002 | Resolved for the committed schedules under cooperation: archive and authored descendants use held parent descriptors and no-follow child opens; the injected substitutions receive no bytes. Arbitrary same-identity output confinement is not claimed. |
| F068-A14-003 | Resolved: `prepare` authenticates the three-component evidence chain descriptor-relatively and returns the stable registered-worktree spelling after target teardown. |
| F068-A15-001 | Resolved: retained transaction, marker, backup, stage, and stage slot state is revalidated immediately before success; tracked current-name rollback and queued substitution/ABA regressions preserve ambiguity. |
| F068-A15-002 | Resolved: dry-run and live `prepare` share the same non-mutating materializer admission helper before dry seed or live publication, with state/interface/order regressions. |
| F068-A15-003 | Resolved: exactly five stale QPBT-067 test anchors now name their final symbols and lines. |
| A17 inner-handoff high | Resolved: staged `.lake` and both journal files are monitored before creation and authenticated before content writes. |
| A17 destination-event high | Resolved: failed and retained target names enter the appropriate monitor before atomic rename; source and destination events are consumed exactly. |
| A18 evidence-path medium | Resolved: evidence normalization authenticates a held no-follow chain before returning the stable worktree spelling. |
| A18 source-snapshot medium | Resolved for cooperating commands: authored directory monitors remain live through destination copying and final namespace rebinding. |
| A18 retained-proof medium | Resolved as repeated traversal validation: wildcard retained monitors plus marker content and transaction/stage records reject observed contamination. |
| A19 cache-descendant high | Resolved for descriptor-relative copy and tested substitutions under cooperation; reflink/fallback writes use held descriptors, without claiming same-identity access control. |
| A19 evidence-continuity medium | Resolved as cooperative evidence recomputation: the materializer returns the retained inode identity and a monitored transaction control-object record; `prepare` requires both. |
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

## A20-A21 transaction-continuity repair

The A20 transaction-security report authenticated at SHA-256
`58a3a885620bff8752d18d6f891aa14c15cada2ddf6e653e7d6ed4422382f17b`;
the A21 regression/protocol report authenticated at SHA-256
`860ef19ed6dca7f84a84b4a50ad8f09dd7bdbc3d7f5dbee47edcbd4b0e9c60ae`.
Both were read in full before this repair.

| Finding | A22 disposition and exact implementation/regression evidence |
|---|---|
| F068-A20-001 | Fixed by wildcard `staging_entry_monitor` accounting and strict `_discard_seed_rollback_root`, which authenticates the held stage binding, drains both monitors, requires an exact empty inventory, and propagates failure. `test_seed_and_prepare_reject_unexpected_final_staging_entry` injects bytes into the held inode before final disposition and requires seed/prepare failure with stage, displaced tree, and journal evidence preserved. |
| F068-A20-002 | Fixed by `_open_seed_journal_parent` and `_assert_seed_journal_ancestors`: each absolute component is opened no-follow or created descriptor-relatively below a preinstalled monitor, and all descriptors/bindings remain live through journal retention. `test_seed_and_prepare_journal_bootstrap_reject_ancestor_substitution` covers a preexisting intermediate symlink, substitution immediately before the no-follow ancestor open, and a genuine journal parent relocated after the complete handoff, symmetrically for seed/prepare; those injected schedules produce no external child writes. |
| F068-A20-003 | A22 originally used `_create_copy_output`, `_create_continuous_directory`, and `_create_continuous_file` with retained parent/self monitors. A28 supersedes the regular-file branch with `_create_detached_copy_file` and `_create_detached_output_file`: this program completes payload and metadata while `st_nlink == 0`, then makes its own link and performs no later program mutation. The five relocation regressions cover their exact early-directory and post-link-file schedules under cooperation; A29's descriptor-first link and final-check relocation schedules remain outside the supported model. |
| F068-A20-004 / F068-A21-001 | These overlap on displaced-`.lake` recursive comparison and use `_descriptor_tree_inventory` plus `_lake_tree_identity_from_descriptor` before and after no-replace retention. The parallel materializer path compares an empty wildcard-monitored backup and pre-exchange `MIPStarRE/` identity plus non-atomic recursive traversal records before publication, after exchange, in retained evidence, and across `prepare` normalization. This is cooperative validation under the no-concurrent-writer precondition, not an atomic descendant snapshot. Regressions are `test_seed_and_prepare_reject_in_place_displaced_tree_mutation`, `test_retained_backup_contamination_is_refused_and_preserved`, `test_retained_original_descendant_mutation_is_refused_and_preserved`, and `test_prepare_evidence_rejects_same_inode_staged_descendant_mutation`. |
| F068-A21-002 | Fixed by running `_recover_interrupted_seed` on dry seed and setting `check_seed_recovery=True` for dry prepare. `test_dry_and_live_seed_prepare_refuse_interrupted_state_before_admission` covers journal and target-local staging state for dry/live seed/prepare, proves capability/input admission is not reached, and byte-compares the retained state. |

The reopened prior findings are dispositioned against the same implementation
and regression evidence: F068-A14-001 is fixed for its immediate-child schedules
by the wildcard stage finalizer and root-to-leaf journal bootstrap;
F068-A14-002 and F068-A19-001 are closed for descriptor-relative handoffs and
the tested substitutions under cooperation; F068-A18-003 and F068-A19-002 are
closed as repeated retained-evidence traversal comparisons under the
no-concurrent-writer precondition. No atomic recursive snapshot or arbitrary
same-identity confinement is claimed. Only an independent review may mark these
findings resolved in the workflow ledger.

## A26-A27 final-boundary repair

| Finding | A28 disposition and exact evidence |
|---|---|
| F068-A26-001 | Closed only for this program's write order under cooperation, not as an access-control repair. Cache, archive, and authored regular outputs are populated and fsynced as zero-link `O_TMPFILE` inodes before this program makes its own descriptor-relative `linkat`; no later program mutation follows. `test_cache_reflink_has_zero_links_before_program_publication` covers the FICLONE schedule. A29-001/002 demonstrate excluded descriptor-first-link and ancestor-relocation schedules. |
| F068-A26-002 | Closed as repeated cooperative traversal checks. Staging and retained-backup checks run after target refresh/fsync; direct materializer evidence is recomputed after result construction; prepare normalization repeats traversal and binding checks. The cited regressions cover their injected schedules, but recursive results are non-atomic and require no concurrent mutation. |
| F068-A26-003 | Closed for participating commands. Dry seed and dry prepare acquire the same per-target `ExclusiveLock` as live operations; `_dry_seed_locked` avoids recursive lock acquisition during dry prepare. `test_dry_seed_holds_target_lock_through_admission` proves competing cooperative admission cannot acquire the lock until dry admission exits. |
| F068-A27-001 | Closed only for aliases present when a regular file is visited under cooperation. Repeated prepublication, postpublication, postcommit, and final-result traversals require `st_nlink == 1`. `test_post_copy_cache_hard_link_is_rejected_before_seed_publication` and `test_post_population_archive_and_authored_hard_links_prevent_publication` cover post-population aliases; no claim is made for an alias inserted after a nested file's visit. |

Under the A32 boundary, F068-A14-002, F068-A19-001, and F068-A20-003 are closed
only for descriptor-relative operations and the reported regression schedules
under cooperation; the universal output-confinement claim is withdrawn.
F068-A14-001 and F068-A20-001 close at their immediate-child wildcard gates.
F068-A18-003, F068-A19-002, F068-A20-004, and F068-A21-001 close as repeated
cooperative traversal comparisons, not atomic snapshots. F068-A21-002 is
serialized for participating commands. Independent immutable review, not this
implementer record, decides canonical closure.

## A29-A30 threat-boundary and capability repair

The normative threat model is cooperating repository agents plus accidental,
non-adversarial races. The owner holds the per-target lock; other participating
commands do not mutate its source, target, staging, transaction, or retained
evidence. Inotify and descriptor-relative checks detect observed interference
but do not provide Linux access control. An actively malicious same-identity
process with `/proc/<pid>/fd`, `ptrace`, `pidfd_getfd`, inherited or in-process
descriptors, or deliberately timed rename/link/write operations is excluded.

| Finding | A32 disposition |
|---|---|
| F068-A29-001 | **Counterexample accepted; stronger claim withdrawn.** The code is not claimed to prevent a same-identity process from linking a producer descriptor before a later write. The supported claim is only this program's zero-link population, own-link, and no-later-write order. |
| F068-A29-002 | **Counterexample accepted; stronger claim withdrawn.** The code is not claimed to prevent deliberate ancestor relocation between a check and recursion or `linkat`. The committed earlier relocation schedules remain regression evidence under cooperation. |
| F068-A30-001 | **Counterexample accepted; exact-snapshot claim withdrawn.** Recursive inventories are non-atomic monitored traversal records under the no-concurrent-writer precondition. Descendant authority is released as traversal returns; no simultaneous terminal filesystem snapshot is claimed. |
| F068-A30-002 | **Repaired by truthful dry semantics and live fail-closed coverage.** Dry output records `detached_file_publication_checked: false`. Cache and direct-materializer regressions inject `O_TMPFILE` refusal and ordered failure of direct `AT_EMPTY_PATH` plus `/proc/self/fd` `linkat`, require public domain errors, preserve the existing destination, and retain partial evidence. |

The scoped prior dispositions are: F068-A26-001 closes only for this program's
write order; F068-A26-002, F068-A18-003, F068-A19-002, F068-A20-004, and
F068-A21-001 close as repeated cooperative traversal comparisons;
F068-A27-001 closes only for aliases present when visited; F068-A14-002,
F068-A19-001, and F068-A20-003 close only for descriptor-relative operations
and their tested schedules under cooperation. F068-A14-001 and F068-A20-001
close at immediate-child wildcard checkpoints. F068-A26-003 and F068-A21-002
close for advisory-lock serialization and interrupted-state refusal among
participating commands. None of these dispositions reinstates adversarial
same-identity confinement or an atomic recursive snapshot.

## A32 validation

| Command | Result (suite-reported time) | Process wall time |
|---|---|---:|
| `python3 -m unittest discover -s tests -p test_mipstarre_materialization.py` | 36/36 passed (7.816 s) | 8.56 s |
| `python3 -m unittest discover -s tests -p test_hot_main_cache.py` | 145/145 passed (96.245 s) | 96.93 s |
| `python3 -m unittest discover -s tests -p test_workflow.py` | 77/77 passed (1.525 s) | 2.54 s |
| `python3 -m unittest discover -s tests -p test_check_workflow.py` | 3/3 passed (0.004 s) | 0.57 s |
| `python3 scripts/workflow.py validate` | valid: 69 issues, 34 PRs, 541 issued sessions, 7 stages | 0.40 s |
| `PYTHONPYCACHEPREFIX=/tmp/i068-a32-pycache python3 -m compileall -q` on the two scripts and two test files | passed with no worktree bytecode | 0.27 s |
| `python3 scripts/check_workflow.py` outside the socket-restricted sandbox | 468/468 passed (388.230 s) | 388.76 s |
| Parent/cumulative `git diff --check`, exact eight-path scope, and five QPBT-067 anchors | passed | below timer resolution |

The first focused cache dry-run check reported four passes and one harness
error: the prepare side effect captured the target before the lock directory
changed the admitted parent generation. Binding inside the existing
`_admit_prepare_target` side effect fixed the owned test harness; the focused
rerun passed 5/5 in 1.005 seconds and the production code was unchanged. The
direct-materializer live-failure focus passed 3/3 in 0.374 seconds.

The first exact aggregate checker run executed inside the managed sandbox and
reported 466 passes plus two errors after 428.840 seconds: both pre-existing
lake-package safety tests received `EPERM` while binding Unix-domain sockets.
The authorized rerun outside that socket restriction passed all 468 tests as
recorded above. An exploratory claim search also used shell-sensitive quoting
once, producing a harmless `(: command not found` diagnostic before the search
was repeated with literal quoting. Neither incident changed repository files.
No production cache warm/seed/prepare, Lake, Lean, build, network, GitHub,
canonical workflow-state, or research-metric operation ran.

## A28 validation

| Command | Result (suite-reported time) | Process wall time |
|---|---|---:|
| `python3 -m unittest discover -s tests -p test_mipstarre_materialization.py` | 34/34 passed (6.719 s) | 6.86 s |
| `python3 -m unittest discover -s tests -p test_hot_main_cache.py` | 143/143 passed (98.165 s) | 98.40 s |
| `python3 -m unittest discover -s tests -p test_workflow.py` | 77/77 passed (1.184 s) | 1.32 s |
| `python3 -m unittest discover -s tests -p test_check_workflow.py` | 3/3 passed (0.003 s) | 0.11 s |
| `python3 scripts/workflow.py validate` | valid: 69 issues, 34 PRs, 541 issued sessions, 7 stages | 0.21 s |
| `python3 scripts/check_workflow.py --skip-tests` | workflow state valid | 0.21 s |
| `PYTHONPYCACHEPREFIX=/tmp/... python3 -m compileall -q` on the four changed Python files | passed with no worktree bytecode | 0.31 s |
| Parent/cumulative `git diff --check`, exact eight-path scope, and five QPBT-067 anchors | passed | below timer resolution |

The first cache-suite run after narrowing `_create_copy_output` to its only
production use reported 142 passes and one test-harness error because the
relocation monkeypatch retained the deleted `directory` keyword. Updating that
owned regression to the directory-only signature produced the clean complete
rerun above. No production cache, Lean, Lake, build, network, canonical-state,
or research-metric operation ran.

## A22 validation (historical)

| Command | Result (suite-reported time) | Process wall time |
|---|---|---:|
| `python3 -m unittest discover -s tests -p 'test_mipstarre_materialization.py'` | 32/32 passed (5.080 s) | 5.22 s |
| `python3 -m unittest discover -s tests -p 'test_hot_main_cache.py'` | 137/137 passed (81.736 s) | 81.97 s |
| `python3 -m unittest discover -s tests -p 'test_workflow.py'` | 77/77 passed (1.385 s) | 1.50 s |
| `python3 -m unittest discover -s tests -p 'test_check_workflow.py'` | 3/3 passed (0.012 s) | 0.08 s |
| `python3 scripts/check_workflow.py --skip-tests` | workflow state valid | 0.19 s |
| `python3 scripts/workflow.py validate` | valid: 69 issues, 34 PRs, 541 issued sessions, 7 stages | 0.20 s |
| Built-in `compile(...)`, `git diff --check`, seven-path scope, and exact anchor checks | passed | below timer resolution |

No aggregate suite was needed: both complete owned suites and the complete
workflow/checker unit suites passed. No Lean/Lake/full build, real cache
warm/seed/prepare, network, GitHub, credential, endpoint, canonical
workflow-state, or research-metric action ran.

## A16 validation (historical)

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
cache copy; A16 and A22 likewise create no real cache copy and delete neither tree.
QPBT-069 remains an active lease. After independent review, a separately
authorized reclamation pass may dry-run the
archived QPBT-040 tree, but only after proving terminal session state, no Git
registration, no live lock/reference/lease, and an authenticated source cache;
quarantine plus the configured grace interval and a repeated final check must
precede deletion.

This A32 candidate includes the evidence-required sequential
`protocols/CHANGELOG.md` entry and still requires a fresh immutable
security/regression review. It is not integration-ready until that gate is
recorded against the frozen A32 commit.
