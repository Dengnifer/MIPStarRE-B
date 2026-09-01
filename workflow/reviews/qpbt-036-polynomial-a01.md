# QPBT-036 polynomial implementation report

## Findings

No implementation blockers found. The candidate implements the reviewed F02
surface in exactly `MIPStarRE/QPBT/Basic/Polynomial.lean`; no `sorry`, `admit`,
`axiom`, or `constant` occurs in the owned file. The inherited singleton hot
cache could not be seeded for this detached base because the cache runner's
foundation-input environment was not propagated to its staging invocation;
the failure was retained by the cache failure envelope. A private copy-on-write
build tree was used for validation instead, so no writable build directory was
shared.

## Source and contract

- Contract: `workflow/reviews/qpbt-035-q014-contract-a02.md`, F02 signatures.
- Paper anchor: `references/2001.04383v3/sections/dependencies/low-degree-code.tex:1-94`.
- Direct imports are exactly `Mathlib.RingTheory.MvPolynomial.Basic` and
  `MIPStarRE.QPBT.Basic.Field`.
- Boolean coordinate indices (`Fin m -> ZMod 2`) and field evaluation points
  (`Fin m -> GaloisField 2 k`) remain distinct.

## Candidate identity

- Base: `358cd108db045d13f4e0095a2948dd4037be2b54`.
- Commit: `8467454fefefdbac7478a2df8f8c1e2d9c25fcf5`.
- Tree: `50fec3a3a7611f63aacff2f15568812e123ca29d`.
- Owned-file SHA-256: `cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c`.
- Manifest: one path, `MIPStarRE/QPBT/Basic/Polynomial.lean`.

## Validation

- `lake env lean MIPStarRE/QPBT/Basic/Polynomial.lean`: passed.
- `lake build MIPStarRE.QPBT.Basic.Polynomial`: passed (2358 targets).
- `lake build`: passed (existing project snapshot; 8992-target build reached
  the completed state after cache reuse).
- Owned-scope debt scan and import scan: passed.
- `blueprint/check.py --check`: passed (`54 nodes, 12 chapters`).
- `scripts/reference_source.py verify`: unavailable in this detached worktree
  because the materialized `references/2001.04383v3/sections/` tree is absent;
  the pinned paper section was inspected from the coordinator worktree.
- `python3 -m compileall -q scripts tests`: not run after the reference-source
  precondition failure; no Python files were changed.
- `git diff --check`: passed.

## Implementation notes

`indicatorPolynomial` uses the paper product of `X i` and `1 - X i`. Its
individual-degree proof uses `degrees_prod_le`, `degrees_sub_le`, and the
multiset count bound. Boolean evaluation is proved by a local two-element
case split for `ZMod 2`; interpolation is a linear map formed by the finite
indicator sum, with Boolean evaluation and injectivity proved directly.

## Metrics

- Session elapsed: approximately 42 minutes wall time (06:02-06:44 UTC),
  including dependency/cache setup and validation.
- Exposed token usage: `null` (collaboration backend did not expose it).
- Subagents: 0 nested; topology `root -> i036-polynomial-a01`.
- Compile attempts: scoped Lean 3 (one missing-olean setup, one successful),
  target build 1, full build 1.
- Cache: singleton warm attempts recorded misses/failures; lock election was
  acquired without duplicate compilation. Private build copied with reflink
  fallback as needed.
- Network/GitHub/credentials: none used.
