# QPBT-035 guarded integration (A13)

## Verdict

**PASS, integration object prepared.** The approved LPR-023 candidate was
integrated with a guarded two-parent merge object using the current immutable
main base as first parent and the approved candidate as second parent. The
linked worktree Git metadata and object store are read-only, so the merge
commit is retained in an isolated temporary object database for the root
coordinator to recreate on the canonical writable ref. No canonical workflow
state, research, or metrics path was changed.

## Immutable identities

| Item | Value |
| --- | --- |
| Current base commit | `0dfa0bceac319ce1ace87999221e8134bd150dde` |
| Current base tree | `cf091f98974b33aa7cdaee84a048d868aceb3f4e` |
| Candidate commit | `9cd85aaf809b4cfce64f7159ce3f92929b388270` |
| Candidate tree | `29c2275a5770332d07d0080e5389f917c36b9074` |
| Candidate sole parent | `783ec5f5b0ed876addb3cf6e02bf0fdc2426fa19` |
| Integration commit (isolated ODB) | `0313c05ff592bd77d25f9819c0747b21379bea7a` |
| Integration tree | `91e35bd09a31acd0267423598ca26b40cf61d7b2` |
| Integration parents (ordered) | `0dfa0bceac319ce1ace87999221e8134bd150dde`, `9cd85aaf809b4cfce64f7159ce3f92929b388270` |
| Candidate A04 report SHA-256 | `aa5681300a77f661fd467dfa6fe1e9bde5b0ea4ed6fe79800d80f01e68eda013` |
| Approved A06 report SHA-256 | `bd3ac5acd186b311da4c03e7feb00a8c58decf0aa550b2ec016ec1589041caa2` |
| A04 signature-marker SHA-256 (`39ed` packet value) | `39edc25942ba55981a952685cf65695e3734631ac7abaa683179383603331bcd` |

The native `git merge --no-commit --no-ff` and repository-index staging both
failed before changing the tree because the linked worktree refused
`ORIG_HEAD.lock`, `index.lock`, and object temporary files (`Read-only file
system`). An isolated object database at `/tmp/qpbt035-a13-objects`, with the
canonical object store read only as an alternate, produced the authenticated
merge object above. The object is not reachable from a canonical ref.

## Selected path manifest

The exact leased blueprint set has 16 paths, path-sorted and newline
terminated. Its name-list SHA-256 is
`f46174ba7e1e9f5144399466edb4671f10320711db66c53dab33f217ad63eb80`.
The corresponding selected `git ls-tree -r` manifest SHA-256 is
`4dc09f6b5d9279e26ff5fd5dee289e26e858f5cfe93d6430ffa03392c0631da3`, identical
at candidate and integration trees. The complete integration-tree
`git ls-tree -r` SHA-256 is
`fb0e46555c8c1fecbe72b4dcac021122f78183d453edf1f048109eeb0bf7fa14`.

```text
blueprint/check.py
blueprint/generated/graph.dot
blueprint/generated/graph.json
blueprint/metadata/nodes.json
blueprint/src/generated/chapter-02-entries.tex
blueprint/src/generated/chapter-03-entries.tex
blueprint/src/generated/chapter-04-entries.tex
blueprint/src/generated/chapter-05-entries.tex
blueprint/src/generated/chapter-06-entries.tex
blueprint/src/generated/chapter-07-entries.tex
blueprint/src/generated/chapter-08-entries.tex
blueprint/src/generated/chapter-09-entries.tex
blueprint/src/generated/chapter-10-entries.tex
blueprint/src/generated/chapter-11-entries.tex
blueprint/src/generated/chapter-12-entries.tex
blueprint/tests/test_check.py
```

The candidate source-fidelity report path was also authenticated and retained:
`workflow/reviews/qpbt-048-source-fidelity-repair-a04.md` has Git blob
`4add285509a51a94d736eebc86b523664c658419` and SHA-256
`aa5681300a77f661fd467dfa6fe1e9bde5b0ea4ed6fe79800d80f01e68eda013` at both
the current base and candidate. It therefore adds no base-to-integration diff,
but remains present in the integration tree as the approved handoff report.

## Candidate preservation proof

Every selected path was read from the candidate tree and applied to the
integration tree. For each of the 16 blueprint paths, candidate and integration
Git blob IDs are byte-identical; the working-tree SHA-256 values were also
checked. The 16-path count and zero outside-lease paths were confirmed with
`git diff --name-only 0dfa0bce..`.

| Path group | Count | Result |
| --- | ---: | --- |
| Candidate blueprint paths selected | 16 | all blobs preserved |
| Candidate A04 report | 1 | identical to current base and candidate |
| Base-to-integration changed paths | 16 | exactly the blueprint lease |
| Changed paths outside lease | 0 | none |
| Canonical workflow/state or research/metrics edits | 0 | none |

## Validation gates

| Gate | Result | Elapsed |
| --- | --- | ---: |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | 32/32 passed | 1.531 s |
| `python3 blueprint/check.py --check` | 54 nodes/12 chapters passed | 0.101 s |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | 54 nodes/12 chapters passed | 0.104 s |
| `python3 scripts/reference_source.py verify --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | 39 files/646 labels; inventory `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`; READY `4d6a33759051b17428b3928d529d18e10da82e3bc09c75fbe429df324612b360` | 0.137 s |
| `python3 blueprint/check.py --write` (pass 1) | passed; deterministic generated outputs | 0.099 s |
| `python3 blueprint/check.py --write` (pass 2) | passed; byte-idempotent | 0.101 s |
| `python3 -m compileall scripts tests` | passed | 0.220 s |
| `python3 scripts/workflow.py validate` | valid; 53 issues, 26 PRs, 419 issued sessions, 7 stages | 0.144 s |
| `python3 scripts/check_workflow.py --skip-tests` | valid | 0.136 s |
| `git diff --check 0dfa0bce..` | passed | 0.042 s |

Generated-diff/declaration synchronization is represented by the two
byte-idempotent `blueprint/check.py --write` passes followed by default and
pinned declaration checks; no separate declaration-sync executable exists in
this repository. No Lean/Lake, target/full build, hot-cache warm/seed,
materialization, network, endpoint, GitHub, or credential action was run.

## Accounting

- Stable session: `i035-integrator-a13-guarded-integration`.
- External thread: `/root/integrator035_bootstrap`.
- Topology: root coordinator -> one integrator; nested agents: 0.
- Token usage: `null` (collaboration backend does not expose per-agent token
  telemetry); no estimate was made.
- Compile/build attempts: 0 Lean/Lake/build; Python compileall: 1.
- Retries/incidents: native merge/staging blocked by read-only linked Git
  metadata; equivalent isolated-ODB commit succeeded.
- Repository edits: 16 blueprint files plus this report in the worktree;
  canonical state, PR, issue, session, stage, research, and metrics edits: 0.
- Candidate preservation failures: 0. Validation failures after integration:
  0.

Root must recreate commit `0313c05ff592bd77d25f9819c0747b21379bea7a` (or an
equivalent no-ff merge with the same ordered parents and tree) on the canonical
writable ref, import this report, and retain the exact candidate blob proof.
