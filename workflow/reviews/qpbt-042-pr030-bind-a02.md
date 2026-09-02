# QPBT-042 / LPR-030 candidate binding

Session `i042-integrator-a02-pr030-bind` authenticated the immutable QPBT-042
candidate for no-byte-change adoption by draft `LPR-030`.

## Identity

| Item | Authenticated value |
| --- | --- |
| Base / sole parent | `c1d6271394fa9aba6eefb27955618a4540469c2f` |
| Candidate head | `16a41327abd1a3fd749c8872c2773f013046d762` |
| Candidate tree | `b52d1894da91c68edfd6b58b2eaf6a177faa4154` |
| Sole changed path | `MIPStarRE/QPBT/Game/Semantics.lean` |
| Lean blob | `e881b7beadc9c9f9ff675341dfdf74fb9fb83f59` |
| Lean SHA-256 | `3f87a8c6ea14f326bc046bb77f6e914552acb0e0963ba1382aa31966fe5e807e` |
| Binary patch SHA-256 | `edcaa0c2eb344754b2811774bebc53fca3d33ddf132b2aa959171a98b0e08246` |

The candidate worktree was clean. At immutable canonical checkpoint `8040a47`,
`LPR-030` binds the same base/head and sole changed path, and all 6/6 registered
checks are passed on that exact pair. At the same checkpoint, `QPBT-042` remains
in review with the same sole owned path and the expected dependencies.

## Evidence

The A01 report at canonical checkpoint `8040a47` authenticates the 18-callable
inventory, source ranges, faithful-boundary statement-integrity table,
validation results, private-cache metrics, and zero proof debt or forbidden
assumptions. Its SHA-256 is
`dfcc194a42105cb46030765ee9206af4e039ea194411540a5c920199c83827fc`.

Exact evidence hashes were independently reproduced:

| Evidence | SHA-256 |
| --- | --- |
| pinned `strategies-distance.tex` | `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f` |
| frozen game-semantics API report | `f37ab823449c85b078330f3912b4ec8eedfc67b8c9ffedb1d1b261434ccc4b27` |
| frozen Q014 contract report | `f98f21f7a9f355ca2f2af4e8ef20a3390f995430d045427b79b1c1a7ed93e1e8` |

## Disposition and counters

Adopt the exact candidate in `LPR-030` without changing candidate bytes. No
finding or paper-gap note was opened. This session made one report-file change,
zero candidate changes, zero compile/build/cache attempts, zero network or
credential operations, and spawned zero nested agents.
