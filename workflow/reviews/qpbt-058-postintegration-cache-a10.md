# QPBT-058 post-integration cache evidence A10

The approved LPR-036 candidate was integrated byte-for-byte at main commit
`8d209d6d2b17d96d0f96c2a9b2f95495c57561eb` (tree
`c234100c01d4b11398e4c098ada6dd28e7e64932`). Its first parent is
`445b04c4253e46392d27e9151e212c5ab401e20d`; its second parent is the exact
reviewed candidate `e9fe2bd4747f36d63ec5b3623c5f0c5bda7149cf`. The merge changes exactly
the two reviewed QPBT-058 paths and reproduces candidate patch SHA-256
`aa23852932f524484c7f443f26cdb83d1b2389c42086ccf61c337f389e3c5442`.

## Validation

- `blueprint/check.py --check`: passed, 54 nodes across 12 chapters.
- Pinned-source check against the authenticated primary source root: passed.
- Blueprint tests: 36/36 passed.
- Source verification: 39 files and 646 labels passed.
- Scoped `lake env lean MIPStarRE/QPBT/Game/Types.lean`: passed, with only the
  two inherited F06A skeleton warnings.
- Signature probe: all 11 F07 declarations type-checked; no F07 theorem closure
  depends on `sorryAx`.

The first pinned-source invocation from the disposable integration worktree
could not see the intentionally ignored split-paper files. It failed before a
build. Re-running the same check against the authenticated primary source root
passed. This was a source-layout preflight miss, not a product failure.

## Singleton cache result

- Cache key: `21a7b15fd273fef0829d2ef790f152e6e0af02d4ba75a905e0583a758bcac187`
- Result: built; immediate status recheck: hit.
- Full build: 8,992 jobs passed.
- Build time: 643.598163 seconds.
- End-to-end warm time: 772.899268 seconds.
- Lock wait: 0.0 seconds; elected builders: 1; duplicate builders: 0.
- Materialization: 3.208658 seconds.
- Package materialization: 17.804950 seconds.
- Package verification: 19.160506 seconds.
- Dependency cache: 54.306261 seconds.

## Integrity

- Artifact inventory: 124,925 files, 4,147 directories, 3 symlinks,
  10,097,592,794 bytes.
- Artifact inventory SHA-256:
  `bc7a64236d2fa7dc1625a7304f525270954e1bc3076ebb0777f93917c28b9590`.
- Authored QPBT inventory: 7 files, 188,846 bytes, SHA-256
  `4c04b235008352b5690f648aba18e4c61a569ac37304bd0846923b17ca75a254`.
- Manifest SHA-256:
  `4a0f4a6de6c8c3bc25a513c3ac2f4405be2c9704a38af70607a1fdda48fc469d`.
- READY content: the manifest SHA-256 above.
- READY file SHA-256:
  `784c553af80d2631ecf93049b3f484ec98f6292d9c42a9c7ec5d4e0c7d3d6b4c`.
- Build-log SHA-256:
  `fce61f45f25031182476b7c769e3460c5059b9a842081d73d96ea3ebe4cf937c`.

Lean/Lake builds: 1. Cache publications: 1. Network, endpoint, GitHub,
credential, and nested-agent actions during the warm: 0. Token usage is
`null`; the root coordinator does not expose per-operation token usage.
