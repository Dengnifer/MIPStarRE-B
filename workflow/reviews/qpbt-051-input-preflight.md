# QPBT-051 authenticated-input preflight evidence

Session: `i051-orchestrator-a01-preflight`

## Verdict

The canonical warm now authenticates its complete local input tuple before a
cache hit or builder election: exactly one Mathlib selector, one pinned
MIPStarRE archive, and the directory containing all eight pinned Lake-package
archives. The checks bind committed pin/manifest shape plus regular,
non-symlinked input size and SHA-256. Input locations remain outside cache
identity.

The new `prepare` command provides one build-readiness path for issue
worktrees. It authenticates the tuple, deep-seeds a private `.lake`, invokes
the identity-bound MIPStarRE materializer with `replace_existing=True`, compares
authored QPBT inventory before and after, and verifies the resulting foundation.
It contains no Lean or Lake invocation.

## Safety invariants

- Any absent Mathlib, MIPStarRE, or Lake-package binding fails before
  `ExclusiveLock`, detached clone, staging, build, manifest, or `READY`.
- Mathlib retains the exactly-one source/archive selector rule.
- Archive and archive-directory paths are absolute, present, and have no
  symlink components; every authenticated archive is a stable regular file
  with pinned byte count and digest.
- The preflight changes neither recipe version nor identity inputs, so cache
  key semantics are unchanged.
- `prepare` calls deep `seed` before source publication and never compiles.
- Foundation replacement/preservation is mandatory and cannot be omitted by
  CLI callers.
- Authored `MIPStarRE/QPBT/` path-and-byte inventory must be identical before
  and after materialization; foundation verification must then pass.
- Failure never publishes cache `READY`; materializer transaction rollback
  remains owned by the existing authenticated materializer.

## Incident disposition

INC-065's third input-preflight omission is addressed by the pre-election tuple
gate. INC-070's missing source after a bare seed and INC-071's third omitted
`--replace-existing` are addressed together by `prepare`. Protocol text now
distinguishes cache seeding from build readiness.

## Validation and accounting

No Lean/Lake command, real warm, real seed, cache materialization, network,
GitHub, endpoint, credential, canonical-state, or metrics write was run.

| Counter | Result |
| --- | --- |
| Python syntax checks | pass |
| Focused hot-cache attempts | 5: one test placement error, one 4-failure compatibility pass, one stale concurrent 2-failure pass, one `65/65` pass in 17.425s, one final `66/66` pass in 20.694s |
| Workflow checker | `3/3` pass in 0.006s |
| Workflow unit tests | `77/77` pass in 1.069s |
| Workflow validation | valid; 59 issues, 33 PRs, 469 issued sessions |
| Repository-wide discovery | `361/363` in 308.703s inside the sandbox; the two Unix-socket fixtures denied there passed `2/2` in 66.911s under the bounded permission rerun |
| Lean/Lake/build attempts | 0 |
| Real warm/seed/materialization attempts | 0 |
| Nested agents | 0 |
| Token usage | `null` |
| Token unavailable reason | collaboration backend does not expose per-session token usage |

Final syntax, workflow-validation, and `git diff --check` gates passed. Exact
candidate commit/tree/parent/blob identities are recorded after the candidate
is frozen. The commit containing this report cannot self-record its own SHA;
that identity is returned out of band to the root coordinator.

## Reviewer checklist

- Authenticate exact base `e8b790a32c230aaf0f17ca2aa389ef41f94867f3`,
  final head/tree/parent, and the six-path owned manifest.
- Confirm complete tuple failure precedes `ExclusiveLock`, hit handling,
  detached clone, staging, and metrics publication.
- Check exact-one Mathlib semantics and pinned size/digest validation for the
  MIPStarRE archive and every Lake-package archive.
- Confirm input paths and evidence do not enter cache identity.
- Check `prepare` order: authenticated tuple, deep private seed, mandatory
  replacement/preservation materialization, authored inventory equality, then
  foundation verification, with no Lean/Lake command.
- Re-run focused and aggregate Python tests, workflow validation, syntax,
  forbidden-scope, changed-path, and `git diff --check` gates.
- Review residual race handling: each downstream materializer reauthenticates
  archive bytes after preflight; directory/file substitution must fail closed.
