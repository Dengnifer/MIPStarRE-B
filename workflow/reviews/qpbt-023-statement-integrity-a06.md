# QPBT-023 statement-integrity review (A06)

Verdict: **approve**

Reviewed immutable PR delta base `942f9438b991ece8942815db16c019b92d9cdd8e`,
head `70fb1f484b0b94522b81082342b528b2fd39b707`, tree
`59b1ca4351e91d1317c870d9e6da820a2b8cbf9f`. Review was read-only. No
repository, Git, workflow state, metrics, network, endpoint, or credential
operations were performed.

## Findings

No correctness findings. The generated contracts preserve the cited paper
hypotheses, conclusions, quantifier order, and error constants, while marking
documented paper gaps rather than turning them into caller assumptions.

## Statement-integrity checks

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
|---|---|---|---|---|---|
| F01 | positive odd `k`, concrete `F_(2^k)/F_2`; uniform algorithmic clause | `k : Nat`, `Odd k`; field/trace data derived; no basis/witness input; algorithm separated in K03A | simultaneous self-dual normal basis and polynomial-time uniform construction | noncomputable mathematical selection in F01; K03A separately owns algorithm/tables/cost | faithful boundary; G16 explicit |
| F03 | finite POVMs, projective binary case, arbitrary postprocess map | explicit finite/decidable carriers; projectivity only where required | fiber-sum postprocess and observable `effect 0 - effect 1` | qualified postprocess/effect declarations with same sign/order | faithful boundary |
| F04-ASYMPTOTIC | indexed states/strategies, `[0,1]` error profile, finite distributions | explicit PMFs, finite carriers, marginals, first/second state choice; `IsBigO atTop` | squared/averaged distances are `O(delta)` | indexed `IsBigO atTop`, without replacing it by finite exact bounds | faithful boundary |
| F04-CONSISTENCY | two POVM families; three premises for Prop. 4.29 | explicit PMF, finite carriers, normalized state, indexed families | off-diagonal mismatch `O(delta)`; triangle `epsilon + 2*sqrt(delta+gamma)` | same finite value, Big-O relation, and three-premise law | faithful boundary |
| F04-DISTANCE-LAWS | consecutive distance premises; shared postprocess map | same finite data and explicit map; factor 2 finite helper | triangle/data processing with constants absorbed only asymptotically | exact factor-2 finite helper plus indexed Big-O laws | exact |
| G16 | source construction for odd extension degree | exactly one declared skeleton hole at `fieldDataOfOddExponent`; no public construction premise | basis existence plus separate uniform algorithm/table theorem | gap note keeps both obligations distinct; second declared hole is only main theorem | faithful boundary |

## Forbidden-assumption audit

Searched all changed generated contracts, README, gap note, and metadata for
`bridge`, `residual`, `repair`, `witness`, `package`, `Hypotheses`,
`Assumptions`, and arbitrary implication inputs. These occur only as explicit
prohibitions or discharge-plan text. No such input is added to a paper-facing
contract. README and metadata declare exactly two minimal skeleton `sorry`s:
`fieldDataOfOddExponent` (G16) and `pauliSoundness`; no axiom/constant debt is
introduced.

## Immutable manifest

The sorted changed-path list is exactly the 22 paths supplied in the review
authority. `git diff --name-only base..head | sort` has SHA-256
`da448352467433f304f824346e00cc9527d3b0f22cbe2f8d33e8e6a9016804bd` and the
candidate tree matches `59b1ca4351e91d1317c870d9e6da820a2b8cbf9f`.

## Validation

- `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3`: PASS (51 nodes, 12 chapters).
- `python3 blueprint/check.py --check`: PASS (51 nodes, 12 chapters).
- Source-anchor audit inspected finite-fields.tex definitions of trace/dual/self-dual/normal bases and strategies-distance.tex definitions of consistency, Proposition 4.29 triangle, and data processing; citations and constants match.
- Token usage: `null` (reviewer endpoint does not expose token accounting).
- Reviewer elapsed time: recorded by the orchestrator session envelope.

Review ID: `review-qpbt-023-a06-statement-integrity`.
