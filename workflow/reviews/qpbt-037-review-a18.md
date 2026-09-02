# QPBT-037 / LPR-032 immutable review (A18)

Session: `i037-reviewer-a18-pauli`  
External identity: `/root/i037_reviewer_a18_pauli`  
Verdict: `approve`

## Findings

No findings.

## Coverage

The reviewer authenticated the exact immutable candidate and checked the scalar
and tensor Pauli definitions against the pinned source and frozen F05/G09
contract. In particular, the review covered:

- scalar X/Z entry orientation and Fourier projector sign and normalization;
- positivity and completeness of the genuine rank-one Fourier and
  computational measurements;
- scalar multiplication, square, G09 order, and the negative trace phase;
- scalar spectral expansion and inversion;
- the bilinear vector dot product and trace-character cancellation;
- direct product-basis tensor entries and full product-space normalization;
- tensor G09 commutation, spectral expansion, and inversion; and
- the `n = 0` and unrestricted `k = 0` boundary cases.

All 16 public declarations match the frozen contract. No public reindexing
premise is required: the later recursive `Matrix.kronecker` association and
indexing boundary remains owned by F10. The candidate contains no `sorry`,
`axiom`, `constant`, obligation input, or incompatible import. The inherited
G16 `sorry` in `fieldDataOfOddExponent` is not used by these proofs.

## Authentication and accounting

- Base and sole parent:
  `c5f4b277c17c54f2bfff3eb02c1101d4f1e85b60`
- Head: `cdb83f4017cfc182eb2611be0fbc5cd3635fbf64`
- Tree: `239f65b911d5535bdd20bb442c6e9c61aa00f8ff`
- Sole changed path: `MIPStarRE/QPBT/Basic/Pauli.lean`
- Lean blob: `d183c3d440bdb49870ba55f8ad06cb029531743e`
- Lean SHA-256:
  `df003a117fb8495bd01bd7ceee45b7c58df5c9e4815bfb4e5a9e344da6b56e12`
- Binary patch SHA-256:
  `0292bed4a9457185b82b27db060091a766aa3f4b0719553da50eacd3d152d08d`
- Review manifest SHA-256:
  `01046acaa7b108cf7e6c63fa85f04dcc1102ae0d564eee56849587dab4f62226`
- Frozen F05 marker SHA-256:
  `2046e1a3784f6bf10a1a7c71b279bd41d5c27ed3424e20797cf7c5bba95b4aa7`
- Manifest entries: 20/20, including 16/16 Git blobs and 4/4
  filesystem files
- Registered candidate checks: 7/7 passed before review
- Governed lifecycle elapsed time: 349.192 seconds
- Read-only shell invocations: 15
- Repository writes, Lean/Lake/build/cache/materialization, network, endpoint,
  GitHub, credential access, and nested agents: 0
- Token usage: `null`; the collaboration backend exposes no per-agent count

Residual risk is limited to relying on the authenticated exact-head scoped,
target, and full-build records because immutable reviewers do not compile. F10
must still prove its explicit tensor/reindexing isometries.

The exact candidate is approved for guarded integration.
