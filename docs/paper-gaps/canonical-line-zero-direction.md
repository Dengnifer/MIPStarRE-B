# Canonical line zero direction and field-bit order

Tracking: `G22`, `G23`, and `QPBT-074`.

## Authenticated source boundary

The pinned arXiv:2001.04383v3 classical-LDT section defines affine lines for
all directions at split lines `92-102`, but defines the canonical projector at
`129-160` through the canonical complement of the singleton set `{v}`. The
underlying construction in `top-level/preliminaries.tex:306-383` requires its
input set to be linearly independent. Consequently it does not define the
projector for `v=0`. The line/point decider at `classical-ldt.tex:324-370` also
asks for the parameter on such a singleton line without selecting one.

The same section defines `chi` by interpreting a field element as an integer
at lines `194-207`. The field representation discussion at
`finite-fields.tex:250-263` fixes basis coordinates but does not say which
coordinate is the most significant bit.

## G22 disposition

For `v != 0`, `canonicalLineProjection` is exactly the one-row reduced-echelon
projector: if `p` is the least coordinate with `v p != 0`, its value at `u` is
`u - (u p / v p) • v`. At `v=0` only, it is the identity. The singleton line
through `u` has canonical representation `(u,0)`, and an incident point is
evaluated at the distinguished parameter zero. Incidence is still checked, so
a different point rejects.

This totalization does not add a nonzero premise, resample or condition away
the zero event, accept a caller-supplied line map or parameter, or assert that
the literal source defined the missing case.

## G23 disposition

`fieldElementIndex D s` is the little-endian integer

```text
sum_i bit(D.coordinates s i) * 2^i
```

with coordinate zero least significant. The future Lean implementation must
prove this is an equivalence with `Fin (2^k)`. The callable theorem
`fieldElementIndex_testBit` states, for every `i : Fin k`, that bit `i` of the
index is exactly `decide (D.coordinates s i = 1)`. This fixes the same
least-coordinate-first order used by the project field-vector codec. Then
`chi` is zero-based integer division by `2^k/m`. Its fibers have the paper's
required cardinality, so the selector is uniform; no opaque
`Fintype.equivFin` choice is permitted.

## Layering effect

`F09A-LDT-GAME-CORE` owns canonical lines, `chi`, truncation, the three concrete
CL maps, bounded answers, and the repetition-one typed decider in
`MIPStarRE.QPBT.Game.ClassicalLDT`. `F09-LDT-GAME` remains downstream in
`MIPStarRE.QPBT.Analysis.ClassicalLDTAdapter` for measurement and
general-repetition adapters. `G02-GAME` directly depends on F09A, so the Game
verifier never imports the Analysis adapter.
