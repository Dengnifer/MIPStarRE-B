# QPBT-024 / LPR-014 integration and singleton-warm readiness (a06)

## Verdict

**HOLD now.** At the evidence cutoff `2026-08-31T16:39:21.437060240Z`,
canonical LPR-014 is `ready`, but `reviews` and `findings` are both empty and
`requested_external_review` is false. Its exact-head checks pass, but the
QPBT-024 gate requiring a fresh independent immutable approval is open. Do not
integrate or warm yet.

Conditional GO requires one formal, independent `approve` review bound to exact
base `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe` and exact head
`9c9b49548fabdd6b01916787d7dc17a4bca36513`, imported into LPR-014 with no open
blocking findings and an `approved` transition. The reviewer cannot be the
implementer or orchestrator. Immediately before action, all SHA/topology,
dirty-scope, archive, process, and lock guards below must still pass. If any
guard differs, stop and re-audit; do not adapt the reviewed candidate.

## Immutable candidate and topology

- Canonical repository: `/home/drx/MIPStarRE-auto`, branch `main`, exact HEAD
  `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe`, tree
  `d2bfeae52ae52ef8a8bcc1f9746a1f94d6e2f48d`.
- Candidate worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-024-postbuild-a01`,
  branch `issue/qpbt-024-postbuild-a01`, clean exact HEAD
  `9c9b49548fabdd6b01916787d7dc17a4bca36513`, tree
  `a7409faf8cbd888e3f04d114332f202ea1436d11`.
- Candidate is exactly one commit ahead and zero behind. Its sole parent and
  merge base are both `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe`.
- Commit subject: `fix(cache): project package build output from source identity`.
- Exact diff: 3 modified paths, 197 insertions, 3 deletions; SHA-bound
  `git diff --check` passed in this read-only audit.

Changed blobs and SHA-256 values:

| Path | Git blob | SHA-256 |
|---|---|---|
| `scripts/materialize_lake_packages.py` | `a8380456ca97130cbc81be734f7ff9a3ecd2a128` | `3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243` |
| `tests/test_hot_main_cache.py` | `9e6a5532d6898075b1379f9e58b7b9d7fb13be68` | `235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe` |
| `tests/test_lake_package_materialization.py` | `a757022254e391bf05e25757bc433140e2abc6df` | `d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d` |

LPR-014 binds the same immutable base/head and changed paths. All seven
registered checks are `passed` on those exact SHAs: focused materializer 28/28,
focused hot cache 46/46, full serial 306/306, aggregate checker 306/306,
compileall, workflow validation, and SHA-bound diff hygiene. None was rerun in
this scout.

## Canonical dirty-state disjointness

At cutoff, the index is clean. Canonical tracked dirt is confined to:

```text
research/metrics/sessions.jsonl
workflow/events.jsonl
workflow/state/issues.json
workflow/state/prs.json
workflow/state/sessions.json
workflow/state/stages.json
```

Canonical untracked files are:

```text
workflow/reviews/qpbt-024-pr014-bind-a04.md
workflow/reviews/qpbt-024-protocol-scope-a03.md
workflow/reviews/qpbt-024-regression-matrix-a02.md
workflow/reviews/qpbt-024-source-projection-a01.md
```

Neither set intersects the three candidate paths. The coordinator changed
LPR-014 from the initially observed `draft` to `ready` during this scout; the
latest state above is authoritative for this cutoff, and still lacks review.
Capture complete porcelain status immediately before integration and require
byte-identical status afterward so the coordinator's state is preserved.

## Authenticated local inputs

All ten inputs are regular files, not symlinks. Current compressed bytes and
SHA-256 values match the committed pins/contracts.

- MIPStarRE archive:
  `/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz`, 1,989,153
  bytes, SHA-256
  `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.
  `references/mipstarre-upstream.json` has SHA-256
  `d5db77534d52be40e247715ed7bb5007b1bc89ac437d545854f6f35cebb2461b`
  and binds source commit `507e81220d95266ff3d589d125b2f87c7300a9fb`,
  decompressed tar SHA-256
  `4e4850855ac74b63cb9ef292281462174da776628a6278006f3728c9458a1d39`,
  and output inventory
  `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.
- Mathlib shallow-repository archive:
  `/tmp/mathlib-81a5d257-shallow-repo.tar.gz`, 51,938,317 bytes, SHA-256
  `c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`.
  The committed cache contract binds commit
  `81a5d257c8e410db227a6665ed08f64fea08e997`, tree
  `5ea66b811b8461daae82f14d356fed2a287d7c40`, decompressed tar SHA-256
  `ad9a60b01736070112fbc1008ea98c67e68fa045c5b69e66873e0b9444ddd3ba`,
  147,712,000 tar bytes, and pack SHA-256
  `4659f2a0cabfec474474f5e83ea3d495e711b735418742dd3d642328adcada02`.
- Lake package archive directory:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830`.
  It contains exactly eight top-level regular `*.tar.gz` files and no other
  top-level object. Hash and size comparisons against
  `references/lake-packages.json` (SHA-256
  `08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0`)
  produced empty diffs.

| Archive | Bytes | SHA-256 |
|---|---:|---|
| `Cli-88679d088c9720c27ebdf2ba4dafe17341747f94.tar.gz` | 23,877 | `e2a1d9d7c341bc6d6f9674940de6c1282ebb2fb668a677c8405c5c0039d3db26` |
| `LeanSearchClient-c5d5b8fe6e5158def25cd28eb94e4141ad97c843.tar.gz` | 12,983 | `1a86db89a695849ce06590284e6b89c5f2353e3972e60b89b9fb4127e0cfff31` |
| `Qq-38d591e778f100aec9762bb582f9c7f55f50e9dc.tar.gz` | 33,003 | `7f5c45d34799e615bf6445c3b7ef14a21c664843f14760468dafc4877ed14772` |
| `aesop-a7dbf0c63b694e47f425f3dcddbc0e178bb432d3.tar.gz` | 208,077 | `b8c00f97dac46c4b1dd64f07bb80c0963ea61ff5dd9b239414481a77c05c5908` |
| `batteries-023ce7d62a0531e22a5331e20b587817a80d49ff.tar.gz` | 349,383 | `a5066fea2fd1a311c3c95d530f07030146de3a193e86a7271ae0a6cad5241294` |
| `importGraph-7e9612bf0b9ee66db3cb5b9988a35afc706f5a12.tar.gz` | 106,222 | `c5ee93880bf68d9ae87280c77390460b8af3ee30f748cd10d098d4121ed7930c` |
| `plausible-e12c1910fe855cbfc38803cd4e55543906d5fa62.tar.gz` | 42,953 | `2825d6f3d7fc9d26151710ae643e08aabb02251bd94c476fd5217f91b59149b3` |
| `proofwidgets-6e311e2a844da9b2cc3971187df2fe0066947b93.tar.gz` | 3,896,457 | `dffb4652003f31f8e393e0f2887526ec4b6cc8244b960afa8dcbc1918b020c68` |

## Retained dba1 failure and changed identity

The retained failed-closed envelope remains at:

```text
.workflow-runtime/cache/failures/
dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276-20260831T232823-2/
```

Its 3,247-byte `failure.json` records exact main
`c0de0900a01724c2a515311424dcbe5e7526ebd4`, cache key
`dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276`,
archive-mode Mathlib authentication, and error
`Lake package verification command failed with exit code 1`. Its 39,177-byte
`build.log` is retained. There is no dba1 snapshot or READY file. Do not retry
dba1 unchanged.

The candidate changes an identity-bearing file,
`scripts/materialize_lake_packages.py`, from old SHA-256
`73bc42b1b4a33806e83ab5502f1b125eae6325f6c0d1063a80d0fa481dd245e5`
to `3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243`,
and changes the exact main commit. Recipe schema/version remain `3`/`4`.
Read-only identity computation from committed candidate blobs yields the new
post-integration key:

```text
9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36
```

No snapshot, failure envelope, or lock file exists for this key at cutoff.
This is the one permitted changed-hypothesis attempt.

## Live builder and lock observation

At cutoff, `ps -C python3,lake,lean,lean4` returned no process. `lsof` returned
no holder for any persistent `.workflow-runtime/locks/*.lock` file. Existing
zero-byte lock files for older keys and metrics are durable rendezvous files,
not evidence of an active holder. Recheck immediately before warm. The warm's
own advisory lock remains the authoritative singleton election and closes the
observation race.

## Compatibility disposition

The parallel A05 package-compatibility scout briefly raised a possible
`batteries/.lake/build.barrel{,.trace}` sibling-output blocker, then withdrew it
after tracing the pinned Lake 4.32.0 path-override flow. These authenticated
packages are materialized without `.git` and supplied through explicit path
overrides, so they cannot enter the Reservoir Git-package barrel path that
creates those siblings. The retained authenticated package archives themselves
contain no `.lake/build` boundary. On the available local evidence, no
compatibility blocker remains against the candidate's exact package-root
`.lake/build` projection. This is readiness evidence only and does not waive
the still-missing immutable approval or authorize a warm.

## Guarded integration after immutable approval

Use the existing candidate commit by fast-forward only. Do not cherry-pick,
rebase, synthesize a merge commit, or commit coordinator state first.

```bash
export QPBT_REPO_ROOT=/home/drx/MIPStarRE-auto
export QPBT_CANDIDATE_ROOT=/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-024-postbuild-a01
export QPBT_RUNTIME_DIR=/home/drx/MIPStarRE-auto/.workflow-runtime
export QPBT_BASE_SHA=38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe
export QPBT_INTEGRATED_SHA=9c9b49548fabdd6b01916787d7dc17a4bca36513
export QPBT_EXPECTED_KEY=9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36

test "$(git -C "$QPBT_REPO_ROOT" branch --show-current)" = main
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_BASE_SHA"
test "$(git -C "$QPBT_CANDIDATE_ROOT" rev-parse HEAD)" = "$QPBT_INTEGRATED_SHA"
test -z "$(git -C "$QPBT_CANDIDATE_ROOT" status --porcelain=v1 --untracked-files=all)"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse "$QPBT_INTEGRATED_SHA^")" = "$QPBT_BASE_SHA"
test "$(git -C "$QPBT_REPO_ROOT" merge-base "$QPBT_BASE_SHA" "$QPBT_INTEGRATED_SHA")" = "$QPBT_BASE_SHA"
test "$(git -C "$QPBT_REPO_ROOT" rev-list --count "$QPBT_BASE_SHA..$QPBT_INTEGRATED_SHA")" = 1
test "$(git -C "$QPBT_REPO_ROOT" rev-list --count "$QPBT_INTEGRATED_SHA..$QPBT_BASE_SHA")" = 0
test -z "$(git -C "$QPBT_REPO_ROOT" diff --cached --name-only)"
test -z "$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1 -- scripts/materialize_lake_packages.py tests/test_hot_main_cache.py tests/test_lake_package_materialization.py)"
jq -e --arg base "$QPBT_BASE_SHA" --arg head "$QPBT_INTEGRATED_SHA" '
  .pull_requests[] | select(.id == "LPR-014") |
  .status == "approved" and
  any(.reviews[];
    .formal_pr_review == true and .verdict == "approve" and
    .base_sha == $base and .head_sha == $head and
    (.finding_ids | length) == 0)
' "$QPBT_REPO_ROOT/workflow/state/prs.json" >/dev/null
python3 "$QPBT_REPO_ROOT/scripts/workflow.py" validate

QPBT_DIRTY_BEFORE="$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1 --untracked-files=all)"
git -C "$QPBT_REPO_ROOT" merge --ff-only "$QPBT_INTEGRATED_SHA"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_INTEGRATED_SHA"
test "$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1 --untracked-files=all)" = "$QPBT_DIRTY_BEFORE"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:scripts/materialize_lake_packages.py)" = a8380456ca97130cbc81be734f7ff9a3ecd2a128
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:tests/test_hot_main_cache.py)" = 9e6a5532d6898075b1379f9e58b7b9d7fb13be68
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:tests/test_lake_package_materialization.py)" = a757022254e391bf05e25757bc433140e2abc6df
git -C "$QPBT_REPO_ROOT" diff --check "$QPBT_BASE_SHA..$QPBT_INTEGRATED_SHA"
```

The root coordinator must import the approval and validate state before this
sequence. Preserve LPR-014 as approved after the physical fast-forward until
the post-integration warm and deep-inventory gate succeeds.

## Exactly one post-integration warm

First bind and reauthenticate inputs. These are guards, not warm attempts:

```bash
export QPBT_MATHLIB_ARCHIVE=/tmp/mathlib-81a5d257-shallow-repo.tar.gz
export QPBT_MIPSTARRE_ARCHIVE=/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz
export QPBT_PACKAGE_ARCHIVES=/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830

test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_INTEGRATED_SHA"
test "$(sha256sum "$QPBT_MATHLIB_ARCHIVE" | cut -d' ' -f1)" = c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7
test "$(sha256sum "$QPBT_MIPSTARRE_ARCHIVE" | cut -d' ' -f1)" = 656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc
test -d "$QPBT_PACKAGE_ARCHIVES"
test ! -L "$QPBT_PACKAGE_ARCHIVES"
test "$(find "$QPBT_PACKAGE_ARCHIVES" -mindepth 1 -maxdepth 1 -type f -name '*.tar.gz' | wc -l)" = 8
test -z "$(find "$QPBT_PACKAGE_ARCHIVES" -mindepth 1 -maxdepth 1 ! -type f -print)"
diff -u <(jq -r '.packages[] | "\(.archive.sha256)  \(.name)-\(.revision).tar.gz"' "$QPBT_REPO_ROOT/references/lake-packages.json" | sort) <(sha256sum "$QPBT_PACKAGE_ARCHIVES"/*.tar.gz | sed 's#  .*/#  #' | sort)
test -z "$(ps -C python3,lake,lean,lean4 -o pid=)"
test ! -e "$QPBT_RUNTIME_DIR/cache/main/$QPBT_EXPECTED_KEY"
test -z "$(find "$QPBT_RUNTIME_DIR/cache/failures" -maxdepth 1 -type d -name "$QPBT_EXPECTED_KEY-*" -print)"
```

Then issue this command exactly once. This is the sole changed-hypothesis warm:

```bash
env -u MATHLIB_SOURCE -u LAKE_PKG_URL_MAP \
  MATHLIB_ARCHIVE="$QPBT_MATHLIB_ARCHIVE" \
  MIPSTARRE_ARCHIVE="$QPBT_MIPSTARRE_ARCHIVE" \
  LAKE_PACKAGE_ARCHIVES="$QPBT_PACKAGE_ARCHIVES" \
  python3 "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" \
    --repo-root "$QPBT_REPO_ROOT" \
    --project-dir . \
    --runtime-dir "$QPBT_RUNTIME_DIR" \
    --main-commit "$QPBT_INTEGRATED_SHA" \
    warm
```

Expected key: `9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36`.
GO is complete only if this one command succeeds, reports an elected build or
valid hit for this exact key, publishes
`.workflow-runtime/cache/main/9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36/READY`,
and the status/deep-inventory verification binds all published artifacts.
Failure must remain failed closed with no READY and must not be retried without
newly reviewed changed evidence.

## Session accounting

- Logical session: `i024-scout-a06-integration-warm`.
- Role/topology: read-only scout under root coordinator; 0 subagents; depth 1.
- Canonical start: `2026-08-31T16:28:47.908298Z`.
- Evidence cutoff: `2026-08-31T16:39:21.437060240Z`.
- Exact elapsed through cutoff: `633.528762240` seconds.
- Repository edits, Git writes, canonical/runtime/cache mutation, network,
  project tests, builds, Lean, Lake, cache status/warm/seed: 0.
- Read-only identity derivation: 1. An initial importlib-based derivation failed
  before computation because the temporary module was not registered in
  `sys.modules`; a corrected normal module import with bytecode disabled
  produced the key above. Both attempts changed no state.
- Expected-absence probes for the new key returned nonzero because its snapshot
  and lock do not exist; this is evidence of a pristine changed hypothesis.
- Token usage: JSON `null`; reason: collaboration backend does not expose
  per-agent token usage. No estimate was made.
- Report SHA-256 is supplied out of band after finalization because embedding a
  report's own digest would change that digest.
