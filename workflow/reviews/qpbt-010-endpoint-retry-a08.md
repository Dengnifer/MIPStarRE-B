# QPBT-010 endpoint retry transport audit A08

- Logical session: `i010-scout-a08-endpoint-retry`
- Audit snapshot: main `fcd1aa928ac0263f83de37143dc8dc5f4d937210`
- Review target: LPR-001 base `77aa1a4ac947c1632ea57262d29d2753ba163c8a`, head `e93d949d06af2a7f4407d198a37aad315deac6aa`
- Candidate: `/home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-010`
- Scope: read-only transport audit; no Codex launch, endpoint/network request, test, build, Lean/Lake/cache command, Git write, or repository/runtime/worktree mutation

## Verdict

**Conditional go for a newly issued real reviewer; no-go to reuse A07 or launch before the two local preconditions below.**

1. **A07's disclosure-authorization blocker is discharged by the current scoped user instruction.** The instruction names the exact LPR-001 base/head, explicitly authorizes `gpt-5.6-sol` at `https://api.finite-dimensional.space` over the Responses API, and asks that it be used. This is the exact endpoint/model/evidence scope A07 said was missing (`/tmp/qpbt010-endpoint-review-a07.md:18-19`). Stage-1's older authorization is narrower: it permits frozen Stage-1 evidence (`workflow/reviews/stage-01-external-review-authorization.md:11-15`), so it is corroborating transport evidence rather than the sole authorization for LPR-001.
2. **Canonical metadata has not caught up.** `workflow/state/prs.json:218-223` still says the requested external review is `awaiting-explicit-disclosure-authorization`. Before launch, the root coordinator must record the new binding to this exact base/head evidence scope and issue a fresh reviewer lease. A07 is archived and terminal (`workflow/state/sessions.json:12004-12046`); protocol forbids rerouting a rejected attempt (`protocols/review.md:33-40`).
3. **Persistence can be redirected safely, but not to an empty home.** The launcher selects inherited `CODEX_HOME`, else the default user home (`scripts/local_agent.py:1056-1060`), probes that root before task/context loading (`:1063-1124`, `:3313-3329`), and the Codex child inherits the same environment (`:1366-1403`, `:2817-2824`). A06 therefore failed at the default home with errno 30 before evidence preparation. A fresh writable `/tmp` or ignored workspace home passes the same probe, but an empty home loses the credential store required by `requires_openai_auth=true`.

The audit proposed projecting authentication into a private temporary Codex home. The coordinator rejected that implementation because the active session constraints prohibit repurposing `CODEX_HOME`. A compliant live retry must instead run host-capable with the existing persistence root unchanged.

## Immutable target evidence

- Main and the requested audit snapshot both resolve to `fcd1aa928ac0263f83de37143dc8dc5f4d937210`.
- Candidate `HEAD` is exactly `e93d949d06af2a7f4407d198a37aad315deac6aa`; status is empty; tree is `b518e346719a7d208604ba4c0b2db2b215fb77a2`.
- Base `77aa1a4ac947c1632ea57262d29d2753ba163c8a` is an ancestor of head.
- Exact delta is three additions: `scripts/reference_transport.py`, `tests/test_reference_transport.py`, and `workflow/reviews/qpbt-010-reference-transport.md` (2,354 inserted lines).
- The current launcher/protocol/tests match main `fcd1aa9...`; SHA-256: `scripts/local_agent.py` `9ac9431d3ef3327950cb9fda17f151d213b6d74f15809478934ed5e8f7f8550e`, `protocols/review.md` `23a9ad2e94c78345e9869a218ad6569cbd629062f500d19ab043a06496cc4f1f`, `tests/test_local_agent.py` `5aae14a9bd496588961acb19c8839224690d3e9fd357e1da819a8c0709589e12`.
- The supplied task `/tmp/qpbt010-review-task-a06.md` is still present with SHA-256 `b22cb49bf1683ec0ba4a241b0280e7754396dc141ceb8b81cbbf6bdbce886ca8`; it names this exact diff and structured reviewer contract.
- Stage-1 endpoint health A02 passed the exact endpoint/model profile with a complete thread/final/usage envelope (`workflow/reviews/stage-01-endpoint-health-a02.md:3-20`). This is health evidence, not a review verdict.

## Governed live retry shape

After issuing a fresh reviewer lease, the host-capable command must retain the existing Codex persistence environment and use this exact target/profile shape:

```bash
python3 /home/drx/MIPStarRE-auto/scripts/local_agent.py \
  --repo-root /home/drx/MIPStarRE-auto \
  --runtime-dir /tmp/qpbt010-endpoint-a08 review \
  --issue QPBT-010 --attempt 8 --slug endpoint-transport \
  --task-file /tmp/qpbt010-review-task-a06.md \
  --cwd /home/drx/MIPStarRE-auto/.workflow-runtime/worktrees/qpbt-010 \
  --base main \
  --base-sha 77aa1a4ac947c1632ea57262d29d2753ba163c8a \
  --head-sha e93d949d06af2a7f4407d198a37aad315deac6aa \
  --model gpt-5.6-sol \
  --model-provider OpenAI --provider-name OpenAI \
  --provider-base-url https://api.finite-dimensional.space \
  --wire-api responses --provider-requires-openai-auth \
  --timeout-seconds 900 \
  --session-id i010-reviewer-a08-endpoint-transport \
  --parent-session-id i001-coordinator-a01-bootstrap
```

The wrapper independently enforces full SHA resolution, exact candidate head, clean status, and ancestry; constructs the isolated committed-evidence harness; applies the all-or-none HTTPS Responses profile; and runs nested Codex with a read-only sandbox, no approvals, disabled user/project instruction loading, bounded process-group cleanup, and structured terminal evidence.

## Remaining risks

- A02's health-window age is not mechanically checkable because no duration is configured.
- A complete `result.json` with exact base/head/tree, prompt/evidence digests, external thread ID, transport profile, final structured review JSON, token availability reason, and archive/retirement evidence is required. A successful transport without a valid verdict does not satisfy the gate.
- The endpoint reviewer is an additional user-requested gate. LPR-001's already-recorded independent local approval remains separate evidence and is not retroactively replaced.

## Audit provenance

Read-only commands used: `sed`/`nl`, `rg`, `wc`, `stat`, `sha256sum`, `jq` on fixed non-secret envelope fields, and Git `rev-parse`, `status`, `ls-tree`, `log`, `show`, `diff`, and `merge-base`. A07 was found at `/tmp/qpbt010-endpoint-review-a07.md` (SHA-256 `c998fe67e36ac7efc671a08f9634b47a7d22befea9ab8457cf0f9d96bcf0c580`), not at its recorded repository path. A06's failed envelope SHA-256 is `6ea837c2bf860531f30773895325fe7b30a5e0a07bfa1c55cf8ee127df8e4435`; its fixed probe says `root_source=default-user-home`, errno 30, cleanup complete, and no evidence prepared/transmitted.

Started `2026-09-01T04:53:28+08:00`; ended `2026-09-01T05:03:34+08:00`; elapsed 606 seconds. The canonical report edits only the proposed persistence route and reviewer attempt number to comply with coordinator constraints; the audit verdict and evidence are unchanged.
