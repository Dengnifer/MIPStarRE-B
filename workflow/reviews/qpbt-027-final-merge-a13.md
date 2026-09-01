# QPBT-027 / LPR-017 final approved-state merge scout A13

## Verdict

**PASS.** Exact approved candidate
`2c6b1f1d0be89d09bad2f60e074cf106be99fd46` cleanly three-way merges into the
exact committed approved-state first parent
`cf7d8fd8d85dcba7d49c8580dce115b1f48e63af`. Git 2.34.1's supported
three-argument `git merge-tree` reports four ordinary merged sections, four
result blobs, zero conflict categories, and zero conflict-marker lines. All four
results are the exact candidate blobs. Both shared reports are byte-identical at
the two tips. All 26 canonical-only paths, including the A11 approval and A12
recovery evidence, are retained unchanged by the three-way result.

This is read-only merge authorization for a true merge with ordered parents:

1. first parent: `cf7d8fd8d85dcba7d49c8580dce115b1f48e63af`
2. second parent: `2c6b1f1d0be89d09bad2f60e074cf106be99fd46`

A squash, fast-forward, candidate-tree replacement, cherry-pick, reversed
parent order, or first-parent drift does not satisfy this result.

## Fixed object identities

| Role | Commit | Tree |
|---|---|---|
| approved-state first parent | `cf7d8fd8d85dcba7d49c8580dce115b1f48e63af` | `2df7e1593f6268aa2440a07e8ba93865ce87d772` |
| approved candidate | `2c6b1f1d0be89d09bad2f60e074cf106be99fd46` | `0c6fdd0f7ce5349b0f543e171871eb0ef292eab6` |
| independently recomputed unique merge base | `506ac7a7b57a2318e0764acfc2558dc62f9e50f0` | `10f8da1ebb8b3fd7ce92dafee19d61fafe2cf8e2` |

The detached scout checkout is exactly the first parent and was clean before
and after inspection. The first parent is nine commits beyond the merge base;
the candidate is two commits beyond it. `git rev-list --left-right --count`
reports `9 2`, so neither tip contains the other and a true merge is required.

## First-parent approval evidence

The first-parent `workflow/state/prs.json` records:

- `LPR-017.status = approved`;
- `base_sha = 506ac7a7b57a2318e0764acfc2558dc62f9e50f0`;
- `head_sha = 2c6b1f1d0be89d09bad2f60e074cf106be99fd46`;
- formal review `review-qpbt-027-pr017-a11-immutable`, verdict `approve`, on
  those exact base/head objects, with no new findings and
  `resolved_finding_ids = [F-LPR017-001]`;
- high finding `F-LPR017-001`, status `resolved`, disposition `fixed`, and
  `resolved_by_review_id = review-qpbt-027-pr017-a11-immutable`.

The A11 reviewer session is canonical, archived, read-only, has role `reviewer`,
and is bound to `LPR-017`. The A11 report is blob
`c406b1b579ccf06c8bc99aa5844c557fb3bded81`, SHA-256
`2d8296adc252e0c3fe39a889fad9e9143bf9e194d365077e67fbef2f5ca21331`,
exactly matching the PR ledger. Its text states `approve`, no findings, and the
resolution of `F-LPR017-001`.

The first parent's approval commit adds the A11 report and A12 recovery report
and updates incidents, sessions, events, PR state, session state, and stage
state. Stage state retains A08, A10, A11, A12, and `INC-048` references.

## Three-way result

The only merge analysis interface used was the Git-2.34-compatible form:

```text
git merge-tree 506ac7a7b57a2318e0764acfc2558dc62f9e50f0 \
  cf7d8fd8d85dcba7d49c8580dce115b1f48e63af \
  2c6b1f1d0be89d09bad2f60e074cf106be99fd46
```

Result inventory:

```text
merged sections:       4
result lines:          4
conflict categories:   0
conflict marker lines: 0
merge-tree lines:      1035
merge-tree SHA-256:    1f87c238c80c91d8f717734847eac25f133f29e77493ec46d138862a31165816
```

The four result blobs are exactly the candidate blobs:

| Candidate-only result path | Git blob | Bytes | SHA-256 |
|---|---|---:|---|
| `protocols/CHANGELOG.md` | `f5fcf6d0511c889fc35e97ae551f8fcc98c13bfc` | 16,510 | `c667bcbdcb5c139242fe7ce6d936209a7a6d0d45c487ac22ae4d0f938023afd5` |
| `protocols/review.md` | `84b5c607426f661ce3defb6b525be99d839f14f9` | 8,927 | `4638e12e9d82d4a2d2bde3e2074068b468368bedaa21c623432f16ec090634ae` |
| `scripts/workflow.py` | `6b5271bc995066641319c4ee0fe880e37d74490e` | 134,259 | `a23110e0b65843525cc51443ef1c0aa8be1ad21df715c4b3c0b8e20b17e61eca` |
| `tests/test_workflow.py` | `ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe` | 83,117 | `89713c6d0dc2bbed1df1cd90977c7257dc3b67cde91321d6e57923751f96eabd` |

The newline-delimited candidate-only path manifest has SHA-256
`cb8e72c6b794d9f4b466fbce802f61cf8ec33ef6b4b594f9ca410b08b061f59e`.
The tab-delimited `path, blob, bytes, SHA-256` inventory has SHA-256
`a24004392af12353f11fa17804c7415a09e1ca51bcc6063863f04e761d7f71cc`.

## Exact path classification

All manifests are lexically sorted, newline-delimited path lists relative to the
unique merge base:

| Class | Count | Base status | Manifest SHA-256 |
|---|---:|---|---|
| canonical-side total | 28 | 20 added, 8 modified | not used as a result class |
| candidate-side total | 6 | 2 added, 4 modified | `814a1285e97c6e0d533fb0efb0ddb2ce3f198d26789973cb67aa06ebeaab244d` |
| canonical-only | 26 | 18 added, 8 modified | `1c93b73a4d4779c4a7ca26c11fdd368597c18e766f4ca474ee5a7ace0718452a` |
| candidate-only | 4 | 4 modified | `cb8e72c6b794d9f4b466fbce802f61cf8ec33ef6b4b594f9ca410b08b061f59e` |
| shared | 2 | 2 added | `b0ff7d50746e21436decbfa03250e0bb4e2c236b6f23d65bbfce0904f8cd7527` |
| union | 32 | 20 added, 12 modified | `e612d5b8fc88840226919b2838bc264848b55b5e22ba3466046b5f5dd09e4082` |

The four candidate-only paths plus the two shared reports account for every
candidate path. There are no other candidate changes.

## Shared report identity

Both shared paths are additions relative to the merge base and have identical
mode `100644`, Git blob, and byte hash at both tips:

| Shared report | Blob at both tips | SHA-256 at both tips |
|---|---|---|
| `workflow/reviews/qpbt-027-finding-reconfirm-a01.md` | `06e0c36a4b376ec309463b2a3ccd19d8eff054a2` | `1885c02167279996773fe29d31cf3665d225d02ffd494b02d743fe2437134e73` |
| `workflow/reviews/qpbt-027-stale-append-fix-a05.md` | `815939ceb85a606cb134a6010b8e9a49c6b17df0` | `a442bc60c86ccae962c956ebe024f1b822792a9e9afbb9d81722458e954d5e61` |

The shared `path, blob, bytes, SHA-256` inventory has SHA-256
`0392836331c69141b898ec51d6703336a187eeda925e7562b1b2a0ea7f6f4c3e`.

## Canonical-only preservation

For each of the eight modified canonical-only paths, the candidate has the
merge-base blob; for each of the eighteen added canonical-only paths, the path
is absent from both merge base and candidate. Therefore the explicit three-way
result retains every following first-parent blob unchanged. The complete
tab-delimited `path, blob, bytes, SHA-256` inventory has SHA-256
`25a9f3f26724b77d4f7de45545f59bd56d7449efbabbac99483656117c3d7add`.

| Canonical-only path | First-parent/result Git blob | SHA-256 |
|---|---|---|
| `research/metrics/incidents.jsonl` | `b8382bf96c369b1c6bf809069062239ba29fe744` | `b876dce2e38531c75550b843f2adfbdcfc3895b1683fea9133702824ad7ce9f0` |
| `research/metrics/sessions.jsonl` | `48707746f9fa9d342422bb431e52527caba5a740` | `0fe9b873d33083b9642743229654d9f11dc48aca7c366a0cca2331d96f780c27` |
| `research/report.md` | `0565717010e078d6aaf9cf62e97022fea7f081a8` | `74e0d34eac6beb823d49c06b21f3b870c040a638232b131b857588236b7ca992` |
| `workflow/events.jsonl` | `61e0d49eebd6c84522b6fbecab127ca6e728ba4b` | `d4a3ebee5a78e9264af1b0d8359e38a43dab00228bf883ad7dc684febbc43a79` |
| `workflow/reviews/qpbt-018-021-closure-evidence-a18.md` | `bb0ae3371123d819c1676bbbea7e14e32483c316` | `11efa324222f1304450c0b8cdcdf7049007625a0511f248c877b38c1bac2c536` |
| `workflow/reviews/qpbt-026-capability-schema-a19.md` | `80d15f96cc97594236bc6d7d55879b2bead3c0a5` | `518f5c4e133b8bd0eb7ef4303ee3a4953e30113ef5e510960e41c9e9657a089f` |
| `workflow/reviews/qpbt-026-disclosure-preflight-a11.md` | `da1e5c1cf6d8fec19a8c21d508c5efbd6f5baabc` | `faa33aa7b0d3282afd45113d90b375287c341c1be34dab3761f238839e5c4314` |
| `workflow/reviews/qpbt-026-offline-isolation-a17.md` | `ea20399f6dceeea1e7d7ac04e90acd46f45935ce` | `9496e6ddbcfd6f700007ba07398ce797c138f22f96f92b0fc30aaa2c4197625e` |
| `workflow/reviews/qpbt-026-review-a14-pr016-immutable.md` | `acced46252836f53dd5fff771abd13216d4c2b60` | `8a613b59d20b27b9eb709547c7719c8c10e963367c49f9cb14881eeb4b74bb29` |
| `workflow/reviews/qpbt-026-review-a18-pr016-immutable.md` | `b7e26c1dabc4a8630be63940030b575d6fb8650f` | `0b203f02ade092400fdc524cb36ec5ee54ab190f3d460392d27f4dde09053cfe` |
| `workflow/reviews/qpbt-026-review-a20-pr016-immutable.md` | `b093dfd97452d213891a7aa787577a9ba72d6d15` | `7cfeb869a3f150fe68ebe4c153e4a6357f235cb87b0affa357c6c3c7b4bdaae0` |
| `workflow/reviews/qpbt-026-stage2-critical-path-a15.md` | `1be0738c4be3823fe0071525cb3147238445cdff` | `266bd04517a5214d5a63c2058b685350268c56707ecafcd96acdccfa5295a17f` |
| `workflow/reviews/qpbt-027-postreview-ledger-a10.md` | `b83b6a0c771a7a8c9f6b16ba0f9df59345f0e9ce` | `0025803b6e92a91960cad61718a80aba050e1ced664dbc0d2c276e198a360560` |
| `workflow/reviews/qpbt-027-pr017-bind-a03.md` | `1cf4da2cb41e7d9db527f1fc013566306abadec0` | `72cb9a30151e10f288cfd74315c9bca4fad144470f31e2d9b5a3c06ac5513c75` |
| `workflow/reviews/qpbt-027-pr017-integration-preflight-a09.md` | `201fa288f348749673bb970c37481bbc810a0b5b` | `5662adf704b47a3d5bff209908288868ea85e3a8c7e6838ee37d6b4714d5cec7` |
| `workflow/reviews/qpbt-027-reconfirm-contract-a02.md` | `a3a9f4cf386196d7747387440f43596dbd4f3f88` | `148c9e1596e8bab2fdc5071c4c57dc8f1cc337ce81005be12c2b926bacb9d5e2` |
| `workflow/reviews/qpbt-027-recovery-merge-a12.md` | `f7bb5bbf015da144d6b47a7343839344e5586d12` | `86adc9c1a5bea9405fbae04354346b34c32bbdb6f6bb91473ca2c7432e857441` |
| `workflow/reviews/qpbt-027-review-a04-pr017-immutable.md` | `cdf4f92d0a7c6769b8d2745c8e64f6af0fb0137b` | `2fd2a123a2ed32b34d674509f4faf78fe398ee44add61270db570bd46a30d58e` |
| `workflow/reviews/qpbt-027-review-a08-pr017-immutable.md` | `3997278c7de9832731f44ace379abe89f08ba48f` | `e6f610c8ebde2959e8d987f2baced343a994f94cca4c247a637055c51ca194e0` |
| `workflow/reviews/qpbt-027-review-a11-pr017-immutable.md` | `c406b1b579ccf06c8bc99aa5844c557fb3bded81` | `2d8296adc252e0c3fe39a889fad9e9143bf9e194d365077e67fbef2f5ca21331` |
| `workflow/reviews/qpbt-027-stale-append-contract-a06.md` | `912d561145a3526c18a9653eded5a5d1b2f596d6` | `302cb14303a2cf1c574724df2968d4d88e5b9c7459c972f85656f76dff7a7e73` |
| `workflow/reviews/qpbt-stage2-integration-order-a07.md` | `e240fe4dc442cd282346124e049990b4b371523c` | `a9cd30a50eacf37f0c73e4328ecd753f433358bc80c991bb711c2988fd294283` |
| `workflow/state/issues.json` | `8b203a12c105cd601e45a39d0d8b70b10be1a36e` | `595c0ecc67fbb45581566ded7e0069beb50a03d5c18fb255fb0ce568242a1e53` |
| `workflow/state/prs.json` | `2e5bc98daffb47a2afd797e8b8bdf02529eefede` | `4ee3dff97dcfb1ac29929bdf8d33c7b7ff81e68f57c59826c0199dffd055820a` |
| `workflow/state/sessions.json` | `fd2ebd5e4f59daa6c95ef2f8260297aafdf3aa48` | `a5913675d80ad6555942ef06c350b0e87721e17c39f33941d280e3690a8f3925` |
| `workflow/state/stages.json` | `a5ea77e1c950fe737994fc625cf7759376c1957e` | `b825e60e05c185fa82c2dfcf7f43c2ccf76bb0f12621b9828d0d7363feb341cb` |

This inventory includes every canonical-only path, not only QPBT-027 evidence.
Consequently, the merge cannot lose unrelated approved/recovery state that was
added after the reviewed base.

## Required merge and post-merge identity gates

Create only a true merge while canonical HEAD is exactly the approved first
parent. Immediately afterward require:

```text
git rev-parse HEAD^1
cf7d8fd8d85dcba7d49c8580dce115b1f48e63af

git rev-parse HEAD^2
2c6b1f1d0be89d09bad2f60e074cf106be99fd46
```

Then verify:

1. `git rev-list --parents -n 1 HEAD` has exactly the merge commit followed by
   those two ordered parents, with no third parent.
2. `git merge-base --is-ancestor 2c6b1f1d0be89d09bad2f60e074cf106be99fd46 HEAD`
   exits zero.
3. `git diff --name-status HEAD^1 HEAD` lists exactly four `M` paths:
   `protocols/CHANGELOG.md`, `protocols/review.md`, `scripts/workflow.py`, and
   `tests/test_workflow.py`.
4. `git ls-tree HEAD` gives the four exact candidate result blobs above, the two
   exact shared blobs above, and all 26 exact first-parent blobs above.
5. Recompute the corresponding byte SHA-256 hashes and the three inventory
   digests; they must match this report.
6. The worktree is clean and `git diff --check HEAD^1 HEAD` is empty.
7. Run the workflow validation and test activation gates required by the
   coordinator after integration; this read-only scout did not run them.

Git 2.34.1's legacy read-only merge-tree interface does not emit a synthetic
tree object ID. Therefore no prospective tree ID is asserted. Parent ordering,
the exact four first-parent delta blobs, the shared identities, and the complete
canonical-only inventory are the deterministic post-merge identity checks.

## Constraints and metrics

- Session: `i027-scout-a13-final-merge`
- Role/topology: one fresh read-only scout; nested agents `0`
- Repository/canonical edits: `0`; Git refs/commits/index/worktree changes: `0`
- Report writes: `1`, this `/tmp` artifact only
- Supported three-argument `git merge-tree` invocations: `6`
- Conflicts/marker lines: `0` / `0`
- Tests/builds/validation commands: `0` / `0` / `0`
- Network/endpoints/GitHub/credentials/Codex launches: all `0`
- Lean/Lake/cache actions: all `0`
- Incidents opened/protocol revisions: `0` / `0`
- Compile attempts/cache hits/cache lock waits/build duration: `0` / `0` / `0` / `null` (no build was authorized or run)
- Session elapsed: `null`; the collaboration backend exposes no canonical per-agent elapsed-time counter, so no estimate was made
- Token usage: input `null`, output `null`, total `null`; the collaboration backend does not expose per-agent token usage, so no estimate was made

Final report hashing and final detached-clean status are recorded externally
after this file is closed.
