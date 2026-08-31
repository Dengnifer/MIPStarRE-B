# QPBT-024 post-warm evidence procedure (a09)

Logical session: `i024-scout-a09-warm-evidence`
Integrated main: `9c9b49548fabdd6b01916787d7dc17a4bca36513`
Expected cache key: `9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36`

## Verdict

**PASS for the frozen verification procedure; cache acceptance remains
conditional on observing `status: "hit"`, exact READY/manifest binding, and a
matching deep inventory.** The commands below are read-only with respect to the
repository and cache. They cannot elect a builder, warm a cache, seed a
worktree, acquire a cache lock, or append a cache metric.

This scout did not inspect the live key, live runtime, processes, locks, warm
output, or retained runtime evidence. It did not run `status`, deep inventory,
tests, Lean, Lake, a build, `warm`, or `seed`. The expected key is therefore a
frozen acceptance value supplied by the dispatch, not a claim about current
live state.

## Committed identity anchors

The exact committed identity inputs at `9c9b495...` are:

```text
lean-toolchain                              2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e
lakefile.toml                               a1c61e97b41ec1fcbf15345a18117540ebc2d9f6f6cfa1021580479e2e9bafdf
lake-manifest.json                         d20abbe9525a311d501feb89299492717e27c88f441ac77191d9394b49e47fa9
references/mipstarre-upstream.json         d5db77534d52be40e247715ed7bb5007b1bc89ac437d545854f6f35cebb2461b
scripts/materialize_mipstarre.py           872b462ca048cd965c764aa08126532072e91bc6a15cc302c7e3acb922458d95
references/lake-packages.json              08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0
references/mathlib-lake-manifest.json      015c7e00ead0f05f2a72b32d9bdef782d4689d05a6297f0ceb0ab5d196c164bd
scripts/materialize_lake_packages.py       3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243
```

The executed verifier must be the committed cache script, SHA-256
`0fd404e2cead596370fbda144dc86810f0fd2b87fe7a6ba011d7e72b661daeab`.
The canonical recipe is schema `3`, id `qpbt-hot-main`, version `4`; the cache
manifest/readiness schema is `3`, and the artifact-inventory schema is `1`.

The committed source contract is schema `1`, pin SHA-256 `d5db775...`, source
commit `507e81220d95266ff3d589d125b2f87c7300a9fb`, source inventory
`d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`,
337 files, 5,970,111 bytes, and zero committed authored QPBT files/bytes with
empty SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Expected paths are:

```text
/home/drx/MIPStarRE-auto/.workflow-runtime/cache/main/9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36
/home/drx/MIPStarRE-auto/.workflow-runtime/cache/main/9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36/.lake/build
/home/drx/MIPStarRE-auto/.workflow-runtime/locks/hot-main-9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36.lock
/home/drx/MIPStarRE-auto/.workflow-runtime/metrics/hot-main.jsonl
```

## Why the verification cannot warm or seed

At committed `scripts/hot_main_cache.py:2456-2514`, `argparse` requires exactly
one subcommand. The first command below selects `status`; `run_cli` therefore
returns only `cache.status()`. `status()` at lines 1839-1847 calls shallow
`is_ready()` and returns JSON. It does not call `warm`, `seed`, `ExclusiveLock`,
or `_append_metric`.

The second command imports the module and calls `status`, `is_ready(deep=True)`,
`artifact_inventory`, and `sha256_file` directly. `is_ready(deep=True)` at
lines 1793-1837 reads `READY` and `manifest.json`, validates exact identity and
source evidence, and hashes `.lake`; it has no write path. `artifact_inventory`
at lines 246-306 opens files read-only and does not follow symlinks. The command
never calls `warm()`, `seed()`, or `_append_metric()`.

The before/after hashes below make any concurrent metric or evidence-byte
change visible. Equality is required. A difference is a stop condition, not
permission to rerun a warm.

## Exact status-ready and deep-inventory commands

Run from the canonical primary worktree only after the one authorized warm has
terminated. These commands create evidence files only under `/tmp`.

```bash
set -euo pipefail

readonly QPBT_REPO=/home/drx/MIPStarRE-auto
readonly QPBT_RUNTIME=/home/drx/MIPStarRE-auto/.workflow-runtime
readonly QPBT_SHA=9c9b49548fabdd6b01916787d7dc17a4bca36513
readonly QPBT_KEY=9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36
readonly QPBT_SNAPSHOT="$QPBT_RUNTIME/cache/main/$QPBT_KEY"
readonly QPBT_METRICS="$QPBT_RUNTIME/metrics/hot-main.jsonl"
readonly QPBT_EVIDENCE=/tmp/qpbt-024-postwarm-evidence

mkdir -p "$QPBT_EVIDENCE"
test "$(git -C "$QPBT_REPO" rev-parse HEAD)" = "$QPBT_SHA"
test "$(sha256sum "$QPBT_REPO/scripts/hot_main_cache.py" | cut -d' ' -f1)" = 0fd404e2cead596370fbda144dc86810f0fd2b87fe7a6ba011d7e72b661daeab

sha256sum "$QPBT_METRICS" > "$QPBT_EVIDENCE/metrics.before.sha256"
wc -l < "$QPBT_METRICS" > "$QPBT_EVIDENCE/metrics.before.lines"
sha256sum "$QPBT_SNAPSHOT/manifest.json" "$QPBT_SNAPSHOT/READY" \
  "$QPBT_SNAPSHOT/build.log" > "$QPBT_EVIDENCE/snapshot.before.sha256"

env -u MATHLIB_SOURCE -u MATHLIB_ARCHIVE -u MIPSTARRE_ARCHIVE \
  -u LAKE_PACKAGE_ARCHIVES -u LAKE_PKG_URL_MAP \
  python3 -B "$QPBT_REPO/scripts/hot_main_cache.py" \
  --repo-root "$QPBT_REPO" \
  --project-dir . \
  --runtime-dir "$QPBT_RUNTIME" \
  --main-commit "$QPBT_SHA" \
  status > "$QPBT_EVIDENCE/status.json"

python3 -B -c 'import json; from pathlib import Path; p=Path("/tmp/qpbt-024-postwarm-evidence/status.json"); s=json.loads(p.read_text(encoding="utf-8")); key="9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36"; sha="9c9b49548fabdd6b01916787d7dc17a4bca36513"; root="/home/drx/MIPStarRE-auto/.workflow-runtime"; assert s["schema_version"]==3; assert s["cache_key"]==key; assert s["main_commit"]==sha; assert s["status"]=="hit"; assert s["snapshot_dir"]==f"{root}/cache/main/{key}"; assert s["build_dir"]==f"{root}/cache/main/{key}/.lake/build"; assert s["lock_path"]==f"{root}/locks/hot-main-{key}.lock"; assert s["recipe"]["recipe_id"]=="qpbt-hot-main" and s["recipe"]["version"]==4 and s["recipe"]["schema_version"]==3; print(json.dumps(s,sort_keys=True))'

python3 -B -c 'import json,sys; from pathlib import Path; sys.path.insert(0,"/home/drx/MIPStarRE-auto/scripts"); from hot_main_cache import HotMainCache,artifact_inventory,sha256_file,validate_mathlib_evidence; repo=Path("/home/drx/MIPStarRE-auto"); runtime=repo/".workflow-runtime"; sha="9c9b49548fabdd6b01916787d7dc17a4bca36513"; key="9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36"; c=HotMainCache(repo,repo,runtime,main_commit=sha); assert c.identity.cache_key==key; assert c.status()["status"]=="hit"; m=json.loads(c.manifest_path.read_text(encoding="utf-8")); assert m["schema_version"]==3 and m["cache_key"]==key and m["main_commit"]==sha; assert m["recipe"]==c.identity.recipe and m["inputs"]==c.identity.inputs and m["source_contract"]==c.identity.source_contract; assert m["source"]=="detached-local-clone"; assert m["materialize_command"]==["python3","scripts/materialize_mipstarre.py","materialize","--archive-env","MIPSTARRE_ARCHIVE"]; assert m["package_materialize_command"]==["python3","scripts/materialize_lake_packages.py","materialize","--archive-directory-env","LAKE_PACKAGE_ARCHIVES"]; assert m["package_verify_command"]==["python3","scripts/materialize_lake_packages.py","verify"]; assert m["dependency_command"]==["lake","--packages=.lake/package-overrides.json","exe","cache","get"]; assert m["command"]==["lake","--packages=.lake/package-overrides.json","build"]; assert m["source_evidence"]==c.identity.source_contract; assert validate_mathlib_evidence(m["mathlib_source"]); assert m["mathlib_source"]["mode"]=="archive"; assert m["mathlib_source"]["archive_sha256"]=="c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7"; assert c.lake_dir.is_dir() and not c.lake_dir.is_symlink() and c.build_dir.is_dir() and not c.build_dir.is_symlink(); ready=c.ready_path.read_text(encoding="ascii").strip(); manifest_sha=sha256_file(c.manifest_path); assert ready==manifest_sha; assert c.is_ready(deep=True); observed=artifact_inventory(c.lake_dir); assert m["artifact_inventory"]==observed; assert observed["schema_version"]==1 and len(observed["sha256"])==64; out={"schema_version":1,"cache_key":key,"main_commit":sha,"status":"hit","snapshot_dir":str(c.snapshot_dir),"manifest_sha256":manifest_sha,"ready_contents":ready,"ready_file_sha256":sha256_file(c.ready_path),"build_log_sha256":sha256_file(c.snapshot_dir/"build.log"),"artifact_inventory":observed,"source_evidence":m["source_evidence"],"mathlib_source":m["mathlib_source"]}; print(json.dumps(out,sort_keys=True))' > "$QPBT_EVIDENCE/deep-inventory.json"

sha256sum "$QPBT_METRICS" > "$QPBT_EVIDENCE/metrics.after.sha256"
wc -l < "$QPBT_METRICS" > "$QPBT_EVIDENCE/metrics.after.lines"
sha256sum "$QPBT_SNAPSHOT/manifest.json" "$QPBT_SNAPSHOT/READY" \
  "$QPBT_SNAPSHOT/build.log" > "$QPBT_EVIDENCE/snapshot.after.sha256"

cmp "$QPBT_EVIDENCE/metrics.before.sha256" "$QPBT_EVIDENCE/metrics.after.sha256"
cmp "$QPBT_EVIDENCE/metrics.before.lines" "$QPBT_EVIDENCE/metrics.after.lines"
cmp "$QPBT_EVIDENCE/snapshot.before.sha256" "$QPBT_EVIDENCE/snapshot.after.sha256"
sha256sum "$QPBT_EVIDENCE/status.json" "$QPBT_EVIDENCE/deep-inventory.json"
```

The `env -u` list is deliberate: `status` does not authenticate warm inputs and
does not need them. Removing them makes it impossible to confuse this evidence
call with the authenticated warm command. Supplying the exact `--runtime-dir`
also prevents omitted-runtime ambiguity.

## Expected status and inventory fields

`status.json` must contain exactly the current identity envelope plus paths:
`schema_version`, `cache_key`, `main_commit`, `inputs`, `recipe`,
`source_contract`, `status`, `snapshot_dir`, `build_dir`, and `lock_path`.
Acceptance requires the fixed SHA/key above and `status: "hit"`.

`deep-inventory.json` records both the READY binding and the inventory. The
inventory has fields `schema_version`, `sha256`, `files`, `directories`,
`symlinks`, and `bytes`. Counts and the inventory digest are build-output facts
and must be recorded from the successful snapshot; they must not be guessed or
copied from the prior dba1 failure. Equality with the manifest is the gate.

The dynamic success evidence hashes to preserve are:

- raw post-warm `status.json` SHA-256;
- raw `deep-inventory.json` SHA-256;
- `manifest.json` SHA-256, equal to the ASCII digest stored in `READY`;
- SHA-256 of the `READY` file bytes themselves;
- `build.log` SHA-256;
- `artifact_inventory.sha256` from the manifest/deep output; and
- the raw matching `hot-main.jsonl` line SHA-256.

## Exact successful warm metric extraction

Run this only as read-only evidence extraction. It asserts that exactly one
warm metric exists for the new key and that it is the elected successful build.

```bash
python3 -B -c 'import hashlib,json; from pathlib import Path; p=Path("/home/drx/MIPStarRE-auto/.workflow-runtime/metrics/hot-main.jsonl"); key="9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36"; sha="9c9b49548fabdd6b01916787d7dc17a4bca36513"; rows=[]; [(rows.append((raw,json.loads(raw))) if json.loads(raw).get("cache_key")==key and json.loads(raw).get("action")=="warm" else None) for raw in p.read_text(encoding="utf-8").splitlines()]; assert len(rows)==1; raw,m=rows[0]; assert m["schema_version"]==3 and m["main_commit"]==sha; assert m["result"]=="built" and m["status"]=="hit"; assert m["cache_hit"]==0 and m["cache_miss"]==1 and m["builds"]==1; assert isinstance(m["elected_owner"]["pid"],int) and m["elected_owner"]["host"]; assert m["mathlib_source_required"] is True; assert m["mathlib_source"]["mode"]=="archive"; assert m["materialize_command"]==["python3","scripts/materialize_mipstarre.py","materialize","--archive-env","MIPSTARRE_ARCHIVE"]; assert m["package_materialize_command"]==["python3","scripts/materialize_lake_packages.py","materialize","--archive-directory-env","LAKE_PACKAGE_ARCHIVES"]; assert m["package_verify_command"]==["python3","scripts/materialize_lake_packages.py","verify"]; assert m["dependency_command"]==["lake","--packages=.lake/package-overrides.json","exe","cache","get"]; assert m["command"]==["lake","--packages=.lake/package-overrides.json","build"]; assert m["lock_waited"] in (0,1) and m["lock_wait_seconds"]>=0; assert m["materialize_seconds"]>=0 and m["package_materialize_seconds"]>=0 and m["package_verify_seconds"]>=0 and m["dependency_cache_seconds"]>=0 and m["build_seconds"]>=0 and m["elapsed_seconds"]>=0; out={"metric_line_sha256":hashlib.sha256((raw+"\n").encode()).hexdigest(),"metric":m}; print(json.dumps(out,sort_keys=True))' > /tmp/qpbt-024-postwarm-evidence/warm-metric.json
sha256sum /tmp/qpbt-024-postwarm-evidence/warm-metric.json
```

The successful metric fields are: envelope `schema_version`, `timestamp`,
`pid`, `cache_key`, `main_commit`; complete identity/status/path fields;
`action`, `result`, `cache_hit`, `cache_miss`, `lock_waited`,
`lock_wait_seconds`, `builds`, `elected_owner`; all five command arrays;
`mathlib_source_required`, `mathlib_source`; stage durations
`materialize_seconds`, `package_materialize_seconds`,
`package_verify_seconds`, `dependency_cache_seconds`, `build_seconds`;
`elapsed_seconds`; and `log_path`. `manifest.json` additionally records
`created_at`, `source`, `total_prepare_seconds`, `artifact_inventory`,
`source_evidence`, and the Mathlib evidence.

## Failure branch and hashes

If post-warm status is `miss`, stop. Do not run the success/deep assertion and
do not invoke a second warm. For a failure after staging began, preserve:

```text
.workflow-runtime/cache/failures/<key>-<local timestamp>-<pid>/failure.json
.workflow-runtime/cache/failures/<key>-<local timestamp>-<pid>/build.log
.workflow-runtime/metrics/hot-main.jsonl (the one matching failed warm line)
warm stderr/stdout captured by the coordinator
```

Require no published snapshot/`READY` for the key and no `READY` in the failure
directory. Hash the raw evidence files and raw metric line:

```bash
sha256sum "$FAILURE_DIR/failure.json" "$FAILURE_DIR/build.log" "$WARM_STDERR"
python3 -B -c 'import hashlib,json; from pathlib import Path; p=Path("/home/drx/MIPStarRE-auto/.workflow-runtime/metrics/hot-main.jsonl"); key="9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36"; rows=[(r,json.loads(r)) for r in p.read_text(encoding="utf-8").splitlines() if json.loads(r).get("cache_key")==key and json.loads(r).get("action")=="warm"]; assert len(rows)==1 and rows[0][1]["result"]=="failed"; print(hashlib.sha256((rows[0][0]+"\n").encode()).hexdigest())'
```

`failure.json` fields are `schema_version`, the full cache identity,
`failed_at`, `error`, `mathlib_source_required`, and `mathlib_source`. The
failed metric adds the command arrays, hit/miss/build/owner/lock fields,
`result: "failed"`, aggregate failure-path `build_seconds`, `elapsed_seconds`,
`error`, and retained `log_path`. A preflight Mathlib-input failure happens
before staging/metric append and may have only CLI error evidence; that absence
must be reported rather than fabricating a failure envelope.

The prior dba1 failure demonstrates the required hashing convention:
`failure.json` SHA-256 `6585f5226a1163527193dafb0dd49d6614e7917dfdc14d08600bd8f37b6ed401`
and `build.log` SHA-256
`7fcc04ad7e13187dfa3159f1495c2981fdb47d0fa5a253249e69573e691b92bf`.
Those are provenance examples only and must not be reused for the new key.

## Source basis

This procedure is grounded in committed `scripts/hot_main_cache.py` readiness,
status, metric, warm-publication, failure-retention, and CLI dispatch paths;
the corruption/source-evidence/READY tests in `tests/test_hot_main_cache.py`;
`protocols/local-development.md`; `protocols/orchestration.md`; and the prior
one-shot/failure reports `qpbt-018-integration-warm-a14.md`,
`qpbt-018-hotcache-verify-order-a16.md`,
`qpbt-018-failure-disposition-a17.md`, and
`stage-04a-cache-postintegration-a53.md`.

## Session accounting

- Start: `2026-09-01T01:01:29.417950890+08:00`.
- Audit end: `2026-09-01T01:15:38.668172247+08:00`.
- Elapsed: `849.250221491` seconds, agent-measured from the timestamps above.
- Topology: one read-only scout, `0` subagents.
- Token usage: JSON `null`.
- Token availability reason: collaboration backend does not expose per-agent
  token usage; no estimate was made.
- Repository edits, Git writes, tests, builds, Lean, Lake, network, cache
  runtime commands, status calls, deep-inventory calls, warm calls, and seed
  calls: `0` each.
- Authored output: this report under `/tmp` only. Its SHA-256 is reported out of
  band because embedding an ordinary file digest would change the file.
