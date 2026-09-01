# QPBT-026 semantic integration prototype review A25

## Verdict

`approve`

No findings.

The exact semantic prototype commit
`8ee49bcca504ccb02ffcb4852f63ca2d2f8fbbd4` faithfully composes the QPBT-027
confirmation-ledger contract with the QPBT-026 disclosure and offline-isolation
contract. The production path remains fail-closed before task/context reads,
probes, evidence/output creation, lease claim, command construction, or runner
invocation, while the only successful review execution path is explicitly
offline, requires an injected non-`codex` runner and validated copied capability
record, constructs and verifies a fresh projected evidence repository, and
records that it is neither externally launchable nor host-isolated.

This is a review of the exact immutable semantic integration prototype only. It
is neither a formal PR-ledger review nor approval of the later activation
object.

## Authentication

- Detached clean HEAD:
  `8ee49bcca504ccb02ffcb4852f63ca2d2f8fbbd4`.
- Tree: `d1651f29f41d555859838a088726f03ac869d541`.
- Ordered parents:
  `(710cfafd586172d3658499f3552c2ae5e27fe512, 5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a)`.
- Unique parent merge base:
  `ea584e9e894391773e09ddad2ce4d082497c7913`.
- The second parent is an ancestor of the reviewed merge.
- The complete first-parent manifest is exactly four modified paths:
  `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/local_agent.py`, and `tests/test_local_agent.py`.
- The Python result blobs exactly equal the second-parent candidate blobs:
  `25a5198e9b3c7e3ace8c6365b7064e8aa55dc506` and
  `f8b51e87f2e1d7ac5fc40d55b0c415b95cebf824`.
- Workflow state, metrics, events, canonical evidence, and the QPBT-027 Python
  workflow implementation/tests are byte-identical to the first parent.
- The five shared QPBT-026 reports have identical blobs across parent 1,
  parent 2, and the result, matching the A22 manifest.
- `git diff --check` passed; no conflict/reject artifacts were found; final
  porcelain status was clean.
- Post-target reports authenticated before use:
  A23 SHA-256
  `8d83df10c405015e6986e443af61771f0daad0442df73899156318d8c5baaf2c`;
  A24 SHA-256
  `3d120c8f166078e160ddf04f28f66a3029325e443428f59fc296dbd1d1a42c6c`.

## Review scope

I independently inspected both protocol blobs, the complete first-parent
Python diff, relevant call sites, and the adversarial tests. In
`protocols/review.md:190`, the merged findings-ledger section preserves
immutable resolution data, optional unique chronological same-PR independent
terminal confirmations, append-only review and confirmation lists, exact
current-base/head approval, and rejection of non-approving reconfirmations. In
`protocols/review.md:32`, the merged disclosure section preserves transport and
content separation, exact fail-closed production ordering, rename endpoint and
credential screening, explicit transport configuration, fresh offline evidence
projection, minimal Git/runner environment, and the absence of a replayable
production capability.

The changelog retains the complete QPBT-027 block followed by the complete
QPBT-026 block and existing history. The implementation and tests substantiate
the protocol rather than merely documenting it. I found no correctness,
security, fail-closed, composition, or test-adequacy defect in this exact
prototype.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py`: PASS, 70/70.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'`: PASS, 63/63.
- `PYTHONPYCACHEPREFIX=/tmp/qpbt-026-integration-review-a25-pycache python3 -m compileall -q scripts tests`: PASS.
- `python3 scripts/workflow.py validate`: PASS, 29 issues, 17 PRs, 0 planned,
  344 issued, 7 stages.
- `python3 scripts/check_workflow.py --skip-tests`: PASS.

Per assignment, aggregate Python and blueprint lanes were not duplicated. The
remaining risk is limited to those coordinator-owned lanes and to the separate
formal PR-ledger and activation reviews explicitly outside this verdict.
