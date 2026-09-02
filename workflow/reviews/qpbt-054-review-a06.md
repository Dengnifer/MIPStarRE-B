# QPBT-054 / LPR-031 immutable repair review (A06)

Session: `i054-reviewer-a06-f06a-repair`  
External identity: `/root/i054_reviewer_a06_f06a_repair`  
Verdict: `request_changes`

## Finding

1. **Medium, blocking: the new executable-boundary paper gap is not linked
   into the canonical gap ledger.** The node says the paper omits how
   `log q(n)` is computed and therefore adds `FieldExponentProgram`
   (`blueprint/metadata/nodes.json:425`), but `gap_ids` remains empty
   (`blueprint/metadata/nodes.json:426`) and the generated blueprint reports
   `gaps none` (`blueprint/src/generated/chapter-02-entries.tex:272`). Existing
   `G16` only tracks basis/table construction (`blueprint/metadata/gaps.json:155`);
   it does not track computability of the exponent from `n` or the resulting
   change to `TIME_S`.

   Required change: add a reciprocal numbered gap entry tied to
   `F06A-EXECUTABLE-CL` and `QPBT-054`, add its ID to the node, regenerate
   consumers, and add a regression assertion for that linkage.

## Prior finding dispositions

- `F-LPR031-A03-001`: resolved. `FieldExponentProgram` contains a concrete
  `FinTM2` wrapper and positive-index `TM2OutputsInTime` executions computing
  `encodeNat (Q.exponent n)`
  (`workflow/reviews/qpbt-054-f06a-repair-a04.md:240`). It is intrinsic to
  `ExecutableCLSampler` (`:268`), and `time` charges its exact executed steps
  via `Nat.max` (`:297`). No arbitrary function-to-machine theorem or public
  discharge obligation appears.
- `F-LPR031-A03-002`: resolved. Every unused position is blanked by
  `canonicalTapes` (`workflow/reviews/qpbt-054-f06a-repair-a04.md:183`), and
  the active contract explicitly disclaims arbitrary unused-payload invariance
  (`blueprint/metadata/nodes.json:424`).

The complete signature is API-coherent by inspection and the authenticated
whole-block elaboration evidence. The checker and tests freeze the repaired
executable terms and canonical-blank semantics. No forbidden assumption
pattern, `axiom`, `constant`, or repository proof debt was introduced.

## Authentication

- Manifest SHA-256: `b0632513d1f7065251f77f912b557bd1ba1e20e020dd9aeb138faf54f444b4df`
- Base: `639c883737e07b91156a9cbc31ec1aa65100a935`
- Rejected head: `83062f78cc52ecf0edf0e725c00850fb458721b5`
- Changed head: `3a248eac86fa8b782134a4fae88169f514a0168d`
- Tree: `77cf487b5d5bf1d5ed3771f282b777ea5d89f5d5`
- Sole parent: `83062f78cc52ecf0edf0e725c00850fb458721b5`
- Full-base patch SHA-256: `39483901a81d39fcb9375304ce5b0aac3bbb33181afc761efc5904c840fe3fdf`
- Repair patch SHA-256: `a2962b67e6668a92aefd83d46b56f0ad7edd698a95371ef1729902787e6c945b`
- Signature SHA-256: `cfe433e36d0670c344b29ab5107557842e7d4fc8358fba2713b8ff2ee107a3a1`
- Entries authenticated: 20 total, 17 Git and 3 filesystem

## Residual risk and accounting

The operational downsize compiler and runtime proof remain future Lean
implementation work. This review did not rerun the eight registered checks or
any build.

- Observed end: `2026-09-02T20:01:29.512911976Z`
- Read-only shell invocations: 100
- Repository and `/tmp` writes: 0
- Lean, Lake, builds, cache, materialization, network, GitHub, credentials, and
  nested agents: 0
- Token usage: `null`; the collaboration backend exposes no per-agent count
