# QPBT-031/032 current-main cache warm (A01)

## Result

The singleton hot-main builder authenticated and published the cache for main
commit `259c73a368ef7403b4e36e190c9bf940497b300f`.

| Field | Value |
| --- | --- |
| cache key | `d71a99abea8f7ebf5bda5194dfef088b06f526230caf5ccbca34d62d5b4267b9` |
| recipe | `qpbt-hot-main`, schema 3, version 5 |
| result | `built` / post-status `hit` |
| materialize MIPStarRE | 2.961076 s |
| materialize Lake packages | 17.839396 s |
| verify Lake packages | 17.460412 s |
| dependency cache | 44.195647 s |
| Lean build | 561.174118 s |
| total elapsed | 671.374626 s |
| build jobs | 8,992 (recipe command `lake --packages=.lake/package-overrides.json build`) |
| artifact inventory | 124,925 files; 4,147 directories; 3 symlinks; 10,097,592,794 bytes |
| inventory SHA-256 | `ae5e34a27c84bb6a2249de25f46725c37ba4d1f28d4802726e0742aa919066b4` |
| READY SHA-256 | `09f11171506031cdbd5a46a8d0ab799dbbb3dcc8f2757eb1d274e1841ab160a2` |
| manifest SHA-256 | `46e97bb51072592a49e29aea9deb70bc3fe3eef48ca13ba129b7f6e412a895a4` |
| build log SHA-256 | `3f8320eb643a3bcaa507c9b007025ea71941a49e15186462f014292f4f483e0d` |

The cache uses Mathlib archive SHA-256
`c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`, the
authenticated MIPStarRE archive pinned by `references/mipstarre-upstream.json`,
and the local Lake package archive directory
`.workflow-runtime/acquisitions/lake-packages-20260830`. Publication was
atomic and no writable build tree is shared with issue worktrees.

## Retries and omissions

Two preliminary invocations used the same exact cache identity and failed
closed before compilation: the first omitted `MIPSTARRE_ARCHIVE` (1.247245 s),
and the second omitted `LAKE_PACKAGE_ARCHIVES` (4.226712 s). The successful
invocation supplied all three authenticated local inputs. These are retained as
input-preflight evidence; no unchanged retry was used after publication.

## Handoff

QPBT-031 and QPBT-032 may each run `hot_main_cache.py seed` once in its private
worktree. A seed is a private copy-on-write/copy fallback and must not invoke a
second main build. The cache key, main SHA, and seed result belong in each
orchestrator's session metric.
