# QPBT-039 / LPR-028 independent review A02

Session: `i039-reviewer-a02-parameters`

External identity: `/root/i039_reviewer_a02_parameters`

Role: fresh independent read-only Lean and source-fidelity reviewer. This
session neither implemented nor orchestrated the candidate.

## Findings

No findings.

Verdict: `approve`.

The sole candidate file is mathematically exact against the pinned paper,
the G01 contract, and blueprint node `G01-PARAMETERS`. The scoped Lean check,
kernel-visible declaration probe, debt scans, diff checks, and deterministic
blueprint/source check all pass. The inherited G16 `sorry` in the imported
field module is not referenced by either new declaration and is not candidate
proof debt.

## Statement integrity

| Paper assumptions | Lean assumptions | Paper conclusion | Lean conclusion | Verdict |
| --- | --- | --- | --- | --- |
| A natural-valued tuple `(q,m,d)` | One project-owned `MIPStarRE.QPBT.Parameters` value whose three fields are `Nat` | Admissible exactly when there exists an odd exponent `k` with `q=2^k` and `Dvd.dvd m q`; `d` is unconstrained | `Exists fun k : Nat => Odd k /\ params.q = 2 ^ k /\ Dvd.dvd params.m params.q` | exact |

Source comparison:

- `references/2001.04383v3/sections/qpbt/qpbt-game-and-soundness.tex:60-63`
  defines admissibility for `(q,m,d)` as admissible field size plus `m | q`.
- `references/2001.04383v3/sections/dependencies/finite-fields.tex:243-248`
  expands admissible field size to `q=2^k` for odd `k`.
- `workflow/reviews/qpbt-035-q014-contract-a02.md:399-415` fixes the exact
  declaration surface, and lines 423-429 record the G01 integrity verdict as
  exact.
- `blueprint/metadata/nodes.json#G01-PARAMETERS` fixes the same statement,
  project-owned encoding, exact import, public names, and zero owned sorries.
- `MIPStarRE/QPBT/Game/Parameters.lean:16-20` supplies exactly the three
  natural fields and `DecidableEq`; lines 27-29 preserve existential type,
  conjunction order, equality direction, and natural divisibility order.

The parameter `d` is intentionally unused by the predicate. There is no added
positivity condition, characteristic-two field witness, LDT alias, coercion,
bridge, residual, repair, witness package, producer, generic assumptions
bundle, implication premise, `sorry`, `axiom`, or `constant`. The sole import
is exactly `MIPStarRE.QPBT.Basic.Field`, as required by the blueprint. Module
documentation cites the exact paper path and `def:admissible`; the public
predicate docstring repeats the source label.

The compiled declarations print as:

```lean
structure MIPStarRE.QPBT.Parameters : Type
fields:
  q : Nat
  m : Nat
  d : Nat

def MIPStarRE.QPBT.Parameters.Admissible :
    MIPStarRE.QPBT.Parameters -> Prop :=
  fun params => Exists fun k =>
    Odd k /\ params.q = 2 ^ k /\ Dvd.dvd params.m params.q
```

`#print axioms MIPStarRE.QPBT.Parameters.Admissible` reports only `propext`;
in particular, it does not report `sorryAx` and does not depend on the imported
G16 field-data selector.

## Candidate authentication

| Binding | Expected | Observed | Result |
| --- | --- | --- | --- |
| Base / sole parent | `874dc07433936e26d62c42cdd779dde42386f99d` | same | pass |
| Head | `f6b19fc9fb87e0616b8367749ff971539bc1b45f` | same | pass |
| Tree | `19df34c6a5687eff9bf64611c8880e45b3ea4339` | same | pass |
| Commit count from base | `1` | `1` | pass |
| Changed path | `MIPStarRE/QPBT/Game/Parameters.lean` only | one added path, mode `100644` | pass |
| Git blob | candidate blob | `f9d65fc4a468997f93b95cb380d780bce46aed25` from both tree lookup and working file | pass |
| File SHA-256 | `2f749aca171739bf57d4a7945fbdbdc55bdaf83418a4cabe1a6582520b3ec2e5` | same before and after checks | pass |
| One-path name-manifest SHA-256 | `4a26a5faf9611c9e689ef03e253f5a4fbfe164d92ac86288eed3aac2422df539` | same | pass |
| Writer report SHA-256 | `4d06d8f0bbc0d07425a1ebc3c682533f50e3f9cca5cd2be781639dbe266b410d` | same | pass |
| G01 marker-payload SHA-256 | `587cb393eff88db0291303da834e483e13f44eda8c2c286e2ab48721120386cb` | same under the checker's between-markers plus `.strip()` convention | pass |

`/tmp/qpbt-039-review-a02` was detached and clean at authentication and after
all checks. Its Git directory is the isolated linked-worktree directory
`/home/drx/MIPStarRE-auto/.git/worktrees/qpbt-039-review-a02`.

The writer's process report records an earlier untracked canonical-root
duplicate. At this review's final isolation check,
`/home/drx/MIPStarRE-auto/MIPStarRE/QPBT/Game/Parameters.lean` was absent and
`git status --short -- MIPStarRE/QPBT/Game/Parameters.lean` was empty. This
reviewer did not remove or modify it. The incident therefore does not
contaminate the detached candidate. The writer worktree remained at the exact
head/tree and had only its required untracked report.

## Source and API evidence

| Artifact | SHA-256 |
| --- | --- |
| Pinned QPBT paper section | `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea` |
| Pinned finite-field dependency section | `379d970ae1b67412db5d25233856702f4ca69e8ee2d11b0afcf7c767b767b9cd` |
| Blueprint metadata | `705b7a474ac65671ac5f1e2288f671c5f7805b5ce5d3b92d08bade160239b8cd` |
| Full G01 contract report | `987d17140ae4e1e808ed0504b874c67dc1285f70245cf71363dafe97fc1dd610` |

`MIPStarRE/QPBT/Basic/Field.lean` defines field data and the tracked G16
selector, but the candidate uses none of those declarations. Its role here is
the exact prerequisite/import frozen by G01. The new public surface elaborates
only through `Nat`, `Odd`, natural power, and natural `Dvd.dvd`.

Consumer search over all candidate `MIPStarRE/**/*.lean` files finds no current
import or use of `MIPStarRE.QPBT.Game.Parameters`, `Parameters.Admissible`, or
the QPBT `Parameters` type outside the new module. This agrees with the
blueprint: `G02-GAME` is the planned consumer and is not implemented by this
candidate. No conflicting parameter declaration or LDT alias exists in the
current Lean tree.

## Validation

All times below are `/usr/bin/time` elapsed wall seconds; `0.00s` means below
the timer's displayed precision.

| Exact command | Result | Time |
| --- | --- | --- |
| `cat /home/drx/MIPStarRE-auto/AGENTS.md` | pass; governing instructions read before repository inspection | `0.00s` |
| `git rev-parse HEAD` | exact head | `0.00s` |
| `git rev-parse 'HEAD^{tree}'` | exact tree | `0.00s` |
| `git show -s --format=%P HEAD` | exact sole parent | `0.00s` |
| `git status --short --branch` in review worktree | `## HEAD (no branch)`, clean | `0.03s` |
| `git diff --name-only BASE HEAD` | sole expected path | `0.00s` |
| `git diff --name-only BASE HEAD | sha256sum` | exact one-path manifest hash | `0.00s` |
| `sha256sum MIPStarRE/QPBT/Game/Parameters.lean` | exact supplied digest | `0.00s` |
| `git rev-parse HEAD:MIPStarRE/QPBT/Game/Parameters.lean` | exact blob | `0.00s` |
| `git hash-object MIPStarRE/QPBT/Game/Parameters.lean` | same exact blob | `0.00s` |
| `sha256sum /home/drx/MIPStarRE-auto/workflow/reviews/qpbt-039-parameters-a01.md` | exact supplied writer-report digest | `0.00s` |
| `lake env lean MIPStarRE/QPBT/Game/Parameters.lean` | pass, no output | `2.10s` |
| `lake env lean /tmp/qpbt-039-review-a02/MIPStarRE/QPBT/Game/Parameters.lean` | pass against the detached review bytes, no output | `2.06s` |
| stdin `#print Parameters` / `#print Parameters.Admissible` probe under `lake env lean /dev/stdin` | pass; exact public structure and predicate shown above | `2.00s` |
| stdin `#print axioms MIPStarRE.QPBT.Parameters.Admissible` probe | pass; `[propext]`, no `sorryAx` | `2.07s` |
| `rg -n '^import ' MIPStarRE/QPBT/Game/Parameters.lean` | line 1 is the sole exact import | `0.00s` |
| `rg -n '\bsorry\b|\baxiom\b|\bconstant\b' MIPStarRE/QPBT/Game/Parameters.lean` | exit 1 as expected: no matches | `0.00s` |
| forbidden-assumption/coercion/positivity/`params.d` scan over the owned file | exit 1 as expected: no matches | `0.00s` |
| `git diff --check BASE HEAD` | pass, no output | `0.00s` |
| `git diff-tree --no-commit-id --name-status -r HEAD` | `A MIPStarRE/QPBT/Game/Parameters.lean` only | `0.00s` |
| `git rev-list --count BASE..HEAD` | `1` | `0.00s` |
| `env PYTHONDONTWRITEBYTECODE=1 python3 blueprint/check.py --check --source-root /home/drx/MIPStarRE-auto/references/2001.04383v3` | pass: 54 nodes, 12 chapters, acyclic, deterministic | `0.08s` |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/workflow.py validate` | pass: valid; 53 issues, 26 PRs, 2 planned sessions, 424 issued sessions, 7 stages | `0.14s` |
| final `git status --short --branch` in review worktree | detached and clean | `0.03s` |
| final candidate `sha256sum` | exact supplied digest unchanged | `0.00s` |

The long forbidden scan searched `_ofObligations`, `Hypotheses`, `Assumptions`,
bridge/residual/repair/witness/package/producer terms, `abbrev`, `instance`,
coercion markers, positivity markers, and `params.d`, in addition to the
separate proof-debt scan.

## Cache and build behavior

- The detached review worktree had no `.lake` directory, so no cache or build
  output was created there.
- The scoped checks reused the already seeded private issue cache at
  `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-039-parameters-a01/.lake`.
  That worktree was independently rebound to the exact candidate head, tree,
  and file digest before use.
- The private build directory resolved inside that issue worktree, at device
  and inode `66314:1185355`; no main-worktree `.lake/build` existed. Thus no
  writable build directory was shared between worktrees.
- The private build-directory stat remained `1788304621 4096` before and after
  all Lean invocations. Git state and candidate bytes also remained unchanged.
- Cache reuse was a hit for all imports. Reviewer cache warms: `0`; seeds: `0`;
  cache builds: `0`; lock wait: not applicable; network: `0`.
- Reviewer Lean invocations: `4` total (two scoped file checks and two
  declaration probes). Reviewer target builds: `0`; reviewer full builds: `0`.
- A full build was deliberately not duplicated. The SHA-authenticated writer
  report records an exact-candidate private full-build pass in `5.95s` and an
  affected-target pass in `3.21s`; this reviewer independently reran the scoped
  checker only, as required by the review packet.

## Residual risks

1. `MIPStarRE/QPBT/Basic/Field.lean:24-26` still contains the tracked G16
   `sorry`. It is inherited, outside this diff, and absent from the axiom
   dependencies of `Parameters.Admissible`; it is not a blocker for G01.
2. There is no implemented consumer yet, so downstream G02 integration is not
   exercised here. The current public declarations nevertheless match the
   frozen callable contract exactly.
3. This reviewer did not rerun a target or full build; the independent scoped
   checks passed, while broader build evidence remains the authenticated writer
   report. This is the intended non-duplicating build protocol for this packet.

## Metrics

- Topology: `/root` -> `/root/i039_reviewer_a02_parameters`.
- Subagents: `0`.
- Findings: `0`; review retries affecting verdict: `0`.
- Read-only process retries: one initial relative paper-source read failed
  because the detached review worktree lacked the materialized section; the
  packet's canonical absolute source path passed immediately. One exploratory
  marker-inclusive hash used the wrong convention; applying the repository
  checker's exact between-markers plus `.strip()` convention produced the
  expected G01 digest.
- Repository/worktree/Git/cache/state edits: `0`.
- Required report paths written: `1`, this file only.
- Token usage: `null`; reason: the collaboration interface does not expose
  per-agent token usage.
- Authoritative end-to-end elapsed: `null`; reason: the interface exposes
  command wall times but no authoritative per-agent session wall clock.
- Protocol revision: repository `AGENTS.md`; the writer cache report identifies
  canonical hot-cache recipe version `7`, but this reviewer invoked no warm,
  seed, or build recipe.

The report SHA-256 is supplied out of band after these final bytes are frozen.
