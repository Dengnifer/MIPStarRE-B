# QPBT-025 / LPR-015 integration-readiness runbook (a05)

## Verdict and findings

1. **BLOCKER at the evidence cutoff:** do not integrate or warm now.
   Canonical LPR-015 is `ready`, its `reviews` array is empty, and it has no
   immutable formal approval. QPBT-025 remains `review`. The conditional
   runbook below becomes authorized only after a fresh independent reviewer
   approves exact base `45d2fe657af587e8e10952aced2e156d349fd65e` and exact
   head `d73cce44d5f9f37d38ee8d916811719408818c03`, root imports that
   review, transitions LPR-015 to `approved`, and validates canonical state.
2. **No immutable-candidate or dirty-scope blocker found.** Candidate HEAD is
   clean, has tree `8a8985252eb019282ab6ef1842ce1b9178a58c07`, and is the
   direct one-commit child of the exact base. Its SHA-bound diff has exactly
   the four LPR-bound paths and `git diff --check` is clean. Main is still on
   the exact base. Its root-owned state/metrics/review dirt is wholly disjoint
   from those four paths, and its index is clean.
3. **No live-build/cache blocker was observed, with a race caveat.** The
   recipe-v5 identity for the exact candidate is
   `5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266`.
   No snapshot, failure envelope, or lock file exists for that key. No matching
   warm/seed/Lake-build/Lean process and no kernel-reported lock holder was
   present. This is a point-in-time observation; re-run the non-mutating guards
   immediately before the warm. The warm's own per-key `fcntl` lock is the
   authoritative singleton election.

The root coordinator independently supplied a read-only exact-head `status`
observation with all warm input environment variables unset: the same key,
recipe version 5, recipe schema 3, the exact flagged verifier argv, and
`status: "miss"`, with no matching snapshot/failure/lock path. This was not a
warm and was not executed by this scout.

## Frozen facts

- Canonical root: `/home/drx/MIPStarRE-auto`, branch `main`, HEAD
  `45d2fe657af587e8e10952aced2e156d349fd65e`, tree
  `07df5125163a5bdddd1b80549cf622f8a0a628cd`.
- Candidate root:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-025-sidecar-a01`,
  branch `issue/qpbt-025-sidecar-a01`, clean HEAD
  `d73cce44d5f9f37d38ee8d916811719408818c03`, tree
  `8a8985252eb019282ab6ef1842ce1b9178a58c07`, sole parent/base
  `45d2fe657af587e8e10952aced2e156d349fd65e`.
- Ahead/behind relative to base: `1` / `0`; merge base is the exact base.
- Diff: 4 files, 1,252 insertions, 45 deletions; exact paths:
  `scripts/hot_main_cache.py`, `scripts/materialize_lake_packages.py`,
  `tests/test_hot_main_cache.py`, and
  `tests/test_lake_package_materialization.py`.
- Candidate blobs / SHA-256:
  - `scripts/hot_main_cache.py`: Git `d434e4045319203c028406baf165aa9808637cf3`,
    SHA-256 `07e9551eb64fb90cdcf99bb0b9cd667b74122677e6381788a6728fa696f0bb35`.
  - `scripts/materialize_lake_packages.py`: Git
    `2324d054b3880597a916d48c2f6f63f2b4325385`, SHA-256
    `54e1aeb538b0b189c7f7ba1dc7461930626ded3194fb5e3289dfb4b84f04e2c4`.
  - `tests/test_hot_main_cache.py`: Git
    `5e2f1c2aa1c3fbbd5412186a3bf40c5ed46fe6d1`, SHA-256
    `d46c6dc68cbbacec1c2b8542467c6ce044ffe00fbcca5f9af93b36f6bd905b09`.
  - `tests/test_lake_package_materialization.py`: Git
    `d6cfa5dc97feeb7b4af6f88ba9ad528e4d9f9ec9`, SHA-256
    `37201c189e15949776c07f11ed6a94a1f91fa3f4d9687c4a852ff4198da23140`.
- Main's observed root-owned dirt at cutoff was:

```text
 M research/metrics/sessions.jsonl
 M workflow/events.jsonl
 M workflow/state/issues.json
 M workflow/state/prs.json
 M workflow/state/sessions.json
 M workflow/state/stages.json
?? workflow/reviews/qpbt-025-scout-a02-sidecar-security.md
?? workflow/reviews/qpbt-025-scout-a03-sidecar-tests.md
?? workflow/reviews/qpbt-025-sidecar-removal-a01.md
```

The approval import will legitimately change this root-owned set. Therefore
the operational guard does not hard-code the list: it requires an empty index,
zero dirt on the four candidate paths, captures the complete root status after
approval, and requires it to remain byte-for-byte identical across the
fast-forward.

## Exact guarded integration

Run in Bash only after the approval prerequisite above is satisfied. Stop at
the first failed assertion; do not adapt, cherry-pick, rebase, merge-commit, or
commit coordinator state before the physical fast-forward.

```bash
set -euo pipefail

export QPBT_REPO_ROOT=/home/drx/MIPStarRE-auto
export QPBT_CANDIDATE_ROOT=/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-025-sidecar-a01
export QPBT_RUNTIME_DIR=/home/drx/MIPStarRE-auto/.workflow-runtime
export QPBT_BASE_SHA=45d2fe657af587e8e10952aced2e156d349fd65e
export QPBT_HEAD_SHA=d73cce44d5f9f37d38ee8d916811719408818c03
export QPBT_HEAD_TREE=8a8985252eb019282ab6ef1842ce1b9178a58c07
export QPBT_EXPECTED_KEY=5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266

test "$(git -C "$QPBT_REPO_ROOT" branch --show-current)" = main
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_BASE_SHA"
test "$(git -C "$QPBT_CANDIDATE_ROOT" rev-parse HEAD)" = "$QPBT_HEAD_SHA"
test "$(git -C "$QPBT_CANDIDATE_ROOT" rev-parse 'HEAD^{tree}')" = "$QPBT_HEAD_TREE"
test "$(git -C "$QPBT_CANDIDATE_ROOT" rev-parse HEAD^)" = "$QPBT_BASE_SHA"
test -z "$(git -C "$QPBT_CANDIDATE_ROOT" status --porcelain=v1 --untracked-files=all)"
test "$(git -C "$QPBT_REPO_ROOT" merge-base "$QPBT_BASE_SHA" "$QPBT_HEAD_SHA")" = "$QPBT_BASE_SHA"
test "$(git -C "$QPBT_REPO_ROOT" rev-list --count "$QPBT_BASE_SHA..$QPBT_HEAD_SHA")" = 1
test "$(git -C "$QPBT_REPO_ROOT" rev-list --count "$QPBT_HEAD_SHA..$QPBT_BASE_SHA")" = 0
test -z "$(git -C "$QPBT_REPO_ROOT" diff --cached --name-only)"
test -z "$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1 --untracked-files=all -- scripts/hot_main_cache.py scripts/materialize_lake_packages.py tests/test_hot_main_cache.py tests/test_lake_package_materialization.py)"
test "$(git -C "$QPBT_REPO_ROOT" diff --name-only "$QPBT_BASE_SHA..$QPBT_HEAD_SHA")" = "$(printf '%s\n' scripts/hot_main_cache.py scripts/materialize_lake_packages.py tests/test_hot_main_cache.py tests/test_lake_package_materialization.py)"
git -C "$QPBT_REPO_ROOT" diff --check "$QPBT_BASE_SHA..$QPBT_HEAD_SHA"

jq -e --arg base "$QPBT_BASE_SHA" --arg head "$QPBT_HEAD_SHA" '
  .pull_requests[] | select(.id == "LPR-015") |
  .status == "approved" and
  .base_sha == $base and .head_sha == $head and
  .integration_sha == null and .merged_at == null and
  (.findings | length) == 0 and
  any(.reviews[];
    .formal_pr_review == true and .verdict == "approve" and
    .base_sha == $base and .head_sha == $head and
    (.finding_ids | length) == 0)
' "$QPBT_REPO_ROOT/workflow/state/prs.json" >/dev/null
python3 "$QPBT_REPO_ROOT/scripts/workflow.py" validate

QPBT_DIRTY_BEFORE="$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1 --untracked-files=all)"
git -C "$QPBT_REPO_ROOT" merge --ff-only "$QPBT_HEAD_SHA"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_HEAD_SHA"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse 'HEAD^{tree}')" = "$QPBT_HEAD_TREE"
test "$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1 --untracked-files=all)" = "$QPBT_DIRTY_BEFORE"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:scripts/hot_main_cache.py)" = d434e4045319203c028406baf165aa9808637cf3
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:scripts/materialize_lake_packages.py)" = 2324d054b3880597a916d48c2f6f63f2b4325385
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:tests/test_hot_main_cache.py)" = 5e2f1c2aa1c3fbbd5412186a3bf40c5ed46fe6d1
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:tests/test_lake_package_materialization.py)" = d6cfa5dc97feeb7b4af6f88ba9ad528e4d9f9ec9
git -C "$QPBT_REPO_ROOT" diff --check "$QPBT_BASE_SHA..$QPBT_HEAD_SHA"
```

Keep LPR-015 `approved` with null integration metadata after this physical
fast-forward. Do not mark either PR merged or either issue done before the
singleton warm and all post-warm checks succeed.

## Pre-warm guards and exactly one warm

These guards are read-only and are not warm attempts. They require the new key
to remain pristine and authenticate all local inputs. A persistent zero-byte
lock file is not itself a holder, but for this never-attempted key even the
lock file must still be absent. `lslocks` checks the kernel lock table without
opening or creating the rendezvous file.

```bash
export QPBT_MATHLIB_ARCHIVE=/tmp/mathlib-81a5d257-shallow-repo.tar.gz
export QPBT_MIPSTARRE_ARCHIVE=/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz
export QPBT_PACKAGE_ARCHIVES=/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830
export QPBT_KEY_LOCK="$QPBT_RUNTIME_DIR/locks/hot-main-$QPBT_EXPECTED_KEY.lock"

test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_HEAD_SHA"
test -f "$QPBT_MATHLIB_ARCHIVE"
test ! -L "$QPBT_MATHLIB_ARCHIVE"
test "$(sha256sum "$QPBT_MATHLIB_ARCHIVE" | cut -d' ' -f1)" = c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7
test -f "$QPBT_MIPSTARRE_ARCHIVE"
test ! -L "$QPBT_MIPSTARRE_ARCHIVE"
test "$(sha256sum "$QPBT_MIPSTARRE_ARCHIVE" | cut -d' ' -f1)" = 656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc
test -d "$QPBT_PACKAGE_ARCHIVES"
test ! -L "$QPBT_PACKAGE_ARCHIVES"
test "$(find "$QPBT_PACKAGE_ARCHIVES" -mindepth 1 -maxdepth 1 -type f -name '*.tar.gz' | wc -l)" = 8
test -z "$(find "$QPBT_PACKAGE_ARCHIVES" -mindepth 1 -maxdepth 1 ! -type f -print)"
diff -u <(jq -r '.packages[] | "\(.archive.sha256)  \(.name)-\(.revision).tar.gz"' "$QPBT_REPO_ROOT/references/lake-packages.json" | sort) <(sha256sum "$QPBT_PACKAGE_ARCHIVES"/*.tar.gz | sed 's#  .*/#  #' | sort)

QPBT_DERIVED_KEY="$(PYTHONDONTWRITEBYTECODE=1 python3 -c 'import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1] + "/scripts"); from hot_main_cache import CacheIdentity, CANONICAL_BUILD_RECIPE; print(CacheIdentity.create(Path(sys.argv[1]), Path(sys.argv[1]), CANONICAL_BUILD_RECIPE, main_commit=sys.argv[2]).cache_key)' "$QPBT_REPO_ROOT" "$QPBT_HEAD_SHA")"
test "$QPBT_DERIVED_KEY" = "$QPBT_EXPECTED_KEY"
test ! -e "$QPBT_RUNTIME_DIR/cache/main/$QPBT_EXPECTED_KEY"
test -z "$(find "$QPBT_RUNTIME_DIR/cache/failures" -maxdepth 1 -type d -name "$QPBT_EXPECTED_KEY-*" -print)"
test ! -e "$QPBT_KEY_LOCK"
test -z "$(lslocks --noheadings --output PATH | awk -v path="$QPBT_KEY_LOCK" '$1 == path { print }')"
if ps -eo args= | rg -q '[h]ot_main_cache\.py.*(warm|seed)|[l]ake .*build|[l]ean(4)? '; then
  echo 'refusing warm: relevant cache/build process is live' >&2
  exit 1
fi
```

Issue the following command exactly once. Do not run `warm --dry-run`, do not
start another warm for this head/key, and do not retry this command if it
fails. Capturing stdout in the variable preserves the exact result for the
postcondition check without adding a second cache invocation.

```bash
QPBT_WARM_JSON="$(
  env -u MATHLIB_SOURCE -u LAKE_PKG_URL_MAP \
    MATHLIB_ARCHIVE="$QPBT_MATHLIB_ARCHIVE" \
    MIPSTARRE_ARCHIVE="$QPBT_MIPSTARRE_ARCHIVE" \
    LAKE_PACKAGE_ARCHIVES="$QPBT_PACKAGE_ARCHIVES" \
    python3 "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" \
      --repo-root "$QPBT_REPO_ROOT" \
      --project-dir . \
      --runtime-dir "$QPBT_RUNTIME_DIR" \
      --main-commit "$QPBT_HEAD_SHA" \
      warm
)"
printf '%s\n' "$QPBT_WARM_JSON"
jq -e --arg key "$QPBT_EXPECTED_KEY" --arg head "$QPBT_HEAD_SHA" '
  .cache_key == $key and .main_commit == $head and
  .status == "hit" and .result == "built" and
  .cache_hit == 0 and .cache_miss == 1 and .builds == 1
' <<<"$QPBT_WARM_JSON" >/dev/null
```

Because the preflight requires no pre-existing snapshot, failure to obtain
`result: "built"` is not an acceptable hit; stop and investigate as a protocol
violation.

## Post-warm status, READY, and deep inventory

Run all of these after the one warm. `status` is read-only and must report the
same exact head/key as a hit.

```bash
QPBT_STATUS_JSON="$(
  python3 "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" \
    --repo-root "$QPBT_REPO_ROOT" \
    --project-dir . \
    --runtime-dir "$QPBT_RUNTIME_DIR" \
    --main-commit "$QPBT_HEAD_SHA" \
    status
)"
printf '%s\n' "$QPBT_STATUS_JSON"
jq -e --arg key "$QPBT_EXPECTED_KEY" --arg head "$QPBT_HEAD_SHA" '
  .cache_key == $key and .main_commit == $head and .status == "hit"
' <<<"$QPBT_STATUS_JSON" >/dev/null

export QPBT_SNAPSHOT="$QPBT_RUNTIME_DIR/cache/main/$QPBT_EXPECTED_KEY"
test -f "$QPBT_SNAPSHOT/manifest.json"
test -f "$QPBT_SNAPSHOT/READY"
test "$(tr -d '\r\n' < "$QPBT_SNAPSHOT/READY")" = "$(sha256sum "$QPBT_SNAPSHOT/manifest.json" | cut -d' ' -f1)"
jq -e --arg key "$QPBT_EXPECTED_KEY" --arg head "$QPBT_HEAD_SHA" '
  .cache_key == $key and .main_commit == $head and
  .recipe.schema_version == 3 and .recipe.version == 5 and
  .recipe.package_verify_command == [
    "python3", "scripts/materialize_lake_packages.py", "verify",
    "--remove-validated-generated-sidecars"
  ]
' "$QPBT_SNAPSHOT/manifest.json" >/dev/null
test ! -e "$QPBT_SNAPSHOT/.lake/packages/proofwidgets/widget/package-lock.json.hash"
test -f "$QPBT_SNAPSHOT/.lake/packages/proofwidgets/widget/package-lock.json"
test -d "$QPBT_SNAPSHOT/.lake/packages/proofwidgets/.lake/build"
test -z "$(find "$QPBT_RUNTIME_DIR/cache/failures" -maxdepth 1 -type d -name "$QPBT_EXPECTED_KEY-*" -print)"

PYTHONDONTWRITEBYTECODE=1 python3 -c '
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
runtime = Path(sys.argv[2])
head = sys.argv[3]
key = sys.argv[4]
sys.path.insert(0, str(repo / "scripts"))
from hot_main_cache import HotMainCache, artifact_inventory, sha256_file

cache = HotMainCache(repo, repo, runtime, main_commit=head)
manifest = json.loads(cache.manifest_path.read_text(encoding="utf-8"))
assert cache.identity.cache_key == key
assert cache.is_ready(deep=True)
assert cache.ready_path.read_text(encoding="ascii").strip() == sha256_file(cache.manifest_path)
assert manifest["cache_key"] == key
assert manifest["main_commit"] == head
assert manifest["artifact_inventory"] == artifact_inventory(cache.lake_dir)
print(json.dumps(manifest["artifact_inventory"], sort_keys=True))
' "$QPBT_REPO_ROOT" "$QPBT_RUNTIME_DIR" "$QPBT_HEAD_SHA" "$QPBT_EXPECTED_KEY"
```

## Closure rules

- **Guard failure before fast-forward:** stop with main at the base; do not
  integrate or warm. Re-audit any changed head, tree, topology, approval,
  candidate cleanliness, changed-path intersection, or canonical state.
- **Fast-forward succeeds but a pre-warm guard fails:** do not warm. Preserve
  physical main at exact H and leave LPR-014/LPR-015 approved with null
  integration metadata and QPBT-024/QPBT-025 in review until root resolves the
  guard without retrying any cache attempt.
- **Warm or any post-warm check fails:** preserve the failure envelope, build
  log, warm metric, and old dba1/9b6 evidence; require no READY/snapshot for the
  new key. Set neither integration SHA, merge neither PR, and close neither
  issue. Never retry exact H/key. A further hypothesis requires a new child,
  owner, worktree, changed candidate, and LPR-016; do not advance LPR-015's
  immutable head.
- **All checks succeed:** append the exact warm/status/READY/deep-inventory
  facts as post-integration evidence, including result, key, main SHA, lock
  wait, build duration, command, inventory, and absence of a failure envelope.
  Do not add a late PR check after approval. Terminally import the orchestrator,
  reviewer, and integration-session metrics. Validate canonical state before
  and after root-only state changes. Then, in physical order: set LPR-014's
  immutable integration SHA to `9c9b49548fabdd6b01916787d7dc17a4bca36513`
  and merge it; set LPR-015's immutable integration SHA to exact H and merge
  it; attach the same warm evidence and close QPBT-025; close QPBT-024 only
  after its child and both PR predicates hold; reconcile INC-044 without
  deleting either historical failure occurrence; leave QPBT-004 `planned`
  with only unfinished QPBT-003 as its blocker.

## Commands and evidence inspected

No tests, builds, workflow validation, `warm`, `seed`, operational `status`,
Lean, Lake, network, Git write, repository/runtime/cache mutation, or canonical
state write was performed. The exact principal read-only commands were:

```text
cat AGENTS.md
git status --short --branch
git status --porcelain=v1 --untracked-files=all
git status --porcelain=v1 --untracked-files=all -- scripts/hot_main_cache.py scripts/materialize_lake_packages.py tests/test_hot_main_cache.py tests/test_lake_package_materialization.py
git diff --cached --name-only
git rev-parse HEAD HEAD^{tree} HEAD^ HEAD^{commit}
git merge-base 45d2fe657af587e8e10952aced2e156d349fd65e d73cce44d5f9f37d38ee8d916811719408818c03
git rev-list --count 45d2fe657af587e8e10952aced2e156d349fd65e..d73cce44d5f9f37d38ee8d916811719408818c03
git rev-list --count d73cce44d5f9f37d38ee8d916811719408818c03..45d2fe657af587e8e10952aced2e156d349fd65e
git diff --name-status 45d2fe657af587e8e10952aced2e156d349fd65e..d73cce44d5f9f37d38ee8d916811719408818c03
git diff --stat 45d2fe657af587e8e10952aced2e156d349fd65e..d73cce44d5f9f37d38ee8d916811719408818c03
git diff --check 45d2fe657af587e8e10952aced2e156d349fd65e..d73cce44d5f9f37d38ee8d916811719408818c03
git show --no-ext-diff --format=fuller --stat d73cce44d5f9f37d38ee8d916811719408818c03
git diff --no-ext-diff --unified=20 45d2fe657af587e8e10952aced2e156d349fd65e..d73cce44d5f9f37d38ee8d916811719408818c03 -- scripts/hot_main_cache.py
git diff --no-ext-diff --unified=5 45d2fe657af587e8e10952aced2e156d349fd65e..d73cce44d5f9f37d38ee8d916811719408818c03 -- scripts/materialize_lake_packages.py
git diff --no-ext-diff --unified=3 45d2fe657af587e8e10952aced2e156d349fd65e..d73cce44d5f9f37d38ee8d916811719408818c03 -- tests/test_hot_main_cache.py
git ls-tree d73cce44d5f9f37d38ee8d916811719408818c03 -- scripts/hot_main_cache.py scripts/materialize_lake_packages.py tests/test_hot_main_cache.py tests/test_lake_package_materialization.py
git show d73cce44d5f9f37d38ee8d916811719408818c03:<each-candidate-path> | sha256sum
rg -n -C 8 'QPBT-025|LPR-015' workflow/state/issues.json workflow/state/prs.json
jq '.issues[] | select(.id == "QPBT-025")' workflow/state/issues.json
jq '.pull_requests[] | select(.id == "LPR-015")' workflow/state/prs.json
jq '.pull_requests[] | select(.id == "LPR-014") | {status,base_sha,head_sha,reviews,findings,integration_sha,merged_at}' workflow/state/prs.json
cat workflow/reviews/qpbt-024-integration-warm-a06.md
cat workflow/reviews/qpbt-024-repair-topology-a17.md
cat workflow/reviews/qpbt-025-sidecar-removal-a01.md
python3 scripts/hot_main_cache.py --help
python3 scripts/hot_main_cache.py warm --help
python3 scripts/hot_main_cache.py status --help
rg -n 'CACHE_RECIPE_VERSION|CACHE_RECIPE_SCHEMA|manifest|READY|inventory|deep|lock|fcntl|status' scripts/hot_main_cache.py
sed -n '135,205p' scripts/hot_main_cache.py
sed -n '1360,1435p' scripts/hot_main_cache.py
sed -n '1520,1610p' scripts/hot_main_cache.py
sed -n '1780,1865p' scripts/hot_main_cache.py
sed -n '1980,2245p' scripts/hot_main_cache.py
sed -n '2450,2535p' scripts/hot_main_cache.py
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import sys; from pathlib import Path; sys.path.insert(0, "scripts"); from hot_main_cache import CacheIdentity, CANONICAL_BUILD_RECIPE; i=CacheIdentity.create(Path.cwd(), Path.cwd(), CANONICAL_BUILD_RECIPE, main_commit="d73cce44d5f9f37d38ee8d916811719408818c03"); print(i.cache_key)'
find .workflow-runtime/locks -maxdepth 1 -type f -name '*.lock' -printf '%f\n'
find .workflow-runtime/cache/failures -maxdepth 1 -type d -name '5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266-*' -print
test -e .workflow-runtime/cache/main/5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266
test -e .workflow-runtime/locks/hot-main-5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266.lock
ps -C python3,lake,lean,lean4 -o pid=,ppid=,lstart=,args=
ps -eo pid=,ppid=,lstart=,args= | rg '[h]ot_main_cache\.py.*(warm|seed)|[l]ake .*build|[l]ean(4)? '
lslocks --noheadings --output PID,COMMAND,PATH
```

An initial `jq '.prs[] | ...' workflow/state/prs.json` inspection failed because
the canonical key is `pull_requests`; the corrected command above succeeded.
An initial wildcard `lsof .workflow-runtime/locks/*.lock` returned no holder
but warned that some unrelated mounted filesystems were unstatable. The
target-key lock was absent, and an independent empty `lslocks` kernel-table
read supplied the fail-closed observation used here.

## Session accounting

- Logical session: `i025-scout-a05-integration-readiness`.
- Role/topology: fresh read-only scout under root coordinator; subagents `0`;
  depth `1`.
- First captured timestamp: `2026-09-01T03:33:44+08:00`.
- Evidence/report cutoff: `2026-09-01T03:41:08.046430378+08:00`.
- Captured interval: `444.046430378` seconds. This is the interval between
  actually captured timestamps, not an estimate of uncaptured setup time.
- Token usage: JSON `null`.
- Token availability reason: the collaboration backend does not expose
  per-session token usage; no estimate was made.
- Compile attempts, cache warms, seeds, operational status calls, tests,
  builds, Lean/Lake commands, network operations, Git writes, and shared
  runtime/cache mutations: `0`.
- Repository/canonical edits: `0`.
- Authored output: `/tmp/qpbt-025-integration-readiness-a05.md` only.

The report SHA-256 is supplied out of band because embedding it would change
the digest.
