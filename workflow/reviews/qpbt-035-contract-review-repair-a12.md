# QPBT-035 contract review repair (A12)

Session: `i035-orchestrator-a12-contract-review-repair`

## Authentication and scope

- Authenticated base: `c35fcd36bea96705851655852eabc78ca9db9b3f`.
- Authenticated base tree: `86d8ca78d3e4bb5fe89d57f25c2bea539d4c8100`.
- Branch: `issue/qpbt-035-q014-contract-a01`.
- The worktree was clean before the repair.
- Canonical start: `2026-09-01T16:03:54.407557Z`.
- Final commit, tree, path-sorted manifest hash, and report hash are returned in
  the terminal session envelope because a report cannot contain its own commit
  or blob hash without changing them.

Only the following review-repair files changed: the canonical blueprint
metadata, checker, focused tests, deterministically generated graph/DOT/chapter
02 output, and this report. Chapter 03 remained byte-identical. No Lean source,
signature manifest, prior review, canonical state, metric, protocol, cache,
dependency, endpoint, network, or GitHub file was changed.

## Pinned source evidence

The orchestrator independently read the already materialized, ignored pinned
source tree at `/home/drx/MIPStarRE-auto/references/2001.04383v3`; it did not
materialize or fetch anything. `reference_source.py verify` authenticated 39
files and 646 labels with inventory SHA-256
`04548808c30c476e9b2b7cb2f728a6d0c348a6706a8ed1bc9fb9945f20a124f4`
and ready SHA-256
`4d6a33759051b17428b3928d529d18e10da82e3bc09c75fbe429df324612b360`.

| Pinned file | SHA-256 | Relevant source |
| --- | --- | --- |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` | lines 553-560 define binary-string representations; 572-600 define the six-input dimension/marginal/linear/factor query machine and step count; 630-680 define executable downsizing and its runtime equation; 708-710 prove the overhead |
| `dependencies/types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` | lines 57-195 define the typed source layer; 95-195 contain the seven-input sampler, downsizing runtime, and typed decider; 197-579 define typed games, graph simulation, detyping, runtime, and descriptions |
| `qpbt/qpbt-parameters.tex` | `e6b5229b597bc27403acd9e71c9d2965b97727045fe71e3f5371b5ddf3b5e7f6` | lines 73-84 own only canonical tuple computation; lines 85-127 own the three QPBT-specific decider/CL complexity items, not the generic sampler boundary |
| `split-manifest.json` | `052cfaceb2e4a7b59778936ceb3daea9a33e3592e01b902cb2a9740c58999a20` | deterministic split contract |
| `source-pin.json` | `66a1e9db74f1454ce50909728a3b741f9da468b5d61902645557793ceb91ac9c` | arXiv `2001.04383v3` pin |

The downstream G02 consumer remains the pointwise-finite instantiation: its
question and answer sigma fibers have explicit finite codecs. That consumer
fact does not justify a generic F07 finiteness assumption.

## Finding dispositions

| Immutable A11 finding | Disposition | Repair evidence |
| --- | --- | --- |
| `F-LPR023-003`: F07 implied that arbitrary dependent question/answer/decider fibers were finite through `finite typed samplers and deciders` | **Resolved** | F07 now limits content-fiber finiteness to the constant `FieldVector` sampler carrier while separately retaining finite type/edge support. Dependent question, answer, and decider fibers are unrestricted; G02 alone supplies pointwise-finite consumer families. The exact map and mutations cover plural, reversed, conjoined, and disclaimer-hidden variants. |
| `F-LPR023-004`: F06 fidelity disagreed with its integrity verdict | **Resolved subfinding** | F06 fidelity is now `faithful-boundary`; the checker freezes agreement with the `faithful boundary` integrity verdict. |
| `F-LPR023-004`: F06 sent its generic executable sampler/query/downsize debt to owners without its source or callables | **Open; dedicated node/issue required before re-review** | A12 removes the false F07A/QPBT-043 and K03/K04 ownership claim. F07A/QPBT-043 now owns only typed/detyping machine clauses sourced to `types.tex:197-579` and transitive F07 typed interfaces; K03/K04 own neither layer. No current node owns `conditionally-linear.tex:553-710` with exact callable names. A root-created issue must add a dedicated node with exact `def:sampler`, `def:downsize_sampler`, and `lem:downsize_sampler` anchors and freeze callables for encoding, six-input queries, sampler distribution/step count, executable downsize correctness/dimension, and its `O(TIME_S(n) log q(n))` cost. A12 does not claim this gap is discharged by prose. |
| `F-LPR023-005`: A07 used shortened stable token `i035-scout-a08-game-semantics` | **Resolved as immutable-history alias** | Immutable A07 is unchanged. This report records that token as a historical alias for canonical stable name `i035-scout-a08-game-semantics-api`; no second session is implied. |

The F06, F07, and F07A callable-name lists and A04/A07 signature manifests are
unchanged. No Lean signature probe was run because the dispatch allowed probes
only if signatures changed.

## Statement integrity

| Node | Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- | --- |
| F06 | Finite coordinate field spaces; recursive complementary factors; executable binary-string CL sampler and downsizing machine | Concrete finite field vectors, recursive certificate, mathematical PMFs, and `FieldData` only for downsize; no machine/cost model yet | Mathematical CL operations plus the six-input executable sampler, downsizing machine, and runtime relation | Mathematical CL operations, direct-sum PMF, and downsize pushforward; the generic executable representation/cost layer is an explicit unowned boundary pending a dedicated source/callable issue | faithful boundary |
| F07 | Finite type graph; typed Turing sampler/decider; typed downsize and runtime | Finite type/edge support and constant `FieldVector` sampler carrier; arbitrary dependent question/answer/decider fibers; mathematical PMFs | Typed graph/sample semantics, typed sampler/decider machines, downsize dimension/runtime | Graph/sample/downsize PMF and total dependent decider; executable representation/cost debt remains explicit at F07A/QPBT-043 | faithful boundary |
| F07A | Finite nonempty graph, typed verifier/game, graph simulation, detyping, PCC/value/Ent semantics, and typed/detyping executable costs | F07 unrestricted dependent fibers, F04A finite game semantics, exact graph-event layer, and the `types.tex:197-579` machine/cost model QPBT-043 must freeze | Exact graph event/law; detyping; completeness/soundness/Ent; level/dimension; typed sampler/decider/description costs | Same 20 callable owners and formulas for the typed/detyping layer; the generic CL sampler/query/downsize layer is explicitly outside this node | faithful boundary |

## Checker and generation

The checker now fails closed on any drift in the exact F07 finiteness contract,
requires F07A's unrestricted-fiber assumption, requires F06 fidelity/integrity
agreement, freezes F06's dedicated-node gap, and limits F07A executable
ownership to its typed/detyping source boundary. The existing exact source
anchors, prerequisites, callable lists, and non-detyping K03/K04 callable
contracts remain unchanged.

Generation was run twice for the initial repair and twice after the root audit.
The final pair was byte-idempotent:

| Generated output | SHA-256 before and after second write |
| --- | --- |
| `blueprint/generated/graph.dot` | `95d35ce1b385cd77796237fef3be0f4f9c842bb18623cca27b26f001879337c3` |
| `blueprint/generated/graph.json` | `d4ab439c75321521bcc4801ec64889c086684fce08d988e19deefcb3af73dd9b` |
| `blueprint/src/generated/chapter-02-entries.tex` | `5d4f3fc0074ecadc89e68636296888bf488b68b16e3f9a0b91172add10682e26` |
| `blueprint/src/generated/chapter-03-entries.tex` | `afdb38a9cc4321d5be450ddcf0881bc655d3df0d7257a48acf20491491e4807f` (unchanged) |

## Validation

| Command | Result | Instrumented elapsed |
| --- | --- | ---: |
| `python3 -m unittest discover -s blueprint/tests -p 'test_*.py'` | 30/30 passed | 1.03 s |
| `python3 blueprint/check.py --check` | 53 nodes, 12 chapters, acyclic and deterministic | 0.09 s |
| `python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | exact pinned-source gate passed | 0.09 s |
| `python3 scripts/reference_source.py verify --reference-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | verified 39 files and 646 labels | 0.13 s |
| `python3 scripts/workflow.py validate` | valid | 0.12 s |
| `python3 scripts/check_workflow.py --root .` | 336/336 passed | 178.12 s |
| focused two-test repair gate | 2/2 passed | 0.35 s |
| second `python3 blueprint/check.py --write` | passed; all four generated hashes unchanged | 0.08 s |
| pre-audit post-report blueprint unit suite | 30/30 passed | 0.88 s |
| pre-audit post-report exact pinned-source gate | passed | 0.09 s |
| pre-audit post-report `workflow.py validate` | valid | 0.12 s |
| pre-audit post-report `check_workflow.py --root . --skip-tests` | valid | 0.12 s |
| post-audit blueprint unit suite | 30/30 passed | 0.98 s |
| post-audit default deterministic check | passed | 0.08 s |
| post-audit exact pinned-source gate | passed | 0.09 s |
| post-audit `workflow.py validate` | valid | 0.12 s |
| post-audit second generation write | passed; all four final hashes unchanged | 0.08 s |
| post-audit `scripts/check_workflow.py --root .` | 336/336 passed | 176.50 s |
| `python3 -m py_compile blueprint/check.py blueprint/tests/test_check.py` | passed | not separately instrumented |
| `git diff --check` and owned-path inspection | passed | not separately instrumented |

No Lean check, target build, full build, cache warm/seed, materialization,
network request, endpoint call, or GitHub operation occurred. Compile attempts,
build attempts, cache actions, and Lean signature probes are all zero.

## Topology and instrumentation

- Topology: one writable orchestrator with one depth-1 read-only scout spawned
  during A12, stable name `i035-scout-a12-f06-f07`, external collaboration ID
  `/root/i035_contract_repair_a12/i035_scout_a12_f06_f07`. It was not an
  existing prior reviewer.
- Subagents: 1 dispatched, 1 completed, 0 writes, 0 nested subagents.
- Immutable findings dispositioned: 3; F-LPR023-003 resolved,
  F-LPR023-004 narrowed but open pending a dedicated root-created issue, and
  F-LPR023-005 resolved by an explicit historical-alias record.
- New focused adversarial test method: 1; adversarial mutation cases: 13.
- Generation attempts: 4 successful; idempotence mismatches: 0.
- Validation failures after the final repair: 0.
- Orchestrator token usage: `null` for input, cached input, output, reasoning
  output, and total. Availability reason: the collaboration backend does not
  expose the current agent's cumulative token counters.
- Scout token usage, read from its completed local rollout: input `2,089,907`,
  cached input `1,932,032`, output `23,670`, reasoning output `17,567`, total
  `2,113,577`. These are exact exposed cumulative counters, not estimates.

The scout started at `2026-09-01T16:04:06.179Z`, completed at
`2026-09-01T16:14:18.069Z`, and elapsed `611.890s`. Its exact dispatch was:

> You are read-only scout i035-scout-a12-f06-f07 under orchestrator
> /root/i035_contract_repair_a12. Work only by reading
> /home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-035-q014-contract-a01
> at authenticated HEAD c35fcd36bea96705851655852eabc78ca9db9b3f and tree
> 86d8ca78d3e4bb5fe89d57f25c2bea539d4c8100; stop if mismatched. Read
> AGENTS.md. Do not edit, build, cache, materialize, network, or touch
> state/metrics. Independently inspect pinned
> references/2001.04383v3/sections/dependencies/conditionally-linear.tex and
> types.tex, blueprint metadata/checker/tests/generated consumers, and report
> exact source-supported repairs for: (1) all places implying F07 arbitrary
> dependent decider/question/answer fibers are finite, including adversarial
> plural/conjoined phrasings checker should reject; constant finite FieldVector
> sampler carrier is allowed; (2) F06 fidelity mismatch and false K03/K04
> deferral, identifying concrete executable representation/cost obligations and
> whether F07A/QPBT-043 is the honest owner. Preserve callable signatures unless
> source inspection requires change. Return path:line findings, recommended
> exact wording/checker predicates/tests, commands/timings, token availability,
> and no-edit cleanliness.

The scout authenticated the clean base, ran source authentication in `0.2s`,
and passed its read-only 29-test blueprint suite in `0.94s`. Its final
`blueprint/check.py --check` observed generated drift in `0.09s` because the
orchestrator was concurrently updating generated consumers; that observation
was expected and not a scout defect. It made zero edits and performed no build,
cache, materialization, network, or nested-agent action. It wrote no `/tmp`
report; findings returned only through collaboration. Its worktree lacked the
gitignored materialized TeX tree, so it reported that limitation. The
orchestrator separately inspected and verified the canonical materialized
pinned tree read-only. The scout independently recommended the exact-map guard
adopted here.

Three transient tooling events were contained. First, one
multi-file `apply_patch` request was rejected before mutation because it named
the checker twice. Second, an underspecified metadata hunk briefly changed
F02's fidelity; the immediate diff inspection detected it, and an ID-anchored
hunk restored F02 and changed F06 instead. The resulting lesson is to anchor
repeated metadata fields by node ID and to use one update block per path. No
off-scope change survived, no validation ran against that transient state, and
no protocol file was changed in this bounded review repair. Third, the first
local stage/amend command failed before index mutation because the managed
sandbox exposed the linked-worktree Git index read-only. The identical
explicit-owned-path command succeeded under the approved Git escalation; no
path selection changed.
