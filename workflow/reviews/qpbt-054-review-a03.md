# QPBT-054 / LPR-031 immutable review (A03)

Session: `i054-reviewer-a03-f06a-contract`  
External identity: `/root/i054_reviewer_a03_f06a_contract`  
Verdict: `request_changes`

## Findings

1. **High, blocking: the declared downsize machine is not constructible for an
   arbitrary `AdmissibleFieldFamily`.** The family stores only an arbitrary
   function `exponent : Nat -> Nat` and an oddness proof
   (`workflow/reviews/qpbt-054-f06a-contract-a01.md:88-90`). The original
   executable sampler exposes only the four paper queries (`:268-276`), while
   `ExecutableCLSampler.downsize` must construct a finite machine whose
   dimension output is `s n * Q.exponent n` (`:321-328`) and whose running time
   satisfies `downsize_time` (`:343-346`).

   For example, take level one, constant dimension one, and identity CL maps
   over an arbitrary noncomputable odd-valued exponent family. The original
   query machine can return constant dimension and factor data and copy the
   encoded vector inputs; it need not compute the exponent. Its alleged
   downsized finite machine would compute the exponent through the dimension
   query. The source construction explicitly multiplies by `log q` at
   `conditionally-linear.tex:628-640`, and the cited finite-field basis
   algorithm receives the odd exponent as an input at
   `finite-fields.tex:283-291`.

   Disposition: unresolved. Add intrinsic executable exponent/field-size data
   with its cost included in the runtime contract, or record and discharge a
   tracked paper gap. Whole-block elaboration with temporary placeholder bodies
   cannot establish this existence claim.

2. **Medium: canonical blank tapes do not prove the paper's ignored-tape
   behavior.** `CLSamplerQuery.tapes` fills unused positions with `[]`
   (`workflow/reviews/qpbt-054-f06a-contract-a01.md:211-228`), and
   `ExecutableCLSampler.execution` is quantified only over those canonical
   query encodings (`:268-276`). This does not show output invariance under
   arbitrary contents on tapes that the paper says are ignored at
   `conditionally-linear.tex:603-611`.

   Disposition: unresolved. Quantify the ignored payloads and state output
   invariance, or explicitly document canonical blanking as boundary
   normalization without claiming ignored-tape semantics.

The candidate does repair the prior prose-in-types, declaration-order, naked
`Prop`, arbitrary-run, nondependent-carrier, positive-index, exact-step
maximum, and injective-packing defects.

## Authentication and accounting

- Base: `639c883737e07b91156a9cbc31ec1aa65100a935`
- Head: `83062f78cc52ecf0edf0e725c00850fb458721b5`
- Manifest SHA-256:
  `6ad3b37ad21d3ac9f10b73b594c178e2d0c3b6581ae4c929d7b29184227c9630`
- Authentication: every declared commit, tree, parent, patch, path, blob,
  file, source, and signature identity matched
- Read-only shell invocations: 13
- Governed lifecycle elapsed time: 504.252 seconds
- Repository writes, Lean/Lake/build/cache/materialization, network, GitHub,
  credential access, and nested agents: 0
- Token usage: `null`; the collaboration backend exposes no per-agent count

Approval is blocked until both findings are resolved on a changed candidate
head and a fresh review confirms the repair.
