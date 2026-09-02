# QPBT-051 / LPR-034 no-byte-change adoption binding

Session `i051-integrator-a02-pr034-bind` authenticated the immutable QPBT-051
candidate for no-byte-change adoption by `LPR-034`. This is provenance and
sequencing evidence, not the required formal security review or approval.

## Immutable identity

| Item | Authenticated value |
| --- | --- |
| Integration checkpoint | `20745fe45450276db3c2130d2631d863e8346ba3` |
| Integration checkpoint tree | `c8be3a058203b155491847bac50caface74a8fb0` |
| Candidate base / sole parent | `e8b790a32c230aaf0f17ca2aa389ef41f94867f3` |
| Candidate base tree | `c60de65a6db6e86080bcb8cca73949d2876bd090` |
| Candidate head | `767606694e62aefd105959dbb5a979b041ae0d65` |
| Candidate tree | `f504453fa9da540e5a3953e4c1710c9c1e48760f` |
| Binary patch SHA-256 | `c083e3a1389cf63dd39f19027f25ae7fd00ef43317e8b62f4d065b1827d5cada` |
| Six-entry `git ls-tree` SHA-256 | `a69bde5df2ed20eaa1d904c72533ad6773895494634c5a14d4ae24638efac9b1` |

The candidate worktree is clean at the exact head. The head has exactly the
declared base as its sole parent. Its diff is exactly six ordinary files, 379
insertions and 7 deletions; both `git diff --check` and `git diff-tree --check`
returned no output.

| Changed path | Git blob | Bytes | File SHA-256 |
| --- | --- | ---: | --- |
| `protocols/CHANGELOG.md` | `5afed1ae027612647c6816ea692665308afada26` | 26872 | `2ecd44fdc3127b6d89a79e06c1db79369cd3d0f53b05747847c3e0954236c4c7` |
| `protocols/local-development.md` | `48bc6212bf72266d1f493e049e1351ee86668069` | 7161 | `c559d0ff8676e7d48a422729a03617d74051cb1ad6390dfe39e4db220b3de3cc` |
| `protocols/orchestration.md` | `5a469bdc97423d0eedcede02babefcc5f4e7c41b` | 15576 | `35503f09ece81a62ed5d13ff035b87a33a6490dd25bf0d7fb1bbb3e94ea6eebf` |
| `scripts/hot_main_cache.py` | `2cea60b535921b18b7c1512613d691544bcdcb8f` | 133004 | `671c318d26e9261617d8263deae2451578bddaa16e5dce3a5144abe253cef52a` |
| `tests/test_hot_main_cache.py` | `3daecbf31ce69f34b8b5f65d8c3dd7f8ab40dcea` | 118963 | `b0efb296e8afc7312341279678ddef57ba6fb75c65a959ac706a24348b61feed` |
| `workflow/reviews/qpbt-051-input-preflight.md` | `a393f6d4acc433156ab04fffc44ab4cdf1fc5bf0` | 4394 | `f747705e4a80a45002bff0656bc789f36a3ed0b3801af54edf042328186d7524` |

The final row is the writer report. Its direct committed-byte digest matches
the archived writer session and every registered check result path.

## Canonical binding and compatibility

At the evidence cutoff, canonical `LPR-034` is `draft` for `QPBT-051` and binds
the exact base, head, branch, and ordered six-path list above. It has no reviews
or findings. QPBT-051 is in `review` with owner
`i051-orchestrator-a01-preflight` and exactly the same six owned paths.

All 6/6 registered checks are `passed` on the exact base/head pair:

| Check | Recorded result |
| --- | --- |
| `check-qpbt-051-auth` | Exact commit, tree, sole parent, six paths, clean worktree, and patch digest authenticated |
| `check-qpbt-051-compile` | Python compilation passed |
| `check-qpbt-051-focused` | Focused hot-cache tests passed `66/66` |
| `check-qpbt-051-workflow-tests` | Checker `3/3` and workflow tests `77/77` passed |
| `check-qpbt-051-aggregate` | Effective aggregate `363/363` after the two sandbox-denied Unix-socket tests passed in a bounded rerun |
| `check-qpbt-051-hygiene` | Exact ownership, whitespace, and workflow validation passed |

These are authenticated committed records, not reruns by this session. The
archived writer session independently binds the same base, head, tree, parent,
patch, report digest, 6/6 path scope, and test results. It records zero Lean,
Lake, build, real cache, real materialization, network, endpoint, GitHub,
credential, and nested-agent actions.

Main advanced from the candidate base to the integration checkpoint through
five commits and changed eleven paths. The intersection of those eleven paths
with the candidate's six paths is empty. Therefore no candidate path changed on
main after the candidate base, and adoption requires no byte reconciliation.

## Limited sequencing inspection

The complete-input implementation was inspected far enough to make this
adoption meaningful. `_preflight_authenticated_inputs` retains the exactly-one
Mathlib selector check, requires absolute local MIPStarRE and Lake-package
archive bindings, validates the committed pin/manifest shapes, and checks the
pinned regular-file byte counts and SHA-256 values. Non-dry-run `warm` calls it
before cache-hit handling or lock acquisition and again after election.

Non-dry-run `prepare` authenticates that tuple, records the authored QPBT
inventory, deep-seeds the private cache, loads and validates the issue
worktree's pinned materializer, calls it with `replace_existing=True`, requires
the authored inventory to remain equal, and only then verifies the materialized
foundation. Its CLI branch delegates directly to this sequence. The focused
tests bind missing-input failure before lock/snapshot/`READY`, exact archive
authentication, successful seed/materialize/verify order, mandatory replacement,
and rejection of authored drift before verification.

This inspection does not decide adversarial path/race behavior, implementation
soundness, or approval. The fresh immutable security review, guarded
integration, and post-integration verification recorded by LPR-034 remain
required.

## Accounting

- Durable session start: `2026-09-02T23:14:10.425175Z`.
- Evidence cutoff: `2026-09-02T23:17:47.062996464Z`; measured elapsed through
  cutoff: `216.637821s`.
- Authentication counters: 1 head, 1 tree, 1 sole parent/base, 6/6 paths, 6/6
  blob/file-digest matches, 1 path-manifest digest, 1 writer-report digest, 1
  binary-patch digest, 6/6 check bindings, and 0/6 main-path conflicts.
- Candidate/repository bytes changed: 0; owned report files changed: 1.
- Lean, Lake, build, cache, materialization, network, endpoint, GitHub,
  credential, and nested-agent actions: 0.
- Token usage is `null`; the collaboration backend exposes no per-agent token
  counts, so no estimate is substituted.

The report-only commit/tree/parent and this report's Git blob and SHA-256 are
returned out of band because a committed report cannot contain its own object
identity. Final cleanliness is also reported after commit.
