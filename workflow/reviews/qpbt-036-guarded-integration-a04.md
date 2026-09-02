# QPBT-036 / LPR-027 guarded integration A04

## Verdict

**Integrated.** The exact approved Polynomial candidate was merged into the
authenticated current `main` in an isolated worktree, validated, fast-forwarded
to canonical `main`, pushed, and verified on `github/main`.

## Immutable identity

| Item | Value |
| --- | --- |
| Canonical base | `309973aaccf258b92486e26ce392863ebc1fdb40` |
| Candidate head | `8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` |
| Candidate parent | `358cd108db045d13f4e0095a2948dd4037be2b54` |
| Candidate tree | `50fec3a3a7611f63aacff2f15568812e123ca29d` |
| Candidate manifest SHA-256 | `0e7fd38a46b63c7ee660fa14fb828e19331233b0c983a687b1a38d0a2ceb3725` |
| Integrated file SHA-256 | `cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c` |
| Integration commit | `4e003ec80d6bd772530fef854b68dd4ee787906f` |
| Integration tree | `081f77396adec00e1f6b7733af8d17ea18203bf5` |
| Ordered parents | `309973aaccf258b92486e26ce392863ebc1fdb40`, `8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` |
| First-parent path | `MIPStarRE/QPBT/Basic/Polynomial.lean` only |

## Validation

| Gate | Result | Elapsed |
| --- | --- | ---: |
| Hot-main warm for exact base | cache miss; one elected build, 8,992 jobs | 656.576 s |
| Private cache seed | cache hit; 124,925 files / 10,097,592,576 bytes | 72.692 s |
| Pinned foundation materialization | source `507e81220d95266ff3d589d125b2f87c7300a9fb` | 2.872 s |
| Initial scoped check | failed only because the cache lacked unreferenced `Field.olean` | 1.76 s |
| `lake build MIPStarRE.QPBT.Basic.Field` | passed; existing tracked G16 `sorry` warning only | 3.90 s |
| `lake env lean MIPStarRE/QPBT/Basic/Polynomial.lean` | passed; lint warnings only | 3.17 s |
| `lake build MIPStarRE.QPBT.Basic.Polynomial` | 2,358 jobs passed | 4.42 s |
| `lake build` | 8,992 jobs passed | 6.02 s |
| default and pinned-source blueprint checks | 54 nodes / 12 chapters passed | 0.19 s |
| workflow validation and checker | passed | 0.30 s |
| owned debt scan and `git diff --check` | passed; no candidate proof debt | <0.1 s |

The initial scoped failure did not compile the candidate and was not retried
unchanged: the missing prerequisite target was built once, after which the
mandated scoped check passed. No second main-cache builder ran. A fresh
read-only integration-risk review reported no findings and confirmed that the
Polynomial and Parameters commits are disjoint and conflict-free.

## Publication

Canonical `main` was later fast-forwarded through this merge and the sequential
Parameters merge. Push succeeded on the first attempt; `git ls-remote github
refs/heads/main` returned final descendant
`4a6683795a71712d6a5c52b7539c2f532fd39f71`.

Token usage is `null`: the integration ran in the root coordinator and the
available tooling exposes no per-operation token counter. Nested implementation
agents: 0; independent read-only integration scouts: 2.
