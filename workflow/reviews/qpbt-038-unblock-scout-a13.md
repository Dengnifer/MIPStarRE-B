# QPBT-038 faithful unblock scout (A13)

Session: `i038-scout-a13-unblock`  
External identity: `/root/i038_scout_a13_unblock`  
Mode: fresh read-only source/contract scout

## Findings

1. Candidate `9070aa4d7db267fd890c9b487defa2940e9810a` is an
   implementation bug, not a paper gap. Its `directSum` and `downsize` ignore
   their maps, `CLSampler.sample` is `PMF.pure (0, 0)`, and typed sampling
   replaces both sampled vectors by zero. The paper instead specifies one
   shared uniform seed, componentwise direct sum, conjugation by downsize, and
   exact pushforward laws at `conditionally-linear.tex:132-138,315-327,
   365-383,394-430,533-550` and `types.tex:84-93,143-183`.
2. Canonical QPBT-038 state is stale. It still requests only F06 followed by
   F07 and omits the integrated `F06A-EXECUTABLE-CL` dependency and its 38
   planned callables, despite the explicit handoff in
   `workflow/reviews/qpbt-048-executable-cl-contract-a01.md:265-293`.
3. QPBT-048 closed on a materially non-elaborated F06A contract. The A04
   manifest contains prose in subtype types (`u in previous marginal range`),
   references `CLStage.pred` before its declaration, uses undeclared
   `validQueryFinset`, reduces core decomposition laws to naked `Prop`, and
   models the machine as arbitrary output/steps/run fields without the claimed
   `Turing.FinTM2` operational boundary. A05 supplied probe-elaborated pieces,
   but it was read-only; A06 reviewed the unchanged metadata and ran no Lean.

The source ambiguities around time aggregation, omitted query domains, codec
construction, and compiler cost require explicit boundary choices. They do
not justify prose placeholders, arbitrary machine relations, or zero maps.

## Smallest faithful unblock

Create one numbered dependency that replaces the F06A manifest with actual
Lean declarations and requires a bounded whole-block elaboration probe. Reuse
the concrete source laws from QPBT-048 A01/A02 and the operational wrapper and
dependent query carriers from A05. Do not dispatch another Types writer until
that contract is independently reviewed.

After the contract repair, one sequential writer owns only
`MIPStarRE/QPBT/Game/Types.lean` in order F06, F06A, F07:

- Define `CLSampler.sample` by mapping `x` to `(S.alice x, S.bob x)` over one
  `PMF.uniformOfFintype` seed.
- Define direct sum by splitting inputs and appending outputs, recursively
  transporting equalized certificates after `raiseLevel`.
- Define downsize by conjugating through `downsizeVector`, transporting the
  register support and recursive certificate through the coordinate
  equivalence and the `GaloisField 2 1`/`ZMod 2` scalar equivalence.
- Bind typed graph edges to the selected Alice/Bob CL distribution and derive
  typed downsize from the mathematical pushforward theorem.

No new certificate constructor, public obligation, generic assumptions, or
proof-debt declaration is needed. Direct-sum certificate, downsize certificate,
and F06A elaboration probes are independent read-only subproblems; writes to
the sole Types file remain sequential.

## Accounting

The collaboration runtime did not expose a start timestamp, elapsed duration,
or token counts. Completion evidence cutoff is
`2026-09-02T17:59:10.610092257Z`; timing is therefore bounded by the active
parent coordinator window rather than estimated. The scout made 103 read-only
shell invocations and inspected the rejected Lean file, both source sections,
QPBT-038/048 state, F06/F06A/F07 metadata, seven QPBT-048 reports, the frozen
F06 contract, `Field.lean`, and targeted Mathlib APIs. It made zero edits,
builds, cache actions, network calls, or nested-agent dispatches.
