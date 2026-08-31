# QPBT-018 / LPR-013 integration and singleton-warm readiness (a14)

## Verdict

**HOLD now; conditional GO after one fresh immutable approval of exact base
`c5a0fecc26eb18452219cf0df31ce2a9113e45f1` and exact head
`c0de0900a01724c2a515311424dcbe5e7526ebd4`.**

At the final observation (`2026-08-31T14:59:50Z`), LPR-013 was `ready` but
had no review records. Its six exact-base checks were passed and it had no
findings, but the acceptance gate requiring a fresh independent reviewer was
therefore still open. No integration or warm is authorized before that review.

After approval, the safe integration is a guarded fast-forward of canonical
`main` from `c5a0fecc...` to its direct child `c0de0900...`. This preserves the
reviewed candidate commit and both reviewed blobs exactly while leaving the
coordinator's disjoint dirty workflow/metrics files intact. Do not commit the
current coordinator state before integration: doing so would move `main` away
from the reviewed base and invalidate LPR-013's exact-base evidence.

## Immutable candidate and current state

- Canonical repository: `/home/drx/MIPStarRE-auto`.
- Canonical branch/HEAD: `main` at
  `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`, tree
  `1cd467af136866b4aee74b7da421402ff4d38d35`.
- Candidate worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-018-current-a10`.
- Candidate branch/HEAD: `issue/qpbt-018-current-a10` at
  `c0de0900a01724c2a515311424dcbe5e7526ebd4`, tree
  `8b3d2caee539921fe4bcbcc456f0fc00ae2bbe17`; the worktree is clean.
- Candidate has exactly one parent, `c5a0fecc...`; the merge base is that same
  SHA. It changes exactly `scripts/hot_main_cache.py` and
  `tests/test_hot_main_cache.py`, with 199 insertions and 8 deletions.
- Candidate Git blobs:
  - `scripts/hot_main_cache.py`:
    `48e020d7392f2e1974f5983d6737171e034417d2`.
  - `tests/test_hot_main_cache.py`:
    `39dca3d47f3e8c79dd7ac1c07f4f69ae723aed06`.
- Candidate file-content SHA-256 values:
  - cache script:
    `0fd404e2cead596370fbda144dc86810f0fd2b87fe7a6ba011d7e72b661daeab`;
  - focused test file:
    `ed2bed4d4aab27f2bd1e7dd98c484d0e1ebee0e80f5265ac6bccc84a03674b75`.
- `git diff --check c5a0fecc..c0de0900` passes.

Canonical tracked dirt is confined to:

```text
research/metrics/incidents.jsonl
research/metrics/sessions.jsonl
workflow/events.jsonl
workflow/state/issues.json
workflow/state/prs.json
workflow/state/sessions.json
workflow/state/stages.json
```

Canonical untracked files are reports under `workflow/reviews/`. Neither set
intersects the two LPR-013 paths. The index is clean. Capture the complete
porcelain status immediately before the fast-forward and require it to be
byte-identical afterward; this proves the coordinator state was not lost.

LPR-013 is correctly bound to this base/head and has six passed checks in
`workflow/state/prs.json`. Its current empty `reviews` list is the only
pre-integration blocker found by this scout. The candidate-binding report is
`workflow/reviews/qpbt-018-pr013-bind-a12.md`, and the implementation/test
evidence is `workflow/reviews/qpbt-018-current-a10.md`.

## Retained EXDEV failure and repaired behavior

The prior failed key is
`a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0`
for exact main `c5a0fecc...`. Its retained envelope is:

```text
/home/drx/MIPStarRE-auto/.workflow-runtime/cache/failures/
  a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0-20260831T220839-2/
```

`failure.json` records one elected miss, zero lock wait, one build attempt,
0.014599 build seconds, 0.134139 elapsed seconds, and failure before Mathlib
preparation. `build.log` records `git clone --local` failing while hardlinking
a loose object with `Invalid cross-device link`. No snapshot or `READY` exists.
This envelope must remain unchanged.

The reviewed candidate retains the initial local clone. It examines only log
bytes appended by that attempt and, only for explicit case-insensitive
`cross-device` or `EXDEV` evidence, removes the fixed partial checkout and
retries exactly once with `--no-local`. It then performs the unchanged exact
detached checkout. Any non-EXDEV clone failure, cleanup failure, fallback clone
failure, detached-checkout failure, authentication failure, dependency failure,
or build failure aborts. Warm retains `failure.json` and `build.log`, appends a
single failed metric, removes staging, and publishes no snapshot or `READY`.
There is no automatic second warm.

## Authenticated local inputs

Use archive mode for Mathlib and explicitly unset `MATHLIB_SOURCE` and any
ambient `LAKE_PKG_URL_MAP`.

### Mathlib archive and repository

- Archive: `/tmp/mathlib-81a5d257-shallow-repo.tar.gz`.
- Observed type/size: regular file, 51,938,317 bytes.
- Recomputed compressed SHA-256:
  `c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`.
- Contracted decompressed tar: 147,712,000 bytes, SHA-256
  `ad9a60b01736070112fbc1008ea98c67e68fa045c5b69e66873e0b9444ddd3ba`.
- Read-only authenticated repository:
  `/tmp/qpbt018-mathlib-source.t8E8oS/mathlib`.
- Reverified with system/global Git configuration disabled and trusted local
  overrides: clean tracked state, HEAD
  `81a5d257c8e410db227a6665ed08f64fea08e997`, tree
  `5ea66b811b8461daae82f14d356fed2a287d7c40`, and shallow boundary at the
  same commit.
- Recomputed pack SHA-256:
  `4659f2a0cabfec474474f5e83ea3d495e711b735418742dd3d642328adcada02`;
  pack size 27,574,578 bytes.
- Root `lake-manifest.json` hash:
  `d20abbe9525a311d501feb89299492717e27c88f441ac77191d9394b49e47fa9`.
- `references/mathlib-lake-manifest.json` hash:
  `015c7e00ead0f05f2a72b32d9bdef782d4689d05a6297f0ceb0ab5d196c164bd`.

### MIPStarRE foundation archive

- Archive:
  `/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz`.
- Observed type/size: regular file, 1,989,153 bytes.
- Recomputed compressed SHA-256:
  `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.
- Pin `references/mipstarre-upstream.json` has SHA-256
  `d5db77534d52be40e247715ed7bb5007b1bc89ac437d545854f6f35cebb2461b`
  and binds source commit `507e81220d95266ff3d589d125b2f87c7300a9fb`,
  decompressed tar SHA-256
  `4e4850855ac74b63cb9ef292281462174da776628a6278006f3728c9458a1d39`,
  and output inventory SHA-256
  `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.

### Eight Lake package archives

Directory:
`/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830`.
All eight exact `name-revision.tar.gz` regular files are present. Recomputed
compressed hashes and observed sizes match `references/lake-packages.json`
(pin-file SHA-256
`08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0`):

| Package/revision | Bytes | Archive SHA-256 | Output inventory / tree |
|---|---:|---|---|
| `plausible-e12c191...` | 42,953 | `2825d6f3d7fc9d26151710ae643e08aabb02251bd94c476fd5217f91b59149b3` | `649ffaeecd9d03bad3b775bcb93669b6e016236b2b23f2e96b9346ba180bfe4b` / `b477789560b0cd76cf3177b9cffa3aaa5cd54e6b` |
| `LeanSearchClient-c5d5b8f...` | 12,983 | `1a86db89a695849ce06590284e6b89c5f2353e3972e60b89b9fb4127e0cfff31` | `4b587cdf57d920f5951f2d5fb40d0e66e707f0519ab64cd6a51cbfb2f647b313` / `d0224b6df6c90cc0b4ed2db6218037d31bfd6f52` |
| `importGraph-7e9612b...` | 106,222 | `c5ee93880bf68d9ae87280c77390460b8af3ee30f748cd10d098d4121ed7930c` | `9800853306226d4aab36f983f5a2b79b96492b565e2d9892d8ec3deb7d8c35b0` / `1043219185d8e3def8b957b342c2df86f38d058e` |
| `proofwidgets-6e311e2...` | 3,896,457 | `dffb4652003f31f8e393e0f2887526ec4b6cc8244b960afa8dcbc1918b020c68` | `b001b475d24f2bfe99e9d1d75fbcb3b18622f8fb3d085377a42135bcca766ca2` / `bec90bac5dd8afade168e76c5b508482f9043b26` |
| `aesop-a7dbf0c...` | 208,077 | `b8c00f97dac46c4b1dd64f07bb80c0963ea61ff5dd9b239414481a77c05c5908` | `720e6fe8f2c2ccc92403faf54091b4a91baddc847c6acf8b092118bc6743f6c0` / `942d19cef97fc177e3ddd90fc4d5ceaf0d4d8b31` |
| `Qq-38d591e...` | 33,003 | `7f5c45d34799e615bf6445c3b7ef14a21c664843f14760468dafc4877ed14772` | `bf8207d454fe5891e5dfe78b0afc65d3e1b11fceab99aca8a341411051eeb106` / `ac63804ee60bfa047d95aa3e216108cd6e0c25b0` |
| `batteries-023ce7d...` | 349,383 | `a5066fea2fd1a311c3c95d530f07030146de3a193e86a7271ae0a6cad5241294` | `a105f80172d539d920a17425b5e4e7b8f2cb8a03ab8f9fe274028283570e8bfc` / `11ebf7815665b26fabf3ad8c4e530975f498d26c` |
| `Cli-88679d0...` | 23,877 | `e2a1d9d7c341bc6d6f9674940de6c1282ebb2fb668a677c8405c5c0039d3db26` | `e164f6dfb831263533db1296f8e382f57913add9633021333dd2b0b35ff46162` / `01e0610ddf9e54ca91da432fe581922e7a513574` |

The package materializer script hash is
`73bc42b1b4a33806e83ab5502f1b125eae6325f6c0d1063a80d0fa481dd245e5`.

## Cache identity and why integration comes first

Read-only status inspection produced:

```text
c5a0fecc... -> a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0 (miss)
c0de0900... -> dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276 (miss)
```

The eight committed identity-file hashes, recipe schema/version (`3`/`4`),
recipe commands, and source contract are unchanged. The full `main_commit` is
itself in the identity payload, so the fast-forward alone changes the key to
`dba1d9c8...`. The expected new snapshot and lock are:

```text
/home/drx/MIPStarRE-auto/.workflow-runtime/cache/main/dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276
/home/drx/MIPStarRE-auto/.workflow-runtime/locks/hot-main-dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276.lock
```

No warm may run before integration because LPR-013 lacks approval and
`c0de0900...` is not yet canonical `main`. Running current-main warm would
repeat the unchanged a582 hypothesis with the old tool. Running a candidate
worktree script would build an unintegrated commit under a separate default
runtime unless manually redirected, would consume the singleton acceptance
attempt before approval, and would not establish the required post-integration
main cache. The warm must execute the reviewed script from canonical `main`
after the guarded fast-forward, with explicit canonical repository/runtime and
exact integrated SHA.

## Active-builder observation

At `2026-08-31T14:59:50Z` there was no live `hot_main_cache.py`, `lake build`,
or `lake env lean` process, and `lslocks` showed no holder for the a582 key,
the predicted dba1 key, or the metrics lock. The durable zero-byte a582 and
metrics lock files are rendezvous files, not active-owner evidence. Recheck
processes and lock holders immediately before the one warm; do not launch while
another builder is live.

## Guarded integration after approval

Use the existing object; do not cherry-pick, rebase, synthesize a merge commit,
or alter candidate files. A fast-forward is the smallest exact integration and
has precedent in merged local PRs LPR-008 and LPR-011.

```bash
export QPBT_REPO_ROOT=/home/drx/MIPStarRE-auto
export QPBT_RUNTIME_DIR=/home/drx/MIPStarRE-auto/.workflow-runtime
export QPBT_BASE_SHA=c5a0fecc26eb18452219cf0df31ce2a9113e45f1
export QPBT_INTEGRATED_SHA=c0de0900a01724c2a515311424dcbe5e7526ebd4

test "$(git -C "$QPBT_REPO_ROOT" branch --show-current)" = main
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_BASE_SHA"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse "$QPBT_INTEGRATED_SHA^")" = "$QPBT_BASE_SHA"
test "$(git -C "$QPBT_REPO_ROOT" merge-base "$QPBT_BASE_SHA" "$QPBT_INTEGRATED_SHA")" = "$QPBT_BASE_SHA"
test -z "$(git -C "$QPBT_REPO_ROOT" diff --cached --name-only)"
test -z "$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1 -- scripts/hot_main_cache.py tests/test_hot_main_cache.py)"
python3 "$QPBT_REPO_ROOT/scripts/workflow.py" validate

QPBT_DIRTY_BEFORE="$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1)"
git -C "$QPBT_REPO_ROOT" merge --ff-only "$QPBT_INTEGRATED_SHA"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD)" = "$QPBT_INTEGRATED_SHA"
test "$(git -C "$QPBT_REPO_ROOT" status --porcelain=v1)" = "$QPBT_DIRTY_BEFORE"
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:scripts/hot_main_cache.py)" = 48e020d7392f2e1974f5983d6737171e034417d2
test "$(git -C "$QPBT_REPO_ROOT" rev-parse HEAD:tests/test_hot_main_cache.py)" = 39dca3d47f3e8c79dd7ac1c07f4f69ae723aed06
test "$(sha256sum "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" | cut -d' ' -f1)" = 0fd404e2cead596370fbda144dc86810f0fd2b87fe7a6ba011d7e72b661daeab
git -C "$QPBT_REPO_ROOT" diff --check "$QPBT_BASE_SHA..$QPBT_INTEGRATED_SHA"
```

The formal reviewer result must be imported and LPR-013 transitioned
`ready -> approved` before this sequence. Preserve LPR-013 as `approved` after
the physical fast-forward until the post-integration singleton gate succeeds.

## Post-integration gates and exactly one warm

Run Python/workflow gates once on the integrated working tree. They do not
compile Lean and do not substitute for the singleton build:

```bash
cd "$QPBT_REPO_ROOT"
python3 -m unittest discover -s tests -p test_hot_main_cache.py -v
python3 -m unittest discover -s tests -v
python3 scripts/check_workflow.py
python3 -m compileall -q scripts tests
python3 scripts/workflow.py validate
git diff --check "$QPBT_BASE_SHA..$QPBT_INTEGRATED_SHA"
```

Bind the three local inputs and verify their current compressed hashes before
the attempt:

```bash
export QPBT_MATHLIB_ARCHIVE=/tmp/mathlib-81a5d257-shallow-repo.tar.gz
export QPBT_MIPSTARRE_ARCHIVE=/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz
export QPBT_PACKAGE_ARCHIVES=/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830

test "$(sha256sum "$QPBT_MATHLIB_ARCHIVE" | cut -d' ' -f1)" = c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7
test "$(sha256sum "$QPBT_MIPSTARRE_ARCHIVE" | cut -d' ' -f1)" = 656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc
test -d "$QPBT_PACKAGE_ARCHIVES" && test ! -L "$QPBT_PACKAGE_ARCHIVES"
```

First capture read-only status. It must report exact key `dba1d9c8...`, exact
main `c0de0900...`, and `miss`:

```bash
env -u MATHLIB_SOURCE -u LAKE_PKG_URL_MAP \
  MATHLIB_ARCHIVE="$QPBT_MATHLIB_ARCHIVE" \
  MIPSTARRE_ARCHIVE="$QPBT_MIPSTARRE_ARCHIVE" \
  LAKE_PACKAGE_ARCHIVES="$QPBT_PACKAGE_ARCHIVES" \
  python3 "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" \
  --repo-root "$QPBT_REPO_ROOT" \
  --project-dir . \
  --runtime-dir "$QPBT_RUNTIME_DIR" \
  --main-commit "$QPBT_INTEGRATED_SHA" status
```

Record the current line count of
`.workflow-runtime/metrics/hot-main.jsonl`, recheck that no builder or relevant
lock holder is live, then invoke the following command exactly once:

```bash
env -u MATHLIB_SOURCE -u LAKE_PKG_URL_MAP \
  MATHLIB_ARCHIVE="$QPBT_MATHLIB_ARCHIVE" \
  MIPSTARRE_ARCHIVE="$QPBT_MIPSTARRE_ARCHIVE" \
  LAKE_PACKAGE_ARCHIVES="$QPBT_PACKAGE_ARCHIVES" \
  python3 "$QPBT_REPO_ROOT/scripts/hot_main_cache.py" \
  --repo-root "$QPBT_REPO_ROOT" \
  --project-dir . \
  --runtime-dir "$QPBT_RUNTIME_DIR" \
  --main-commit "$QPBT_INTEGRATED_SHA" warm
```

Do not run a separate `lake build`; canonical warm already runs the exact
dependency command and full `lake --packages=.lake/package-overrides.json
build`. Do not invoke a second warm after either success or failure.

On success, require `result: built`, `status: hit`, `builds: 1`, the dba1 key,
and exact c0de main identity. A `hit` or `hit_after_wait` is acceptable only if
authoritative evidence proves another already-elected invocation published the
same exact key; given the observed empty snapshot directory and no live owner,
`built` is expected. Run the identical status command again and require `hit`.

Status performs shallow manifest/READY validation. Also require deep artifact
inventory equality without mutating the cache:

```bash
python3 -c 'import json,sys; from pathlib import Path; sys.path.insert(0,"/home/drx/MIPStarRE-auto/scripts"); from hot_main_cache import HotMainCache,artifact_inventory,sha256_file; c=HotMainCache(Path("/home/drx/MIPStarRE-auto"),Path("/home/drx/MIPStarRE-auto"),Path("/home/drx/MIPStarRE-auto/.workflow-runtime"),main_commit="c0de0900a01724c2a515311424dcbe5e7526ebd4"); m=json.loads(c.manifest_path.read_text()); assert c.identity.cache_key=="dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276"; assert c.is_ready(deep=True); assert c.ready_path.read_text(encoding="ascii").strip()==sha256_file(c.manifest_path); assert m["artifact_inventory"]==artifact_inventory(c.lake_dir); print(json.dumps(m["artifact_inventory"],sort_keys=True))'
```

## Evidence to record

For the integration, record base/head/tree, fast-forward result, unchanged
porcelain dirty-state envelope, exact production/test blobs and SHA-256 values,
formal review identity/verdict, each post-integration command, result, and
duration.

For warm, preserve and import:

1. pre-warm and post-warm status JSON, both bound to c0de/dba1;
2. exact argv and archive environment paths, plus all recomputed digests;
3. start/end timestamps, exit status, builder PID/host, cache hit/miss, build
   count, lock wait and seconds, materialization/package verification,
   dependency-cache, build, and total elapsed seconds;
4. the single newly appended `hot-main.jsonl` metric and before/after line
   counts proving one invocation;
5. immutable snapshot path, `build.log`, `manifest.json`, `READY`, READY-to-
   manifest digest equality, deep artifact inventory output, source evidence,
   and Mathlib archive/commit/tree/pack evidence;
6. whether the EXDEV fallback marker appears in `build.log`, proving the
   changed hypothesis was exercised on this host;
7. continued existence and unchanged identity of the old a582 failure
   envelope; and
8. final process/lock observation showing no builder left running.

On failure, record the same command/timing/metric data, exact error and retained
failure-envelope paths, confirm that no dba1 snapshot or `READY` was published,
and stop. Do not retry. Classify the failure against an existing incident/issue
where applicable; open a new issue only if it is a genuinely new failure
class, following the workflow's occurrence rule.

## Lifecycle dispositions

Current disposition is HOLD:

- LPR-013 stays `ready`; QPBT-018 stays `review`.
- LPR-012 stays `approved`, with physical integration commit c5a retained as
  evidence but `integration_sha`/`merged_at` still null; QPBT-021 stays
  `review`.

After exact-head review approval but before warm:

- transition LPR-013 to `approved`;
- fast-forward physically to c0de, but keep LPR-013 `approved` and both issues
  in `review` until the singleton gate succeeds;
- leave LPR-012/QPBT-021 unchanged.

After all post-integration gates and the one verified warm succeed:

- record LPR-013 `integration_sha` as c0de and transition it to `merged`;
- transition QPBT-018 to `done`;
- record LPR-012's physical `integration_sha` as c5a0fecc and transition it to
  `merged`;
- transition QPBT-021 to `done`;
- import integration/warm reports and metrics, validate before and after state
  transitions, then commit the coordinator state checkpoint.

If any gate fails, none of those closure transitions is authorized.

## Session accounting

- Elapsed: approximately 12 minutes; the collaboration backend exposes no
  authoritative per-session timer, so this is labeled approximate.
- Subagents: 0; topology is root coordinator -> this read-only scout.
- Token usage: `null`; per-agent token usage is not exposed by the
  collaboration backend, so no estimate was made.
- Repository/canonical/runtime/cache/worktree/ref edits: 0.
- Authored output: this report only.
- Shell process invocations: 37 read-only inspection groups.
- Cache commands: status 2, warm 0, seed 0. Status appended no metrics.
- Tests/workflow checker/compileall: 0.
- Lean/Lake/build invocations: 0.
- Network/GitHub operations: 0.
- Git operations were read-only only; no fetch, merge, checkout, commit, or ref
  update was performed.
