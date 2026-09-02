# QPBT-037 tensor proof scout (A16)

Session: `i037-prover-a16-tensor`  
External identity: `/root/i037_orchestrator_a15_pauli/i037_prover_a16_tensor`  
Mode: bounded read-only proof search

## Result

The remaining F05 tensor layer is constructively provable with the concrete
product computational basis already selected by the parent implementation.
The scout validated vector trace-character nondegeneracy, the uniform
character expectation, direct product-basis tensor operators, genuine
rank-one projectors, projector positivity and completeness, twisted
commutation, spectral expansion, Fourier inversion, function extensionality,
and the nonzero-coordinate witness used by character cancellation.

This matches the multi-register equations in
`references/2001.04383v3/sections/dependencies/pauli.tex:90-110`. An additional
equality to recursively associated `Matrix.kronecker` terms would require
explicit reindexing equivalences, but F05 and its consumers only require the
same concrete product-basis matrices. No extra public assumption or helper
contract is needed.

## Validation and accounting

- Temporary proof fragments: elaborated through `lake env lean /dev/stdin`
- Parent proof harness: `lake env lean /tmp/qpbt037_scalar.lean`, exit 0 in
  6.86 seconds (`user` 14.43 seconds, `sys` 2.23 seconds)
- Harness SHA-256:
  `3e3bd4d572c4fbe0ca01f019765d5c862de3a0f97da953b1ad04f0a4606a3591`
- Final diagnostics: none; the parent removed all three preliminary unused-simp
  warnings before accepting the scout result
- Repository edits, Git writes, builds, cache operations, network actions, and
  nested agents: 0
- Elapsed governed session time: 1055.463 seconds
- Token usage: `null`; the collaboration backend exposes no per-agent count

The temporary harness is parent-owned implementation scratch, not an immutable
candidate or review artifact. The parent remains responsible for promoting the
proofs into the sole owned Lean file and running the acceptance gates.
