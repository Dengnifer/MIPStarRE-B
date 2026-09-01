# QPBT-045 / LPR-024 repair A07

## Outcome

The exact A06 ordering defect was independently reproduced and repaired.  The
on-disk authored QPBT inventory now sorts records by complete relative path
before hashing, matching the committed Git inventory for same-stem layouts.
Four identity-isolated complete-warm regressions were added: exact
`Game.lean` plus `Game/Types.lean` acceptance, root substitution rejection,
nested substitution rejection, and exit-zero Git diagnostics rejection.
Every adversarial warm raises `CacheError`, publishes neither a snapshot nor a
`READY`, and the substitution cases preserve their external sentinel.

The descriptor-bound traversal, no-follow and incarnation checks, single-link
identity, five authored verification phases, recipe-v7 identity, replacement
behavior, and existing regressions remain unchanged.  No real cache warm,
seed, build, or publication was attempted.  QPBT-045 and LPR-024 still require
a fresh immutable review and guarded integration before the real warm gate.

## Authority and immutable base

The clean authenticated base was HEAD
`3c3f0c15aef87920d0668cc18d1fd03bc0274b7f`, tree
`af566d43899a77dc328325eb2f08fd8b786198f2`, with sole parent
`bc41314fb74baced6f6a043cbc8956a18a2e0003`.  The worktree was the dedicated
QPBT-045 worktree named in the canonical A07 session packet.  The formal A06
report was read as untrusted evidence; its report SHA-256 is
`d400d0653cd15a987c3ccc4b942d0bce3222b9e95f43f94833134bb18757c7a3`.
Canonical workflow state and research metrics were not edited.

The pre-report implementation scope contained exactly:

| Path | Change |
| --- | --- |
| `scripts/hot_main_cache.py` | one record-ordering line |
| `tests/test_hot_main_cache.py` | four complete-warm regression tests and one shared helper |

The pre-report textual and binary Git diff SHA-256 was
`448127bf5d4c7fd82e0962e9c06d67adb0e93d1367baa56a128a75b77ff46f98`.
`git diff --check` passed.

## Independent reproduction and repair

A disposable fixture containing exactly `MIPStarRE/QPBT/Game.lean` and
`MIPStarRE/QPBT/Game/Types.lean` reproduced F-LPR024-004 on the authenticated
base.  Both committed and on-disk inventories reported 2 files and 93 bytes,
but the committed digest was
`886a215d6a0fec3e6ae9f1c3e7b8a0f19be1a15da8bda9e50b4ba869eecf2abb` while the
on-disk digest was
`74f6fde5cdefee230ce343544389d503d27947381f178b86b89189f07e4434f9`.
The disposable reproducer source had SHA-256
`cdeba69a02e8d4e3b4d460c95b73e324716f10c414602443595a293201b2737d` and was
kept under `/tmp` only.

The smallest production repair is the path sort immediately before the
on-disk digest loop in `authored_tree_facts_on_disk`.  Rerunning the identical
fixture after the repair gave 2 files, 93 bytes, and the matching digest
`886a215d6a0fec3e6ae9f1c3e7b8a0f19be1a15da8bda9e50b4ba869eecf2abb` on both
sides.

The exact new warm tests use separate temporary repositories and runtimes.
The same-stem case commits both paths, compares committed/on-disk facts before
warming, completes all five authored checks, and asserts deep readiness.  The
root and nested substitution callbacks replace a bound directory with a
symlink to an external directory during descriptor scanning; each asserts the
substitution occurred, the sentinel remains `unchanged`, `CacheError` names
the `before_materialization` boundary, no snapshot exists, no `READY` exists,
and the retained failure tree has no `READY`.  The Git-warning callback injects
exit-zero stderr at the actual porcelain-status boundary and asserts
`CacheError`, no snapshot, and no `READY`.

## Finding dispositions

| Finding | Candidate disposition | Evidence |
| --- | --- | --- |
| `F-LPR024-001` root/intermediate substitution | resolved in candidate; pending fresh review | Existing descriptor-bound traversal plus the two new full-warm tests; both reject and preserve external sentinels. |
| `F-LPR024-002` hard-linked authored file | remains resolved; regression retained | Existing single-link checks and full-warm hard-link test remain green. |
| `F-LPR024-003` scan failure/Git diagnostics | resolved in candidate; pending fresh review | Existing unreadable-subtree test plus the new full-warm exit-zero-warning test; both publication paths remain fail-closed. |
| `F-LPR024-004` same-stem inventory order | resolved in candidate; pending fresh review | Base mismatch reproduced; sorted on-disk records now equal committed facts and the exact full-warm same-stem test passes. |

This is a repair candidate, not an approval.  Root must authenticate the new
immutable head and request a fresh independent mathematical/security review;
only that review can resolve the four formal dispositions and permit guarded
integration.

## Validation

| Gate or probe | Result | Timing |
| --- | --- | ---: |
| Base same-stem reproducer | mismatch reproduced; post-repair equality confirmed | 0.15 s each |
| Four new complete-warm tests | 4/4 passed | 0.51 s |
| Existing adversarial/ordinary repair set | 8/8 passed | 1.06 s |
| `python3 tests/test_hot_main_cache.py` | 60/60 passed | 12.58 s real |
| `python3 tests/test_mipstarre_materialization.py` | 11/11 passed | 0.57 s real |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | 358/358 passed; exactly one aggregate attempt | 183.35 s real |
| `python3 -m compileall -q scripts tests` | passed; bytecode redirected to `/tmp` | 0.36 s |
| `python3 scripts/workflow.py validate --json` | valid; 48 issues, 23 PRs, 0 planned, 392 issued, 7 stages | 0.13 s |
| `python3 scripts/check_workflow.py --skip-tests` | workflow state valid | 0.38 s |
| `python3 tests/test_check_workflow.py` | 3/3 passed | 0.31 s |
| `git diff --check` (working tree) | passed | 0.00 s |
| `git diff --check f4b00c7616b8710220a4f8480cfb23412914d151` | passed | 0.00 s |

The aggregate emitted expected argparse diagnostics from negative-path tests
and ended with `OK`; no retry was made.  No Lean/Lake/build/cache publication,
network, endpoint, GitHub, credential, or nested-agent action occurred.

## Metrics and accounting

- Canonical session: `i045-orchestrator-a07-pr024-review-repair`.
- External logical session: `/root/i023_orchestrator_a01_leaf_contract/i023_simplifier_a05_readme_sync#logical:i045-orchestrator-a07-pr024-review-repair`.
- Canonical start: `2026-09-01T17:44:40.294977Z`.
- Pre-report evidence cut: `2026-09-01T17:56:16.319018Z`; measured elapsed
  `696.024041` s from the recorded start.
- Token usage: JSON `null`; the collaboration backend exposes no per-agent
  token usage, so no estimate was made.
- Topology: root coordinator -> one writable A07 repair session; nested
  agents: 0.
- Independent reproduction attempts: 2 (base mismatch and repaired equality).
- Focused test attempts: 3 (new four-test set, eight-test neighboring set,
  final 60-test suite), all passed.
- Materializer suite attempts: 1, passed 11/11.
- Aggregate attempts: exactly 1, passed 358/358; retries 0.
- Workflow/checker/test-checker attempts: 3, all passed.
- Compileall attempts: 1, passed.
- Production warm/seed/build/publication, Lean/Lake, network/endpoint/GitHub,
  credentials, nested sessions, canonical state, and research metrics: 0.
- Repository content paths edited: exactly the two implementation/test paths
  above plus this report; no protocol file was changed because the existing
  v7 protocol already describes the repaired behavior.

Final commit/tree/parent, exact path manifest, report digest, and post-commit
identity are returned outside this self-referential report.
