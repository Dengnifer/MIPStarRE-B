# QPBT-025 generated-sidecar security scout (a02)

## Session identity and scope

- Stable logical name: `i025-scout-a02-sidecar-security`.
- Role: independent read-only security scout under the QPBT-025 orchestrator.
- Owned worktree inspected:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-025-sidecar-a01`.
- Base and observed `HEAD`:
  `45d2fe657af587e8e10952aced2e156d349fd65e`.
- Base and observed committed tree:
  `07df5125163a5bdddd1b80549cf622f8a0a628cd`.
- The observed commit and committed tree did not change. Unstaged implementation
  edits appeared concurrently while this scout was running and are attributed
  to the orchestrator, not this scout.
- Topology: root coordinator -> QPBT-025 orchestrator -> this read-only scout.
  Subagents: `0`; depth below orchestrator: `1`.

## Verdict

The frozen A14 design is sound within its stated private, serialized staging
trust boundary: validate one exact internal revision-bound contract, remove
only the descriptor-bound generated sidecar, then run both existing exact
source-tree comparisons without projection. Bare `verify` remains read-only;
the canonical hot-cache verifier uses one non-parameterized explicit removal
flag before and after Lake; snapshots and seeds omit the sidecar while retaining
and inventory-binding package-local `.lake/build` output.

The live in-progress implementation follows that design. Four pitfalls reported
to the orchestrator during the scout were subsequently observed as dispositioned
in the current diff:

1. Metadata snapshot sequencing was fixed. `_read_bound_regular` now returns
   its stable post-read `stat_result`; `_remove_generated_sidecar` validates
   sidecar permissions from that same snapshot and retains its corresponding
   full identity for the immediate pre-unlink descriptor/name check
   (`scripts/materialize_lake_packages.py:1389-1422,1531-1546`). This prevents
   the previous gap in which a later unsafe mode could become the retained
   unlink identity after an earlier safe-mode check.
2. Persistent absence was fixed. `_PreparedPackageSource` stores the removed
   bound parent/name and every later `assert_current` requires that exact name
   to remain absent (`scripts/materialize_lake_packages.py:1449,1469-1472,
   1554-1560`). Because `verify` asserts the prepared source after scan and
   after each tree computation, recreation in an observed verifier phase fails.
3. Required open capabilities now fail closed. Sidecar removal explicitly
   rejects a platform without `O_NOFOLLOW` or `O_NONBLOCK` before binding the
   target or sidecar (`scripts/materialize_lake_packages.py:1482-1489`). The
   supported Linux path therefore cannot silently degrade its no-follow or
   nonblocking claim.
4. Contract path validation was strengthened. Raw target and sidecar strings
   must be NUL-free, exactly equal to their canonical `PurePosixPath` forms,
   composed of safe components, share the same parent, and have the exact
   target/`target + ".hash"` relationship
   (`scripts/materialize_lake_packages.py:328-368`).

No remaining design blocker was identified by this read-only inspection. This
is not execution validation: the orchestrator's focused tests and prescribed
validation gates remain necessary.

## Frozen security invariants

### Authority and archive ownership

- Deletion authority is one immutable internal tuple only:
  `proofwidgets`, revision
  `6e311e2a844da9b2cc3971187df2fe0066947b93`, target
  `widget/package-lock.json`, target SHA-256
  `3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d`,
  sidecar `widget/package-lock.json.hash`, and exact bytes
  `179e66574f04806e`.
- No pin-schema deletion field, caller-selected package/path/hash, suffix rule,
  `*.hash` glob, trace parser, archive overlay, or Git-index projection may
  grant cleanup authority.
- Archive inspection must prove the target is the exact regular member with
  the exact digest and the declared sidecar is absent. This check occurs after
  the complete normalized entry map and before facts return or entry writing.
- An unrelated or future archive-owned `.hash` remains authenticated source;
  mutation or deletion must fail exact tree identity. The declared sidecar
  appearing in its matching archive is a provenance contradiction and fails.
- A different package or ProofWidgets revision receives no exception.

### Descriptor-relative validation and removal

- Bind the package from the already bound `.lake/packages` descriptor and bind
  each fixed parent component independently with `O_DIRECTORY|O_NOFOLLOW`.
  Bind target and sidecar beneath the held parent with
  `O_NOFOLLOW|O_NONBLOCK`; never validate or unlink through a recomposed lexical
  path.
- Target and sidecar must each be regular and singly linked. The target must
  hash to the exact contract digest. The sidecar must be exactly 16 bytes with
  exact lowercase ASCII content and no newline, have no execute bits, and have
  no setuid, setgid, or sticky bits.
- Stable file identity must include device, inode, full mode, size, mtime,
  ctime, and link count. Read through the held descriptor with a hard byte
  bound; compare pre/post descriptor identity; immediately before unlink compare
  the same identity against both the held descriptor and a no-follow name stat.
- Immediately before mutation, recheck target, every bound parent, package
  root, packages root, and project layout. Unlink only the sidecar basename via
  `os.unlink(..., dir_fd=bound_parent_fd)`, fsync that same parent, require exact
  name absence, and repeat incarnation checks.
- Symlinks are never followed; FIFOs/sockets cannot block; multiply-linked
  files fail before unlink. Symlink targets and hardlink peers are not modified.
  Malformed or unsafe sidecars remain present. If the exact sidecar is removed
  and later ordinary source drift is found, failure after cleanup is intended
  in disposable private staging and must publish no `READY`.
- Descriptor checks narrow ordinary substitution races but cannot atomically
  exclude an actively racing same-UID process. The security argument therefore
  retains the existing private staging directory, single elected builder, and
  sequential child-completion assumptions; it must not claim stronger race
  exclusion.

### Source comparison, publication, and seed

- Cleanup occurs before `_scan_tree` and before both existing unprojected Git
  tree computations. Package, parent, and target descriptors remain open across
  scan and both comparisons; `/proc/self/fd/<package-fd>` is the work tree.
- Recheck bound incarnations and removed-name absence after scan, after the
  archive-tree computation, after the Gitlink-aware computation, and on context
  exit. Every undeclared extra path and every source/config/manifest/Gitlink
  mutation remains visible.
- Bare `verify` performs no cleanup and rejects a present sidecar through the
  ordinary exact tree comparison. Only
  `verify --remove-validated-generated-sidecars` enables the compiled-in policy;
  the flag accepts no value.
- Canonical warm order remains materialize, flagged verify, dependency command,
  build, flagged verify, project/source checks, whole-`.lake` inventory,
  manifest/`READY`, atomic publication. The recipe version is exactly `5`; the
  recipe schema remains `3`; no new phase or field is introduced.
- The post-build verifier removes the sidecar before inventory. The complete
  remaining `.lake` inventory includes package-local `.lake/build/**` but no
  sidecar. Deep readiness binds that exact path set cryptographically. Seed
  deep-verifies the source snapshot, copies it privately, makes only the copy
  writable, and verifies the destination inventory; direct tests must still
  assert sidecar absence and build-artifact presence because the manifest
  inventory is aggregate rather than path-listed.

## Source anchors and paths inspected

The repository `AGENTS.md` was read fully before inspection. Required review
anchors read:

- `workflow/reviews/qpbt-024-postintegration-warm-failure-9b6.md`
- `workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md`
- `workflow/reviews/qpbt-024-sidecar-security-a12.md`
- `workflow/reviews/qpbt-024-sidecar-synthesis-a14.md`
- `workflow/reviews/qpbt-024-sidecar-hooks-a15.md`
- `workflow/reviews/qpbt-024-sidecar-tests-a16.md`

Implementation paths inspected:

- `scripts/materialize_lake_packages.py`
- `scripts/hot_main_cache.py`

The concurrent diff/status also showed
`tests/test_lake_package_materialization.py`, but this scout did not execute any
test and did not treat the in-progress test file as a validation result.

## Read-only commands

Commands were run with the owned worktree as their working directory. Repeated
commands are recorded because the worktree changed concurrently.

```text
cat AGENTS.md
nl -ba workflow/reviews/qpbt-024-postintegration-warm-failure-9b6.md
nl -ba workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md
nl -ba workflow/reviews/qpbt-024-sidecar-security-a12.md
nl -ba workflow/reviews/qpbt-024-sidecar-synthesis-a14.md
nl -ba workflow/reviews/qpbt-024-sidecar-hooks-a15.md
nl -ba workflow/reviews/qpbt-024-sidecar-tests-a16.md
wc -l workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md
wc -l workflow/reviews/qpbt-024-sidecar-security-a12.md
wc -l workflow/reviews/qpbt-024-sidecar-synthesis-a14.md
wc -l workflow/reviews/qpbt-024-sidecar-hooks-a15.md
sed -n '1,170p' workflow/reviews/qpbt-024-sidecar-security-a12.md | nl -ba
sed -n '171,340p' workflow/reviews/qpbt-024-sidecar-security-a12.md | nl -ba -v171
sed -n '1,185p' workflow/reviews/qpbt-024-sidecar-synthesis-a14.md | nl -ba
sed -n '186,380p' workflow/reviews/qpbt-024-sidecar-synthesis-a14.md | nl -ba -v186
sed -n '1,155p' workflow/reviews/qpbt-024-sidecar-hooks-a15.md | nl -ba
sed -n '156,320p' workflow/reviews/qpbt-024-sidecar-hooks-a15.md | nl -ba -v156
sed -n '160,315p' workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md | nl -ba -v160
git status --short --branch
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
rg -n <scoped security and implementation symbol patterns> scripts/materialize_lake_packages.py scripts/hot_main_cache.py
git diff -- scripts/materialize_lake_packages.py scripts/hot_main_cache.py
git diff -- scripts/materialize_lake_packages.py
git diff -- scripts/hot_main_cache.py
git diff --stat
nl -ba scripts/materialize_lake_packages.py | sed -n '1,330p'
nl -ba scripts/materialize_lake_packages.py | sed -n '340,680p'
nl -ba scripts/materialize_lake_packages.py | sed -n '730,930p'
nl -ba scripts/materialize_lake_packages.py | sed -n '920,1090p'
nl -ba scripts/materialize_lake_packages.py | sed -n '1180,1365p'
nl -ba scripts/materialize_lake_packages.py | sed -n '1330,1595p'
nl -ba scripts/materialize_lake_packages.py | sed -n '1880,1985p'
nl -ba scripts/materialize_lake_packages.py | sed -n '2030,2160p'
nl -ba scripts/materialize_lake_packages.py | sed -n '2225,2310p'
nl -ba scripts/materialize_lake_packages.py | sed -n '2435,2485p'
nl -ba scripts/hot_main_cache.py | sed -n '120,320p'
nl -ba scripts/hot_main_cache.py | sed -n '1760,1850p'
nl -ba scripts/hot_main_cache.py | sed -n '1970,2220p'
nl -ba scripts/hot_main_cache.py | sed -n '2290,2465p'
date --iso-8601=ns
```

The literal `rg` invocations were scoped to sidecar, binding, verification,
tree-computation, inventory, readiness, warm, seed, recipe, permission,
canonical-path, and tombstone symbols in the two implementation scripts. No
unbounded filesystem search was performed.

## Accounting

- Repository file edits by this scout: `0`.
- Workflow/state edits by this scout: `0`.
- Git writes by this scout: `0`.
- Tests run: `0`.
- Builds run: `0`.
- Warm invocations: `0`.
- Seed invocations: `0`.
- Lean invocations: `0`.
- Lake invocations: `0`.
- Network operations: `0`.
- Runtime mutations: `0`.
- Cache mutations: `0`.
- Subagents: `0`.
- Token usage: JSON `null`.
- Token availability reason: the collaboration backend does not expose
  per-agent token usage; no estimate was made.
- Canonical start timestamp: unavailable because no timestamp was recorded
  before the initial mandated `AGENTS.md` read. Elapsed time is therefore also
  unavailable and is not estimated.
- Evidence cutoff timestamp: `2026-09-01T02:43:31.251054790+08:00`.

Final observed Git status, attributable entirely to concurrent orchestrator
implementation work:

```text
## issue/qpbt-025-sidecar-a01
 M scripts/hot_main_cache.py
 M scripts/materialize_lake_packages.py
 M tests/test_hot_main_cache.py
 M tests/test_lake_package_materialization.py
```

The envelope SHA-256 is supplied out of band because embedding it here would
change the digest.
