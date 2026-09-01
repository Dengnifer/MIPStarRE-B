# LPR-024 formal no-byte-change adoption

## Verdict

`authenticated for adoption`

The exact LPR-024 draft candidate is authenticated without changing candidate
bytes. The detached head, tree, sole parent/base, five-path manifest, writer
report, six registered check records, and diff scope agree with one another and
with the canonical LPR-024 record observed at the evidence cutoff. The candidate
is ready for a fresh independent immutable review.

This is identity/provenance adoption, not code review, PR approval, integration
approval, production cache-warm authorization, QPBT-045 acceptance, or INC-060
closure. The recorded test results were authenticated as committed evidence but
were not rerun because this session's dispatch explicitly prohibited tests,
builds, warms, and cache actions.

## Immutable Git binding

- PR: `LPR-024`; canonical status observed: `draft`
- Issue: `QPBT-045`; canonical status observed: `review`
- Base commit: `f4b00c7616b8710220a4f8480cfb23412914d151`
- Base tree: `f120a82f74df4d32bfb6b0491636546c7651b64a`
- Head commit: `bc41314fb74baced6f6a043cbc8956a18a2e0003`
- Head tree: `c71eb62b31004c1b219f93e25475d5f1aa7356b7`
- Direct ancestry: the head has exactly one parent, equal to the formal base
- Worktree state: clean and detached at the exact head before report creation
- Diff scope: exactly five paths, 621 insertions, and 7 deletions
- Diff hygiene: `git diff --check BASE..HEAD` passed independently with no output

Canonical `workflow/state/prs.json` binds this exact base/head pair and lists
the same five changed paths in the same path order. No rename inference or
working-tree fallback was used.

## Five-path manifest

The byte-exact, path-sorted `git ls-tree HEAD -- <five paths>` output, including
trailing newlines, has SHA-256
`2707b1097d9d3cc4ba2588f54b88ea8ac159ce8c6d0d3e3ec08d91ea0b38fd26`.
It exactly matches the canonical authentication check and the dispatch-bound
digest.

| Path | Mode | Git blob | Bytes | Filesystem SHA-256 |
| --- | --- | --- | ---: | --- |
| `protocols/CHANGELOG.md` | 100644 | `6ccc5f77f8b930e6fac418d3d6ee85a8807ad756` | 25664 | `4c11a5c983ccd924a3f72b2693f7970f0ce17f656af5a7f4aba7115fc8a1ba39` |
| `protocols/local-development.md` | 100644 | `9ad77b3a3be39300101d4c901791a3c310ef833b` | 5767 | `b34dadd5e22b3a9681eb950087eebdccf21b15849e98bdd1149fa98ded6213c6` |
| `scripts/hot_main_cache.py` | 100644 | `126ab84935d9528b2aaaa71366966538df9a9664` | 117069 | `35b1bd45155f95095beecd7f77a34ba4a734939e8dd8f64b0baf811228b5e8dc` |
| `tests/test_hot_main_cache.py` | 100644 | `82663231536a19063fe394ca03d0fb60d178534c` | 96389 | `28fc2ddf6472550f7f7abed433196be809694d401586c06cbea5e2fb9433cde5` |
| `workflow/reviews/qpbt-045-hot-main-preservation-a01.md` | 100644 | `e1d84f82f2f65c66581b39c91c3411a687212397` | 8147 | `738890e5eaa16e9d29efda6e1b1153a555744380aab2c5e20093adae073e15e5` |

All five entries are ordinary files. Their filesystem bytes agree with their
authenticated committed blobs. The writer report SHA-256 is exactly
`738890e5eaa16e9d29efda6e1b1153a555744380aab2c5e20093adae073e15e5`,
matching the dispatch.

## Six-check authentication

Every registered check has canonical status `passed`, exact base
`f4b00c7616b8710220a4f8480cfb23412914d151`, exact head
`bc41314fb74baced6f6a043cbc8956a18a2e0003`, and the authenticated writer report
as its result path.

| Check | Canonical claim | Adoption evidence | Verdict |
| --- | --- | --- | --- |
| `check-qpbt-045-auth` | immutable candidate authentication | Head, tree, sole parent, clean detached state, five paths, and manifest digest independently reproduced | authenticated and independently reproduced |
| `check-qpbt-045-focused` | hot-cache regressions 51/51; 11.26 s wall | Exact result and timing appear in the authenticated committed report | authenticated recorded evidence; not rerun |
| `check-qpbt-045-materializer` | materializer regressions 11/11; 0.41 s wall | Exact result and timing appear in the authenticated committed report | authenticated recorded evidence; not rerun |
| `check-qpbt-045-aggregate` | aggregate regressions 349/349 in one attempt; 183.12 s wall | Exact result, attempt count, and timing appear in the authenticated committed report | authenticated recorded evidence; not rerun |
| `check-qpbt-045-workflow` | validation/checker and checker tests 3/3 passed | Exact command family and result appear in the authenticated committed report | authenticated recorded evidence; not rerun |
| `check-qpbt-045-diff` | `git diff --check BASE..HEAD` passed | Reproduced independently with empty output | authenticated and independently reproduced |

The writer report also records one passed compileall attempt, zero Lean/Lake
compiles, zero production cache operations, and the still-pending independent
review and guarded current-main warm. Those statements remain report evidence;
this adoption session does not elevate them into new execution evidence.

## Byte-preservation and scope

The candidate worktree was clean before authentication and remained clean after
all reads. HEAD, tree, parent, path list, manifest, blob identities, filesystem
hashes, report hash, and diff hygiene were unchanged. This report is outside the
candidate worktree and its five-path manifest. No candidate file, repository
file, index, ref, or Git object was written.

No test, build, Lean/Lake command, cache warm, cache seed, publication, network
request, endpoint request, GitHub operation, credential access, or nested-agent
dispatch occurred. No canonical workflow state, event, research, or metrics
file was edited.

## Session metrics

- Stable session: `i045-integrator-a02-pr024-bind`
- External thread: `/root/i045_pr024_bind_a02`
- Topology: root coordinator -> one formal no-byte-change adoption integrator;
  nested agents: 0
- Durable dispatch start: `2026-09-01T16:42:49.025480Z`
- Evidence cutoff: `2026-09-01T16:44:33.917614Z`
- Agent elapsed through evidence cutoff: `104.892134s`
- Timing quality: canonical durable-dispatch start plus agent UTC evidence sample
- Token usage:
  `{"input":null,"output":null,"total":null,"availability_reason":"Collaboration backend does not expose per-agent token usage"}`
- Candidate/repository paths edited: 0; report files edited: 1
- Git writes and canonical state/event/metrics/research edits: 0
- Tests, builds, Lean/Lake, warm/seed/cache, network, endpoint, GitHub, credential,
  and nested-agent actions: 0
- Authentication counters: 1 head, 1 tree, 1 sole parent/base, 5/5 manifest
  paths, 5/5 filesystem/blob byte matches, 1 manifest digest, 1 writer-report
  digest, 6/6 check bindings, and 1 diff-hygiene reproduction

Only `/tmp/qpbt-045-pr024-bind-a02.md` was written. Its final SHA-256 is supplied
out of band to the root coordinator.
