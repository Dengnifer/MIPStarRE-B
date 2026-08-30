# Stage 3 Blueprint and Lean Reconnaissance

- Sessions: `i003-scout-a01-blueprint-recon`, `i003-scout-a02-lean-reuse`
- Issue: `QPBT-003`
- Backend: Codex collaboration, read-only
- Workspace edits: none

The source scout mapped Section 7.3 and Appendix A into a public QPBT surface,
an explicit proof dependency graph, 19 proposed blueprint chapters, and named
internal error terms. The Lean scout audited the upstream project at Lean and
Mathlib 4.32.0, identified reusable field, measurement, state-distance,
Naimark, orthonormalization, and LDT APIs, and proposed minimal and full QPBT
file trees under `MIPStarRE/QPBT/`.

The reconnaissance identified three additional statement-integrity boundaries:

1. the paper says `ind_m(u) = 0` iff `u = 0`, although the indicator vector is
   never zero;
2. the claimed cross-basis commutation for arbitrary vectors is false without
   the generalized Pauli phase;
3. Appendix A invokes classical LDT in dimension `2m+2`, while its earlier CL
   encoding assumes the dimension divides `q`, which QPBT admissibility does
   not provide.

These are inputs to `QPBT-009`, not silent extra hypotheses. The recommended
formalization boundary uses finite coordinate Hilbert spaces, explicit
POVM/PVM postprocessing, heterogeneous questions via dependent sums, and a
public soundness theorem with no bridge or extraction assumptions.

Exact elapsed times and token usage were not exposed by the collaboration
backend; the canonical sessions record the coordinator-observed time window.
