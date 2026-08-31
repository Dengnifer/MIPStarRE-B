# LPR-015 / QPBT-025 immutable security review (A04)

## Verdict

`approve`

No blocker, high, medium, or low findings. No finding dispositions are
required.

## Review identity and immutable target

- Logical session: `i025-reviewer-a04-pr015-immutable`.
- Role: fresh independent read-only reviewer; not the implementer or
  orchestrator; subagents `0`.
- Review worktree:
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-025-sidecar-a01`.
- Base: `45d2fe657af587e8e10952aced2e156d349fd65e`.
- Head: `d73cce44d5f9f37d38ee8d916811719408818c03`.
- Head tree: `8a8985252eb019282ab6ef1842ce1b9178a58c07`.
- Sole parent: `45d2fe657af587e8e10952aced2e156d349fd65e`.
- Commits in `base..head`: `1`.
- Branch: `issue/qpbt-025-sidecar-a01`; final status was clean.
- File modes did not change.
- Exact changed paths, and no others:

```text
scripts/hot_main_cache.py
scripts/materialize_lake_packages.py
tests/test_hot_main_cache.py
tests/test_lake_package_materialization.py
```

The target identity, parent, tree, cleanliness, and path set matched the
review request both before inspection and after all validation.

## Sources reviewed

`AGENTS.md` was read completely before review. I then read the complete frozen
source chain:

```text
workflow/reviews/qpbt-024-postintegration-warm-failure-9b6.md
workflow/reviews/qpbt-024-proofwidgets-sidecar-a11.md
workflow/reviews/qpbt-024-sidecar-security-a12.md
workflow/reviews/qpbt-024-sidecar-synthesis-a14.md
workflow/reviews/qpbt-024-sidecar-hooks-a15.md
workflow/reviews/qpbt-024-sidecar-tests-a16.md
workflow/reviews/qpbt-024-repair-topology-a17.md
```

I also inspected root-canonical QPBT-025 and LPR-015 state, the complete
base-to-head diff, surrounding materializer binding/tree code, both hot-cache
verifier call sites, publication/failure handling, deep readiness and seed
validation, and the assertion bodies of the new tests.

## Security and behavioral review

The deletion authority is internal, immutable, and exact at
`scripts/materialize_lake_packages.py:44-66`: package `proofwidgets`, revision
`6e311e2a844da9b2cc3971187df2fe0066947b93`, target
`widget/package-lock.json`, target SHA-256
`3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d`,
sidecar `widget/package-lock.json.hash`, and exact 16 bytes
`179e66574f04806e`. There is no suffix rule, glob, caller-supplied path,
package, digest, or payload.

Archive inspection at `scripts/materialize_lake_packages.py:827-846` requires
the exact target to be an authenticated regular archive member with the exact
digest and requires the sidecar path to be absent. It runs before archive
facts are accepted at `scripts/materialize_lake_packages.py:964`. All unrelated
`.hash` entries remain ordinary archive/source members.

Bare `verify` remains read-only with respect to package trees. Only the Boolean
`--remove-validated-generated-sidecars` flag activates removal for the single
compiled-in exact contract (`scripts/materialize_lake_packages.py:1569-1598`,
`:2471-2499`). A present sidecar under bare verify remains on disk and fails
the ordinary exact tree comparison.

The mutating path binds the package, fixed parent, target, and sidecar through
descriptor-relative no-follow/nonblocking opens. It requires regular,
singly-linked target and sidecar objects; exact target digest; exact sidecar
size and bytes; and no execute, setuid, setgid, or sticky bits. It compares
descriptor/name identity including mode, size, timestamps, and link count
immediately before `os.unlink(..., dir_fd=...)`, fsyncs the bound parent,
requires name absence, and rechecks target, parents, package, layout, and
sidecar absence (`scripts/materialize_lake_packages.py:1325-1598`). Malformed,
special, linked, mode-drifted, substituted, or reappearing objects fail before
or after the exact mutation and are never normalized into a successful result.

The package descriptor remains open while the source is exposed as
`/proc/self/fd/<fd>`. `_run_git` passes referenced descriptors into Git, so the
source tree computations remain attached to the selected package incarnation.
Both original unprojected source authorities remain: archive tree with no
Gitlinks and reconstructed Git tree with pinned Gitlinks
(`scripts/materialize_lake_packages.py:2287-2315`). The only pre-existing
projection remains the separately validated exact `.lake/build` boundary.

I explicitly reviewed the context-manager exceptional exit. The normal
post-`yield` recheck at `scripts/materialize_lake_packages.py:1598` is skipped
when `_scan_tree` or a Git operation raises. This is not a finding: the
exception propagates and verification cannot succeed; each successful Git
tree computation is separately followed by `prepared.assert_current()` before
its comparison at `scripts/materialize_lake_packages.py:2302` and `:2312`; and
the exact unlink already performs its own pre/post rechecks at `:1545-1562`.
The hot-cache verifier error exits before publication
(`scripts/hot_main_cache.py:2147-2154`), while READY is only created later at
`:2205-2215`. An exceptional-exit assertion could improve diagnostic
attribution, but cannot broaden deletion or permit READY.

The canonical recipe changes only from version 4 to exactly 5 and appends the
non-parameterized flag to the existing verifier argv
(`scripts/hot_main_cache.py:205-225`). Recipe schema remains 3 and serialized
field shape/order is unchanged. The same exact flagged command is invoked
pre-build and post-build at `scripts/hot_main_cache.py:2121-2127` and
`:2147-2154`. Main SHA, changed materializer blob, exact argv, and version all
bind cache identity (`scripts/hot_main_cache.py:1377-1417`), so the key churns.

Final verification/removal precedes whole-`.lake` inventory and READY. Thus a
successful snapshot and deep-verified seed omit only the exact sidecar while
retaining package-local `.lake/build`; invalid/malformed sidecar or other
source drift takes the retained failure path and cannot publish READY. Deep
readiness and destination inventory checks cover later sidecar injection
(`scripts/hot_main_cache.py:1794-1838`, `:2180-2215`, `:2320-2333`).

The focused tests use real descriptors/filesystem objects for absent/exact
cleanup, bare purity, fsync, malformed bytes, symlink/directory/FIFO/socket,
hardlinks, unsafe modes, target and parent substitution, sidecar reappearance,
wrong revision/package, unrelated and archive-owned hashes, source drift,
both tree authorities, and `.lake/build`. Hot-cache tests assert exact call
order, exact version/schema/argv, snapshot and seed absence, retained build
output, deep-inventory rejection after injection, cache-key churn, failure
envelopes, and no READY. Assertions inspect positive and negative filesystem
state rather than only matching helper names or diagnostics.

## Validation

Prescribed validation ran in the requested order. There were 6 primary
validation command invocations and 10 final immutable identity/path probes;
all returned exit status 0.

| Command | Result | Duration |
|---|---:|---:|
| `/usr/bin/time -f 'ELAPSED=%e' python3 -m unittest discover -s tests -p test_lake_package_materialization.py -v` | 34/34 passed | 153.33 s |
| `/usr/bin/time -f 'ELAPSED=%e' python3 -m unittest discover -s tests -p test_hot_main_cache.py -v` | 46/46 passed | 11.24 s |
| `/usr/bin/time -f 'ELAPSED=%e' python3 scripts/check_workflow.py` | 312/312 passed; aggregate serial coverage | 177.65 s |
| `/usr/bin/time -f 'ELAPSED=%e' python3 -m compileall -q scripts tests` | passed | 0.03 s |
| `/usr/bin/time -f 'ELAPSED=%e' python3 scripts/workflow.py validate` | valid; 26 issues, 14 PRs, 296 issued sessions, 7 stages | 0.10 s |
| `/usr/bin/time -f 'ELAPSED=%e' git diff --check 45d2fe657af587e8e10952aced2e156d349fd65e..d73cce44d5f9f37d38ee8d916811719408818c03` | passed, no output | 0.00 s |

Final probes confirmed exact HEAD, tree, sole parent, one-commit range, clean
branch, exact changed paths, no mode summary, no worktree diff for the four
paths, and distinct base/head blobs for both implementation scripts. The 10
probes completed in approximately 0.5 seconds of combined tool wall time.

Across the review I issued 78 `exec_command` invocations: 61 static
evidence/inspection commands, the 6 primary validation commands, the 10 final
identity probes, and 1 final report-digest command. One static inspection
invocation contained two read-only `jq` command segments. Long-running test
processes were only polled, not reissued.

## Residual risk and accounting

The real authenticated recipe-v5 warm was deliberately not executed. No real
Lake or Lean command, cache warm, cache seed, build, or network operation ran.
The final integration gate must still run exactly one authenticated new-key
warm and verify status, READY/manifest binding, and deep inventory. The
materializer suite uses synthetic package archives; the exact production
authority is frozen by constants, the production pin regression, and the
authenticated A11/A12 provenance, but this review did not reopen or execute
the real ProofWidgets archive.

Descriptor and incarnation checks do not defeat an actively racing same-UID
process that has equal authority over private staging. This is the explicitly
documented residual trust boundary; observed substitutions fail closed, and a
successful path rechecks after both tree computations.

- Start: `2026-09-01T03:25:51+08:00`.
- Evidence cutoff/end: `2026-09-01T03:42:48+08:00`.
- Elapsed: `1017` seconds, derived from second-resolution recorded timestamps.
- Token usage: JSON `null`.
- Token availability reason: the collaboration backend does not expose
  per-agent token usage; no estimate was made.
- Subagents: `0`; topology: root coordinator -> one fresh independent
  read-only reviewer.
- Manual/repository/canonical-state/metrics edits: `0`.
- Review-target Git writes/object creation: `0`; GitHub writes: `0`.
- Warm: `0`; seed: `0`; Lean: `0`; Lake: `0`; builds: `0`; network: `0`;
  shared cache/runtime mutations: `0`.
- The prescribed Python tests and compile check used disposable/ignored
  interpreter and test fixtures only; the final target branch remained clean.
- Deliberate authored artifact: `/tmp/qpbt-025-review-a04-pr015.md` only.

The report SHA-256 is supplied out of band because embedding it here would
change the digest.
