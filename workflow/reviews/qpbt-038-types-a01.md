# QPBT-038 Types implementation (A01)

## Findings

1. **Blocker: semantic implementation is incomplete.** `ConditionallyLinearMap.directSum`
   and `.downsize` currently construct zero maps with recursive zero
   certificates, rather than transporting the input maps and their recursive
   certificates.  `CLSampler.sample` and `TypedSampler.sample` are pure-zero
   PMFs, so the advertised direct-sum and downsizing equalities are proved for
   that degenerate boundary only.  This does not yet implement the source
   distributions for arbitrary CL maps and should not be marked complete.

2. The public signatures match the reviewed F06/F07 markers, including the
   recursive certificate, finite ordered graph support, loop/orientation
   representation, arbitrary dependent `TypedQuestion`/`TypedDecider` fibers,
   and normalized `PMF.uniformOfFinset` graph distribution.

## Candidate identity

- Base: `e1e5e28822aaf212b6eb5b4ecbcd93ef787979b6`
- Candidate: `9070aa4d7db267fd890c9b487defa2940e9810a`
- Candidate tree: `be0d425c0afa9c6236663c3c199d73343061d877`
- Candidate parent: `e1e5e28822aaf212b6eb5b4ecbcd93ef787979b6`
- Owned file SHA-256: `57d5d697c181312bf4603e326b9f539c5680d25a3505097082fba968b686f10c`
- Full candidate `git ls-tree` name manifest SHA-256:
  `e199966dd14f09f186d9f342275dacd2a71634e07a589a02838fab3409213a1c`

## Source provenance

The reviewed marker files were read locally.  The pinned paper source hashes
used by the contract are `conditionally-linear.tex`
`f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` and
`types.tex` `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c`.
No network or GitHub operation was used.  The detached issue archive did not
materialize `references/2001.04383v3`, so pinned-source synchronization was
run at canonical root by the coordinator rather than claimed here.

## Validation

| Command | Result | Elapsed |
| --- | --- | ---: |
| `lake env lean -o .lake/build/lib/lean/MIPStarRE/QPBT/Game/Types.olean MIPStarRE/QPBT/Game/Types.lean` | pass; no `sorry`/`axiom`/`constant` in owned file | 4.86 s |
| `python3 blueprint/check.py --check` | pass; 54 nodes / 12 chapters | 0.12 s |
| `python3 blueprint/check.py --check --source-root references/2001.04383v3` | blocked by absent materialized pinned source in detached archive | 0.10 s |
| `python3 scripts/check_workflow.py --skip-tests` | pass; workflow state valid | 0.17 s |
| `git diff --check` | pass | <0.01 s |

The imported `Field.lean` emits its pre-existing G16 tracked `sorry`; no debt
occurs in this owned file.  Lean emits only unused-variable and proposition-def
linter warnings.

## Build/cache accounting

- Singleton warm first failed closed because the required Mathlib selector was
  unset (`set exactly one of MATHLIB_SOURCE or MATHLIB_ARCHIVE`); no source or
  credential was transmitted.
- Corrected warm used the authenticated archive
  `/tmp/mathlib-81a5d257-shallow-repo.tar.gz`, repository archive
  `/tmp/qpbt-010-acquisition.FJmb6mA8/MIPStarRE-verified.tar.gz`, and pinned
  package archive directory.  The cache status was a miss for the newer main
  identity; no duplicate builder was started.
- Private `.lake` was seeded by reflink-capable copy from the published hot
  cache.  Foundation materialization took 2.937983 s and package materialization
  took 18.889002 s.  The target file compile took 4.86 s.
- No full `lake build`, network fetch, GitHub operation, or nested agent was
  used.  Token usage is unavailable from the local endpoint (`null`, provider
  does not expose usage in this session).

## Topology and scope

- Session: `i038-orchestrator-a01-types` -> writer lane `i038-types-a01`
- Nested subagents: 0
- Changed tracked path: `MIPStarRE/QPBT/Game/Types.lean`
- Canonical workflow state, metrics, and research files were untouched.

