# QPBT-026 final activation audit A27

## Findings

No findings.

## Verdict

**approve** for exact commit `8e2a645e272ba4de9d1218ca5a13bf86534b55fd`
and tree `ccd2ecf221756b539242faea25490809d9527e90` only.

This is an independent hostile read-only final activation audit. It is
explicitly **not** a formal PR-ledger review or approval.

## Object and provenance audit

- The audit worktree remained clean and detached at required base
  `d1e211351d366edf9f3f6d7fcb44f0c49787a3a2`.
- The target is a commit with exactly two ordered parents:
  `3c0e7c5675a7fca0bba925f016e8df39c0d444c0`, then
  `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.
- The parents have the single merge base
  `ea584e9e894391773e09ddad2ce4d082497c7913`; the second parent is an
  ancestor of the target, and the merge base is an ancestor of both parents.
- The complete first-parent delta is exactly four modified `100644` paths:
  `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/local_agent.py`, and `tests/test_local_agent.py`.
- Result blobs are exactly `107c5eb147811e0d3909717c74e2f32eb43d1ac5`,
  `037b625f0f77cfef1997d793aa14d48893d91dc0`,
  `25a5198e9b3c7e3ace8c6365b7064e8aa55dc506`, and
  `f8b51e87f2e1d7ac5fc40d55b0c415b95cebf824`, respectively.
- The two protocol blobs exactly match approved prototype
  `8ee49bcca504ccb02ffcb4852f63ca2d2f8fbbd4`; the two Python blobs exactly
  match the candidate second parent. Every other tree entry is preserved from
  the first parent.
- QPBT-027 blobs are exactly
  `6b5271bc995066641319c4ee0fe880e37d74490e` and
  `ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe`. All five specified QPBT-026
  report blobs match across both parents and the target.
- Conflict/reject-marker scanning found no match, and `git diff --check` passed.
- Superseded unreviewed commit
  `17415b8b00883962e64dbede1fe2c079f0654956` is not the target and has a
  different tree (`0163c085d1c79189025742c59a3a3c3c2efa6c0e`).

## Semantic audit

The protocol and implementation compose consistently. Production review is
fail-closed: both the CLI and library entry points require an explicit complete
transport profile, resolve a clean immutable committed target, validate all
legacy version-1 authorization fields and changed paths, and then unconditionally
raise the isolation error (`scripts/local_agent.py:843`,
`scripts/local_agent.py:3002`, `scripts/local_agent.py:3066`,
`scripts/local_agent.py:3840`). That rejection precedes task/context packet
reads, persistence or capability probes, harness/output preparation, lease
claim, command construction, and runner invocation.

The remaining success path is explicitly offline test mode. It requires an
injected non-default runner and a copied, schema-checked capability record,
rejects transport and authorization data, uses a non-`codex` executable marker,
passes a minimal Git environment, constructs a fresh projected harness without
source objects, alternates, or remotes, verifies every manifested byte, and
labels the projection `external_launchable: false` and host isolation
`not-enforced` (`scripts/local_agent.py:2260`, `scripts/local_agent.py:2493`,
`scripts/local_agent.py:2683`, `scripts/local_agent.py:3145`). Tests exercise
early failure, non-invocation, replay resistance, ambient Git-selector removal,
manifest tampering, sensitive renames, and production rejection.

## Authenticated validation evidence

The authority JSON SHA-256 is exactly
`1111e7abdbdb6ee208d21dbfe3681bc97fcd841314b042627cc8bd879161c7ce`.
The root validation report SHA-256 is exactly
`2c798ca5d0abb765a7c234467bb92c40ed5dc78948302d5ba1c316334e43f82b`.
It binds the exact target and records: workflow tests 70/70, local-agent tests
63/63, aggregate tests 336/336 in 187.177 seconds, compileall passed, workflow
validation and checker passed, blueprint 26/26 with a deterministic acyclic
48-node/12-chapter graph, and passing identity, marker, diff-check, and clean
worktree gates. I authenticated this evidence and did not duplicate the long
aggregate run.

## Residual risk

Production external review remains intentionally unavailable until exact-content
authorization and enforceable filesystem isolation are implemented. The offline
runner is an injected in-process test double, not an OS isolation proof; the
protocol and emitted metadata state that limitation accurately. No Lean source,
pin, declaration list, or build recipe changed, so no Lean/Lake/cache action was
warranted for this activation audit.
