# QPBT-026 semantic prototype root validation

## Scope

Root independently validated immutable semantic prototype
`8ee49bcca504ccb02ffcb4852f63ca2d2f8fbbd4`, tree
`d1651f29f41d555859838a088726f03ac869d541`, with ordered parents
`710cfafd586172d3658499f3552c2ae5e27fe512` and
`5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.

The first-parent delta is exactly four modified paths:

- `protocols/CHANGELOG.md`
- `protocols/review.md`
- `scripts/local_agent.py`
- `tests/test_local_agent.py`

The two Python blobs exactly match the LPR-016 candidate. The worktree was
porcelain-clean, the ordered parents and tree matched A23, and
`git diff --check HEAD^1..HEAD` passed.

## Results

| gate | result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` | PASS, 336/336 in 199.317 s |
| `make -C blueprint test check graph` | PASS, 26/26; 48 nodes, 12 chapters, acyclic and deterministic |
| `python3 scripts/workflow.py validate` | PASS |
| `python3 scripts/check_workflow.py --skip-tests` | PASS |

The aggregate and blueprint lanes were root-owned and were not duplicated by
A25. No Lean source, pin, declaration list, or build recipe changed, so this
workflow-only prototype gate used no Lean/Lake build or hot-main cache action.

This evidence validates the semantic prototype only. The final activation
object has a later first-parent tree containing canonical evidence, so A24's
protocol requires newly observed aggregate, blueprint, compile, workflow, and
identity gates on that exact object before its separate activation audit.
