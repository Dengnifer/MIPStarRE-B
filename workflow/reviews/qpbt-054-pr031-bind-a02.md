# QPBT-054 / LPR-031 candidate binding

Session `i054-integrator-a02-pr031-bind` authenticated the immutable QPBT-054
candidate for no-byte-change adoption by `LPR-031`.

## Identity

| Item | Authenticated value |
| --- | --- |
| Base / sole parent | `639c883737e07b91156a9cbc31ec1aa65100a935` |
| Candidate head | `83062f78cc52ecf0edf0e725c00850fb458721b5` |
| Candidate tree | `5e946206cb60ad88e2df37eaec49f8f1922ffa3d` |
| Binary patch SHA-256 | `b3fca84ea6dda5beba17b5815eb94218aa4d58de4e13a2e5c91a9c6c45635373` |

The candidate branch and registered worktree both resolve to the exact head.
The commit has the declared sole parent and exactly the six paths below. The
candidate worktree is clean, and `git diff-tree --check` reports no defect.

| Changed path | Git blob | File SHA-256 |
| --- | --- | --- |
| `blueprint/check.py` | `719f68185e9bbb66e66255787ea00849972cf1e0` | `32958aeb497558a7619e01d66ca204e3da90496400724939715f83a58af6053c` |
| `blueprint/generated/graph.json` | `302a495f29d0932a48488397c486476a051fd8ca` | `470b7cc9f250d4280725db0dd78c78f24c88f10397c6859ef1c802119139aa0c` |
| `blueprint/metadata/nodes.json` | `70e4d1f747562209bd34926af34eca958743edb3` | `b0fb145e6a6c6b09e4fe10cbb7469de03300e707320903b7f9ef3abbadf20866` |
| `blueprint/src/generated/chapter-02-entries.tex` | `d8418da55d63b46a592636108b836db2172eacda` | `02376d6841300e7baf9881286c96a0ab39a644a9138c46571f0937e89883dad4` |
| `blueprint/tests/test_check.py` | `261e77c483bb0b1556f4485ca3de85d8a390d7d0` | `308b707b9c77bb05b56144b37b090d416258612721e416c117ef707e8483c4eb` |
| `workflow/reviews/qpbt-054-f06a-contract-a01.md` | `013a75a46d106e09c7841c25ba5c9e3f6839da55` | `8059cfbd230f1ce5bcf8c1cba2d18267859ecdd59d0d9f62c11e8e76da81bd9c` |

`blueprint/generated/graph.dot` is in QPBT-054's writable manifest but is
byte-identical across the candidate and therefore correctly absent from the
changed-path set.

## Canonical binding

At immutable canonical checkpoint
`97062bb75de85cf6b241b7af7ec080ef2e73f9e1`, `LPR-031` is ready and binds the
same base, head, branch, six changed paths, and QPBT-054 issue. All 5/5
registered checks are passed on that exact base/head pair: immutable candidate
authentication, whole-block Lean signature elaboration, blueprint checks and
regressions, source/workflow authentication, and contract/generated-output/diff
hygiene. Each check points to the exact A01 report above. QPBT-054 remains in
review with its expected owner and exact owned-path superset.

The marker-delimited F06A signature block was independently extracted from the
committed report and hashes to
`0e376f7539828c204b37ea88ad8f7330ad699a57c216ebe4d02397c5753b5948`.
That exact path, marker pair, and hash occur in the committed metadata; the
checker and both generated consumers retain the same contract. Together with
the clean worktree and exact content identities above, this confirms that the
candidate semantics remained unchanged during binding.

## Disposition and counters

Adopt exact head `83062f78cc52ecf0edf0e725c00850fb458721b5` in
`LPR-031` without changing candidate bytes, then obtain the required fresh
immutable mathematical/API review. This session made one report-file change
and zero candidate changes. It ran zero Lean/Lake/build/cache/materialization
actions, made zero network/GitHub/credential operations, and spawned zero
nested agents.
