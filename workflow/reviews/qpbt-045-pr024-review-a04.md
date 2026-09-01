# QPBT-045 / LPR-024 post-adoption immutable review A04

## Findings

### F-LPR024-001 - High - Lexical traversal accepts replaced root and child directories

`scripts/hot_main_cache.py:506` checks the lexical `MIPStarRE/QPBT` entry once,
then `scripts/hot_main_cache.py:519` traverses that path with `os.walk` and
`scripts/hot_main_cache.py:530` opens files again by full lexical path.
`O_NOFOLLOW` in `_authored_file_facts` protects only the final file component.
No descriptor binds the root or an intermediate directory, and no lexical
directory incarnation is rechecked before and after its scan.

Two independent deterministic probes reproduced the gap. The root probe
replaced `QPBT` with a symlink to an external byte-identical tree after the
check at line 506 and before `os.walk`; the inventory was accepted while the
root was a symlink. The child probe replaced `QPBT/Nested` after the caller's
directory check and after `os.walk` decided it was not a link, but before the
recursive `scandir`; the external byte-identical child was likewise accepted.
Both returned their exact baseline file count, byte count, and digest.

Repair gate: traverse from a no-follow directory descriptor anchored inside
the detached project, open every child with `dir_fd`, `O_DIRECTORY`, and
`O_NOFOLLOW`, and verify the root and every child's lexical device/inode
incarnation before and after use. Every scan, stat, open, and recheck error must
fail closed. Add deterministic root- and nested-substitution regressions that
assert a `CacheError`, no snapshot, and no `READY`. The established
`BoundDirectory` and `_open_child_directory` pattern at
`scripts/materialize_lake_packages.py:434`-`464` is the relevant local model.

### F-LPR024-002 - High - Exact two-link source passes all five checks and publishes `READY`

`scripts/hot_main_cache.py:462` accepts any regular file. The before/after
identity at `scripts/hot_main_cache.py:474` omits `st_nlink`, so an exact
hard-linked authored source has the same accepted inventory as its single-link
form. This conflicts with the local authenticated-file contract at
`scripts/materialize_lake_packages.py:687`-`700`, which requires one link and
includes link count in the strong identity.

The direct helper probe produced the same inventory before and after adding an
external hard link while `st_nlink == 2`. More importantly, a complete
identity-isolated fake warm replaced committed `Owned.lean` with a hard link to
an external exact-byte file immediately after the fake build. Git reported no
source changes, all five authored-tree checks passed, `warm()` returned
`built`, `is_ready(deep=True)` returned true, and both the snapshot and
`READY` were published. This falsifies the fail-closed linked-source claims at
`protocols/CHANGELOG.md:21`-`23` and
`protocols/local-development.md:52`-`54`.

Repair gate: require `st_nlink == 1` both before and after every authored-file
read and include link count in the before/after identity tuple. Add a complete
fake-warm regression that injects an exact hard link at the post-build boundary
and proves a `CacheError`, no published snapshot, and no `READY`.

### F-LPR024-003 - Medium - Scan failures and successful Git diagnostics can hide generated source

`scripts/hot_main_cache.py:519` calls `os.walk` without `onerror`; Python's
walker suppresses recursive `scandir` errors by default. A deterministic
`PermissionError(EACCES)` at `QPBT/Hidden` therefore omitted
`Hidden/Generated.lean` and returned exactly the visible baseline inventory.
The surrounding cleanliness check at `scripts/hot_main_cache.py:680`-`686`
also returns stdout-only results when Git exits zero, discarding stderr. An
exit-zero Git result with the corresponding permission-denied warning and
empty stdout consequently produced `git_source_changes() == []`.

This review process runs as the only UID mapped in its user namespace, so a
real `chmod 000` fixture cannot deny this process access. The first privilege
fixture attempt failed with `EINVAL`; the final probe injected the same
`PermissionError` at the exact recursive `os.scandir` boundary and separately
injected Git's exit-zero warning at the exact subprocess boundary. These are
deterministic reproductions of the two fail-open branches, not claims about a
permission mode that root could not exercise here.

Repair gate: the replacement descriptor walker must raise on every enumeration
or child-inspection error. `git_source_changes` must also reject nonempty status
diagnostics on a successful exit (at minimum every diagnostic indicating an
incomplete traversal). Add an unreadable/generated-subtree regression that
exercises the scan and Git-warning paths and proves no snapshot or `READY`.

## Verdict and integration gate

Verdict: **request changes**. The post-PR adoption check is authentic, but it
only binds identity and does not repair or approve the candidate. LPR-024 must
remain `changes_requested`; QPBT-045 and INC-060 must remain open, and the
candidate must not be integrated or used for the guarded real warm. A new
immutable head must close all three findings and receive a fresh independent
review before integration. Exactly one lock-elected real current-main warm
remains the final post-integration gate.

## Immutable authentication

| Item | Independently authenticated value |
| --- | --- |
| Formal base / tree | `f4b00c7616b8710220a4f8480cfb23412914d151` / `f120a82f74df4d32bfb6b0491636546c7651b64a` |
| Reviewed head / tree | `bc41314fb74baced6f6a043cbc8956a18a2e0003` / `c71eb62b31004c1b219f93e25475d5f1aa7356b7` |
| Ancestry | one parent, exactly the formal base |
| Diff scope | five expected paths; 621 insertions and 7 deletions |
| Path-sorted `git ls-tree` manifest SHA-256 | `2707b1097d9d3cc4ba2588f54b88ea8ac159ce8c6d0d3e3ec08d91ea0b38fd26` |
| A01 writer report SHA-256 | `738890e5eaa16e9d29efda6e1b1153a555744380aab2c5e20093adae073e15e5` |
| A02 adoption report SHA-256 | `709ea72315f625673e687c27598e801d3fac459dc9ee4e576669a4dabc410f2d` |
| A02 canonical check | seventh LPR-024 check; passed and bound to the exact base/head and adoption digest |

The five paths are `protocols/CHANGELOG.md`,
`protocols/local-development.md`, `scripts/hot_main_cache.py`,
`tests/test_hot_main_cache.py`, and
`workflow/reviews/qpbt-045-hot-main-preservation-a01.md`. The detached worktree
was clean before and after review, and `git diff --check BASE..HEAD` passed.
The canonical A03 report was treated as untrusted; its SHA-256 was
`4323c08af9367c9f2972c15eb1e095f19e471249bbab9a753fc7732a8cb50591`,
but the findings above rest on independent inspection and reproductions.

## Validation and positive scope

| Gate | Result |
| --- | --- |
| `python3 tests/test_hot_main_cache.py` | pass, 51/51; test-reported 12.516 s, `/usr/bin/time` real 12.66 s |
| `python3 tests/test_mipstarre_materialization.py` | pass, 11/11; test-reported 0.536 s, `/usr/bin/time` real 0.62 s |
| `python3 scripts/workflow.py validate --json` | pass; 48 issues, 23 PRs, 0 planned sessions, 392 issued sessions, 7 stages; real 0.13 s |
| `python3 scripts/check_workflow.py --skip-tests` | pass; real 0.14 s |
| `git diff --check BASE..HEAD` | pass; real 0.00 s |
| Root substitution | reproduced: external symlinked root accepted with exact baseline inventory |
| Intermediate substitution | reproduced: external symlinked child accepted with exact baseline inventory |
| Direct hard-link helper | reproduced: exact inventory accepted with `st_nlink == 2` |
| Full fake hard-link warm | reproduced: `built`, Git-clean, deep-ready, snapshot and `READY` published |
| Recursive scan failure | reproduced by exact-boundary `EACCES` injection: hidden generated source omitted |
| Git stderr omission | reproduced: exit zero plus permission warning returned an empty change list |

The candidate does correctly bump the canonical recipe to v6, includes the
identity-bound `--replace-existing` argument, calls the authored verifier at all
five named boundaries, and binds the declared inventory/phase record into
manifest readiness. Ordinary missing, altered, untracked, generated, and
static-symlink cases in the focused suite pass. Those positive properties do
not close the directory-race, hard-link, or incomplete-traversal gaps.

No aggregate, real warm, cache seed, production build/publication, Lean/Lake
command, network or endpoint request, GitHub operation, credential access,
repository or canonical Git write, canonical state/metric edit, or nested-agent
dispatch occurred. Tests and probes used only automatically cleaned temporary
Git/cache fixtures; the deliberately vulnerable fake warm published `READY`
only inside such a fixture.

## Metrics

- Canonical session: `i045-reviewer-a04-pr024-postadoption`
- External collaboration ID: `/root/i045_pr024_review_a04`
- Topology: root coordinator -> one fresh read-only reviewer; nested agents: 0
- Durable start: `2026-09-01T16:57:14.276027Z`
- Evidence freeze: `2026-09-01T17:03:12.374417Z`
- Reviewer elapsed through evidence freeze: 358.098390 s
- Token usage: JSON `null`; availability reason: collaboration backend does
  not expose per-agent token usage. No estimate was made.
- Focused test-suite attempts: 2, both passed, 62 tests total. Workflow/checker
  attempts: 2, both passed. Diff-hygiene attempts: 1, passed. Aggregate,
  Lean/Lake, and production-cache attempts: 0.
- Adversarial probe command attempts: 3. The first aborted only at the
  unavailable-UID permission setup after `chown` returned `EINVAL`; the second
  completed all target behaviors but its direct-helper comparison had a
  reviewer-side escaped-separator oracle error; the third corrected that
  comparison against a single-link baseline. Confirmed target reproductions:
  6 (root substitution, intermediate substitution, direct hard link, complete
  hard-link warm, recursive scan failure, and Git-stderr omission).
- Candidate/repository files edited: 0. Report files edited: 1. Real cache
  builders, production publications, network actions, and nested sessions: 0.

Residual risk after repair remains the real pinned-input materialization and
Lean build plus filesystem-specific behavior of the new descriptor traversal.
Those belong to the fresh immutable review and the one post-integration
lock-elected warm; they do not justify weakening this request-changes verdict.
