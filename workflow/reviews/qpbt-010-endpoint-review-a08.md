# QPBT-010 endpoint review A08

- Session: `i010-reviewer-a08-endpoint-transport`
- Target: LPR-001 base `77aa1a4ac947c1632ea57262d29d2753ba163c8a`, head `e93d949d06af2a7f4407d198a37aad315deac6aa`, tree `b518e346719a7d208604ba4c0b2db2b215fb77a2`
- Model: `gpt-5.6-sol`
- Endpoint: `https://api.finite-dimensional.space`
- Verdict: **blocked before launch**

## Outcome

The root coordinator requested one host-capable invocation of the governed
read-only reviewer using the existing Codex persistence store. The execution
policy rejected the command before `scripts/local_agent.py` started because
the user had not explicitly authorized sending the contents of the three exact
private-repository files to the named external endpoint.

No Codex process, review harness, endpoint request, network connection,
external thread, model output, prompt, usage envelope, or review verdict was
created. No repository evidence was prepared or transmitted. The issued
session is terminal failure evidence only and confers no approval.

## Required authorization

A retry requires an explicit user statement authorizing transmission of the
contents of this exact immutable LPR-001 evidence scope to
`https://api.finite-dimensional.space` for review by `gpt-5.6-sol`:

- `scripts/reference_transport.py`
- `tests/test_reference_transport.py`
- `workflow/reviews/qpbt-010-reference-transport.md`

The authorization should bind base
`77aa1a4ac947c1632ea57262d29d2753ba163c8a`, head
`e93d949d06af2a7f4407d198a37aad315deac6aa`, and tree
`b518e346719a7d208604ba4c0b2db2b215fb77a2`. Credentials remain excluded and
must never be read, copied, or recorded by the workflow.

## Safety disposition

The coordinator will not retry, redirect `CODEX_HOME`, copy authentication
state, invoke the endpoint indirectly, or otherwise work around the rejection.
The earlier local immutable approval remains valid evidence but does not
satisfy this supplemental endpoint-specific gate.

The rejected execution request returned after approximately 6.4 seconds. All
test/build/PDF/Lean/Lake/warm/seed/cache counts are zero for this attempt.
