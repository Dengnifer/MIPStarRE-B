# QPBT-035 finite-game semantics API scout (A08)

Session: `i035-scout-a08-game-semantics-api`

## Decision and findings

**Decision: approve `F04A-GAME-SEMANTICS` as the missing reusable owner, with
the no-move dependency and callable surface below.** The source formulas admit
a finite, project-native Lean boundary. The resulting detyping node needs only
`F04A-GAME-SEMANTICS` and `F07-TYPED` as direct prerequisites.

1. **High, implementation scheduling: QPBT-042 cannot dispatch before the
   accepted F04 strategy and exact-consistency contracts are authored.** The
   current 86-line `MIPStarRE/QPBT/Basic/Approximation.lean` implements the F03
   slice only. `PureStrategy` and `MeasurementConsistentOn` are frozen and
   independently reviewed in
   `workflow/reviews/qpbt-023-leaf-contract-a04.md`, but are not yet Lean
   declarations. QPBT-042 must depend on QPBT-041, which owns that continuation.
   It must not duplicate them in `Game/Semantics.lean`
   or treat a reviewed blueprint signature as an implemented API.

2. **Resolved ownership constraint: do not move or relist `PureStrategy` under
   F04A.** Moving it would reopen the accepted F04-DISTANCE contract and would
   eventually force the foundational `Basic/Approximation.lean` layer to import
   `Game/Semantics.lean`. The elaborated no-move solution is a one-field,
   game-indexed `FiniteGameStrategy` wrapper whose only field is the inherited
   `PureStrategy`. It adds no state, measurement, hypothesis, or proof input.

3. **No source or API blocker remains at the finite mathematical boundary.**
   PMFs, finite sums, qualified POVMs, local tensor actions, real parts of
   expectations, matrix rank, real `sSup`, and `WithTop Nat` `sInf` all
   elaborate at the pinned toolchain. Executable machine and cost semantics
   remain in F07A and are not smuggled into F04A.

## Exact source ownership

The pinned source is
`references/2001.04383v3/sections/dependencies/strategies-distance.tex`,
SHA-256
`a3a2e3fd8f2c594f790c1c1f0df0aba93cfc3d2f905048437c93890cc9033e5f`.

| Generated lines | Original lines | Labels/content owned |
| --- | --- | --- |
| `4-51` | `2887-2934` | `def:game`, `def:tensor-product-strategy`, `def:tensor-product-value`: finite game data, tensor strategy, fixed-strategy value, and supremal game value |
| `62-81` | `2945-2964` | `def:projective-strategy`, `rem:symmetric-games`: projective strategies and game/strategy symmetry |
| `126-190` | `3009-3073` | `def:comm-strategy`, `def:consistent-measurement`, `def:consistent-strategy`, `def:spcc`, Schmidt rank, and `def:ent` |

The omitted lines `52-61`, `82-125`, and `191+` are remarks or the separate
symmetrization theorem and distance development. F04A does not claim that
theorem or the later distance laws.

## Proposed exact metadata

```json
{
  "id": "F04A-GAME-SEMANTICS",
  "chapter": "02",
  "title": "Finite two-player game and quantum strategy semantics",
  "kind": "definition",
  "public": false,
  "status": "not-started",
  "fidelity": "faithful-boundary",
  "source": {
    "path": "references/2001.04383v3/sections/dependencies/strategies-distance.tex",
    "label": "def:game",
    "generated_lines": [4, 51],
    "original_lines": [2887, 2934]
  },
  "additional_sources": [
    {
      "path": "references/2001.04383v3/sections/dependencies/strategies-distance.tex",
      "label": "def:projective-strategy",
      "generated_lines": [62, 81],
      "original_lines": [2945, 2964]
    },
    {
      "path": "references/2001.04383v3/sections/dependencies/strategies-distance.tex",
      "label": "def:comm-strategy",
      "generated_lines": [126, 190],
      "original_lines": [3009, 3073]
    }
  ],
  "statement": "Define finite two-player one-round games; a game-indexed wrapper around the established finite pure tensor strategy; exact strategy and supremal game values; projective, symmetric, support-commuting, consistent, PCC, and SPCC predicates; coefficient-matrix Schmidt rank; and the extended-natural entanglement requirement.",
  "lean": {
    "module": "MIPStarRE.QPBT.Game.Semantics",
    "names": [
      "MIPStarRE.QPBT.FiniteGame",
      "MIPStarRE.QPBT.FiniteGameStrategy",
      "MIPStarRE.QPBT.strategyValue",
      "MIPStarRE.QPBT.StrategyWinsWithProbability",
      "MIPStarRE.QPBT.FiniteDimensionalGameStrategy",
      "MIPStarRE.QPBT.FiniteDimensionalGameStrategy.value",
      "MIPStarRE.QPBT.gameValue",
      "MIPStarRE.QPBT.ProjectiveStrategy",
      "MIPStarRE.QPBT.SymmetricGame",
      "MIPStarRE.QPBT.SymmetricStrategy",
      "MIPStarRE.QPBT.SupportCommutingStrategy",
      "MIPStarRE.QPBT.ConsistentStrategy",
      "MIPStarRE.QPBT.PCCStrategy",
      "MIPStarRE.QPBT.SPCCStrategy",
      "MIPStarRE.QPBT.schmidtRank",
      "MIPStarRE.QPBT.FiniteDimensionalGameStrategy.schmidtRank",
      "MIPStarRE.QPBT.entanglementRequirement",
      "MIPStarRE.QPBT.HasValueOnePCCStrategy"
    ]
  },
  "transitive_definitions": [
    "F03-MEASUREMENT",
    "F04-DISTANCE",
    "F04-ASYMPTOTIC",
    "F04-CONSISTENCY"
  ],
  "prerequisites": ["F04-CONSISTENCY"],
  "encoding": "Reuse the accepted PureStrategy and MeasurementConsistentOn declarations. FiniteGame stores a PMF and Bool predicate. FiniteGameStrategy is a one-field game-indexed wrapper, not a second strategy representation. Quantify all finite Hilbert coordinates canonically by Fin dimensions, define game value by real sSup, Schmidt rank by Matrix.rank of the coefficient matrix, and Ent by WithTop Nat sInf so the empty attainable set is infinity.",
  "boundary_hypotheses": "Question, answer, and coordinate carriers are explicit finite decidable types. Shared-space predicates use one coordinate type for both players. Canonical Fin dimensions represent arbitrary finite coordinate Hilbert spaces. No executable sampler, machine description, cost model, caller-supplied semantic obligation, or public bridge assumption enters this node.",
  "gap_ids": [],
  "integrity": {
    "paper_assumptions": "Finite question and answer alphabets, a question distribution, Boolean decision predicate, normalized finite-dimensional pure tensor strategies with POVMs, and a common local Hilbert space for commuting/consistent/PCC predicates.",
    "lean_assumptions": "Explicit Fintype/DecidableEq carriers, Mathlib PMF, the reviewed PureStrategy and MeasurementConsistentOn interfaces, and canonical Fin coordinate representatives for the dimension-varying extrema.",
    "paper_conclusion": "Exact fixed-strategy and game values; projective, symmetric, commuting, consistent, PCC, and SPCC predicates; Schmidt rank; and the minimum rank requirement or infinity.",
    "lean_conclusion": "The same formulas, predicates, supremum, matrix rank, and extended-natural minimum, with the game-strategy association represented by a data-free wrapper.",
    "verdict": "faithful boundary"
  }
}
```

The direct imports are:

```lean
import Mathlib.LinearAlgebra.Matrix.Rank
import Mathlib.Order.ConditionallyCompleteLattice.Basic
import Mathlib.Probability.ProbabilityMassFunction.Constructions
import MIPStarRE.QPBT.Basic.Approximation
```

The inherited APIs are `PureStrategy`, `ProjectiveMeasurementFamily`,
`MeasurementConsistentOn`, `aliceLocal`, `bobLocal`, and `operatorAction`.
F04A does not list any inherited name as an owned callable.

## Exact Lean boundary

The following common context is binding for the displayed declarations.

<!-- BEGIN F04A-GAME-SEMANTICS-SIGNATURES -->
```lean
namespace MIPStarRE.QPBT

universe uQuestionA uQuestionB uOutcomeA uOutcomeB uAlice uBob uCoord

structure FiniteGame
    (QuestionA : Type uQuestionA) (QuestionB : Type uQuestionB)
    (OutcomeA : Type uOutcomeA) (OutcomeB : Type uOutcomeB)
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB] where
  questionDistribution : PMF (QuestionA × QuestionB)
  accepts : QuestionA -> QuestionB -> OutcomeA -> OutcomeB -> Bool

structure FiniteGameStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (Alice : Type uAlice) (Bob : Type uBob)
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob] where
  toPureStrategy :
    PureStrategy QuestionA QuestionB OutcomeA OutcomeB Alice Bob

noncomputable def strategyValue
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteGameStrategy G Alice Bob) : Real

def StrategyWinsWithProbability
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteGameStrategy G Alice Bob) (nu : Real) : Prop

def ProjectiveStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Alice] [DecidableEq Alice]
    [Fintype Bob] [DecidableEq Bob]
    {G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB}
    (S : FiniteGameStrategy G Alice Bob) : Prop

def SupportCommutingStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Coord : Type uCoord}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Coord] [DecidableEq Coord]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteGameStrategy G Coord Coord) : Prop

def ConsistentStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Coord : Type uCoord}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Coord] [DecidableEq Coord]
    {G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB}
    (S : FiniteGameStrategy G Coord Coord) : Prop

def PCCStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    {Coord : Type uCoord}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    [Fintype Coord] [DecidableEq Coord]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteGameStrategy G Coord Coord) : Prop

def SymmetricGame
    {Question : Type uQuestionA} {Outcome : Type uOutcomeA}
    [Fintype Question] [DecidableEq Question]
    [Fintype Outcome] [DecidableEq Outcome]
    (G : FiniteGame Question Question Outcome Outcome) : Prop

def SymmetricStrategy
    {Question : Type uQuestionA} {Outcome : Type uOutcomeA}
    {Coord : Type uCoord}
    [Fintype Question] [DecidableEq Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    {G : FiniteGame Question Question Outcome Outcome}
    (S : FiniteGameStrategy G Coord Coord) : Prop

def SPCCStrategy
    {Question : Type uQuestionA} {Outcome : Type uOutcomeA}
    {Coord : Type uCoord}
    [Fintype Question] [DecidableEq Question]
    [Fintype Outcome] [DecidableEq Outcome]
    [Fintype Coord] [DecidableEq Coord]
    (G : FiniteGame Question Question Outcome Outcome)
    (S : FiniteGameStrategy G Coord Coord) : Prop

abbrev FiniteDimensionalGameStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB) :=
  Sigma fun aliceDim : Nat => Sigma fun bobDim : Nat =>
    FiniteGameStrategy G (Fin aliceDim) (Fin bobDim)

noncomputable def FiniteDimensionalGameStrategy.value
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (S : FiniteDimensionalGameStrategy G) : Real

noncomputable def gameValue
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB) : Real

noncomputable def schmidtRank
    {Alice : Type uAlice} {Bob : Type uBob}
    [Fintype Alice] [Fintype Bob]
    (psi : EuclideanSpace Complex (Alice × Bob)) : Nat

noncomputable def FiniteDimensionalGameStrategy.schmidtRank
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    {G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB}
    (S : FiniteDimensionalGameStrategy G) : Nat

noncomputable def entanglementRequirement
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB)
    (nu : Set.Icc (0 : Real) 1) : WithTop Nat

def HasValueOnePCCStrategy
    {QuestionA : Type uQuestionA} {QuestionB : Type uQuestionB}
    {OutcomeA : Type uOutcomeA} {OutcomeB : Type uOutcomeB}
    [Fintype QuestionA] [DecidableEq QuestionA]
    [Fintype QuestionB] [DecidableEq QuestionB]
    [Fintype OutcomeA] [DecidableEq OutcomeA]
    [Fintype OutcomeB] [DecidableEq OutcomeB]
    (G : FiniteGame QuestionA QuestionB OutcomeA OutcomeB) : Prop

end MIPStarRE.QPBT
```
<!-- END F04A-GAME-SEMANTICS-SIGNATURES -->

The source-fixed bodies are:

- `strategyValue` is the four finite sums weighted by
  `(G.questionDistribution (x,y)).toReal`; the Bool predicate selects
  `Complex.re (inner Complex psi ((A_x_a tensor B_y_b) psi))` or zero.
- `StrategyWinsWithProbability G S nu` is `strategyValue G S >= nu`.
- `gameValue G` is
  `sSup (Set.range (FiniteDimensionalGameStrategy.value G))`.
- `ProjectiveStrategy` is pointwise idempotence of every Alice and Bob effect.
- `SymmetricGame` fixes both PMF and predicate exchange equalities;
  `SymmetricStrategy` fixes coordinate-swap state equality and equality of the
  two measurement families.
- `SupportCommutingStrategy` quantifies exactly over pairs with
  `G.questionDistribution (x,y) != 0` and all outcomes.
- `ConsistentStrategy` applies the inherited `MeasurementConsistentOn` to every
  Alice and every Bob measurement on the shared state.
- `PCCStrategy` is projective and consistent and support-commuting;
  `SPCCStrategy` is PCC and symmetric.
- `schmidtRank psi` is
  `Matrix.rank (fun i j => psi (i,j))`.
- `entanglementRequirement G nu` is the `sInf` of the `WithTop Nat` bounds `d`
  for which a canonical finite-dimensional strategy has value at least `nu`
  and Schmidt rank at most `d`. `WithTop.sInf_empty` is `top`, matching the
  paper's infinity clause.
- `HasValueOnePCCStrategy G` quantifies one common `Fin dim` local carrier and a
  PCC strategy whose exact value is one.

These formulas were included, with bodies, in the successful probe. The
displayed signature block intentionally has declarations without bodies so it
can serve as a stable callable manifest; no `axiom`, `constant`, `opaque`, or
`sorry` was used by the probe.

## F07A dependency disposition

After this node exists, the exact direct prerequisites for
`F07A-DETYPING` are:

```json
["F04A-GAME-SEMANTICS", "F07-TYPED"]
```

F04A transitively supplies F03, F04-DISTANCE, and F04-CONSISTENCY. F07
transitively supplies F06. The detyping node therefore does not need redundant
direct edges to F03, F04, or F06. It still owns typed verifier/game formation,
graph simulation, detyping definitions, the published error factor, Ent
transfer, and executable clauses; F04A supplies only the reusable game and
strategy vocabulary.

## Exact QPBT-041 through QPBT-043 issue chain

```text
QPBT-041 - feat(QPBT/Basic): complete finite strategy and consistency semantics

kind: formalization
execution_category: implementation
parent_id: QPBT-000
dependency_ids: [QPBT-032]
owned_paths: [MIPStarRE/QPBT/Basic/Approximation.lean]
source_refs:
  - blueprint/metadata/nodes.json#F04-DISTANCE
  - blueprint/metadata/nodes.json#F04-ASYMPTOTIC
  - blueprint/metadata/nodes.json#F04-CONSISTENCY
  - blueprint/metadata/nodes.json#F04-DISTANCE-LAWS
  - workflow/reviews/qpbt-023-leaf-contract-a04.md

QPBT-042 - feat(QPBT/Game): implement finite game and strategy semantics

kind: formalization
execution_category: implementation
parent_id: QPBT-000
dependency_ids: [QPBT-041]
owned_paths: [MIPStarRE/QPBT/Game/Semantics.lean]
source_refs:
  - blueprint/metadata/nodes.json#F04A-GAME-SEMANTICS
  - strategies-distance.tex:4-51,62-81,126-190
  - workflow/reviews/qpbt-023-leaf-contract-a04.md
  - workflow/reviews/qpbt-035-game-semantics-api-a08.md

QPBT-043 - feat(QPBT/Game): formalize graph simulation and verifier detyping

kind: formalization
execution_category: implementation
parent_id: QPBT-000
dependency_ids: [QPBT-038, QPBT-042]
owned_paths: [MIPStarRE/QPBT/Game/Detyping.lean]
source_refs:
  - blueprint/metadata/nodes.json#F07A-DETYPING
  - types.tex:197-579
  - workflow/reviews/qpbt-035-detype-source-a05.md
  - workflow/reviews/qpbt-035-game-semantics-api-a08.md
```

QPBT-041 acceptance gates:

1. Own only the existing `MIPStarRE/QPBT/Basic/Approximation.lean` path and
   preserve the integrated F03 declarations byte-for-byte except for imports or
   namespace context strictly needed by the accepted continuation.
2. Implement the remaining accepted F04-DISTANCE, F04-ASYMPTOTIC,
   F04-CONSISTENCY, and F04-DISTANCE-LAWS callable manifests from
   `qpbt-023-leaf-contract-a04.md`, including `PureStrategy` and
   `MeasurementConsistentOn`; do not reopen their reviewed signatures.
3. Add no `sorry`, axiom, constant, obligation input, or generic bridge
   assumption; pass scoped Lean, target build, declaration/source sync, debt and
   assumption scans, one private full build, and fresh immutable review.

QPBT-042 acceptance gates:

1. Own only `MIPStarRE/QPBT/Game/Semantics.lean`; import and reuse the accepted
   `PureStrategy` and `MeasurementConsistentOn` APIs without editing or
   redefining them.
2. Implement all 18 F04A callable names with the exact domains and formulas
   above, including support-relative commutation, shared-space PCC, canonical
   finite-dimension quantification, the exact strategy value, and real `sSup`.
3. Define Schmidt rank as coefficient-matrix rank and Ent as `WithTop Nat`
   `sInf`; prove the finite coordinate/reindexing facts needed for this boundary
   rather than adding a public representation or invariance assumption.
4. Add no `sorry`, `axiom`, `constant`, generic assumptions, obligation input,
   executable machine claim, or cost-model claim.
5. Pass the scoped Lean check, target build, debt/assumption/import scan,
   declaration/source synchronization, one private full build, and a fresh
   immutable mathematical/API review.

QPBT-043 acceptance is the A05 source inventory: implement every F07A callable,
both graph-event conclusions, all five published detyping clauses, exact level
and dimension relations, and the executable cost/description clauses without
public obligations or hidden assumptions. Its QPBT-038 edge supplies F06/F07;
its QPBT-042 edge supplies the reusable game/value/PCC/Ent layer.

This exact chain is material. QPBT-032 alone is not a sufficient dependency for
Semantics because it intentionally implemented F03 only. All three issues are
children of QPBT-000, not QPBT-014, so QPBT-014 remains closable after its
accepted QPBT-035 through QPBT-040 wave.

## Statement integrity

| Paper item | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| Game | Four finite alphabets, distribution on question pairs, Boolean predicate | Explicit finite decidable types, PMF, Bool | The game tuple | Same data | exact |
| Tensor strategy | Normalized finite bipartite pure state and two POVM families | Accepted `PureStrategy`, wrapped without new data | A strategy for the game's alphabets | Same strategy tied to `G` by its type | faithful boundary |
| Fixed-strategy value | Four finite sums of PMF, predicate, and tensor-effect expectation | PMF `toReal`, `Complex.re`, matrix Kronecker/local action | `val*(G,S)` | Same order and formula | exact finite-coordinate encoding |
| Game value | Supremum over all finite tensor strategies | `sSup` over `Fin da`, `Fin db` representatives | `val*(G)` | Same supremum | faithful boundary |
| Projective/symmetric | Pointwise projectivity and player-exchange symmetry | Effect idempotence, coordinate swap, effect equality | Same predicates | Same predicates | faithful boundary |
| Commuting/consistent/PCC/SPCC | Common local Hilbert space; PMF support; exact state-action consistency | One coordinate type, nonzero PMF support, inherited exact consistency | Same conjunctions | Same conjunctions | exact finite-coordinate encoding |
| Schmidt rank | Least tensor decomposition rank | Rank of coefficient matrix | Schmidt rank | Equal finite-dimensional invariant | faithful boundary |
| Ent | Minimum attainable rank bound, infinity if unattainable | `WithTop Nat` `sInf` over exact value/rank bounds | `Ent(G,nu)` | Same minimum/infinity behavior | faithful boundary |

## Authentication and probe results

- Immutable detached HEAD:
  `3f2630a7631a0164b6ef4aca1fd081ba264beeb2`.
- Immutable tree:
  `4effdd7686905e59c188b70c71b04a6cb46e8b21`.
- Worktree `/tmp/qpbt-035-game-semantics-a08` remained clean; no candidate
  byte was changed.
- Candidate metadata SHA-256:
  `0977ed07a22c1a3730e4fa2e6b112c3166deaf402d42b1a516cac9699a38b64c`.
- Candidate F03-only `Approximation.lean` SHA-256:
  `13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a`.
- Authenticated A03/A04/A05 report SHA-256 values:
  `a1ed48ff7a642c8811f56d1aa77caec32e3cf1608a33dd474fffb16b367e4caf`,
  `a55e7789d6a899b31e6fc8625dfb6116c9430884fb2ce83fc6e1182bb2d3225e`,
  and `de9c4c87820f76c8162f7d2f06bbcd0a66a6ed14cc8d57ed2c6d1414bccd81fb`.
- Accepted F04 contract report SHA-256:
  `45dfbb3142df500eff3260d89055c4763c543036d62fad2ff3b32c9b036b0f0f`.
- Authenticated upstream `Quantum/Measurement.lean` SHA-256:
  `c84a712e34425a46ae17d9f04d789ae7393ae97da3cf7ee3f93fe0e6705b9d0d`.
- Authenticated upstream `Quantum/FiniteMatrix/Basic.lean` SHA-256:
  `09f00e0a381ce51f99dd9c583ececaaf8ff0f8c1c40ed2e102d7eda5599f90f3`.
- Mathlib commit:
  `81a5d257c8e410db227a6665ed08f64fea08e997`.
- Final bounded probe: 482 lines, 21,631 bytes, SHA-256
  `ab22cecd1ced868fef8b1bbe4daf81c1604f60e3fe6cd1fd003a91edac16c5e7`.
- Probe 1, the direct finite boundary including `sSup`, matrix rank, Ent, and
  PCC/SPCC: exit 0 in `20.42094839` seconds.
- Probe 2, the no-move wrapper and inherited consistency design: exit 0 in
  `4.924658653` seconds.
- Probe 3, the complete revised no-move predicate surface: exit 0 in
  `4.901597632` seconds.
- Exact command for all three attempts:
  `lake env lean /tmp/qpbt-035-game-semantics-probe-a08.lean`, run against the
  authenticated hot-main materialization. No target or full build was run.

## Session metrics

- Durable dispatch start: `2026-09-01T14:59:14.143025Z`.
- Evidence cutoff: `2026-09-01T15:13:32.027396270Z`.
- Elapsed to cutoff: `857.884371270` seconds.
- Token usage: `null`; the collaboration backend does not expose per-agent
  token usage.
- Topology: one scout, zero nested agents.
- Actions: 3 bounded Lean probe attempts, all passed; 0 target/full builds; 0
  cache warm/seed/publication actions; 0 repository edits; 0 Git writes; 0
  canonical state/metrics/research edits; 0 network, endpoint, GitHub, or
  credential operations; 0 nested-agent launches; 3 temporary probe edits; 1
  `/tmp` report written.
- Early coordination: one initial recommendation sent to root and A07, then one
  explicit corrected no-move recommendation sent to both after the integrated
  ownership constraint was supplied.
- Report SHA-256: supplied out of band after the final bytes are written.
