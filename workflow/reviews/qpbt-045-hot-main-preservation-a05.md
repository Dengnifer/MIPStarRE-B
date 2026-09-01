# QPBT-045 / LPR-024 security repair A05

## Outcome

All three A03 source-confinement findings were independently reproduced on the
authenticated LPR-024 head and are repaired in this candidate. Authored-tree
inventory now recurses only through descriptor-bound directories, rejects
hard-linked files, fails on incomplete filesystem or Git inspection, and
invalidates snapshots made under the rejected verifier by advancing the
canonical recipe from v6 to v7.

No production cache warm, seed, build, or publication occurred. No Lean/Lake,
network, endpoint, GitHub, or credential action occurred. QPBT-045 and INC-060
must remain open until a fresh immutable review approves this head, guarded
integration completes, and the one lock-elected real current-main warm passes.

## Authority and authentication

- Canonical session: `i045-orchestrator-a05-pr024-security-repair`.
- Parent: root coordinator `i001-coordinator-a01-bootstrap`.
- Issue / local PR: `QPBT-045` / `LPR-024`.
- Worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-045-hot-main-preservation-a01`.
- Required and observed base HEAD:
  `bc41314fb74baced6f6a043cbc8956a18a2e0003`.
- Required and observed base tree:
  `c71eb62b31004c1b219f93e25475d5f1aa7356b7`.
- Base parent: `f4b00c7616b8710220a4f8480cfb23412914d151`.
- Initial and pre-report worktree scope: clean initially; before this report,
  exactly the four owned implementation/protocol paths were modified.
- A03 untrusted-evidence SHA-256:
  `4323c08af9367c9f2972c15eb1e095f19e471249bbab9a753fc7732a8cb50591`.

The canonical QPBT-045 issue, LPR-024 record, A03 report, current candidate
code/tests/protocol, and descriptor/`dir_fd`/no-follow/link-count patterns in
`materialize_lake_packages.py` were read before edits. Canonical workflow state
and research metrics were not edited.

## Independent reproduction

The temporary read-only probe `/tmp/i045_pr024_reproduce.py` (SHA-256
`e8dc0f88b56eb3c7a72a58ca567119d3a0a1d5a25ea9ee1bf56c17b82918f1f0`)
ran once against the exact base and reproduced four concrete observations:

1. Replacing `MIPStarRE/QPBT` with a symlink to a byte-identical external tree
   between the lexical check and `os.walk` returned the committed inventory.
2. A two-link regular `Owned.lean` with exact committed bytes was accepted.
3. A deterministic `PermissionError` from scanning a generated nested subtree
   was silently omitted and returned the baseline inventory.
4. `git status` exit 0 with a permission-denied warning on stderr returned an
   empty source-change list.

The probe printed all four reproduction markers and exited 0 in one attempt.
It wrote no repository path and performed no warm or publication.

## Repair

### Descriptor-bound authored inventory

`authored_tree_facts_on_disk` binds the project directory with
`O_DIRECTORY | O_NOFOLLOW`, then opens `MIPStarRE`, `QPBT`, and every recursive
child relative to held parent descriptors. Every bind compares the pre-open
name identity, bound descriptor identity, and post-open lexical identity. Each
directory rechecks its lexical incarnation before and after use and compares
strong directory metadata across the complete scan. Directory entries are
enumerated with `os.scandir(directory_fd)` and then inspected/opened relative
to that same descriptor. Every scan, stat, open, read, and recheck error fails
closed.

Files must be regular with `st_nlink == 1` at name inspection, descriptor
inspection, descriptor recheck, and final name recheck. The common strong
identity contains device, inode, mode, size, mtime, ctime, and link count.
Content length and digest are computed only through the held no-follow file
descriptor. Replacement, unlink/relink, metadata drift, and new hard links are
therefore rejected.

### Git completeness and cache identity

`git_source_changes` now rejects any nonempty stderr from the exact cleanliness
command even when Git exits zero; the first bounded diagnostic is included in
the error. This prevents a permission warning from certifying an incompletely
inspected checkout.

The canonical recipe advances from v6 to v7. The verifier implementation is
not otherwise an identity input, so a version bump is required to keep a
snapshot produced by the rejected verifier from remaining addressable. The
materializer argv and `--replace-existing` behavior are unchanged.

`protocols/local-development.md` and `protocols/CHANGELOG.md` now state the
descriptor, incarnation, single-link, error, Git-diagnostic, and v7 rules. This
is the smallest protocol change supported by the independently reproduced
immutable-review evidence; no new workflow issue was needed beyond QPBT-045.

## Finding dispositions

| Finding | Disposition | Evidence |
| --- | --- | --- |
| `F-LPR024-001` high: root/intermediate substitution | resolved in candidate, pending fresh review | No-follow root/child `dir_fd` recursion plus pre/post lexical and scan-identity checks; deterministic root and nested after-bind substitutions both fail while the external sentinel remains unchanged. |
| `F-LPR024-002` high: exact hard link publishes | resolved in candidate, pending fresh review | Four-point single-link enforcement and strong identity including `st_nlink`; helper and full fake-warm hard-link regressions fail, with no snapshot or `READY`. |
| `F-LPR024-003` medium: unreadable subtree/Git warning omitted | resolved in candidate, pending fresh review | Descriptor `scandir` errors propagate; deterministic generated-subtree denial fails the full fake warm with no snapshot/`READY`; exit-zero Git warning raises `CacheError`. |

Ordinary zero-file and one-file authored inventories, exact nonzero
preservation, upstream refresh, existing drift boundaries, recipe-v5 failure,
and materializer replacement/rollback behavior remain green.

## Validation

| Command | Result | Timing |
| --- | --- | ---: |
| `python3 /tmp/i045_pr024_reproduce.py` on the base | pass; all 3 findings / 4 observations reproduced | 0.3 s tool wall |
| First targeted 8-test repair run | 7 pass; unreadable fixture used mode 000 and cleanup surfaced `PermissionError` after the verifier had already failed closed | 0.689 s test |
| Corrected unreadable targeted test | pass, 1/1 | 0.098 s test |
| Repeated adversarial/ordinary targeted set | pass, 8/8 | 0.591 s test |
| Legacy boundary targeted set | pass, 4/4 | 0.640 s test |
| Final `python3 tests/test_hot_main_cache.py` | pass, 56/56 | 12.054 s test; 12.119 s tool wall |
| Final `python3 tests/test_mipstarre_materialization.py` | pass, 11/11 | 0.344 s test; 0.330 s tool wall |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | pass, 354/354; exactly one aggregate attempt | 182.083 s test |
| `python3 -m compileall -q scripts tests` | pass; ignored bytecode only | 0.010 s tool wall |
| `python3 scripts/workflow.py validate --json` | pass; 48 issues, 23 PRs, 0 planned sessions, 392 issued sessions, 7 stages | 0.040 s tool wall |
| `python3 scripts/check_workflow.py --skip-tests` | pass | 0.180 s tool wall |
| `python3 tests/test_check_workflow.py` | pass, 3/3 | 0.002 s test; 0.041 s tool wall |
| `git diff --check` | pass | pre-report and final gates |

The first unreadable-fixture error was a test-design correction, not an
implementation escape: mode 000 caused the new no-follow child open itself to
fail closed, then impeded disposable failure-tree cleanup. The deterministic
fixture now injects the intended nested `scandir` denial without altering
cleanup permissions. No aggregate retry occurred.

## Metrics and action accounting

- Canonical start: `2026-09-01T16:57:14.378182Z`.
- Pre-commit evidence cut: `2026-09-01T17:16:51.916572958Z`.
- Elapsed through that cut: `1177.538390958` seconds from same-host realtime
  timestamps; root lifecycle timing remains authoritative.
- Token usage: JSON `null`.
- Token availability reason: collaboration backend does not expose per-agent
  token usage; no estimate was made.
- Topology: root coordinator -> one writable A05 repair orchestrator; nested
  agents: 0.
- Independent reproduction attempts: 1; observations reproduced: 4.
- Targeted repair test commands before final suites: 4; three passed and one
  exposed the bounded fixture-cleanup correction described above.
- Final focused suites: 2 attempts, both passed (`56/56` and `11/11`).
- Aggregate attempts: 1, passed `354/354`; aggregate retries: 0.
- Compileall attempts: 1, passed.
- Workflow validation/checker commands: 3, all passed.
- Production cache warm/seed/build/publication attempts: 0.
- Lean/Lake commands and builds: 0.
- Network, endpoint, GitHub, and credential actions: 0.
- External review actions: 0; root must dispatch a fresh immutable reviewer.
- Repository content paths written: the 5 exact owned paths only, including
  this report. One temporary reproduction file and one unused temporary
  compile directory were created under `/tmp`; compileall produced ignored
  bytecode only and did not change tracked scope.
- Git write remaining at report cut: one exact-path candidate commit.

Final commit, tree, parent, path-sorted blob manifest SHA-256, report SHA-256,
and post-commit elapsed are returned out of band because embedding them in this
committed report would be self-referential.
