# QPBT-037 Fourier unblock scout (A14)

Session: `i037-scout-a14-fourier`  
External identity: `/root/i037_scout_a14_fourier`  
Mode: fresh read-only source/API scout

## Findings

1. The pinned `MIPStarRE.Quantum` foundation is no longer a blocker. It is
   intentionally excluded from Git by `.gitignore` and is authenticated and
   materialized by the canonical cache recipe. QPBT-042 already exercised
   that boundary successfully. It must not be vendored or edited for F05.
2. No new generic Quantum helper module is needed. The existing
   `Quantum.Measurement.ofSumEqOne` packages positive effects whose sum is the
   identity, and Mathlib provides
   `Matrix.posSemidef_vecMulVec_self_star` for the individual rank-one effects.
3. The remaining proof obligation is finite-field trace-character
   orthogonality. The source defines the Fourier projectors at
   `references/2001.04383v3/sections/dependencies/pauli.tex:52-88` and reuses
   the same cancellation in the tensor formulas at `:90-110`. The relevant
   existing lemmas are `AddChar.expect_eq_ite`,
   `ZMod.injective_stdAddChar`, and
   `FiniteField.trace_to_zmod_nondegenerate`.

## Smallest implementation plan

Keep sole writable ownership of `MIPStarRE/QPBT/Basic/Pauli.lean` and the four
frozen imports. Prove two private helpers, one for
`fieldTrace k (c * x)` and one for
`fieldTrace k (fieldDotProduct c x)`, each stating that the uniform additive
character expectation is `1` exactly at zero and `0` otherwise. Construct the
actual X Fourier rank-one effects and Z computational rank-one effects through
`Measurement.ofSumEqOne`; the previously rejected diagonal X measurement is
not source-faithful.

The helpers are unconditional concrete-field facts. They add no assumption,
proof-debt constant, or public API. QPBT-037 is independent of QPBT-038 and can
restart immediately from a fresh exact base.

## Validation packet

```text
lake env lean MIPStarRE/QPBT/Basic/Pauli.lean
lake build MIPStarRE.QPBT.Basic.Pauli
owned-file sorry/admit/axiom/constant/obligation scan
exact import and G09 phase/order scan
python3 blueprint/check.py --check
python3 blueprint/check.py --check --source-root references/2001.04383v3
lake build
git diff --check
```

## Accounting

The collaboration runtime did not expose a start timestamp, elapsed duration,
or token counts. Completion evidence cutoff is
`2026-09-02T17:58:01.822726400Z`; timing is therefore bounded by the active
parent coordinator window rather than estimated. The scout made 57 read-only
shell invocations across 28 directly opened files and scoped searches. It
reported three findings, zero edits, builds, Git mutations, network calls, or
nested agents.
