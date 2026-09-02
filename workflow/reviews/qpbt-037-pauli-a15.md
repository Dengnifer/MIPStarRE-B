# QPBT-037 Pauli implementation (A15)

Session: `i037-orchestrator-a15-pauli`  
External identity: `/root/i037_orchestrator_a15_pauli`  
Issue: `QPBT-037`

## Candidate

- Commit: `cdb83f4017cfc182eb2611be0fbc5cd3635fbf64`
- Tree: `239f65b911d5535bdd20bb442c6e9c61aa00f8ff`
- Sole parent: `c5f4b277c17c54f2bfff3eb02c1101d4f1e85b60`
- Changed path: `MIPStarRE/QPBT/Basic/Pauli.lean` only
- File SHA-256:
  `df003a117fb8495bd01bd7ceee45b7c58df5c9e4815bfb4e5a9e344da6b56e12`
- Diff: one new file, 857 insertions; candidate worktree clean

## Mathematical result

The candidate implements every frozen F05 declaration using concrete
characteristic-two field matrices. It includes scalar X shifts and Z trace
phases, Fourier/computational rank-one measurements, multiplication and square
laws, twisted commutation, spectral expansion and Fourier inversion, the
finite-field vector dot product, and the corresponding product-basis tensor
operators and projectors.

The source mapping is to
`references/2001.04383v3/sections/dependencies/pauli.tex:1-110`, including
`eq:twisted-fq`, `eq:pauli-obs-proj-single`,
`eq:pauli-inversion-0-single`, `eq:pauli-obs-proj`, and
`eq:pauli-inversion-0`. The product-basis definitions give the paper's tensor
matrices on the canonical function basis; no irrelevant recursive-Kronecker
reindexing theorem is added.

## Acceptance evidence

- `lake env lean MIPStarRE/QPBT/Basic/Pauli.lean`: passed in 7.43 seconds with
  zero diagnostics
- `lake build MIPStarRE.QPBT.Basic.Pauli`: passed in 27.07 seconds; Pauli's own
  build took 8.0 seconds
- `lake build`: passed in 6.24 seconds across 8,992 jobs
- Default and pinned-source blueprint checks: passed, 54 nodes
- Owned-file proof-debt and forbidden-assumption scan: empty
- Exact four-import and G09 phase/order scans: passed
- `git diff --check`: passed

The target build replayed the already tracked G16 `sorry` warning from
`Field.lean`; `Pauli.lean` itself has no `sorry`, `axiom`, `constant`, or public
obligation input. The private hot-main seed remained isolated; this session did
not rebuild or publish main. One read-only tensor scout was used.

## Accounting

- Governed elapsed time: 2397.179 seconds
- Nested agents: 1
- Token usage: `null`; the collaboration backend exposes no per-agent count
- GitHub and network actions: 0

This report records implementation evidence, not approval. The exact candidate
still requires a fresh immutable source-fidelity and Lean API review.
