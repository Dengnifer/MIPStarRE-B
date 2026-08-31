# QPBT-025 post-integration recipe-v5 warm success

## Outcome

The exact independently approved LPR-015 candidate was fast-forwarded onto
local `main`, and the one newly authorized recipe-v5 warm succeeded. All
post-warm acceptance checks passed:

- exact main/head: `d73cce44d5f9f37d38ee8d916811719408818c03`;
- exact cache key:
  `5377961b0bebafd24648ea2ae9d0bc6e10f5c9481433db433e55b687c8bcd266`;
- warm result `built`, status `hit`, cache miss `1`, builds `1`;
- exactly one matching warm metric and no matching failure envelope;
- `READY` equals the SHA-256 of `manifest.json`;
- deep artifact inventory equals the manifest inventory;
- `proofwidgets/widget/package-lock.json.hash` is absent;
- the authenticated target and proofwidgets package build directory remain;
- recipe version is `5`, recipe schema is `3`, and both canonical verifier
  calls use the exact non-parameterized removal flag.

This is the success branch authorized by QPBT-025. The old
`9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36`
hypothesis was not retried. No second warm or seed was run.

## Reviewed integration

Before integration, root revalidated all of the following:

- canonical main was branch `main` at exact base
  `45d2fe657af587e8e10952aced2e156d349fd65e`;
- candidate head/tree were
  `d73cce44d5f9f37d38ee8d916811719408818c03` /
  `8a8985252eb019282ab6ef1842ce1b9178a58c07`;
- the candidate was clean, had the base as its sole parent, and was exactly one
  commit ahead and zero behind;
- its exact four-path diff passed `git diff --check`;
- canonical index and all four candidate paths were clean;
- root-owned workflow/metrics/review dirt was disjoint from the candidate;
- LPR-015 was `approved` by the fresh independent A04 review, with no findings,
  on the exact base/head; and
- workflow state and research-ledger reconciliation passed.

Root then ran only:

```text
git merge --ff-only d73cce44d5f9f37d38ee8d916811719408818c03
```

The update was a one-commit fast-forward. The complete root-owned dirty status
was byte-for-byte unchanged across it. Post-integration blob checks matched:

| Path | Git blob |
|---|---|
| `scripts/hot_main_cache.py` | `d434e4045319203c028406baf165aa9808637cf3` |
| `scripts/materialize_lake_packages.py` | `2324d054b3880597a916d48c2f6f63f2b4325385` |
| `tests/test_hot_main_cache.py` | `5e2f1c2aa1c3fbbd5412186a3bf40c5ed46fe6d1` |
| `tests/test_lake_package_materialization.py` | `d6cfa5dc97feeb7b4af6f88ba9ad528e4d9f9ec9` |

## Pre-warm gate

The pre-warm gate authenticated ten local inputs: the pinned MIPStarRE archive,
the pinned Mathlib shallow-repository archive, and exactly eight regular Lake
package archives. The two outer archive SHA-256 values were:

```text
Mathlib    c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7
MIPStarRE  656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc
```

The eight package archive names, sizes, and hashes matched
`references/lake-packages.json` exactly. Read-only identity computation from
the integrated commit produced the expected recipe-v5 key. Before the attempt,
there was no snapshot, failure directory, or rendezvous file for the new key,
no kernel-reported holder, and no relevant live warm/seed/Lake/Lean process.

## Singleton warm

Root invoked exactly one warm, with local authenticated archive variables and
the exact integrated main override:

```text
env -u MATHLIB_SOURCE -u LAKE_PKG_URL_MAP \
  MATHLIB_ARCHIVE=/tmp/mathlib-81a5d257-shallow-repo.tar.gz \
  MIPSTARRE_ARCHIVE=/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz \
  LAKE_PACKAGE_ARCHIVES=/home/drx/MIPStarRE-auto/.workflow-runtime/acquisitions/lake-packages-20260830 \
  python3 scripts/hot_main_cache.py \
    --repo-root /home/drx/MIPStarRE-auto \
    --project-dir . \
    --runtime-dir /home/drx/MIPStarRE-auto/.workflow-runtime \
    --main-commit d73cce44d5f9f37d38ee8d916811719408818c03 \
    warm
```

The terminal result was:

| Field | Value |
|---|---:|
| result / status | `built` / `hit` |
| cache hit / miss | `0` / `1` |
| lock waited / seconds | `0` / `0.0` |
| builds | `1` |
| materialize seconds | `3.038161` |
| package materialize seconds | `17.847069` |
| package verify seconds | `16.824722` |
| dependency cache seconds | `39.60957` |
| build seconds | `551.877742` |
| total elapsed seconds | `655.003154` |
| elected owner | PID `2`, host `GHZ` |
| metric timestamp | `2026-08-31T20:02:45.006319Z` |

The exact package verifier command recorded in the recipe, manifest, and warm
metric is:

```text
python3 scripts/materialize_lake_packages.py verify --remove-validated-generated-sidecars
```

It was reused by the existing pre-build and post-build verifier call sites.

## Post-warm evidence

Read-only `status` returned `hit` for the exact head and key. READY and artifact
evidence is:

| Evidence | Value |
|---|---|
| manifest SHA-256 / READY content | `f41716f8a1213bd1fbff2939723c739653c360d6b797d93be69cb5a42f5ad234` |
| READY file SHA-256 | `06720bffaa45dfc2fe92f5816caf9e31178d52bd4a95bcb4fdf70eceae4aa80a` |
| build log SHA-256 | `4737436c617f7072fd7bfb6d0fd65f900e8713fb7bfd722eb98e22e0c58b7b5c` |
| warm metric line SHA-256 | `5022a23bf7a4a686588a5bba912e136051b743328a640c7dcb3b6185de1cb919` |
| inventory SHA-256 | `321e2813533a93c8218eefb277bd3425d3b55a59d978a233fc9b4795de42df60` |
| inventory files | `124925` |
| inventory directories | `4147` |
| inventory symlinks | `3` |
| inventory bytes | `10097592794` |

Independent recomputation with `artifact_inventory` equaled the complete
manifest inventory, and `HotMainCache.is_ready(deep=True)` returned true.
There is exactly one matching `action: warm` metric for the key. The published
snapshot has no matching failure envelope and directly satisfies:

```text
sidecar absent:             true
package-lock target present: true
proofwidgets .lake/build:    present
```

## Lifecycle consequence

This evidence authorizes the monotone success closure frozen by A17/A05:

1. bind LPR-014 integration to its already physical head `9c9b495...` and
   transition it from approved to merged;
2. bind LPR-015 integration to `d73cce4...` and transition it from approved to
   merged;
3. transition child QPBT-025 from review to done;
4. transition parent QPBT-024 from review to done only after the child is done;
5. preserve QPBT-004's dependency edges to QPBT-003 and completed QPBT-024,
   while recording that QPBT-003 is its sole unfinished dependency;
6. resolve INC-044 while retaining both historical failure occurrences and all
   old failure evidence.

No late PR check is added after approval. Integration metadata and issue
evidence point to this report; historical failure evidence remains immutable.

## Accounting

- Operational cache warms: `1` exactly.
- Cache seeds: `0`.
- Warm retries for this head/key: `0`.
- Direct root compile attempts outside the warm: `0`.
- Network acquisitions: `0`; all build inputs were authenticated local files.
- Warm subprocess build: `1` full Lake build, elected by the per-key lock.
- Parallel post-warm read-only closure scouts: `1`.
- Root token usage: JSON `null`; the service does not expose a scoped token
  count for this operation, so no estimate is made.

The report SHA-256 is recorded out of band because embedding it here would
change the digest.
