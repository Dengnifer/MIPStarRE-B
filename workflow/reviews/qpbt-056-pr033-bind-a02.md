# QPBT-056 / LPR-033 candidate binding (A02)

Session `i056-integrator-a02-pr033-bind` authenticated the immutable QPBT-056
candidate for no-byte-change adoption by `LPR-033`.

## Identity

| Item | Authenticated value |
| --- | --- |
| Canonical checkpoint | `e8b790a32c230aaf0f17ca2aa389ef41f94867f3` |
| Canonical checkpoint tree | `c60de65a6db6e86080bcb8cca73949d2876bd090` |
| Canonical checkpoint parent | `3ab1a03af5d19e5d0de02ad1080b313d62dedfda` |
| Candidate base / sole parent | `4cc1762f85da1bd46599311b77c4647d5f3c30b4` |
| Candidate base tree | `0da9b4f149b653ff5dfbcd9440016101c9dc1e7b` |
| Candidate head | `c1bfd95226e0c068f7d818689f56ab41088ff545` |
| Candidate tree | `27d113095e14b6063e6931f5dca6b8ee818edeca` |
| Binary patch SHA-256 | `5b59f3045a5835b22800f588ae7d8e38e7e73be067b6cc3f156365d6f3501464` |

The candidate worktree resolves to the exact head and is clean. The head has
the declared sole parent and exactly the two added paths below. Both
`git diff --check` and `git diff-tree --check` report no defect.

| Changed path | Git blob | File SHA-256 |
| --- | --- | --- |
| `MIPStarRE/QPBT/Game/Types.lean` | `1f8ffe50e1aefa3ba5946bd1e94e61a2c28319b1` | `db09fff1f8e9bb12b2c35d97503fc58954ab2600f98162b78b1d5c73c8d24191` |
| `workflow/reviews/qpbt-056-f06-a01.md` | `e6e4eb91b6bdad90ab9662d541b2ceb817e3ea93` | `d472542a9e141bf37e467140071c65bdf4546ebd389ecb6e0e0700aa88fd9b8a` |

The second row is the committed writer report. Its recorded identity agrees
with the archived writer session and with direct hashing from the candidate
commit.

## Canonical binding

At the immutable canonical checkpoint above, `LPR-033` is ready for
`QPBT-056` and binds base `4cc1762f85da1bd46599311b77c4647d5f3c30b4`,
head `c1bfd95226e0c068f7d818689f56ab41088ff545`, branch
`issue/qpbt-056-f06-a01`, and exactly the two changed paths listed above.
QPBT-056 is in review, has owner `i056-orchestrator-a01-f06`, and owns exactly
those two paths. The PR currently has no reviews or findings; its remaining
gate is this no-byte-change adoption check followed by fresh immutable
mathematical/API review and guarded integration.

All 6/6 registered checks are `passed` on the exact candidate base/head pair:

| Check | Recorded result |
| --- | --- |
| `check-qpbt-056-auth` | Exact commit, tree, sole parent, two new paths, clean worktree, and binary patch authenticated |
| `check-qpbt-056-scoped` | Final changed bytes elaborated without diagnostics in 5.23 seconds; exact 14-name API probe passed in 2.93 seconds |
| `check-qpbt-056-target` | Affected target passed across 3,085 jobs in 7.62 seconds; only inherited tracked G16 warning |
| `check-qpbt-056-full` | Private full build passed across 8,992 jobs in 7.32 seconds using one isolated private cache |
| `check-qpbt-056-blueprint-source` | 54 nodes, 12 chapters, 34/34 tests, and 39 source files with 646 labels synchronized |
| `check-qpbt-056-hygiene` | Frozen declaration surface, imports, debt, assumptions, workflow, and committed diff hygiene passed |

The archived writer session binds the same base, head, tree, blobs, file
digests, and patch digest. Its report records a proof-complete candidate, exact
14-name and two-import surfaces, clean target debt and forbidden-assumption
scans, and a fresh post-commit immutable review as the next required gate.

## Disposition and counters

Adopt exact head `c1bfd95226e0c068f7d818689f56ab41088ff545` in
`LPR-033` without changing candidate bytes, then obtain the required fresh
immutable mathematical/API review. This session changed and committed only
this binding report and made zero candidate-byte changes.

Before writing the report, authentication used six read-only shell batches,
16 Git invocations, three `sha256sum` invocations, and three `rg` invocations.
The final report-only Git inspection and commit accounting is returned out of
band with the binding commit identity. The session ran zero Lean, Lake, build,
cache, materialization, network, GitHub, credential, or nested-agent actions.
Exact per-agent token usage is `null` because the collaboration backend does
not expose per-agent token counts; no estimate is substituted. The root
coordinator records canonical lifecycle elapsed time from issued-session start
and terminal timestamps; a local authentication-to-commit elapsed measurement
is returned out of band.

The binding report's commit, tree, parent, Git blob, and SHA-256 are necessarily
returned out of band because the report cannot contain the identity of the
commit or blob that contains itself.
