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
uses one Linux `renameat2(RENAME_EXCHANGE)` operation; non-replacement uses
`RENAME_NOREPLACE`. There is no ordinary-rename fallback and replacement never
has an absent-destination interval. Before cache/input admission or target
mutation, seed requires descriptor-relative calls, inotify, a conservatively
approved local filesystem, kernel support for both flags, and successful
no-replace/exchange semantics on a disposable same-device directory under
`/tmp`. If `/tmp` is not on the target device, seed and prepare refuse.

Publication, validation, and the success-metric append share one rollback
boundary; the original is atomically exchanged back on any unambiguous
precommit failure. A root-to-target monitor installs each parent watch before
opening the next child, continuously holds all ancestor descriptors, and stays
permanently poisoned after a relevant rename, substitution, monitor failure,
or swap-and-restore event. The registered worktree root, project root, and
worktree parent also remain bound by no-follow descriptors. Fresh Git
registration, worktree `HEAD`, repository attachment, namespace, and identity
checks run before publication, around metric commit, during finalization, and
before return. Target-local staging and all rollback/retention moves are
descriptor-relative atomic exchange or no-replace operations. Seed validation
walks every copied
symlink without following it: both the lexical first hop and fully resolved
target must remain inside the private `.lake`. Broken, cyclic, and every
external package or layer link fail closed; mode bits are not evidence of
durable immutability.

Seed and prepare hold the per-target lock while checking for interrupted
replacement state. A journal and adjacent digest are both mutable repository-
local bytes and therefore are not an independent ownership proof. No later
process consumes them as authority: any journal directory or
`.lake.backup-*` entry blocks the operation before cache/input admission,
without rename, chmod, unlink, or recursive deletion, and reports every path
for manual disposition. This includes canonical self-consistent journals,
matching commit markers, and durable success metrics. The live process still
publishes a digest-bound diagnostic journal before exchange and can use only
its continuously held descriptors and in-memory bindings to roll back a
synchronous precommit failure. Journal bytes are never reloaded as mutation
authority. Successful journal and empty-staging finalization uses atomic
no-replace moves to uniquely named retained evidence; seed and prepare never
unlink or `rmdir` transaction objects. After a successful commit, the displaced
old tree must still match its continuously open descriptor and recorded
inventory; it is moved no-replace to a `.lake.retained-*` path and is never
recursively deleted. Any collision, identity mismatch, monitor poison, or ABA
preserves all objects and reports manual disposition.

Metric append failures truncate and fsync on the original descriptor while the
original metrics lock remains continuously held. Successful append plus fsync
is the commit point. The target identity guard runs before write, before fsync,
and after fsync; a guard failure truncates under that same lock. Descriptor or
lock cleanup faults after commit do not roll back the target or a competing
writer's record.

Before issue-worktree compilation, run `python3 scripts/hot_main_cache.py
prepare --worktree /absolute/issue-worktree` with the same three environment
bindings. `prepare` deep-seeds private `.lake`, invokes foundation
materialization with replacement/preservation mandatory, and verifies the
foundation. One target-operation lock spans admission, seed, authenticated
target-module and pin capture, materialization, final foundation and authored
`MIPStarRE/QPBT/` verification, and final target/cache identity checks. The
authenticated materializer must expose the exact private descriptor-bound
adaptation surface; a module missing any required no-follow, cleanup, recovery,
or error interface is refused before seed publication. There is no lexical-path
fallback. Existing `MIPStarRE.transaction` or cleanup state is rejected before
archive/cache input admission and rechecked before materializer invocation; the
adapter refuses persisted recovery rather than allowing authenticated code to
interpret same-principal transaction bytes. The
authored inventory returned by `prepare` is the post-verifier inventory and
must equal both the initial inventory and the verifier evidence. It never
invokes Lean or Lake. Pass `--replace` only to transactionally replace an
existing private `.lake`; its displaced tree remains continuously present in
the staging exchange slot until every preparation check succeeds and the
success-metric append completes, and is atomically restored on a later
unambiguous failure. After commit, a matching displaced tree is moved no-replace
to retained state and its path is reported without changing a successful
result; automatic transaction deletion is forbidden.

The cache record includes key, source SHA, elected owner, hit/miss, lock wait,
dependency-cache duration, build duration, total duration, exit status, and log
path. Cache cleanup is explicit and outside ordinary agent runs.

A coordinator read-only capacity check on 2026-09-04 observed the filesystem at
97% utilization with 164 GB free. Archived QPBT-040 and active QPBT-069 each
held a separate approximately 9.8 GB `.lake` after reflink was unavailable.
Do not create another private copy merely to investigate this pressure, and do
not delete either tree during an implementation or review session. QPBT-069 is
an active lease. After QPBT-068 receives independent review, a separately
authorized reclamation pass may consider the archived QPBT-040 tree only after
a dry-run inventory proves its session terminal, its worktree unregistered, no
live lock or explicit/implicit reference remains, and the corresponding cache
snapshot remains authenticated. Move an eligible tree to quarantine first,
observe the configured grace interval, and repeat the lease/reference and
manifest checks before irreversible deletion. Unsupported reflink remains a
capacity result, not permission to hard-link mutable build artifacts.

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
