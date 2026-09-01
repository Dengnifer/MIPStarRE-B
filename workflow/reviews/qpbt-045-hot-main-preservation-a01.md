# QPBT-045 A01 hot-main preservation implementation

## Outcome

Recipe v6 is ready for fresh immutable review. It delegates replacement to the
already authenticated and atomic MIPStarRE materializer, binds the committed
authored QPBT inventory, and rejects drift at every required build boundary.
No production cache warm, Lean build, source acquisition, network request,
endpoint request, GitHub operation, or credential access occurred. INC-060
remains open until independent review, guarded integration, and one
lock-elected exact-current-main warm pass.

## Authority and identity

- Canonical session: `i045-orchestrator-a01-hot-main-preservation`
- External collaboration ID: `/root/i045_hot_main_preservation_a01`
- Issue: `QPBT-045`
- Authenticated base: `f4b00c7616b8710220a4f8480cfb23412914d151`
- Authenticated base tree: `f120a82f74df4d32bfb6b0491636546c7651b64a`
- Worktree: `.workflow-runtime/worktrees/qpbt-045-hot-main-preservation-a01`
- Owned implementation paths: `scripts/hot_main_cache.py`,
  `tests/test_hot_main_cache.py`, `protocols/local-development.md`, and
  `protocols/CHANGELOG.md`
- Owned report: `workflow/reviews/qpbt-045-hot-main-preservation-a01.md`

The worktree matched the exact base and was clean before editing. No canonical
workflow state or research metric file was edited.

## Incident reproduction

The retained production evidence records recipe v5 failing for exact main
`a648a7d6d2d24489e393e39c4d1cc7b7f1292ec8` and cache key
`3d5cb99499071dc935470d5c4dc0cd236bedd1baf867a720041648cbec9d9793`.
Its source contract authenticated two authored QPBT files, 5,319 bytes, and
SHA-256 `0578da860a522b58b69c2c16df366c7eee3abd97c425900401e4e83c992803ed`.
The materialization argv lacked `--replace-existing`, and the materializer
failed closed before dependency retrieval or Lean compilation with `invalid
existing MIPStarRE output was preserved`.

The focused `test_recipe_v5_reproduces_nonzero_authored_failure_without_ready`
replays that command-level contract in a temporary Git fixture: a nonempty
committed authored tree, the exact v5 materialization argv, exit status 2, no
dependency/build callback, no published snapshot, and no `READY`. It does not
rerun the production warm or consume the pinned source archives.

## Repair

1. The canonical recipe is deterministically bumped from v5 to v6 and appends
   `--replace-existing` to the exact authenticated MIPStarRE materializer argv.
2. The hot-cache layer computes the same path, byte-count, and per-file digest
   inventory for the detached `MIPStarRE/QPBT/` tree that cache identity derives
   from exact committed Git blobs. It rejects links, special files, unsafe
   directories, and files that change while read.
3. The inventory must equal the commit-bound contract at
   `before_materialization`, `after_materialization`,
   `after_dependency_retrieval`, `after_build`, and `before_publication`.
4. The manifest and metric evidence record the inventory and all five phases;
   readiness requires that exact record in addition to final source evidence
   and the existing artifact inventory.
5. The materializer's existing atomic transaction remains responsible for
   replacing stale upstream content and copying the reserved authored subtree.
   Its focused suite proves exact authored preservation, stale upstream
   removal, rollback, recovery, and link rejection without changing that
   separately owned implementation.

## Acceptance evidence

| Gate | Evidence | Verdict |
| --- | --- | --- |
| Reproduce recipe-v5 failure | Exact retained INC-060 evidence plus isolated v5 regression; materialization exits 2 before later callbacks and publishes no `READY` | pass |
| Replacement-mode authenticated materialization | Canonical recipe v6 contains the exact identity-bound materializer path, pin environment, and `--replace-existing` | pass |
| Preserve authored source and refresh upstream | Nonzero hot-cache fixture passes all five checks; existing materializer fixture preserves `Owned.lean` byte-for-byte and removes stale upstream `untrusted` content | pass |
| Five inventory boundaries | Named constant, fail-closed warm checks, manifest/readiness binding, and mutation injection at every boundary | pass |
| Missing/added/altered/untracked/generated/malicious source | Regressions delete, rewrite, add untracked/generated files, and substitute a symlink; every case fails with no `READY` | pass |
| Zero and nonzero authored trees | Zero-tree source evidence/readiness test and one-file preserved-tree build both pass | pass |
| Deterministic key versioning | Equal v6 recipes yield one key; a version-only v7 change yields a different key; canonical argv/version are asserted | pass |
| Preserve security and atomicity contracts | Full dependency-free aggregate passes, including source authentication, archive bounds, lock election, atomic publication, seed rollback, and deep inventory tests | pass |
| Fresh immutable review | Must be dispatched by the root coordinator against the final commit and exact manifest | pending |
| Guarded current-main warm | Allowed only after reviewed integration; must use the singleton lock and three authenticated local inputs | pending |

## Validation

| Command | Result | Timing |
| --- | --- | ---: |
| Baseline `python3 tests/test_hot_main_cache.py` | pass, 46/46 | 11.793 s test; 11.94 s wall |
| First post-edit `python3 tests/test_hot_main_cache.py` | 49/51; two stale test expectations (`v5`, old generic drift error), no implementation failure | 12.245 s test; 12.39 s wall |
| Final `python3 tests/test_hot_main_cache.py` | pass, 51/51 | 11.138 s test; 11.26 s wall |
| `python3 tests/test_mipstarre_materialization.py` | pass, 11/11 | 0.317 s test; 0.41 s wall |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | pass, 349/349; exactly one aggregate run | 182.405 s test; 183.12 s wall |
| `python3 -m compileall -q scripts tests` with pycache under `/tmp` | pass | 0.34 s wall |
| `python3 tests/test_check_workflow.py` | pass, 3/3 | 0.003 s test; 0.08 s wall |
| `python3 scripts/workflow.py validate --json` | pass: 48 issues, 23 PRs, 0 planned sessions, 392 issued sessions, 7 stages | 0.13 s wall |
| `python3 scripts/check_workflow.py --skip-tests` | pass | 0.12 s wall |
| `git diff --check` | pass | 0.03 s wall |

Test commands: six substantive executions before report freeze (one baseline,
one expectation-only failure, two focused suites, one aggregate, and one
workflow checker suite); five passed and one exposed the two stale assertions.
Aggregate attempts: one, passed; aggregate retries: zero. Python compile
attempts: one, passed. Workflow validation/checker attempts: three, all passed.
Lean/Lake compile attempts and builds: zero. Production cache warm/seed/build/
publication attempts: zero. The fake hot-cache tests publish only inside
disposable temporary directories.

## Delegation and usage

The permitted read-only scout was attempted once as
`i045-scout-a02-cache-contract`, but collaboration admission rejected it with
`agent thread limit reached` before any external thread or canonical session
existed. Issued nested subagents: zero. Topology is therefore root coordinator
-> this writable A01 orchestrator. Collaboration does not expose per-agent
token usage, so token fields must remain JSON `null` with availability reason
`Collaboration backend does not expose per-agent token usage`; no estimate is
made.

## Incident disposition and residual risk

- INC-054 remains the resolved first occurrence; no historical record changed.
- INC-060 has a validated repair candidate but remains open. Closing it before
  independent review, integration, and the guarded real warm would overstate
  evidence.
- The production archives, Mathlib reservoir, filesystem-lock behavior, and
  actual Lean compilation are intentionally unexercised by this session. The
  post-integration warm is the remaining operational proof and must not be
  duplicated by another agent.
- Final commit/tree and path-sorted blob manifest hashes are returned out of
  band because embedding the containing commit or report hash here would be
  self-referential.
