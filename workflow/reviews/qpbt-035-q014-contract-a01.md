# QPBT-035 contract-freeze ownership handoff (A01)

Session: `i035-orchestrator-a01-q014-contract`

## Result

A01 stopped before contract edits because the current machine-readable
implementation-contract validator accepts only the first-wave writer lanes
`field` and `approximation`.  Representing the four QPBT-014 lanes as one of
those values would be false metadata, while omitting `implementation_contract`
would weaken the accepted machine gate.  Continue this work as A02 only after
adding `blueprint/check.py` and `blueprint/tests/test_check.py` to the exact
owned manifest.

The immutable handoff checkpoint is commit
`1c9abda5e4896cdf6c72e8e8131788dbd88b7c4a`, tree
`79513abd27ad53999ae63c6e04ccccf8f22c5ca1`.  Before this report, `git status
--short --branch`, `git diff --name-only`, and `git ls-files --others
--exclude-standard` showed no tracked or untracked repository edits.  A01 made
zero edits outside its original ownership; its only tracked edit is this
report.

## Blocker evidence and requested ownership

`blueprint/check.py:174-175` rejects every `writer_lane` outside
`{"field", "approximation"}`.  QPBT-035 must truthfully publish contracts for
`polynomial`, `pauli`, `types`, and `parameters`, and the canonical test suite
must reject unknown values while accepting exactly that expanded closed set.

Requested A02 ownership expansion:

- `blueprint/check.py`
- `blueprint/tests/test_check.py`

The smallest sufficient change is an explicit closed writer-lane constant,
use of that constant in `_implementation_contract_errors`, and adversarial
unit coverage for all admitted values plus an unknown value.  No other
ownership expansion is requested.

## Completed reading and source authentication

A01 completely read `AGENTS.md`, QPBT-035, the 389-line QPBT-033 preflight, the
240-line QPBT-013 cache/build closeout, the relevant blueprint nodes and G09,
integrated `Field.lean` and `Approximation.lean`, and the complete pinned F02,
F05, F06, F07, and G01 source files from the already authenticated local
QPBT-002 materialization.  No network was used.

| Source | SHA-256 |
| --- | --- |
| `dependencies/low-degree-code.tex` | `e77125aa2c20f037b949f8890efcaaf370f5ca25407048a5ac142115104bdc9e` |
| `dependencies/pauli.tex` | `aba301b2e225f0ceaeff6a942a75ee6d5db73283ba25e208e2e43452818aef2f` |
| `dependencies/conditionally-linear.tex` | `f6a63d2bf196cb0a16196c1ff4a753ec137dd391568a484ed5d99676b9552638` |
| `dependencies/types.tex` | `732b0621059f5222804ecf2cbd1eb6ae7e324fc6b5ea3dd9102cf5199d32fc6c` |
| `qpbt/qpbt-game-and-soundness.tex` | `30c735197503d81b37dc33129f15270fe216cc9458d96620a6488109994e62ea` |

The source hashes agree with QPBT-033.  G09 was read from
`blueprint/metadata/gaps.json`; the issue source-ref path
`docs/paper-gaps/pauli-trace-phase.md` is absent at this base.  The integrated
source hashes are `2737e90dcef1f657d1f092788c43d52f6702e48081708b439509181c0750900e`
for `Field.lean` and
`13ab03de2a2d19b88f4a93af9c8324c1d21e0989db4e7325f43d3703eeb6779a`
for `Approximation.lean`.

## Cache, materialization, and probes

The private worktree was seeded exactly once from authenticated key
`d71a99abea8f7ebf5bda5194dfef088b06f526230caf5ccbca34d62d5b4267b9`
for main `259c73a368ef7403b4e36e190c9bf940497b300f`.  It was a hit: 124,925 files,
3 symlinks, 10,097,592,794 bytes, zero builds, zero lock wait, and
`138.258072` seconds.  There was no warm.

Pinned local MIPStarRE source was materialized once with `--replace-existing`
from archive SHA-256
`656d92a4ad1fb24216ab0b26c6956b1cfb88ba7816257baa0e668415c0a7adcc`.
It published 337 files / 5,970,111 bytes in `5.948803` seconds and preserved
both authored QPBT files (5,319 bytes; aggregate SHA-256
`0578da860a522b58b69c2c16df366c7eee3abd97c425900401e4e83c992803ed`).

Temporary probes under `/tmp` established the callable types of
`MvPolynomial.restrictDegree`, `MvPolynomial.eval`, `PMF.uniformOfFintype`,
`PMF.map`, `ZMod.stdAddChar`, `AddChar.expect_eq_ite`,
`MIPStarRE.Quantum.Op`, `MIPStarRE.Quantum.Measurement`, and `fieldTrace`.
They also established two negative API facts: there is no
`MvPolynomial.restrictDegreeAddMonoidHom`, and `Measurement.effect` is an
inherited projection rather than a namespaced constant.  The initial F02
signature probe exposed and locally corrected two syntax/interface mistakes
(subtype dot notation and an ASCII linear-map arrow); it was not rerun after
the ownership stop.  These are temporary probe artifacts, not repository
changes.

Probe/type-check action accounting before handoff:

- one pre-olean API probe failed closed because integrated `Field.olean` was
  absent;
- one Field check type-checked but could not publish its olean before the
  private output directory existed;
- one Field olean check passed in `3.0` seconds with the authorized G16 warning;
- one Approximation olean check passed in `4.8` seconds;
- one API discovery probe completed with the two intentional unknown-constant
  diagnostics in `4.2` seconds;
- one initial F02 signature probe completed with the two corrected diagnostics
  in `2.4` seconds;
- full builds `0`, target builds `0`, repository Lean source edits `0`.

## A01 metrics

```json
{
  "session_id": "i035-orchestrator-a01-q014-contract",
  "stage_id": "STAGE-04A",
  "issue_id": "QPBT-035",
  "role": "orchestrator",
  "backend": "codex-collaboration",
  "requested_model": "gpt-5.6-sol",
  "external_id": "/root/i035_q014_contract",
  "agent_measured_elapsed_seconds_at_handoff": 703,
  "timing_basis": "worktree birth 2026-09-01T13:02:07.531958780Z to handoff measurement 2026-09-01T13:13:50Z",
  "token_usage": null,
  "token_usage_unavailable_reason": "collaboration session token usage is not exposed",
  "topology": {"parent": "/root", "nested_agents": 0},
  "actions": {
    "tracked_repository_edits_before_report": 0,
    "tracked_repository_edits_after_report": 1,
    "unowned_edits": 0,
    "cache_seeds": 1,
    "cache_hits": 1,
    "cache_warms": 0,
    "cache_builds": 0,
    "materializations": 1,
    "lean_probe_attempts": 6,
    "full_builds": 0,
    "network_calls": 0,
    "endpoint_calls": 0,
    "github_operations": 0,
    "credential_accesses": 0,
    "nested_agents": 0
  },
  "outcome": "ownership-expansion-handoff"
}
```

The report SHA-256 is supplied out of band because embedding a file's own hash
would be self-referential.
