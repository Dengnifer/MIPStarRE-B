# Self-dual normal basis construction gap

Status: open (`G16`, tracked by `QPBT-023`)

Affected blueprint nodes: `F01-FIELD`, `K03A-FIELD-ARITHMETIC`

## Pinned source contract

The source is arXiv:2001.04383v3, split file
`references/2001.04383v3/sections/dependencies/finite-fields.tex`:

- lines 62-83 (original 1378-1399) define trace, duality, self-duality,
  and normality, and state that a self-dual normal basis exists when the
  base field is `F_2` and the extension degree is odd;
- lines 243-307 (original 1559-1623), especially
  `lem:efficient_basis`, require one deterministic algorithm which, for every
  positive odd `k`, outputs both a self-dual normal basis of `F_(2^k)` over
  `F_2` and its multiplication tables in `poly(k)` time; and
- lines 350-400 (original 1666-1716), `lem:efficient_arithmetic`, use the
  basis and tables returned by that algorithm for all subsequent represented
  arithmetic and projection bounds.

Thus the paper has two related but distinct obligations. The mathematical
layer needs one `Fin k`-indexed basis whose vectors form a Frobenius orbit and
whose trace pairing is the Kronecker delta. The computational layer needs a
single uniform algorithm which selects such a basis, emits coherent
multiplication tables, and satisfies the stated cost bounds.

The `Fin k` index is zero-based in Lean: index `j` represents the paper's
Frobenius exponent `j` in the range `0,...,k-1`. The paper writes the same
basis as `e_1,...,e_k` when discussing coordinates; that one-based display
does not change the orbit convention.

## Formalization gap

The pinned Lean dependency supplies finite-field, field-trace, normal-basis,
and trace-dual infrastructure, but the QPBT-023 API search found no theorem or
executable construction which simultaneously supplies normality and trace
self-duality for every odd extension degree. Choosing a normal basis and then
taking its trace dual does not by itself prove that the result is the same
normal basis. Conversely, an arbitrary self-dual basis does not by itself
supply a Frobenius orbit or the paper's uniform algorithm and tables.

It would therefore be source-drifting to make `F01` accept a basis, a
self-duality proof, a normality proof, an algorithm, or a generic witness
package from its caller. It would also be incorrect to identify a
noncomputable choice of an existing basis with the deterministic algorithm of
`lem:efficient_basis`.

## Discharge plan

1. Prove simultaneous existence over the concrete field `GaloisField 2 k`:
   for every odd natural `k`, there is an element whose `k` Frobenius iterates
   form a basis and have trace pairing equal to the Kronecker delta. This
   theorem has no caller-supplied basis or construction premise.
2. Package that theorem as the noncomputable mathematical basis selected by
   `F01`. Prove the trace-coordinate and Frobenius-index facts used by QPBT.
3. Treat `lem:efficient_basis` separately. Pin and formalize (or faithfully
   import with verified provenance) the cited Shoup-Lenstra-Wang algorithmic
   chain, including its output representation, correctness, and multiplication
   tables.
4. Prove that the algorithmic output realizes the same `F01` abstract
   self-dual-normal-basis interface; do not require definitional equality with
   the noncomputable choice.
5. Prove `K03A` in the repository's explicit computation model, including the
   table, arithmetic, trace, inverse, and complementary-projection bounds.

Until steps 1-2 are complete, `F01` remains a paper gap. Until steps 3-5 are
complete, the algorithmic and complexity claim in `K03A` remains a separate
paper gap. Neither gap may be discharged by adding a public assumption or by
marking a conditional `_ofObligations` helper as the paper theorem.

## Declared skeleton proof debt

The minimal skeleton may use one tracked `sorry` at the exact source-faithful
declaration `MIPStarRE.QPBT.fieldDataOfOddExponent`. Its public inputs remain
only `k : Nat` and `Odd k`, and its return remains the concrete simultaneous
self-dual-normal `FieldData k`; the hole must not migrate to a public premise.
Together with the separately declared main-theorem hole at
`MIPStarRE.QPBT.pauliSoundness`, this makes the minimal-skeleton count exactly
two. `blueprint/metadata/nodes.json` records both names and identifies the
field hole with `G16`.

This exception applies only to the declared skeleton stage. A proof-complete
stage permits zero `sorry`, `axiom`, or `constant` debt. Consequently, the
implementation issue's gate must read "no unintended `sorry`/`axiom`/`constant`;
only the declared G16 and main-theorem holes" for the minimal skeleton, while
retaining an unconditional zero-hole gate for proof completion.

## Acceptance evidence

- the source-faithful `F01` theorem depends only on odd `k` and concrete
  finite-field boundary data derived from it;
- its chosen basis has both normality and trace self-duality proved;
- the uniform algorithm/table theorem is separately callable and its output is
  proved coherent with the mathematical interface;
- `K03A` proves, rather than assumes, algorithm correctness and complexity; and
- the changed Lean files, generated blueprint declarations, and full project
  build pass fresh independent review.
