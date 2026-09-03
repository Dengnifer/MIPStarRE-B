# QPBT-053 refactor investigation (attempt A01)

Status: **blocked by the repository provenance boundary; no implementation
candidate was produced.**

Investigation timestamp (UTC): 2026-09-03T11:11:39Z
Issue: `QPBT-053`
Worktree: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-053-refactor-a01`
Branch: `issue/qpbt-053-refactor-a01`
Immutable base: `6b43c72ab382fa53ee7cfd259a56ec2fbe41b623`

## Requested source move

The reusable theorem is currently the public
`MIPStarRE.LDT.qBipartiteConsDefect_of_measurements` in
`MIPStarRE/LDT/Test/StrategyRole/Algebra.lean:96-124`.  The QPBT file has a
private duplicate, `qBipartiteConsDefect_measurements_eq_sub`, at
`MIPStarRE/QPBT/Basic/Approximation.lean:842-884`, used again at line 899.
`MIPStarRE/LDT/Preliminaries/ComparisonCore.lean` is the lowest existing
preliminary module that already imports the required definitions
(`Preliminaries.Defs` and `Basic.MeasurementLift`) and is a plausible home for
the generic theorem.

The import graph also exposes a contract issue: `StrategyRole/Algebra.lean`
currently imports only `StrategyRole/Core.lean`, while downstream strategy
modules obtain the theorem through `StrategyFailures.lean` importing Algebra.
After relocation, Algebra would need an import of ComparisonCore (or every
downstream consumer would need an out-of-scope import edit).  This is a
required dependency edge, not a proof or statement change, but it conflicts
with a literal reading of the acceptance gate “do not broaden imports.”

## Read-only checks

The worktree was clean at the exact base above.  The authenticated foundation
was materialized locally, but both requested LDT files are ignored upstream
bytes:

```
git check-ignore -v MIPStarRE/LDT/Test/StrategyRole/Algebra.lean
  .gitignore:11:MIPStarRE/*
git check-ignore -v MIPStarRE/LDT/Preliminaries/ComparisonCore.lean
  .gitignore:11:MIPStarRE/*
git ls-files --error-unmatch MIPStarRE/LDT/Test/StrategyRole/Algebra.lean
  error: pathspec ... did not match any file(s) known to git
```

The materialized bytes were read-only verified for provenance during worktree
setup.  Their observed SHA-256 values were:

| path | SHA-256 |
| --- | --- |
| `MIPStarRE/LDT/Test/StrategyRole/Algebra.lean` | `5fe15afd083491059eb7b4fdaab8143ee1a9afcd97394d646f839cf9489de34b` |
| `MIPStarRE/LDT/Preliminaries/ComparisonCore.lean` | `f148d77e457645b12139b638ba783a13f0e45943f231a4cc4dd348972f4cab9b` |
| `MIPStarRE/QPBT/Basic/Approximation.lean` | `c430c02e7168710134e2eeb1a3f70d2720aafa9fd9e3d46835437a9f19bd404d` |

No source edit, Lean invocation, build, or Git commit was performed.  Force-
adding either LDT file would record unlicensed upstream source in the project,
contradicting the established QPBT-004 provenance policy and `AGENTS.md`,
which permits tracking only project-authored `MIPStarRE/QPBT/**` paths.

## Rights-compliant redesign recommendation

1. Keep QPBT-053 blocked and open a dependency issue to establish a tracked
   extension boundary.  The issue should explicitly choose one of:
   - obtain redistribution rights and permit a narrowly patched upstream LDT
     subtree; or
   - add an authenticated, versioned overlay/patch mechanism applied by the
     materializer, with the patch manifest and generated evidence tracked; or
   - upstream the generic theorem and pin a foundation revision that contains
     it.
2. Once that boundary is approved, perform the intended move in one changed
   head, add the necessary Algebra-to-ComparisonCore import edge (or document
   why a consumer import is preferred), and re-run the normal scoped/full
   Lean and declaration-synchronization gates.
3. Until then, do not force-add ignored LDT files and do not claim the private
   QPBT duplicate has been replaced.  A tracked QPBT-only adapter would be
   rights-compliant but would not satisfy the stated requirement to relocate
   the theorem into the existing LDT preliminary layer.

## Acceptance verdict

**Not accepted / blocked:** the requested file move cannot be committed under
the current ownership and provenance rules.  No candidate SHA exists.
