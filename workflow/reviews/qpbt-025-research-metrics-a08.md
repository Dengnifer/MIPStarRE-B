# QPBT-025 research-metrics audit (A08)

Measured audit interval: 171 seconds, from `2026-09-01T04:15:17+08:00` through `2026-09-01T04:18:08+08:00`.

## Live accounting

At the audit cutoff, `workflow/state/sessions.json` contains **304 issued sessions**, comprising **303 non-coordinator sessions** and the root coordinator. Exactly **172** issued sessions belong to Stage 04A; this agrees with `workflow/state/stages.json`, whose stage counters are 34 + 61 + 36 + 172 = 303 non-coordinator sessions. The lifecycle-active count is **4** (`status == "running"`): the root coordinator and three read-only QPBT-025 scouts, A06-A08. Only two records currently have `archive_status == "active"`; A07 and A08 are `not_requested`, so `status` is the correct live-activity field.

`research/metrics/sessions.jsonl` contains 300 unique terminal subagent records: 34 Stage 01, 61 Stage 02, 36 Stage 03, and 169 Stage 04A. The three-record difference from the live Stage-04A count is exactly the three running read-only scouts. Token usage remains JSON `null`: the collaboration backend does not expose per-agent token usage, and the root record says scoped usage is available only as aggregate goal usage at completion. No estimate is warranted.

## Accepted recipe-v5 warm

The measured success evidence is bound to main/head `d73cce44d5f9f37d38ee8d916811719408818c03`, tree `8a8985252eb019282ab6ef1842ce1b9178a58c07`, and cache key `5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266`. Recipe version/schema are 5/3. One authenticated warm produced `built` and subsequent `hit`, with cache hit/miss 0/1, builds 1, lock waited 0 (`0.0` seconds), no retry, and no seed.

Measured phases were: materialize `3.038161` s; package materialize `17.847069` s; package verify `16.824722` s; dependency cache `39.60957` s; Lake build `551.877742` s; total `655.003154` s. The metric timestamp is `2026-08-31T20:02:45.006319Z`.

Authenticated input hashes are Mathlib `c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7` and MIPStarRE `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`. Output hashes are: manifest SHA-256 and READY content `f41716f8a1213bd1fbff2939723c739653c360d6b797d93be69cb5a42f5ad234`; READY-file SHA-256 `06720bffaa45dfc2fe92f5816caf9e31178d52bd4a95bcb4fdf70eceae4aa80a`; build-log SHA-256 `4737436c617f7072fd7bfb6d0fd65f900e8713fb7bfd722eb98e22e0c58b7b5c`; warm-metric-line SHA-256 `5022a23bf7a4a686588a5bba912e136051b743328a640c7dcb3b6185de1cb919`; inventory SHA-256 `321e2813533a93c8218eefb277bd3425d3b55a59d978a233fc9b4795de42df60`.

The deep inventory equals the manifest inventory: **124,925 files**, **4,147 directories**, **3 symlinks**, and **10,097,592,794 bytes**. The generated ProofWidgets sidecar is absent, its authenticated target and package build directory remain, `READY` authenticates the manifest, and the exact key has one warm metric and no failure envelope.

## Proposed report correction

Replace the stale Stage-04A checkpoint (`269` total / `268` non-coordinator / `137` Stage 04A) with `304` / `303` / `172`, and state that four sessions are running at this cutoff. Add the accepted warm measurements above. Preserve earlier miss/failure passages as dated history, but stop describing the cache or full Lake build as pending in the current checkpoint.

Revise the Stage-04A schedule assumption to: **“The recipe-v5 main cache is accepted; the remaining critical gate is unfinished QPBT-003, including the source-faithful callable-contract and self-dual-normal-basis boundary.”** Stage 04A therefore remains in progress; cache closure removes one operational blocker but does not close the mathematical dependency. The measured parallelism lesson is **three independent read-only lanes around one singleton builder**: only the elected builder performs the warm/build, while evidence, closure, and metrics audits use the other lanes without duplicate warm, seed, Lake, or Lean work.

## Inconsistencies

- `research/metrics/builds.jsonl`, named by the audit contract, does not exist. The warm timings and hashes above are therefore cross-checked only against the permitted post-integration success report; no independent build-ledger line was available.
- `research/report.md` is stale at 269/268/137 and says 39 incidents, while the permitted incident ledger has 44 entries through INC-044.
- INC-044 remains canonically `mitigating` with the old `9b6...` miss as its latest status, although the recipe-v5 success report authorizes resolution. That is pending closure-ledger work, not evidence that the accepted `537...` cache failed.
- The warm-success report records one post-warm closure scout at its accounting cutoff; live state now records three running read-only post-warm scouts. Treat the former as historical, not the current active count.

## Commands inspected

Read-only inspection used `cat AGENTS.md`; `wc -l` on the governed files; `jq` projections/counts over stages, sessions, terminal session metrics, and INC-044; and `rg`, `sed`, `tail`, and `nl` on the report and warm-success review. No tests, build, Lean, Lake, warm, seed, runtime/cache access, Git write, network operation, or repository edit was performed. Repository edits: **zero**. The only created file is this requested report under `/tmp`.
