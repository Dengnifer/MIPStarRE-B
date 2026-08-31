# QPBT-025 ProofWidgets generated-sidecar removal (a01)

## Session identity and outcome

- Stable logical name: `i025-orchestrator-a01-sidecar-removal`.
- Issue / draft local PR: `QPBT-025` / `LPR-015`.
- Role: sole writable orchestrator for the issue worktree.
- Worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-025-sidecar-a01`.
- Branch: `issue/qpbt-025-sidecar-a01`.
- Immutable base / parent:
  `45d2fe657af587e8e10952aced2e156d349fd65e`.
- Base tree: `07df5125163a5bdddd1b80549cf622f8a0a628cd`.
- Candidate head: `d73cce44d5f9f37d38ee8d916811719408818c03`.
- Candidate tree: `8a8985252eb019282ab6ef1842ce1b9178a58c07`.
- Commit title: `fix(cache): remove trusted ProofWidgets hash sidecar`.
- Commit time: `2026-09-01T03:21:15+08:00`.
- Final worktree status: clean (`## issue/qpbt-025-sidecar-a01`).
- Result: implementation and regression matrix complete; all coordinator-owned
  acceptance gates on the exact four-file tree passed; exact candidate
  committed. Post-integration warm was not run or claimed.

The session start timestamp was not captured before the mandatory `AGENTS.md`
and source-anchor reads. Total session elapsed time is therefore JSON `null`
with availability reason "no reliable session-start timestamp"; it is not
estimated.

## Sources and adjudication

The worktree's `AGENTS.md` was read completely before edits. The following
required adjudication anchors were read before implementation:

- `workflow/reviews/qpbt-024-postintegration-warm-failure-9b6.md`
- `workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md`
- `workflow/reviews/qpbt-024-sidecar-security-a12.md`
- `workflow/reviews/qpbt-024-sidecar-synthesis-a14.md`
- `workflow/reviews/qpbt-024-sidecar-hooks-a15.md`
- `workflow/reviews/qpbt-024-sidecar-tests-a16.md`

A14/A15 and the issued QPBT-025 contract were treated as final authority where
earlier reports differed. In particular, A11's retained-sidecar proposal was
rejected, and A16's stale recipe-version-4 sentence was superseded by A15 and
the issue's exact version-5 requirement.

## Exact implementation

`scripts/materialize_lake_packages.py` now contains one immutable internal
contract and no caller- or pin-controlled deletion list:

```text
package        proofwidgets
revision       6e311e2a844da9b2cc3971187df2fe0066947b93
target         widget/package-lock.json
target_sha256  3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d
sidecar        widget/package-lock.json.hash
sidecar_bytes  179e66574f04806e
```

The materializer validates the contract's raw paths, safe components, exact
target/sidecar adjacency, revision and digest forms, and canonical 16-byte
lowercase sidecar value. Archive inspection applies the contract only to the
exact package and revision, requires the target to be the exact regular member
with the exact SHA-256, and rejects an archive-owned declared sidecar. Other
packages, revisions, and archive-owned `.hash` paths remain ordinary
authenticated source.

Bare `verify` remains read-only with respect to sidecar cleanup. The only
mutating interface is the exact non-parameterized flag:

```text
verify --remove-validated-generated-sidecars
```

In flagged mode, the exact package and every fixed parent are bound below the
held `.lake/packages` descriptor. Target and sidecar use no-follow,
nonblocking, descriptor-relative opens; removal fails closed if those platform
capabilities are unavailable. Both files must be regular and singly linked.
The target is bounded-read and must have the exact SHA-256. The sidecar must
have exact bytes and size, with no execute, setuid, setgid, or sticky bits.

Stable identities include device, inode, full mode, size, mtime, ctime, and
link count. The permission predicate uses the same stable post-read metadata
snapshot retained for the immediate pre-unlink descriptor/name comparison.
The code rechecks target, parent directories, package, packages root, and
project layout before mutation. It unlinks only the exact basename through the
bound parent descriptor, fsyncs that parent, proves name absence, retains an
absence tombstone, and rechecks the tombstone and held descriptors after scan,
after each tree hash, and on context exit.

Both existing source-tree comparisons remain unprojected and in their original
order. A validated sidecar can be removed before a later unrelated source-drift
failure, but no other path is excluded or repaired. Package-local
`.lake/build/**` remains accepted under the existing narrow boundary and is
retained for whole-`.lake` inventory binding.

`scripts/hot_main_cache.py` changes only the existing canonical recipe:

- recipe version `4 -> 5`;
- build-recipe schema remains `3`;
- the existing `package_verify_command` gains the exact flag;
- no phase, serialized field, or recipe-schema change is introduced;
- both existing verifier call sites reuse the one flagged argv.

The resulting order remains materialize, flagged verify, dependencies, build,
flagged verify, source checks, inventory, manifest/READY, and publication. The
sidecar is absent before inventory, snapshot publication, and seed copying;
package-local build output remains present. Materializer bytes, exact verifier
argv, recipe version, and main commit each participate in cache-key churn;
dirty uncommitted materializer bytes do not redefine committed identity.

## Changed paths and stat

Exactly the four owned paths changed:

```text
2     1  scripts/hot_main_cache.py
398  21  scripts/materialize_lake_packages.py
187  23  tests/test_hot_main_cache.py
665   0  tests/test_lake_package_materialization.py
```

Aggregate diff:

```text
4 files changed, 1252 insertions(+), 45 deletions(-)
```

No pin, protocol, workflow/state, review, research/metrics, reference, cache,
or shared-runtime file was edited.

## Regression matrix

The focused materializer suite covers:

- absent flagged no-op and bare-verify purity;
- exact removal, evidence JSON, exact parent fsync, target preservation, and
  retained package-local build output;
- wrong lowercase hash, uppercase, short, long, newline, and non-hex payloads;
- sidecar symlink, directory, FIFO, Unix socket, hardlink/multiple-link,
  executable, setuid, setgid, sticky, and mocked character/block modes;
- target symlink, directory, FIFO, Unix socket, hardlink, wrong bytes, and mode
  drift;
- pre-existing symlinked parent plus target, sidecar-name, sidecar-mode,
  parent, package-root, and post-unlink-recreation substitutions at all fixed
  phase seams;
- unsafe/traversal/absolute-equivalent, repeated-separator, dot-component,
  NUL, backslash, nonadjacent, and noncanonical internal contract values;
- wrong revision and same path under another package;
- undeclared, sibling, and nested hash lookalikes;
- target, trace, package.json, lakefile, manifest, ordinary source, and extra
  path drift after legitimate cleanup;
- archive-owned unrelated `.hash` preservation plus mutation/deletion failure;
- wrong archive target type/digest and archive-owned declared-sidecar rejection;
- exact production tuple and outer proofwidgets pin facts;
- independent archive-tree and Gitlink-reconstructed-tree verification; and
- all pre-existing `.lake/build` boundary defenses.

The hot-cache suite covers exact five-command order, snapshot and seed
omission, retained build output, deep inventory equality, negative inventory
binding after sidecar injection, malformed/drift failure envelopes, no
snapshot/READY on failure, materializer/argv/version key churn, recipe version
5, schema 3, and unchanged recipe field set.

## Read-only scouts and dispositions

Topology: root coordinator -> this writable orchestrator -> two parallel
read-only sibling scouts. Each scout spawned zero children, made zero
repository edits, and ran zero tests, builds, warms, seeds, Lean, Lake, network,
runtime, or cache operations.

1. `i025-scout-a02-sidecar-security`
   - Envelope: `/tmp/qpbt-025-scout-a02-sidecar-security.md`
   - SHA-256:
     `9e284039a9bc26d113affa74d3ede6ca66189e74379a152bb97a755a453f4af3`
   - Finding disposition: the high metadata-snapshot gap was fixed by
     returning and validating the exact stable post-read stat used for unlink;
     the medium recreation window was fixed with a persistent bound-parent
     tombstone checked throughout both tree comparisons; no-follow/nonblocking
     availability now fails closed; raw canonical/NUL/component path validation
     was added. All findings are resolved in the candidate.

2. `i025-scout-a03-sidecar-tests`
   - Envelope: `/tmp/qpbt-025-scout-a03-sidecar-tests.md`
   - SHA-256:
     `e704fe3e15a2b4e14f9f421ecc856e8c9122057036fa30402b544882a2d08ac9`
   - Finding disposition: recipe version 5/schema 3 was frozen; the six grouped
     materializer areas, strengthened dual-tree/Gitlink case, successful and
     failed hot-cache lifecycles, parser purity, path normalization, exact
     fsync, key churn, deep negative inventory, and no-READY rows were all
     implemented. The matrix was consolidated by security/lifecycle layer but
     no required acceptance class was intentionally omitted.

Both envelopes were read and their final SHA-256 values independently
recomputed before acceptance.

## Development failures and retries

Development attempts are distinct from final acceptance gates:

1. Initial focused materializer discovery failed during import before tests:
   Python `dataclass` processing was incompatible with the suite's raw
   `importlib` module loader. Result: one loader error, wall `0.08s`. The
   immutable contract record was changed to `NamedTuple`.
2. The next focused materializer run executed 34 tests and had one error:
   missing `stat` import in the new test, unittest `141.568s`, wall `141.70s`.
   The import was added.
3. Two targeted materializer tests then passed, unittest `7.602s`, wall
   `7.71s`.
4. An early focused hot-cache run passed 46/46, unittest `10.658s`, wall
   `10.76s`.
5. Two targeted archive/recipe tests passed, unittest `6.465s`, wall `6.59s`.
6. A focused materializer run passed 34/34, unittest `144.511s`, wall
   `144.62s`.
7. After the final omission-sensitive fsync/race assertions, a focused
   materializer run had one failed assertion: the test incorrectly required
   zero global fsyncs although existing project-layout verification fsyncs
   `.lake`. Result: 34 tests, unittest `153.285s`, wall `153.41s`. The assertion
   was narrowed to require no contract-parent fsync in the absent case and an
   exact `proofwidgets/widget` parent fsync in the removal case.
8. That exact targeted test passed, unittest `3.336s`, wall `3.44s`.
9. The orchestrator's stabilized focused materializer run passed 34/34,
   unittest `152.844s`, wall `152.95s`.
10. The orchestrator's stabilized focused hot-cache run passed 46/46,
    unittest `11.024s`, wall `11.13s`.
11. The orchestrator full serial run passed 312/312, unittest `288.772s`, wall
    `289.01s`.
12. After a conversation pause, the orchestrator reran focused hot-cache as
    requested: 46/46, unittest `10.697s`, wall `10.81s`.

One orchestrator `scripts/check_workflow.py` invocation was interrupted by a
conversation pause after partial green output and has no terminal result or
reliable duration. It changed no repository file and is not counted as an
acceptance gate. The coordinator then performed the exact final acceptance
sequence below on the unchanged passing four-file tree. This coordinator
intervention and its results are recorded separately rather than conflated
with orchestrator attempts.

## Final acceptance gates

The root coordinator reported these exact-worktree results on the current
four-file candidate before packaging:

| Gate | Result | Test duration | Wall duration |
|---|---|---:|---:|
| `python3 -m unittest discover -s tests -p test_lake_package_materialization.py -v` | 34/34 pass | 261.466s | 261.56s |
| `python3 -m unittest discover -s tests -p test_hot_main_cache.py -v` | 46/46 pass | 12.227s | 12.32s |
| `python3 -m unittest discover -s tests -p 'test_*.py' -v` | 312/312 pass | 199.384s | 199.52s |
| `python3 scripts/check_workflow.py` | 312/312 pass | 179.675s | 179.85s |
| `python3 -m compileall -q scripts tests` | pass | n/a | 0.03s |
| `python3 scripts/workflow.py validate` | valid: 26 issues, 14 PRs, 296 issued sessions in branch snapshot | n/a | unavailable |
| `python3 scripts/check_workflow.py --skip-tests` | valid | n/a | unavailable |
| precommit `git diff --check` | pass | n/a | unavailable |

After commit, the orchestrator ran the required exact SHA-bound gate:

```text
git diff --check 45d2fe657af587e8e10952aced2e156d349fd65e..HEAD
```

It passed with no output. Parent/base equality, exact changed paths, diff stat,
candidate tree, commit subject, and clean status were also independently
checked after commit.

## Activity and prohibited-operation accounting

```json
{
  "writable_orchestrators": 1,
  "read_only_scouts": 2,
  "scout_subagents": 0,
  "repository_commits": 1,
  "changed_repository_paths": 4,
  "workflow_state_edits": 0,
  "research_metric_edits": 0,
  "review_file_edits": 0,
  "pin_edits": 0,
  "protocol_edits": 0,
  "canonical_hot_cache_warms": 0,
  "operational_hot_cache_seeds": 0,
  "lake_builds": 0,
  "lean_commands": 0,
  "lake_commands": 0,
  "network_operations": 0,
  "shared_runtime_mutations": 0,
  "shared_cache_mutations": 0,
  "github_write_operations": 0
}
```

Unit tests exercised fake/private temporary warm and seed lifecycles; these are
test fixtures, not operational hot-cache warm/seed invocations and did not
touch shared runtime/cache state. No Lake, Lean, full build, dependency
retrieval, network, canonical warm, or operational seed was run by this
orchestrator or either scout.

Token usage is JSON `null`. Availability reason: the collaboration backend
does not expose per-agent or aggregate token usage, so no estimate was made.

## Final handoff

- Base: `45d2fe657af587e8e10952aced2e156d349fd65e`
- Base tree: `07df5125163a5bdddd1b80549cf622f8a0a628cd`
- Head: `d73cce44d5f9f37d38ee8d916811719408818c03`
- Head tree: `8a8985252eb019282ab6ef1842ce1b9178a58c07`
- Parent: `45d2fe657af587e8e10952aced2e156d349fd65e`
- Exact changed paths: the four owned paths listed above
- Final status: clean
- Post-integration warm: not run; root coordinator retains review,
  integration, and warm authority

The report SHA-256 is supplied out of band because embedding it would change
the digest.
