# QPBT-031 Field Skeleton

Session: `i031-orchestrator-a01-field-skeleton`
Issue: `QPBT-031`
Role: field-lane orchestrator/writer
Status: candidate complete

Measured implementation session elapsed approximately 8 minutes from the first
worktree/cache operation through candidate commit; the orchestration service's
external session-start timestamp was not exposed.

## Immutable input and ownership

- Base HEAD: `259c73a368ef7403b4e36e190c9bf940497b300f`
- Base tree: `b3a404a012f9f120f1fa5fa692e51b92d000d615`
- Worktree: `.workflow-runtime/worktrees/qpbt-031-field-a01`
- Owned implementation path: `MIPStarRE/QPBT/Basic/Field.lean`
- Owned report path: `workflow/reviews/qpbt-031-field-skeleton-a01.md`
- No other tracked or untracked authored paths were changed.

The source contract was read from `blueprint/metadata/nodes.json` (`F01-FIELD`),
the immutable F01 signature manifest in
`workflow/reviews/qpbt-023-leaf-contract-a04.md`, and
`docs/paper-gaps/self-dual-normal-basis.md`. The pinned MIPStarRE archive was
materialized offline with SHA-256
`656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.

## Implementation

`Field.lean` contains the exact frozen imports and declarations:
`FieldData`, `fieldDataOfOddExponent`,
`fieldData_nonempty_of_odd`, `fieldTrace`, `FieldData.coordinates`,
`FieldData.multiplicationMatrix`, and
`FieldData.multiplicationMatrix_mulVec_coordinates`.

The only proof debt is the source-faithful G16 selector
`fieldDataOfOddExponent`; the coordinate/multiplication identity is proved via
`LinearMap.toMatrix_mulVec_repr`, and the nonempty theorem is derived from the
selector without another obligation.

## Validation

| Check | Result |
| --- | --- |
| Private hot-main seed | cache key `d71a99abea8f7ebf5bda5194dfef088b06f526230caf5ccbca34d62d5b4267b9`; hit; 67.078540 s |
| Offline source materialization | 7.968887 s; 337 files; inventory `d8d9e7632f5dcdb0cbe7bceeb55c71a0dbbcf6f901c6efd7f4c4814090d096db` |
| Scoped Lean check | `lake env lean MIPStarRE/QPBT/Basic/Field.lean`: pass; 1 warning for declared G16 `sorry` |
| Proof-debt scan | exactly one `sorry`, at `fieldDataOfOddExponent`; no `axiom` or `constant` |
| Blueprint tests | `python3 blueprint/tests/test_check.py`: 28/28 pass |
| Workflow validation | `python3 scripts/workflow.py validate`: valid |
| Diff check | `git diff --check`: pass |

No full project build was run in this issue lane; the immutable hot-main build
was already warmed by the singleton builder and the private `.lake` cache was
seeded before the scoped check. Exposed token usage is unavailable and is
recorded as `null` rather than estimated.

## Statement integrity

| Paper/F01 assumption | Lean assumption | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| Positive odd `k`; concrete `F_(2^k)/F_2` | `k : Nat`, `hk : Odd k`; `GaloisField 2 k` and its instances are derived | Simultaneous self-dual normal basis exists; deterministic algorithm is separate K03A obligation | `FieldData k` exposes normality and trace-self-duality; selector is the single tracked G16 hole; algorithmic K03A claim is not asserted here | faithful boundary |
