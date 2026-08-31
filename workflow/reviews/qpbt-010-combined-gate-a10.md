# QPBT Stage 2/3 combined acceptance-gate audit A10

- Session: `i010-scout-a10-combined-gate`
- Audited main: `fcd1aa928ac0263f83de37143dc8dc5f4d937210`
- Source report SHA-256: `b073ff387410ec7da142fa2d9c2022e51e700ce68ad5e1bf1bfde7a64ae2cd33`
- Elapsed: 659.198603 seconds

## Verdict

`65315213d047d9181804ad74d573f533c904ef4f` is the historical second-commit
equivalent. It integrated LPR-001, LPR-002, and LPR-004 in order and is the
common `integration_sha` in all three PR records. No replacement or empty
second commit is required.

Issue closure requires one fresh strict gate on a disposable checkout of the
current committed main snapshot. The gate must authenticate and materialize
the pinned source archive, verify the exact source inventory, run focused and
aggregate tests, check the blueprint against that materialization, force the
graph/PDF products, and prove no tracked mutation.

## Exact gate families

1. Bind exact current HEAD and ancestry of `65315213...`, LPR-002 head
   `63037dd...`, and LPR-004 head `3f4d4b3...`.
2. Prove the approved LPR-002 and LPR-004 path sets are unchanged.
3. Authenticate `/tmp/2001.04383v3-source.tar` as 233,859 bytes with SHA-256
   `d645cd51dd26cae59195e61aeeb5c886a254ef4adf15da7e5657ad90c7ec2174`.
4. Run `reference_source.py validate-contracts`, `inspect-archive`, isolated
   `materialize`, and `verify`.
5. Run 49 transport tests, 49 source tests, and 26 blueprint tests.
6. Run both deterministic blueprint checks, including `--source-root
   references/2001.04383v3`.
7. Run `make -C blueprint test check graph`, a clean PDF rebuild, and the PDF
   geometry/identifier checker.
8. Run `python3 scripts/check_workflow.py`, compileall, workflow validation,
   diff hygiene, clean tracked status, and ignored-product tracking checks.

All commands must pass in one isolated run. Expected semantic results are:

- source materialization: 39 files, 646 labels, inventory SHA-256
  `04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`;
- blueprint: 48 nodes, 12 chapters, deterministic outputs and exact anchors;
- PDF: 45 pages and 109 planned Lean identifiers, with positive word geometry
  and no disallowed overlap;
- focused tests: historical floors 49/49, 49/49, and 26/26;
- aggregate, compile, state, diff, and tracked-status checks: all clean.

The author source, split sections, graph SVG, and PDF are intentionally ignored
products. The strict gate uses blueprint `--check`, never `--write`, so stale
tracked artifacts fail instead of being repaired during acceptance. PDF bytes
are not a criterion because the renderer is not byte-deterministic; semantic
geometry and identifier extraction are authoritative.

## Isolation

Run in a disposable local clone. Put reference transaction output and Python
bytecode under the same temporary root. `reference_source.py materialize`,
Graphviz, latexmk, and compileall are the mutating commands and must never run
against the coordinator's live checkout for this gate. No Lean/Lake or hot
cache command belongs to this Stage 2/3 gate.

## Audit scope

The scout inspected issue/PR records, integration reports, blueprint and source
tools, exact Git ancestry, trees, and approved paths. It ran no acceptance
command, test, generator, PDF/build, Lean/Lake, network, warm/seed, runtime or
cache mutation, worktree creation, Git write, or repository edit. Token usage
is unavailable from the collaboration backend and was not estimated.
