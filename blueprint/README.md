# QPBT Lean Blueprint

This is the speculative, source-faithful blueprint for the quantum Pauli basis
test in arXiv:2001.04383v3. It remains provisional until `QPBT-002` and
`QPBT-009` are accepted. The blueprint contains no copied author TeX and makes
no claim that a planned Lean declaration exists.

`metadata/nodes.json` is the canonical declaration and dependency graph.
`metadata/gaps.json` records every source-facing repair, and
`metadata/external-sources.json` records exact external trust boundaries. Run:

```sh
python3 blueprint/check.py --check
python3 blueprint/check.py --check \
  --source-root .workflow-runtime/worktrees/qpbt-002/references/2001.04383v3
python3 -m unittest discover -s blueprint/tests -p 'test_*.py'
make -C blueprint pdf
```

For every node, `transitive_definitions` is the sorted set of definition-kind
nodes in its strict prerequisite closure. The checker derives this closure and
rejects missing, extra, or theorem-valued entries. It also rejects unresolved
external theorem pins on the soundness dependency path. `EXT-TENSOR` records
the official arXiv metadata contract for `2111.08131v3` (published version,
last revised 2022-12-06); this pins the source boundary but does not claim its
theorem has been proved in Lean.

The source-root gate verifies each generated-file anchor and its corresponding
original `compression_arXiv_v3.tex` line using the split manifest. `--write`
regenerates `generated/graph.json`, `generated/graph.dot`, and the TeX entry
fragments. `--check` fails if any generated output is stale.

The PDF is written to `blueprint/build/main.pdf`. Build products and the
Graphviz SVG are ignored. The PDF target verifies that all planned Lean
identifiers remain extractable and that no extracted word crosses a physical
page boundary. The tracked DOT and JSON are deterministic review artifacts.
