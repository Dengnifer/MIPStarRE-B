# Local Development and Cache

## Worktree isolation

Each writable implementation issue uses a dedicated branch and worktree. The
issue orchestrator is its only integration owner. Read-only scouts may inspect
any tree. A prover may edit only delegated paths. Reviewers never edit.

Before dispatch, record the exact base SHA and confirm a clean worktree. After
delivery, inspect `git diff --check`, changed paths, scoped type-checks, and the
result envelope. Do not let agents commit canonical workflow state or raw run
logs.

## Hot-main cache

The GitHub "latest successful main artifact" is replaced by a content-addressed
local cache under `.workflow-runtime/cache/main/`.

When `--runtime-dir` is omitted, the cache command derives this runtime root
from the primary non-bare Git worktree (`.workflow-runtime` beneath the root
reported by `git worktree list --porcelain`). Linked issue worktrees therefore
share one lock and one published snapshot for a cache key. Prunable or
unresolvable registered entries are ignored; if the repository root or primary
worktree cannot be resolved, the command fails closed and asks for an explicit
runtime directory. An explicit `--runtime-dir` keeps its existing semantics:
absolute paths remain absolute and relative paths resolve beneath the supplied
`--repo-root`.

The cache key contains:

- the local `main` commit SHA;
- SHA-256 of `lean-toolchain`;
- SHA-256 of `lakefile.toml`; and
- SHA-256 of `lake-manifest.json` and every versioned source/materializer pin;
- the commit-bound path-and-byte inventory of `MIPStarRE/QPBT/`; and
- the identifier, version, and exact argv of the canonical dependency and
  build recipe.

`python3 scripts/hot_main_cache.py warm` first authenticates the complete local
input tuple: exactly one of `MATHLIB_SOURCE` or `MATHLIB_ARCHIVE`, the
`MIPSTARRE_ARCHIVE`, and the directory named by `LAKE_PACKAGE_ARCHIVES` with
all eight pinned archives. Paths must be absolute, present, and free of symlink
components. Every verifier, pin, and manifest is captured through a bounded
no-follow descriptor, authenticated against the commit-bound cache inputs, and
executed or parsed only from those captured bytes. Regular-file sizes, SHA-256
digests, and pinned manifest shapes are checked before cache-hit handling or
lock acquisition. These locations remain excluded from cache identity.

After that preflight, `python3 scripts/hot_main_cache.py warm` takes an exclusive `flock`. The elected
owner builds a detached local clone in a key-specific staging directory, runs
Mathlib cache retrieval when needed, and runs the full build. It writes the
manifest and metrics only after success, then atomically renames staging to the
published key. Waiters re-check the manifest after the lock is released and
report a cache hit instead of compiling.

Canonical recipe v7 invokes the authenticated MIPStarRE materializer with
`--replace-existing`. The materializer refreshes the pinned upstream tree while
copying the reserved committed `MIPStarRE/QPBT/` subtree byte-for-byte through
its atomic transaction. The cache independently compares that authored
path-and-byte inventory with the exact main commit before materialization,
after materialization, after dependency retrieval, after the build, and
immediately before publication. A missing, added, altered, untracked,
generated, linked, or otherwise unsafe authored source fails the elected warm;
failed staging never contains or publishes `READY`. The manifest records the
verified inventory and all five boundaries. Each inventory walk binds the
project, foundation, authored root, and recursive child directories with
no-follow descriptors, rechecks their lexical incarnations before and after
use, and reads only single-link regular files whose strong descriptor/name
identity remains unchanged. Any traversal error or Git cleanliness diagnostic
fails closed. Recipe v7 invalidates snapshots created under the rejected v6
verifier. Do not retry an older recipe-v5 failure after authored QPBT sources
exist.

Publication also records a content-addressed inventory of the entire `.lake`
tree. The `READY` marker binds the manifest bytes. Cheap status and warm-hit
checks use that marker; `seed` performs deep source and destination inventory
verification so corruption cannot enter an issue worktree unnoticed.

Failed staging output is retained or logged as diagnostic state but is never
published as successful. A new main SHA or input hash produces a new key; it
does not mutate an older cache.

`python3 scripts/hot_main_cache.py seed --worktree PATH` waits for a published
key, verifies that the target is a live compatible registered Git worktree, and
copies `.lake` with copy-on-write reflinks when available. Every issue worktree
receives a private writable copy. Hard-linked or directly shared `.lake/build`
trees are forbidden because Lean processes can update artifacts. Replacement
uses a private backup and distinct old-moved/new-published transaction state.
Publication, validation, and the success-metric append share one rollback
boundary; the original is restored on any precommit failure. Backup deletion
is best-effort only after that commit point. Seed validation walks every copied
symlink without following it: both the lexical first hop and fully resolved
target must remain inside the private `.lake`. Broken, cyclic, and every
external package or layer link fail closed; mode bits are not evidence of
durable immutability.

Seed and prepare hold the per-target lock while authenticating and recovering
an interrupted replacement journal. Recovery never infers ownership from a
`.lake.backup-*` filename: an invalid/missing journal or unowned backup-shaped
entry fails unchanged. A valid uncommitted journal restores the authenticated
prior tree before cache or input admission. The journal is digest-bound and
durably published before the first rename; recovery is idempotent and does not
consult the shared cache. An uncommitted replacement is retained separately
before the original is restored. A replacement with a durable success metric
is committed even if the process dies before writing the matching commit
marker; recovery keeps it and deletes only its journal-authenticated backup.
Metric append failures truncate and fsync on the original descriptor while the
original metrics lock remains continuously held. Successful append plus fsync
is the commit point; descriptor or lock cleanup faults after it do not roll back
the target or a competing writer's record.

Before issue-worktree compilation, run `python3 scripts/hot_main_cache.py
prepare --worktree /absolute/issue-worktree` with the same three environment
bindings. `prepare` deep-seeds private `.lake`, invokes foundation
materialization with replacement/preservation mandatory, and verifies the
foundation. One target-operation lock spans admission, seed, authenticated
target-module and pin capture, materialization, final foundation and authored
`MIPStarRE/QPBT/` verification, and final target/cache identity checks. The
authored inventory returned by `prepare` is the post-verifier inventory and
must equal both the initial inventory and the verifier evidence. It never
invokes Lean or Lake. Pass `--replace` only to transactionally replace an
existing private `.lake`; its backup is retained until every preparation check
succeeds and the success-metric append completes, and is restored on a later
failure. Backup deletion is best-effort after that commit point and a retained
backup is reported without changing a successful result.

The cache record includes key, source SHA, elected owner, hit/miss, lock wait,
dependency-cache duration, build duration, total duration, exit status, and log
path. Cache cleanup is explicit and outside ordinary agent runs.

## Validation ladder

The canonical focused Python validation command is:

```text
python3 tests/test_check_workflow.py
```

Run that exact argv when validating workflow-ledger changes. The `tests/`
directory is intentionally not imported as a package; use a direct test path
or unittest discovery rather than a `tests.test_*` module name.

During proof work:

1. Search source and Mathlib.
2. Run `lake env lean path/to/changed.lean`.
3. Scan owned files for unexpected `sorry`, `admit`, `axiom`, and `constant`.
4. Run affected Lake targets and workflow unit tests.
5. Run blueprint declaration and source-integrity checks.

Before review:

1. verify the local PR base/head and clean generated state;
2. run all scoped checks recorded by the issue;
3. run `lake build` using the issue worktree's private cache;
4. build/lint the blueprint when it changed;
5. validate local issue/PR/session state; and
6. save command, exit status, duration, and log paths in the PR record.

A registered validation command is evidence only after that exact command has
run successfully. A similar-looking command or an agent-reported paraphrase is
not interchangeable.

After integration, warm the new main cache once. Main cache builds are never
cancelled merely because another agent is waiting. Issue-level builds may be
cancelled and retried when their head changes.

## Fixed-point bounds

Automated fix/review loops are serialized per PR and stop after five consecutive
agent-authored fix attempts. A repeated identical failure is not retried without
a changed hypothesis, source, or protocol. On the third recurrence, record a
workflow incident and evaluate a root-cause protocol change.
