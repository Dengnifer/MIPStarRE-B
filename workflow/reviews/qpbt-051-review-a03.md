# LPR-034 / QPBT-051 immutable security review

## Findings

### Blocker - F051-A03-001: the preflight executes mutable verifier and pin bytes as though they were identity-bound

Location: `scripts/hot_main_cache.py:2159`

Evidence: `CacheIdentity.create` derives `identity.inputs` from Git blobs at lines 1781-1788, and the canonical recipe includes both materializer modules and both pin files in that identity. However, `_load_identity_module` imports `self.project_dir / relative_path` directly at lines 2159-2168 without reading it through a no-follow descriptor or comparing the executed bytes with `self.identity.inputs`. The preflight then lets that mutable module parse mutable worktree pins at lines 2201-2218. `prepare` repeats the same defect for the issue-worktree module at lines 2980-2988. Its prior target hash check occurs inside `seed`; after `seed` returns there is an unguarded interval before `exec_module` reopens the path.

Impact: a dirty or concurrently replaced materializer can execute arbitrary Python and can synthesize the archive size/digest contract used by the purported pre-election authentication. A dirty `mipstarre-upstream.json` or `lake-packages.json` can likewise redefine the accepted archive digests. `warm` can therefore accept a hit or elect a builder without authenticating the inputs against the commit-bound cache identity, contrary to `protocols/local-development.md:39` and `protocols/CHANGELOG.md:8`. The detached builder may reject the bad input later, but that does not repair the pre-election gate; in `prepare`, the unbound module can also fake materialization and verification.

Smallest fix: authenticate every live identity input against `self.identity.inputs` before it influences preflight, and execute/parse the exact authenticated bytes rather than hashing a path and reopening it. Use a bounded no-follow read (or the immutable Git blob), compile the captured module payload, and add byte-oriented pin loading or an equivalently bound snapshot for both JSON pins and manifest inputs. Apply the same mechanism to the target module/pin used by `prepare`. Add regressions that dirty or substitute each module and pin between target admission and loading and prove failure before hit/lock/seed/materialization.

### Major - F051-A03-002: authored QPBT can change during verification and still produce `prepared`

Location: `scripts/hot_main_cache.py:2993`

Evidence: `prepare` compares the authored inventory immediately after `materialize` at lines 2993-2995, then calls `verify_materialized` at line 2996 and returns the pre-verification `authored_after` value at line 3004. The authenticated verifier scans authored QPBT first (`scripts/materialize_mipstarre.py:565`) and then scans the foundation, leaving a real interval in which QPBT can change after its verifier snapshot. The new tests cover drift caused by `materialize` and explicitly require that verification not run (`tests/test_hot_main_cache.py:1666`), but do not cover drift caused during verification.

Impact: the command can report a verified, build-ready worktree while its authored QPBT bytes differ from the inventory captured before preparation. This violates the acceptance gate requiring no authored-source drift and leaves the returned `authored_qpbt` evidence stale.

Smallest fix: scan authored QPBT again after `verify_materialized`, compare that final inventory with `authored_before` and with the verifier's authored fields, and return only the final value. Add a verifier-side mutation regression and require failure with no `prepared` result.

### Major - F051-A03-003: `prepare` releases the target lock before its materialize/verify phases

Location: `scripts/hot_main_cache.py:2978`

Evidence: `prepare` delegates to `seed` at line 2978. `seed` holds the path-derived target lock only across lines 2897-2959, so it is released on return. Module loading, foundation materialization, authored checks, and foundation verification at lines 2979-2996 run outside that target lock, with no final `_eligible_seed_target` or deep seeded-destination check. Two cache managers can have identical identity-input hashes but different main commits/cache artifacts. A concurrent `seed --replace` can therefore replace `.lake` after the first prepare's seed and before its return; the first command will still return seed evidence for its own cache even though the target contains the other cache. A later-phase failure also occurs after `seed` has discarded its replacement backup, so `prepare` has no operation-wide rollback boundary.

Impact: `prepared` is not an atomic statement about the target worktree. Cooperative cache operations can interleave and make its cache evidence false, and the combined command's failure cleanup does not preserve a pre-existing `.lake` across later foundation failure.

Smallest fix: use one per-target operation lock across target admission, seed publication, authenticated module/pin loading, materialization, final authored/foundation verification, and a final deep `.lake`/target identity check. Refactor `seed` so `prepare` can reuse the already-held lock without self-deadlocking. If `prepare --replace` is intended to be transactional as documented, defer disposal of the old `.lake` backup until the whole operation succeeds and restore it on later failure. Add an interleaving test with two distinct cache identities and a post-seed failure rollback test.

## Verdict

`request_changes`

The blocker defeats the defining authenticated-input gate, and the two major findings allow `prepare` to return stale safety evidence. No approval is possible at head `767606694e62aefd105959dbb5a979b041ae0d65`.

## Suspected-area decisions and positive checks

- Package directory/file substitution is not an additional archive-content defect in the authenticated downstream materializer. `scripts/materialize_lake_packages.py:468` binds the archive directory by descriptor, `:678` opens each named archive relative to that descriptor with no-follow semantics and stable-file checks, and `:2213` reauthenticates every archive before publication. Directory/file replacement fails closed unless it supplies the same pinned bytes. The new preflight's strict path claim remains dependent on fixing F051-A03-001; race regressions should accompany that fix.
- Dynamic module identity is a real blocker: F051-A03-001.
- A final authored check after `verify_materialized` is required: F051-A03-002.
- An operation-wide prepare lock is required for an exact atomic result: F051-A03-003.
- Mandatory replacement/preservation is wired correctly at `scripts/hot_main_cache.py:2989`: `replace_existing=True` is not caller-optional. The foundation materializer has its own lock and transaction/rollback, and `prepare` invokes a separate final foundation verification.
- Static call tracing found no Lean or Lake invocation in `prepare`: it performs Git worktree admission, authenticated-input preflight, deep `seed`, and in-process foundation materialization/verification. No compile/build path is called.
- The six-path protocol/changelog delta is in scope, but its claims of authenticated preflight and combined preparation are stronger than the implementation until these findings are fixed.
- The new tests establish basic ordering, mandatory replacement, a final-file symlink rejection, and pre-verification authored drift. They do not exercise mutable module/pin identity, verifier-phase drift, or prepare/seed interleaving, which correspond directly to the findings above.

## Authentication

- Manifest: 1/1 SHA-256 match, `40ebd81772e58a7eeaba9e5ec4bcccde15f0c5c247292d10a87e4a5798118510`.
- Manifest Git entries: 19/19 locator-to-blob matches, 19/19 blob-type checks, and 19/19 file SHA-256 matches (12 candidate entries and 7 canonical-checkpoint entries).
- Candidate base: commit `e8b790a32c230aaf0f17ca2aa389ef41f94867f3`, tree `c60de65a6db6e86080bcb8cca73949d2876bd090`.
- Candidate head: commit `767606694e62aefd105959dbb5a979b041ae0d65`, tree `f504453fa9da540e5a3953e4c1710c9c1e48760f`, sole parent equal to the base, and exactly 1 commit in `base..head`.
- Changed set: exactly 6/6 declared paths, all mode `100644`; statuses are five modified files and one added report. `git diff --check` emitted no diagnostics.
- Binary patch: 1/1 SHA-256 match using `git diff --binary BASE HEAD`, `c083e3a1389cf63dd39f19027f25ae7fd00ef43317e8b62f4d065b1827d5cada`.
- Canonical checkpoint: commit `be262a3c15d4be138028e56cfbe17d32211c5b1b`, tree `9856c15cbc0ad84649bc86372b378560831bcd8d`.
- Review independence: authenticated session records identify the candidate writer/orchestrator and binder/integrator as separate archived writable sessions; this session made no repository or Git writes.

## Accounting

- First recorded UTC timestamp (immediately after the required manifest hash and manifest enumeration): `2026-09-02T23:27:23Z`.
- Evidence cutoff: `2026-09-02T23:34:34Z`; recorded review interval: `431s`. The initial hash preceded the first timestamp, so no unexposed sub-second duration is estimated.
- Findings: 1 blocker, 2 major, 0 minor.
- Tool counters for the completed review including the final out-of-band digest read: 51 read-only `exec_command` invocations, 1 `apply_patch` write to this `/tmp` report, 0 repository writes, 0 `view_image`, 0 web calls, 0 collaboration calls, and 0 nested agents.
- Prohibited-action counters: Python tests 0; Python compile 0; Lean 0; Lake 0; compile/build 0; cache actions 0; materialization actions 0; network 0; endpoint 0; GitHub 0; credentials 0; nested-agent actions 0.
- Token usage: `null`; no per-session token count is exposed, so none is estimated.
- Validation evidence was authenticated from the manifest objects but not rerun, as required by the review constraints.

The report SHA-256 is returned out of band because the report cannot contain its own digest.
