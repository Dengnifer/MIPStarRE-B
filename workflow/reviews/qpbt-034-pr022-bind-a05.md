# LPR-022 formal no-byte-change adoption

## Verdict

`authenticated for adoption`

The independently approved LPR-022 candidate is authenticated without changing
candidate bytes. The exact detached head, tree, base ancestry, seven-path
manifest, implementation report, approving review, and both finding
dispositions agree with canonical PR state. The candidate is ready for the root
coordinator's guarded canonical adoption and integration steps.

This report does not change LPR-022's canonical `changes_requested` status,
QPBT-034's canonical `review` status, metrics, research records, candidate
files, or Git history.

## Immutable binding

- PR: `LPR-022`
- Issue: `QPBT-034`
- Base commit: `17608ac90f1896cc019e8a7a7619ada6a3c05cef`
- Base tree: `6d7e8918d1ff9bc19fa672923eaf339e56c2c535`
- Head commit: `f672839e2d221cba44e70db6ab523eebdd4d0d4a`
- Head tree: `119e7f038655033878c874b074cbcf9c477cba32`
- Worktree state: detached at the exact head
- Direct ancestry: pass; `git merge-base` is the exact PR base
- Ancestry path after the base: `3683e4b8128f3c442c64b7b271c9245109cd6441`,
  `1c01622d672514c9b91e61ff4d03b27583a6391f`,
  `7811f53c00bf168416650cf19e7e51002e6e7cb7`, and the exact head
- Diff scope: exactly 7 paths, 1007 insertions, 43 deletions

Canonical `workflow/state/prs.json` binds the same base and head and lists the
same seven changed paths. Canonical `workflow/state/issues.json` identifies
QPBT-034 and requires the two A02 findings to be resolved on a changed head with
a fresh immutable review; those gates are evidenced below.

## Seven-path manifest

| Path | Mode | Git blob | Bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| `protocols/CHANGELOG.md` | 100644 | `4aa7d5a92cab5468368dd7d1043ef7c1eee084dd` | 24033 | `eaff089ae3a0dad1ce2ebeebff64f4de42314cc1ac3a571135f6d056944b131b` |
| `protocols/orchestration.md` | 100644 | `61f53c35ffa69ed61997dc97454e2963c1c4eb65` | 15124 | `c31cfde4c0dbece6af1cf24700a99b2702129e668e1e89b9bcae89341d5f1f30` |
| `scripts/workflow.py` | 100644 | `7695df623ea4c1dad220411def36e30fa3df3f88` | 141266 | `04e0d92a5f52949322a4c5089269cc9f223b0e32f3ca36c3b6b6651ded0b02ab` |
| `tests/test_local_agent.py` | 100644 | `75a8a33e1928da0dc8635abafb33cc7815f4d0b2` | 117762 | `71c249c9e3927e0e491498e4f8d0d5d20888ec2de3b437c5741e9a555dd4541d` |
| `tests/test_workflow.py` | 100644 | `04dd1a8e6f22ba7608f29652cf74d9d021a968fe` | 98446 | `cae992aaae2afe21ff37903e9345ae8b9e939da5699a1d67766ba3c743c65e0e` |
| `workflow/reviews/qpbt-034-live-admission-a01.md` | 100644 | `c97e4b0c192664479703fd7c0e99fa864bb1b218` | 8993 | `81e60885fff4c8f8961105f3ffe8adfb33090032538b07e8208b0f0957e9390d` |
| `workflow/reviews/qpbt-034-live-admission-a03.md` | 100644 | `72b0e1d21f7fdf626850ff946dbd3c392c51874d` | 7949 | `fef150cf4d9618817d414c69623d47e6109fbb2eaee7c479ede90c852d2ec837` |

The A04 manifest records were extracted and hashed independently. Result:
`2f81f811a8043caf7a76b2e84cdc9830b395ac6a5fc600790c3fdd904ad925d5`,
exactly matching the approving review and canonical PR review record.

## Review-chain authentication

- A02 immutable review:
  `workflow/reviews/qpbt-034-pr022-review-a02.md`, SHA-256
  `2371d3578022674699566184e2a75fa2f4f934a88a04a7f048b8184f4f9c3b6c`;
  verdict `request_changes` at head `1c01622d672514c9b91e61ff4d03b27583a6391f`.
- A03 repair report:
  `workflow/reviews/qpbt-034-live-admission-a03.md`, SHA-256
  `fef150cf4d9618817d414c69623d47e6109fbb2eaee7c479ede90c852d2ec837`;
  its committed blob and working-tree bytes are exact.
- A04 resolution review:
  `workflow/reviews/qpbt-034-pr022-resolution-a04.md`, SHA-256
  `be8edc8454ea5a3e792cd4619434a29b44caa85e714a464e65e25c717e5636b9`;
  verdict `approve`, formally bound to the exact PR base and exact candidate
  head above.

The canonical A04 review record repeats that exact base/head binding, records
zero new findings, and resolves both prior finding IDs.

## Finding dispositions

- `F-LPR022-001`: canonical status `resolved`, disposition `fixed`, resolved by
  `review-qpbt-034-pr022-a04-resolution`. The changed head scopes prelaunch
  confirmation to `codex-collaboration` and preserves the governed `codex-cli`
  null-ID lease through real runner-ID import.
- `F-LPR022-002`: canonical status `resolved`, disposition `fixed`, resolved by
  `review-qpbt-034-pr022-a04-resolution`. The changed head restores exact
  sessions/event snapshots for `BaseException`, re-raises, and passes the five
  publication-boundary interrupt matrix with deterministic retry.

The A04 report independently replays both fixes and records workflow 77/77,
local-agent 64/64, aggregate 344/344, checker 3/3, compileall, canonical
validation, and diff hygiene as passing. This adoption session intentionally
did not repeat test, build, Lean, Lake, or cache actions.

## Byte-preservation check

Before this report was created, `git status --porcelain=v1
--untracked-files=all` was empty. Every candidate working-tree file above
matched its authenticated SHA-256 and committed blob. After report creation,
tracked status remained empty, HEAD and tree remained exact, all seven hashes
remained exact, and this report was the sole untracked path. It is outside the
seven-path candidate manifest. No candidate byte or Git object was changed.

## Metrics and scope

- Stable session: `i034-integrator-a05-pr022-bind`
- External thread: `/root/i034_integrator_a05_pr022_bind`
- Topology: root coordinator -> one formal no-byte-change adoption integrator;
  nested agents: 0
- Started: `2026-09-01T14:07:56.296176Z`
- Evidence cutoff: `2026-09-01T14:11:10.109743525Z`
- Agent elapsed through evidence cutoff: `193.813567525s`
- Timing quality: canonical durable-dispatch start plus agent UTC evidence
  sample
- Token usage: `{"input":null,"output":null,"total":null,"availability_reason":"Collaboration backend does not expose per-agent token usage"}`
- Candidate paths edited: 0; report files edited: 1
- Git writes: 0; canonical state/event/metrics/research edits: 0
- Endpoint/network/GitHub/credential operations: 0
- Tests, Lean/Lake, build, and cache actions: 0
- Agent spawns, nested dispatches, and external actions/messages: 0
- Authentication counts: 7/7 manifest paths, 3/3 report hashes, 2/2 finding
  dispositions, and 1/1 approving review head bindings matched

Only `workflow/reviews/qpbt-034-pr022-bind-a05.md` was written. Its final
SHA-256 is supplied out of band to the root coordinator.
