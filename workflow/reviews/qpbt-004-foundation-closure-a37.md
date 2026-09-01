# QPBT-004 foundation acceptance reconciliation (A37)

## Outcome

The three written QPBT-004 acceptance gates pass on immutable base
`942f9438b991ece8942815db16c019b92d9cdd8e` (tree
`09123f4b25c892a146aabaa77d73cf0c5f35a0c6`). No project byte required a
change under the acceptance-only rule. The previously reviewed LPR-005
foundation integration is an ancestor of the base, its seven project/pin paths
remain byte-identical, the exact-base singleton hot cache built successfully,
and `MIPStarRE.lean` type-checked from a private seed.

This is orchestrator acceptance evidence, not self-approval. The independent
LPR-005 approval remains the mathematical/project review authority. Root may
use this report to move QPBT-004 to independent closure review.

| Written gate | Evidence | Verdict |
|---|---|---|
| Lean and Mathlib pins are recorded | `lean-toolchain` is `leanprover/lean4:v4.32.0`; root `lake-manifest.json` and the upstream provenance pin agree on Mathlib `81a5d257c8e410db227a6665ed08f64fea08e997` | pass |
| Reusable imported foundations have provenance | Upstream commit `507e81220d95266ff3d589d125b2f87c7300a9fb`, exact authenticated archive, exact 337-file inventory, and nine unique path/SHA-256 foundation entries are recorded and rebound by the warm manifest | pass |
| The empty project build and local cache gate pass | One elected recipe-v5 warm built all 8,992 jobs; status was `hit`; a private seed passed; `lake env lean MIPStarRE.lean` exited 0 | pass |

## Immutable authority

- Logical session: `i004-orchestrator-a37-foundation-closure`.
- Branch/worktree: `issue/qpbt-004-lean-foundations-a01` in the session-owned
  linked worktree.
- Exact base/head before this report:
  `942f9438b991ece8942815db16c019b92d9cdd8e`.
- Exact base tree: `09123f4b25c892a146aabaa77d73cf0c5f35a0c6`.
- Base parent: `711a178cdc706c594d8e614d06a23ad4c9bf2cf3`.
- LPR-005 integration
  `687e182c7ad41520c226a59160c084ab53ad6f38` is an ancestor of the base.
- `git diff --exit-code 687e182..942f943 --` over `MIPStarRE.lean`,
  `lakefile.toml`, `lake-manifest.json`, `lean-toolchain`, and all three
  provenance pins passed with no output.
- The worktree was clean before operational work. Its only ignored runtime
  outputs afterward were the private `.lake/` tree and Python bytecode caches.

## Pin and provenance evidence

The exact tracked SHA-256 values are:

| Path | SHA-256 |
|---|---|
| `lean-toolchain` | `2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e` |
| `lakefile.toml` | `a1c61e97b41ec1fcbf15345a18117540ebc2d9f6f6cfa1021580479e2e9bafdf` |
| `lake-manifest.json` | `d20abbe9525a311d501feb89299492717e27c88f441ac77191d9394b49e47fa9` |
| `references/mipstarre-upstream.json` | `d5db77534d52be40e247715ed7bb5007b1bc89ac437d545854f6f35cebb2461b` |
| `references/mathlib-lake-manifest.json` | `015c7e00ead0f05f2a72b32d9bdef782d4689d05a6297f0ceb0ab5d196c164bd` |
| `references/lake-packages.json` | `08b3b5b26cb8aec598ef396a31b1a08971bdf6ec76b626fb3735fe866546b4f0` |
| `MIPStarRE.lean` | `ce172123d2b7c08b98398a39abdee70899509f347293d2e8f203abd53d5ba40d` |

The upstream archive is SHA-256
`656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`
and 1,989,153 bytes. The source contract records 337 files, 5,970,111 bytes,
and inventory SHA-256
`d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.
All nine selected foundation paths are unique and have 64-hex SHA-256 values.
No upstream source is tracked; the pin still records redistribution permission
as not established and requires local materialization.

The Mathlib archive used by the warm is 51,938,317 bytes with SHA-256
`c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`.
Exactly eight authenticated transitive package archives were supplied locally.
There was no network acquisition.

## Singleton warm and cache evidence

The warm was explicitly bound with `--main-commit 942f9438...`; the primary
`main` ref had advanced for root-owned state work and was not used to compute
this cache identity.

| Field | Value |
|---|---:|
| cache key | `4a5d9cf4d7de3d89c9bf7805d59f5c1739b39fd56d66b19b2454941da8873807` |
| recipe schema/version | `3` / `5` |
| result/status | `built` / `hit` |
| cache hit/miss | `0` / `1` |
| elected builds | `1` |
| lock waited/seconds | `0` / `0.0` |
| source materialization | `3.113146s` |
| package materialization | `20.411895s` |
| package verification | `22.960028s` |
| dependency cache | `50.10436s` |
| Lake build | `884.495783s` |
| total warm | `1039.829438s` |
| elected owner | PID `2`, host `GHZ` |

The exact build command was
`lake --packages=.lake/package-overrides.json build`; the log ends with
`Build completed successfully (8992 jobs).` Post-build package verification
also returned `status: verified`.

Publication evidence:

| Object | Evidence |
|---|---|
| manifest SHA-256 / READY content | `86d9aa6c53a0ffa468f55a7a285b24f2fe21137150c7b7c0b1e2dcb1e55e28bb` |
| READY file SHA-256 | `2307e22ff78ec0489504b8735b2d6c9be89b7c91e04477bed86c092285465ae1` |
| build log SHA-256 | `297a3a4486e153298546691b674bf66c3de73fe73855eea2147ff0b098d2612c` |
| warm metric raw-line SHA-256 | `464809b136decd0f1a41c8a29524f8094d5be198a9154b71f52b54f81279866c` |
| artifact inventory SHA-256 | `ba096053b9ceb4232b646dd896d5ecefac739dbba37c9f78498d4fd820fb1548` |
| artifact inventory | 124,925 files; 4,147 directories; 3 symlinks; 10,097,592,794 bytes |

The prescribed post-warm `status` returned `hit` for the same base/key. The
successful private seed took `267.003357s`, waited `0.0s`, built nothing, and
copied all 124,925 files / 10,097,592,794 bytes plus three symlinks. The host
reported `reflinked: 0`, so all regular files were private byte copies. Its raw
metric-line SHA-256 is
`3f6f4407790e9aca63d588f282efcbfdbc62fbd6756491e7da6ab6451caf5fb8`.

One seed invocation was refused before copying because the linked-worktree
default treated the target as the main worktree (`refusing to seed the main
worktree`). The one corrected retry supplied
`--repo-root /home/drx/MIPStarRE-auto` explicitly and succeeded. Thus warm
attempts/retries were `1/0`; seed attempts were `2`, with one pre-copy refusal
and one success. No cache or project byte was mutated by the refused command.

## Validation

| Command | Result | Time |
|---|---|---:|
| `lake env lean MIPStarRE.lean` | pass, exit 0; max RSS 6,838,484 KiB | `35.71s` |
| MIPStarRE materializer tests | `11/11` pass | `1.15s` |
| Lake package materializer tests | `34/34` pass | `181.95s` |
| hot-main cache tests | `46/46` pass | `15.48s` |
| `python3 -m compileall -q scripts tests` | pass | `0.29s` |
| `python3 scripts/workflow.py validate` | pass before and after; 31 issues, 18 PRs, 354 issued sessions, 7 stages | n/a |
| `git diff --check` | pass | n/a |

The exact-base aggregate command
`python3 scripts/check_workflow.py` stopped before tests in `0.17s` with the
single root-owned accounting mismatch
`stages[1].subagents_issued: expected 110, got 108`. It did not report a Lean,
pin, provenance, build, cache, or QPBT-004 project-byte failure. Root corrected
that canonical drift in descendant commit
`743051546a52128cf910157d3e57e42e726ccbad` by updating the Stage 2/3/4A
counts; that commit is an ancestor of current main, and root independently
reported current `workflow.py validate` and `check_workflow.py` passing. The
immutable 942f943 base was not rewritten and this session did not edit
root-owned workflow or research state.

Under the direct acceptance-only rule, the superseded accounting mismatch is
reported separately and does not reopen one of QPBT-004's three written gates.

## Accounting

- Session topology: root coordinator -> this QPBT-004 orchestrator; zero child
  agents; maximum depth one below root.
- Operational warm calls: one; operational seed calls: two (one refused before
  copy, one successful); status calls: one.
- Full Lake builds: one, exclusively inside the elected warm.
- Direct Lean typechecks: one.
- Network/GitHub/endpoint/credential/external-review operations: zero.
- Tracked project edits: zero. Authored output: this report only.
- Session start: `2026-09-01T08:02:29.741394Z`.
- Evidence cutoff: `2026-09-01T08:33:10.930116064Z`.
- Elapsed through evidence cutoff: `1841.188722064s`.
- Token usage: JSON `null`; availability reason: the collaboration backend does
  not expose per-agent token usage. No estimate is made.

The report SHA-256 and report commit/tree are supplied to the coordinator out
of band because embedding the report's own digest would change it.
