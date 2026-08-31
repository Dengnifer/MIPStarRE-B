# QPBT-024 post-integration warm failure at 9b6

## Verdict

**FAILED CLOSED. Do not retry the unchanged hypothesis.** The sole authorized
post-integration warm for main
`9c9b49548fabdd6b01916787d7dc17a4bca36513` and cache key
`9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36`
completed all 8,992 Lean jobs, then the retained post-build package verifier
rejected `proofwidgets`:

```text
Build completed successfully (8992 jobs).
error: materialized archive tree differs for proofwidgets
error: Lake package verification command failed with exit code 1
```

The attempt published no cache snapshot or READY marker. A read-only status
call after termination returned `status: "miss"`. Exactly one warm metric is
present for this key, with `result: "failed"`, `builds: 1`, and no lock wait.
No second warm was issued.

## Integrated identity

- LPR-014 was independently approved with zero findings before integration.
- Main fast-forwarded from
  `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe` to exact reviewed head
  `9c9b49548fabdd6b01916787d7dc17a4bca36513` at reflog time
  `2026-08-31T16:56:18Z`.
- The fast-forward changed exactly:
  `scripts/materialize_lake_packages.py`,
  `tests/test_lake_package_materialization.py`, and
  `tests/test_hot_main_cache.py`.
- The authenticated integrated materializer digest recorded by the failure
  envelope and independently recomputed is:

```text
3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243  scripts/materialize_lake_packages.py
```

## Executed command

The coordinator issued this command exactly once after authenticating main,
the local MIPStarRE and Mathlib archives, all eight Lake package archives, the
absence of a prior key/snapshot/failure, and the absence of a live builder:

```bash
env -u MATHLIB_SOURCE -u LAKE_PKG_URL_MAP \
  MATHLIB_ARCHIVE=/tmp/mathlib-81a5d257-shallow-repo.tar.gz \
  MIPSTARRE_ARCHIVE=/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz \
  LAKE_PACKAGE_ARCHIVES=/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830 \
  python3 /home/drx/MIPStarRE-auto/scripts/hot_main_cache.py \
    --repo-root /home/drx/MIPStarRE-auto \
    --project-dir . \
    --runtime-dir /home/drx/MIPStarRE-auto/.workflow-runtime \
    --main-commit 9c9b49548fabdd6b01916787d7dc17a4bca36513 \
    warm
```

The key lock was created at `2026-08-31T16:58:09.209712Z`. The failure
envelope records `failed_at: 2026-08-31T17:08:52.439761Z`; the terminal metric
was appended at `2026-08-31T17:08:59.532005Z`. The metric records
`build_seconds: 643.111606` and `elapsed_seconds: 650.317818`.

## Retained evidence

Failure directory:

```text
.workflow-runtime/cache/failures/
9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36-20260901T010852-2/
```

It contains exactly two files and no READY marker:

```text
a97fa0f97189d1e704808d1ea5e0aa209d269d915b6c5b293b7e117f9d536c48  failure.json
ed0f4d6e2f05f52e175723aac2d69b60230b50962c706c67098d81c665e1fe45  build.log
```

`failure.json` is 3,247 bytes. `build.log` is 39,195 bytes and 407 lines.
The envelope binds recipe schema 3/version 4, exact main/key/input digests,
archive-backed Mathlib commit
`81a5d257c8e410db227a6665ed08f64fea08e997`, and the terminal verifier error.

The raw matching warm metric line, including its final newline, has SHA-256
`9ce27db86209c0e33b0b80f79d641d72a123ef74b105970d0c37e75be7aa7689`.
There is exactly one matching row. The complete hot-main metric file after the
attempt has SHA-256
`576093ca9954c25dddc21a1b711a58ec5681656f56ae25edb324fb57138a9800`.

The post-termination status command was the committed read-only `status`
subcommand with all acquisition variables unset. It returned schema 3, the
exact main/key/identity, and `status: "miss"`. Its pretty-printed stdout has
SHA-256
`25729be075108244daad0426dc22a6678f413429e7fabaa16863f6a97142525d`.

There is no published
`.workflow-runtime/cache/main/9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36`,
no retained staging directory, no READY in the failure directory, no live
Python/Lake/Lean builder, and no observed holder of the durable zero-byte key
lock after termination. The `lsof` probe emitted filesystem-visibility
warnings, so the terminated command and empty process probe are the stronger
no-live-builder evidence.

## Proofwidgets diagnosis

The authenticated proofwidgets archive is exact revision
`6e311e2a844da9b2cc3971187df2fe0066947b93`, 3,896,457 bytes, SHA-256
`dffb4652003f31f8e393e0f2887526ec4b6cc8244b960afa8dcbc1918b020c68`.
The package pin file SHA-256 is
`08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0`.

The failed staging package tree was deliberately removed by failed-closed
cleanup, so the exact changed path cannot be recovered directly from that
attempt. A same-revision, same-Lean-4.32.0 retained package was compared against
fresh extraction of the authenticated archive. Excluding only its legacy
`.git` metadata and `.lake` build directory, the complete recursive diff is:

```text
Only in .../proofwidgets/widget: package-lock.json.hash
```

That object is a single-link regular file, mode 0664, 16 bytes, with ASCII
contents `179e66574f04806e` and SHA-256
`971a4e08a78d3b185902cde49867376deb03135a517d4380eb1cb6604cfcb38b`.
The archive already authenticates `widget/package-lock.json` and its trace,
but does not contain this sidecar.

Installed Lake 4.32.0 `Lake/Build/Common.lean` defines `fetchFileHash` to
create `file ++ ".hash"` when absent. Proofwidgets `lakefile.lean` fetches its
authenticated `widget/package-lock.json` through `buildFileAfterDep`, which
uses this mechanism. The sidecar is therefore the leading root-cause
hypothesis for the proofwidgets tree difference.

This is a bounded inference, not a claim that the deleted failed staging bytes
were inspected. Independent A11-A13 audits must confirm the all-package scope,
security boundary, and protocol effect before implementation. In particular,
the failure does not authorize a generic `*.hash` exclusion, a proofwidgets-
specific exception, or weakening source mutation checks.

## Lifecycle disposition

- LPR-014 remains `approved` with null `integration_sha`; QPBT-024 remains in
  `review` until a new bounded repair is owned and issued.
- LPR-012/LPR-013 and QPBT-021/QPBT-018 remain held at their existing states.
- QPBT-004 remains `planned` and blocked by QPBT-003 plus QPBT-024.
- INC-044 receives a second occurrence of the same broad class: build-induced
  generated package output was treated as authenticated archive source drift.
- The unchanged main/key pair must not be retried. A later warm requires a
  newly reviewed changed hypothesis and a newly derived cache key.

## Accounting

The warm was root-owned: one invocation, one elected build, 8,992 successful
Lean jobs, zero cache hits, zero lock wait, one failed post-build verifier, and
zero publication. Per-root-action token usage is unavailable; no token
estimate is made. The initial sandbox-denied Git fast-forward attempt changed
nothing and is unrelated to the warm result; the approved fast-forward was
then completed with repository-write permission before the warm guards ran.
