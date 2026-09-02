# QPBT-039 / LPR-028 guarded integration A04

## Verdict

**Integrated and published.** The exact approved Parameters candidate was
merged on top of the validated Polynomial integration, checked in the same
private cache, fast-forwarded to canonical `main`, pushed, and authenticated on
the remote.

## Immutable identity

| Item | Value |
| --- | --- |
| Canonical integration base | `4e003ec80d6bd772530fef854b68dd4ee787906f` |
| Candidate head | `f6b19fc9fb87e0616b8367749ff971539bc1b45f` |
| Candidate parent | `874dc07433936e26d62c42cdd779dde42386f99d` |
| Candidate tree | `19df34c6a5687eff9bf64611c8880e45b3ea4339` |
| Candidate manifest SHA-256 | `4a26a5faf9611c9e689ef03e253f5a4fbfe164d92ac86288eed3aac2422df539` |
| Integrated file SHA-256 | `2f749aca171739bf57d4a7945fbdbdc55bdaf83418a4cabe1a6582520b3ec2e5` |
| Integration commit | `4a6683795a71712d6a5c52b7539c2f532fd39f71` |
| Integration tree | `66b39bdec8764c71aad5544a3ca8581ced44dbfb` |
| Ordered parents | `4e003ec80d6bd772530fef854b68dd4ee787906f`, `f6b19fc9fb87e0616b8367749ff971539bc1b45f` |
| First-parent path | `MIPStarRE/QPBT/Game/Parameters.lean` only |

## Validation

| Gate | Result | Elapsed |
| --- | --- | ---: |
| `lake env lean MIPStarRE/QPBT/Game/Parameters.lean` | passed | 1.97 s |
| `lake build MIPStarRE.QPBT.Game.Parameters` | 2,358 jobs passed | 3.10 s |
| incremental combined `lake build` | 8,992 jobs passed | 5.72 s |
| default and pinned-source blueprint checks | 54 nodes / 12 chapters passed | 0.19 s |
| workflow validation and checker | passed | 0.27 s |
| owned debt scan and `git diff --check` | passed; no candidate proof debt | <0.1 s |

This merge reused the private cache seeded once for the Polynomial merge. It did
not warm, seed, or compile a duplicate main snapshot. A fresh read-only
integration-risk review found no interaction: the modules have disjoint paths
and declarations and share the unchanged `Field.lean` dependency.

## Publication

Push to `github main` succeeded on the first attempt. The independent remote
readback returned exact SHA
`4a6683795a71712d6a5c52b7539c2f532fd39f71` for `refs/heads/main`.

Token usage is `null`: the integration ran in the root coordinator and the
available tooling exposes no per-operation token counter. Nested implementation
agents: 0; independent read-only integration scouts: 2.
