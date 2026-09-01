# QPBT-045 root singleton warm evidence

This is root-coordinator evidence for the post-integration acceptance gate. It
is not a formal PR review and does not alter the immutable A09 integration
report.

## Authenticated target

- Main commit: `b9cef4736f5b404ac63ab4b27133544f797f2960`
- Main tree: `34a4dabc6672108c50b65a67ba1a4b844213302c`
- Candidate integration: `47b0bf444d9f29e82e03e51a6d2c89ff5958e6d5`
- Recipe: `qpbt-hot-main` schema 3, version 7
- Cache key: `6769ce0a7274640b5deef277c966ea811808b3458b925548a4bf5b4c2392f1ce`

The read-only preflight authenticated the exact local inputs before the
successful invocation:

- Mathlib archive: `/tmp/mathlib-81a5d257-shallow-repo.tar.gz`,
  51,938,317 bytes, SHA-256
  `c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`.
- MIPStarRE archive: `/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz`,
  1,989,153 bytes, SHA-256
  `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.
- Lake package archives:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830`,
  containing the eight pinned archives recorded by `references/lake-packages.json`.

## Invocation and result

The first unqualified invocation failed closed before lock acquisition with
`set exactly one of MATHLIB_SOURCE or MATHLIB_ARCHIVE`; it created no staging
tree, snapshot, `READY`, or build. This is recorded as INC-065 and led to the
complete-input follow-up QPBT-051. The corrected command supplied exactly one
`MATHLIB_ARCHIVE` plus `MIPSTARRE_ARCHIVE` and `LAKE_PACKAGE_ARCHIVES` and was
run once.

The lock-elected invocation reported:

| field | value |
|---|---|
| result | `built` |
| status after publication | `hit` |
| elected owner | PID `2` on `GHZ` |
| builders | `1` |
| lock wait | `0.0` seconds |
| materialization | `2.919058` seconds |
| package materialization | `17.539748` seconds |
| package verification | `16.265412` seconds |
| dependency cache | `42.017862` seconds |
| Lean build | `553.322734` seconds; build log reaches `8992/8992` |
| total elapsed | `660.198314` seconds |

The published snapshot is
`.workflow-runtime/cache/main/6769ce0a7274640b5deef277c966ea811808b3458b925548a4bf5b4c2392f1ce`.
Its manifest SHA-256 is
`aa7e13ea5bd1522d6be91e40e469646439bc2941b513b285d901563b17a673bb`, and
`READY` contains exactly that digest. The `READY` file SHA-256 is
`dffcc4273eb6009fae4a597094a39e2ec36c3497217fdb711958a3f79fc7b398`; the
build log SHA-256 is
`a42bef6f778293a8337c7d261877ac3f1189423bbd983b22586f4c172f109ae6`.

The deep `.lake` inventory independently verified against the manifest is:

```text
schema_version=1
sha256=fced5d201aa76027eacfbc5b53d6c7ffd486791a9af8ea466366fd9d4687af02
files=124925 directories=4147 symlinks=3 bytes=10097592794
```

The source contract remained exact at all five authored-QPBT boundaries:
337 foundation files / 5,970,111 bytes and two authored files / 5,319 bytes
with authored digest
`0578da860a522b58b69c2c16df366c7eee3abd97c425900401e4e83c992803ed`.
Mathlib evidence binds commit
`81a5d257c8e410db227a6665ed08f64fea08e997`, tree
`5ea66b811b8461daae82f14d356fed2a287d7c40`, and pack digest
`4659f2a0cabfec474474f5e83ea3d495e711b735418742dd3d642328adcada02`.

No second builder, seed, network request, GitHub operation, credential, or
shared writable build tree was used. The cache is deep-ready and QPBT-045's
production warm gate is satisfied.
