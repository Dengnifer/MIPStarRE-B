# LPR-017 immutable review A08

## Verdict

`approve`

## Findings

No new findings.

## Existing finding disposition

`F-LPR017-001` is resolved. The repaired public update path constructs a deep-copy
candidate and applies every assignment before authorization
(`scripts/workflow.py:2941-2945`). The append guard then examines only each
finding's newly appended confirmation suffix while resolving reviews from that
complete candidate (`scripts/workflow.py:2503-2537`). Every new ID must be a
unique string, differ from the resolution review, name an approving review on the
candidate's exact base/head, and satisfy start/completion chronology relative to
the resolution or preceding confirmation (`scripts/workflow.py:2531-2563`).

The surrounding append-only guard preserves existing review prefixes and finding
identity/resolution evidence (`scripts/workflow.py:2457-2500`,
`scripts/workflow.py:2566-2580`). It does not rebind an existing confirmation
prefix to a later head. Full static validation separately enforces unique review
identity, terminal read-only same-PR/base reviewer provenance and independence,
confirmation chronology, and current-head approval
(`scripts/workflow.py:460-462`, `scripts/workflow.py:514-568`,
`scripts/workflow.py:584-679`, `scripts/workflow.py:752-776`).

I inspected the three relevant public mutation shapes. `update pr` is guarded as
above; a status transition cannot append evidence; and initial `add pr` has no
prior append state, so its complete supplied history is subject to the same
atomic static validator before persistence (`scripts/workflow.py:1739-1755`,
`scripts/workflow.py:2906-2919`, `scripts/workflow.py:2920-2969`,
`scripts/workflow.py:2970-2987`). I found no relevant public mutation bypass.
Validation rejection occurs before either `prs.json` replacement or event append.

## Coverage reviewed

The committed regression matrix covers a pre-existing finding's valid current
append and malformed/unknown/duplicate/wrong-base/wrong-head/non-approve/
out-of-order cases (`tests/test_workflow.py:1105`), a newly appended finding with
stale evidence (`tests/test_workflow.py:1114`), reviewer role/independence and
wrong-PR provenance (`tests/test_workflow.py:1041`), immutable historical
prefixes and resolution fields (`tests/test_workflow.py:1062`), all six public
assignment permutations with exact rejection atomicity
(`tests/test_workflow.py:1711`), and later preservation of a legitimately
appended historical prefix (`tests/test_workflow.py:1741`).

I additionally replayed the stale append through the public CLI for a
pre-existing finding in all 6/6 `findings`/`reviews`/`head_sha` assignment
orders. Every order raised the expected wrong-head error and left `prs.json` and
`events.jsonl` byte-for-byte unchanged.

## Immutable identity

- Worktree: `/tmp/qpbt-027-pr017-review-a08`; detached and clean before and after review.
- Base: `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`.
- Base tree: `10f8da1ebb8b3fd7ce92dafee19d61fafe2cf8e2`.
- Head: `2c6b1f1d0be89d09bad2f60e074cf106be99fd46`.
- Head tree: `0c6fdd0f7ce5349b0f543e171871eb0ef292eab6`.
- Direct parent: `44ecdce96e5536407f89266b2be59820be56f01c`.
- Parent tree: `03e24c81b284f1b9f2e9bafbbc457e8c5f352e9e`.
- Merge base of required base and head: exact required base; ancestry check passed.
- Total base..head manifest: exactly the prescribed six paths.
- Direct parent..head manifest: exactly `scripts/workflow.py`,
  `tests/test_workflow.py`, and
  `workflow/reviews/qpbt-027-stale-append-fix-a05.md`.
- `git diff --check` passed.

Report SHA-256 identities checked independently:

- `workflow/reviews/qpbt-027-finding-reconfirm-a01.md`:
  `1885c02167279996773fe29d31cf3665d225d02ffd494b02d743fe2437134e73`.
- `workflow/reviews/qpbt-027-stale-append-fix-a05.md`:
  `a442bc60c86ccae962c956ebe024f1b822792a9e9afbb9d81722458e954d5e61`.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py`: pass, 70/70;
  test runner 0.522 s, wall 0.61 s.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'`:
  pass, 323/323; test runner 282.119 s, wall 282.40 s.
- `PYTHONPYCACHEPREFIX=/tmp/qpbt-027-review-a08-pycache python3 -m compileall -q scripts/workflow.py tests/test_workflow.py`:
  pass, wall 0.21 s.
- `python3 scripts/workflow.py validate`: pass, 27 issues, 16 PRs, 0 planned
  sessions, 322 issued sessions, 7 stages; wall 0.11 s.
- `python3 scripts/check_workflow.py --skip-tests`: pass; wall 0.13 s.
- Independent pre-existing-finding permutation/atomicity replay: pass, 6/6.

## Residual risk

The intended boundary remains: update-time provenance can prove that a newly
appended confirmation is current at the mutation that records it, while static
validation cannot reconstruct that fact for an already present historical
prefix. An initial full-record add and any out-of-band file edit therefore
receive full semantic/history validation but cannot receive prior-state append
provenance validation. This is the documented separation, not a bypass in the
public update protocol. No Lean, paper, blueprint, build, or cache surface
changed.

## Actions and metrics

- New findings: 0. Existing findings disposed: 1 resolved (`F-LPR017-001`).
- Repository edits: 0. Authorized `/tmp` report writes: 1.
- Subagents: 0; topology: root coordinator -> this reviewer.
- Workflow-module test attempts: 1, passed.
- Aggregate-test attempts: 2. One initial output-capture attempt ended without a
  retained result after its first 30-second yield; the clean rerun completed and
  passed 323/323.
- Compileall attempts: 1, passed. Canonical validation attempts: 1, passed.
  Workflow checker attempts: 1, passed.
- Independent focused-probe attempts: 2. The first command-construction attempt
  failed locally with `NameError` before invoking the protocol path; the corrected
  replay passed 6/6.
- Git writes, network/endpoint/GitHub/credential/Codex/Lean/Lake/build/cache
  actions: 0 each.
- Token usage: `input=null`, `output=null`, `total=null`; availability reason:
  per-agent token usage is not exposed by the collaboration backend.
- Canonical session elapsed: `null`; availability reason: no canonical
  per-agent elapsed-time measurement is exposed to this reviewer.
