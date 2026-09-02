# F04 consistency-law contract correction

## Scope

This note records a formalization-contract mismatch against
arXiv:2001.04383v3. The paper statements are unambiguous; the discrepancy was
introduced by the frozen F04 blueprint contract in
`workflow/reviews/qpbt-023-leaf-contract-a04.md`.

The authenticated source inputs are:

- arXiv archive SHA-256
  `d645cd51dd26cae59195e61aeeb5c886a254ef4adf15da7e5657ad90c7ec2174`;
- `compression_arXiv_v3.tex` SHA-256
  `38b3e662bb85bb902fcd056436fe9ecbe9e68d1990a074d0c0c12b39d5972ea9`;
- `sections/dependencies/strategies-distance.tex` SHA-256
  `a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f`;
- upstream MIPStarRE commit
  `507e81220d95266ff3d589d125b2f87c7300a9fb`, archive SHA-256
  `656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`,
  and materialized inventory SHA-256
  `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db`.

## G17: frozen contract mismatch

### Fact 4.26

Primary-source line 311 defines `\abc[delta]` as
`\otimes I_bob \simeq_delta I_alice \otimes`. Consequently, Fact 4.26 at
split lines 391-395 is a heterogeneous Alice/Bob POVM-consistency implication:
applying the same outcome map to both POVM families preserves their consistency
relation and its error profile.

The superseded F04 contract instead used `MeasurementFamiliesBigO`, a
same-space state-dependent-distance relation. That statement may be useful in
its own right, but it is not Fact 4.26. The corrected paper-labelled contract is
`POVMConsistencyBigOPostprocessLaw`, with proof obligation
`povmConsistencyBigO_postprocess`. It permits distinct Alice and Bob coordinate
types and applies the same `MeasurementFamily.postprocess ... f` on both sides.
No same-space postprocessing auxiliary is retained because no current consumer
requires one.

This agrees with the pinned upstream theorem
`MIPStarRE.LDT.Preliminaries.simeqDataProcessing_heterogeneous` in
`ComparisonCore.lean:464-475`. That file has SHA-256
`f148d77e457645b12139b638ba783a13f0e45943f231a4cc4dd348972f4cab9b`.

### Proposition 4.29

The paper's consistency relations are evaluated on a quantum state, hence a
unit vector. The superseded `POVMConsistencyBigOTriangleLaw` accepted an
arbitrary vector family. Its exact scale
`epsilon + 2 * sqrt (delta + gamma)` is not invariant under arbitrary state
rescaling.

The corrected Law and theorem quantify
`(hpsi : forall n, norm (psi n) = 1)` immediately after `psi` and before the
four POVM families. They preserve the displayed premise order `A~B` at
`epsilon`, `C~B` at `delta`, and `C~D` at `gamma`, and conclude `A~D` at the
paper's exact scale. The pinned upstream heterogeneous theorem has the same
state-first order and explicit normalization at `Triangles/SimEq.lean:125-145`;
that file has SHA-256
`6ed102b06eb3ab080b816fc8592a4418deb6f71911517c7669bc08fa85346a48`.
Its additional finite-distribution mass premise is discharged by the QPBT PMF
carrier.

## Faithful boundary notes

`MeasurementConsistentOn` expresses equality of the Alice and Bob local
actions for an arbitrary qualified `Quantum.Measurement`. The paper's
Definition 3.2 restricts `M` to a projective measurement. The general Lean
predicate is reusable, but a paper-labelled use must pair it with a separate
projectivity hypothesis; the generalization alone is not the paper definition.

The paper's strategy-distance definition says that measurement comparisons
hold on either the first or the second strategy state. The current
`StrategyStateChoice` and `StrategyFamiliesBigO` API exposes that choice as a
helper parameter. A paper-facing strategy-distance proposition must
existentially quantify one shared choice. The source's singular description of
"the approximations" favors a shared choice, but it does not explicitly discuss
whether Alice and Bob may choose different states; this remains documented
boundary ambiguity rather than being silently decided here.

## Disposition

`workflow/reviews/qpbt-032-f04-contract-correction-a01.md` supersedes only the
F04 consistency and distance-law signature blocks from the historical QPBT-023
report. Historical evidence is not edited. `blueprint/metadata/gaps.json`
records reciprocal `G17` links from `F04-CONSISTENCY` and
`F04-DISTANCE-LAWS`.

This correction changes planned contracts before their Lean implementation. It
does not weaken a paper theorem, add a public assumption, or claim a completed
proof.
