# QPBT-057 current-main immutable review (A07)

Session: `i057-reviewer-a07-current-main`  
External collaboration identity: `/root/i057_reviewer_a07_current_main`  
Issue: `QPBT-057`

## Verdict

**REQUEST_CHANGES**

## Findings

1. **Blocker: the selected downsized executable is not selected with the resource property later claimed for it.**  
   `MIPStarRE/QPBT/Game/Types.lean:1559` only asserts nonemptiness of a sigma containing a machine, correctness executions, and a binary-field exponent program. It places no step bound on either selected program. `MIPStarRE/QPBT/Game/Types.lean:1571` then defines the public downsized sampler by `Classical.choice` from exactly that correctness-only sigma. Finally, `MIPStarRE/QPBT/Game/Types.lean:1614` claims the global-positive `RuntimeBigO` bound for that selected sampler. Correct machines and exponent programs can insert an unbounded index-dependent delay while preserving every execution/output proposition in the sigma, so correctness alone cannot establish the claimed bound, and classical choice does not preferentially select an efficient witness. This is a load-bearing definition/statement mismatch, not merely the authorized absence of a proof body. The smallest repair is to make the private compiler witness carry a resource guarantee for the same machine, executions, and exponent program used to construct `downsize` (or otherwise define an explicit resource-certified compiler), then derive the public runtime theorem from that selected data. The public frozen signature need not change.

2. **Blocker: the reported build/cache validation is not bound to the authenticated current candidate.**  
   `workflow/reviews/qpbt-057-f06a-a02.md:5` records base `038d878f...`, `:6` records implementation commit `a1333041...`, and `:7` records implementation tree `b5c9dc90...`; its scoped, target, full-build, and cache claims at `:35-54` therefore concern that older snapshot/cache key. The authenticated review candidate is base `9eb476a4...`, head `a67031de...`, tree `71acb8bd...`. The current issue record repeats pass claims but supplies no current-head command log or current-main cache identity. Because the canonical build protocol keys the build recipe/cache to the exact main SHA, unchanged `Types.lean` bytes do not by themselves transfer whole-tree build evidence across bases. Re-run and record the required scoped check, affected target, full build, and blueprint synchronization against the exact current base/head before the next immutable review.

## Authentication

- Manifest SHA-256: `375351b59e2b3ea49682570376acc00180b77d101bbfca2f0cc6f172820fa889`, exact.
- Clean detached `HEAD`: `a67031de5a3804360e113dd4a881e94376fc435f`, exact.
- Head tree: `71acb8bd5ea77959a03a1124c2fce018457b9605`, exact.
- Head parent: `f51b636169dc0b008f8de9b877086c518d7ac945`, exact.
- Base/tree: `9eb476a41595fc70060ed9bb2ea91a50c793ede3` / `bb64aa48a0d6deb12995d449778064a296a1a9b8`, exact.
- Ordinary Git diff SHA-256: `d13454544557b44a38e7c2b3cb2c992dd5551cab3e14aa274269772ae36bfa2f`, exact.
- Changed paths are exactly `MIPStarRE/QPBT/Game/Types.lean` and `workflow/reviews/qpbt-057-f06a-a02.md`.
- All twelve manifest-listed file hashes match. The three `local:` paper sources were authenticated at their canonical `/home/drx/MIPStarRE-auto` paths because the detached worktree does not contain the ignored source tree.

## Checks completed

- The candidate has exactly the frozen four imports. Comparison with the complete QPBT-059 signature marker found no added, removed, reordered, or signature-changed public F06A declaration; this preserves the marker's exact 56-name API. All non-marker implementation declarations in the F06A section are private.
- `packSixTapes` serializes all six `List.ofFn` tapes in order, maps `false` to `01` and `true` to `10`, and appends `00` to every tape. Its left-inverse proof covers empty tapes, adjacent empty-tape delimiters, and arbitrary delimiter-bearing patterns in source tapes through dual-rail escaping; the injectivity proof is sound.
- Canonical queries place `n`, side, mode, one-based stage, prefix/vector, and factor input on the intended six tapes and leave unused tapes blank. Outputs have the paper's dimension, marginal, linear, and factor-indicator meanings.
- `CLQueryDecomposition` supplies chosen marginal maps, valid prior-output prefixes, coordinate factor cover/disjointness, supported linear maps, marginal sums, and the top-map identity. It therefore ties query answers to a complete chosen decomposition of the associated CL map rather than to arbitrary public obligations.
- The field codec is a fixed-order bijective binary-coordinate encoding through the selected F01 `FieldData`. Downsized factor blocks and vector coordinates use the same coordinate-major order.
- Dimension is `s(n) * exponent(n) = s(n) * log_2(q(n))`; the associated maps are basis conjugates; and the PMF theorem is the exact shared-uniform-seed pushforward. These checks passed independently of finding 1.
- `RuntimeBigO` correctly implements the paper's stronger global convention: one positive real constant and every positive natural index. Source `time` charges the valid-query maximum and the intrinsic exponent program, matching documented paper gap G19. Finding 1 concerns selection of the downsized resource witness, not this boundary's signature.
- The only `sorry` tokens are at `MIPStarRE/QPBT/Game/Types.lean:1568` and `:1618`, in the two authorized theorem bodies whose warning anchors are declarations at `:1559` and `:1614`. There is no declared `axiom`, `constant`, generic `Hypotheses`/`Assumptions`, `_ofObligations` helper, public bridge/residual/repair/package/producer, or arbitrary implication premise.
- Source anchors are coherent: dual rail is `preliminaries.tex:105-111`; sampler modes/distribution are `conditionally-linear.tex:572-626`; downsizing is `:630-680`; and field representation is `finite-fields.tex:245-291,350-410`.

## Statement integrity

| Paper item | Paper assumptions/conclusion | Lean assumptions/conclusion | Verdict |
| --- | --- | --- | --- |
| Tuple encoding | A fixed `k`-tuple codec, dual rail per bit, `00` after each string, linear encoding time | Fixed six tapes, exact same bit/delimiter codec, injective serialization | exact specialization |
| CL sampler definition | Positive index; admissible `q(n)`; dimension `s(n)`; one six-input machine answering dimension/marginal/linear/factor queries for chosen Alice/Bob CL decompositions | Positive-index execution; odd exponent family; typed valid queries; one packed `FinTM2`; chosen decomposition laws; canonical blank unused tapes | faithful boundary |
| Sampler distribution | Apply both chosen CL maps to one uniform ambient seed | `ExecutableCLSampler.sample` delegates to the same shared-seed `CLSampler.sample` | exact |
| Field representation | Coordinates in the algorithm-selected self-dual normal basis over `F_2` | `fieldCodec` uses canonical F01 `FieldData.coordinates` and a width-exact encoding | faithful boundary |
| Downsized maps and factors | Coordinate conjugation; each selected factor coordinate expands to a block of `log q` binary coordinates | Associated-map conjugation and coordinate-register expansion by the exponent | exact |
| Downsized distribution | Push the original CL distribution through binary coordinates on both outputs | Exact `PMF.map` through `downsizeVector` on both components | exact |
| Downsized dimension | `s(n) log q(n)` | `s(n) * Nat.log 2 (Q.fieldSize n)` at positive `n` | exact |
| Downsized runtime | For `ell >= 1`, the constructed downsized sampler has global `O(TIME_S(n) log q(n))` runtime | Same public quantifiers and conclusion, with intrinsic exponent computation charged per G19, but `downsize` currently chooses from a correctness-only witness | documented mismatch; finding 1 |

## Residual risk

No Lean elaboration or build was rerun under the read-only packet constraint. Even after the two blockers are repaired, the operational compiler and runtime proof remain intentionally deferred Stage-4A debt until QPBT-061; their eventual proof must validate the parser, simulation, field-coordinate computation, factor-block emission, and exact global resource inequality without changing the frozen public API.

## Accounting

- Authenticated substantive review interval: `2026-09-03T12:37:08Z` to `2026-09-03T12:42:57Z` (`349` seconds).
- Token usage: `null`; the collaboration backend exposes no per-session token count.
- Findings: `2` blockers; retries: `0`; incidents: `0`.
- Nested agents/subagents: `0`; topology: one reviewer session only.
- Lean elaboration attempts: `0`; target builds: `0`; full builds: `0`.
- Cache warm/seed/read/write actions: `0`; lock wait: `0` seconds.
- Network/endpoint/GitHub/credential actions: `0`.
- Repository, Git, workflow-state, metrics, protocol, and candidate writes: `0`.
- Review artifacts written: `1`, this `/tmp` report only.
