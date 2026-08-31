# LPR-014 immutable candidate binding audit (a04)

## Verdict

The existing QPBT-024 candidate may be adopted unchanged as LPR-014
implementer evidence. The exact clean commit, registered checks, archived
writer/scout provenance, report hashes, and active lease state are mutually
consistent. Bind archived session
`i024-orchestrator-a01-source-projection` as the implementer; do not alter the
candidate bytes, base/head SHAs, checks, or provenance reports.

This is not an approval or integration verdict. LPR-014 remains `draft` with
no reviews or findings, and still requires a fresh independent immutable
review, exact guarded integration, and exactly one changed-hypothesis
authenticated main warm with status-ready/deep-inventory evidence.

## Candidate authentication

- Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-024-postbuild-a01`
- Branch: `issue/qpbt-024-postbuild-a01`
- Worktree status: clean; `git status --short --branch` printed only the branch header.
- Base/direct sole parent: `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe`
- Base tree registered by the writer evidence: `d2bfeae52ae52ef8a8bcc1f9746a1f94d6e2f48d`
- Head: `9c9b49548fabdd6b01916787d7dc17a4bca36513`
- Head tree: `a7409faf8cbd888e3f04d114332f202ea1436d11`
- Commit subject: `fix(cache): project package build output from source identity`
- Commit topology: one parent, exactly the registered base.
- Diff scope: exactly three modified paths; no additions, deletions, renames, or extra paths.

Exact head blobs and file SHA-256 values:

```text
a8380456ca97130cbc81be734f7ff9a3ecd2a128  3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243  scripts/materialize_lake_packages.py
9e6a5532d6898075b1379f9e58b7b9d7fb13be68  235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe  tests/test_hot_main_cache.py
a757022254e391bf05e25757bc433140e2abc6df  d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d  tests/test_lake_package_materialization.py
```

## LPR-014 registration

Canonical `workflow/state/prs.json` registers LPR-014 as `draft`, base/head
`38dc1b9...`/`9c9b495...`, the same three changed paths, no reviews, no
findings, and currently an empty `implementer_session_ids` array. All seven
registered checks are `passed`, bind the exact same base/head, and cite
`workflow/reviews/qpbt-024-source-projection-a01.md`:

1. `check-qpbt-024-focused-materializer-9c9b495`
2. `check-qpbt-024-focused-hot-cache-9c9b495`
3. `check-qpbt-024-full-serial-9c9b495`
4. `check-qpbt-024-workflow-checker-9c9b495`
5. `check-qpbt-024-compileall-9c9b495`
6. `check-qpbt-024-workflow-validate-9c9b495`
7. `check-qpbt-024-diff-hygiene-9c9b495`

No check was rerun in this binding audit. The registered evidence already
records focused materializer 28/28, focused hot cache 46/46, full serial
306/306, checker 306/306, compileall passed, workflow validation passed, and
SHA-bound diff hygiene passed on the exact immutable head.

Canonical ledger hashes observed during this audit:

```text
46c64881518c23d05d2a7b87b0989de14a5a67ba0c92f3d5816ef80f59f1de42  workflow/state/prs.json
19851e2f07b582e6fc2ce14bdcb0a5af4738e3f64c84a4da879c8a37ab8454c9  workflow/state/sessions.json
```

## Provenance and child disposition

The LPR provenance list contains exactly the archived writer and its two
read-only children:

- `i024-orchestrator-a01-source-projection`: archived, exact base/head/tree,
  exact three paths, final gates passed, `nested_agents: 2`, no network,
  Lean/Lake builds, warm, seed, shared-cache mutation, or canonical-state edit.
- `i024-scout-a02-regression-matrix`: archived read-only. Its exact-boundary
  matrix was inspected and dispositioned by the writer; the final candidate
  includes the manifest and lookalike-path regressions it requested.
- `i024-scout-a03-protocol-scope`: archived read-only. Its conclusion was
  inspected and accepted: this is an implementation correction, not a
  normative protocol change; no protocol/changelog edit or separate protocol
  review is required.

Source `/tmp` and imported canonical report bytes have matching SHA-256 values:

```text
3f0bc92b995e74f2b57330d431db395c3bcc670ccafa497fcc803a664b1e4677  qpbt-024-source-projection-a01.md
2997a94dd93733bbd699393828e619bdd29366decb6a4c9c7c785be5eef6ebdc  qpbt-024-regression-matrix-a02.md
caad36e3d544878e52733100b5f66e1dcc87ad25800f3b02dee8a26e41ef4917  qpbt-024-protocol-scope-a03.md
```

## Active ownership

The canonical session ledger has no other running non-coordinator session.
After excluding the root coordinator, the complete active non-coordinator
query returns only this governed binding session, with the exact three owned
paths and issue worktree. The prior writable orchestrator and both scouts are
archived. Therefore no competing implementation/review lease overlaps the
candidate.

The persistent root coordinator is separately running as the canonical issuer
and state/metrics writer. Its broad bootstrap ownership literally names
`tests/test_hot_main_cache.py`, but it is the coordinator excluded from the
non-coordinator implementation-lease conflict calculation; dispatch recorded
`active_non_coordinator: 0` before issuing this session. No root or candidate
write was performed by this audit.

## Adoption disposition

Adopt the candidate without a new commit or rerun:

- set LPR-014 implementer evidence to the archived writer session
  `i024-orchestrator-a01-source-projection`;
- preserve the existing three provenance session IDs and seven exact-head
  checks;
- preserve LPR-014 `draft` until fresh immutable review;
- do not list this read-only binding integrator as an implementer or reviewer;
- do not authorize integration or the post-integration warm from this result.

## Session accounting

- Logical session: `i024-integrator-a04-pr014-bind`
- Role/topology: one integrator under the root coordinator; 0 subagents; depth 1
- Canonical started_at: `2026-08-31T16:25:36.339518Z`
- Evidence cutoff: `2026-08-31T16:27:14.563806156Z`
- Exact elapsed through cutoff: `98.224288156` seconds
- Read-only shell command strings: 15
- Repository edits: 0; Git index/ref changes: 0; canonical/runtime/cache actions: 0
- Tests, compileall, workflow commands, builds, warm, seed, Lean, Lake, and network actions: 0
- Subagents: 0
- One read-only `jq` selection initially used the wrong top-level PR shape and returned an error; it changed no state and was immediately corrected to `.pull_requests[]`.
- Token usage: JSON `null`; availability reason: collaboration backend does not expose per-agent token usage. No estimate was made.
- Report SHA-256: supplied out of band after finalization because embedding the report's own digest would change it.
