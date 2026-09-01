# QPBT-050 / LPR-026 guarded integration A03

## Verdict

**Integrated in an isolated object database; canonical refs remain read-only.**
The approved LPR-026 candidate blobs were applied selectively to the
authenticated current base. The candidate branch was not merged wholesale,
so its stale workflow-state history was excluded. The imported A03 security
review report and all current canonical workflow files were preserved.

## Authentication

| Item | Value |
| --- | --- |
| Current base commit | `d4a9c589c0e26cd85dc355a428d80cadd5d0225e` |
| Current base tree | `d7127278f8d02ef00033cda151c2bb55e719b1a2` |
| Candidate head | `c70267e3d65aeb3c47b4680ab53693c5b9ead6fa` |
| Candidate tree | `1c1be2d9c9e7c790842fab47077055f929826c06` |
| Candidate sole parent | `5e67781ac40cb3f0bfda141e6b631479db994ba7` |
| Candidate parent-to-head manifest | `a3358d0d5ce28b5569eaaff61872f9f231c47d693c0df31996ef732e2b8319da` |
| Candidate A03 report SHA-256 | `8bfefa83a421eb2a7c8bfb49dbbae20ccae04eaae720d0d29249c42bf88c82fd` |
| Integration commit object | `95adaf43b7964bee9f76429742302cef003d20ce` |
| Integration tree | `43d053038eb0dfadd498ff7e614bc7f17f099cfd` |
| Integration parents | `d4a9c589c0e26cd85dc355a428d80cadd5d0225e`, `c70267e3d65aeb3c47b4680ab53693c5b9ead6fa` |
| Resulting base-to-integration path manifest | `26ee9f688b059b6ba424800c77b98f7401a06af1bc816621d7079a87c5604274` |

The candidate changed implementation/test/A02 report blobs and the preceding
A01 hardening report blob were authenticated exactly:

```text
scripts/hot_main_cache.py d2f8f92a633334d35d86816e9746db9f85a183bb
tests/test_hot_main_cache.py 6092e4ac7ef1e30203ffcb220e4273b8cf8d8706
workflow/reviews/qpbt-050-fsmonitor-hardening-a01.md 1757017446f7faa6c643ae6f4c4cf3ed041f30af
workflow/reviews/qpbt-050-fsmonitor-repair-a02.md fcc92d662354456392d4fa90e7b6ac2af68e4f2e
```

The imported A03 report remains blob `55bc29dcf8c745031080466b4d22b8bf0efa5519`
and SHA-256 `8bfefa83a421eb2a7c8bfb49dbbae20ccae04eaae720d0d29249c42bf88c82fd`.
No `workflow/state/*` or `research/metrics/*` path is in the integration diff.

## Validation

| Gate | Result | Elapsed |
| --- | --- | ---: |
| `python3 tests/test_hot_main_cache.py` | 62/62 passed | 12.31 s |
| `python3 -m compileall scripts tests` | passed | 0.20 s |
| `python3 scripts/workflow.py validate` | valid (52 issues, 26 PRs, 417 issued sessions, 7 stages) | 0.13 s |
| `python3 scripts/check_workflow.py --skip-tests` | valid | 0.13 s |
| `git diff --check` | passed | 0.03 s |
| candidate blob/path identity | exact; four selected blobs match candidate | <0.1 s |

The focused suite includes the approved fsmonitor-hook and hostile ambient-Git
seed regressions. No production `warm`/`seed`/publication, hot-cache cache
publication, Lean/Lake/build, network, endpoint, GitHub, credential, or nested
agent operation was performed.

## Integration mechanics and metrics

The linked worktree's shared index and object database reject writes with
`Read-only file system`. The integration merge and final report commit objects
were therefore created in `/tmp/qpbt050-objects-a03` using the repository object
store as read-only alternates; the exact tree and parent authentication above
remains reproducible. The worktree files match the integration tree's selected
blobs; canonical ref publication is deferred to the coordinator.

- Session: `i050-integrator-a03-guarded-integration`
- External identity: `/root/integrator050_bootstrap`
- Topology: root coordinator -> one integrator; nested agents 0
- Token usage: `null` (collaboration backend does not expose per-agent token usage)
- Compile attempts: 1 Python compileall; Lean/Lake attempts 0
- Cache actions/publications: 0; cache lock acquisitions 0
- Retries: 1 materialization retry using temporary index; incidents: 1 read-only Git metadata
- Candidate branch merge: excluded except for the four authenticated blobs
- Report SHA-256: recorded by coordinator after this file is finalized
