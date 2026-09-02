# QPBT-054 / LPR-031 corrected-manifest review (A10)

Session: `i054-reviewer-a10-manifest-auth`
External identity: `/root/i054_reviewer_a10_manifest_auth`
Verdict: `approve`

## Findings

None.

## Finding dispositions

- `F-LPR031-A08-001`: resolved. The corrected `gaps.json` Git blob is the exact
  40-character `ed9f21e6797dcaebf088236c829f7c27ea432bb5`; its content
  SHA-256 is
  `1cbc97f938bf3aeb5734242c96ac794b80c79d54b9890b85d65d326a7cdea167`.
- `F-LPR031-A06-001`: resolved. The exact A08 report is authenticated, and the
  candidate object, frozen signature, and pinned-source bytes are unchanged.

## Authentication

- A10 manifest SHA-256:
  `6c369cf726f1c369e9406f6bb597078dddc28805d1be1f2c16df025576be3628`.
- Canonical checkpoint/tree: `cc9194ad4a38aaf4971db871bdae34f10b447230`
  / `0ba66c89b9605400fa2fba232b2b971f707e08b3`.
- Base/head/tree/sole parent: `639c883737e07b91156a9cbc31ec1aa65100a935`
  / `f4259860776f85e65cbe78718b58734d7be31a80`
  / `9a37c6ff62d5f23931a0d5e271c0c403d8e96987`
  / `1c5f12b045683ca50f4ff321d4c55c527bbc54c0`.
- Linear ancestry, ancestry relation, three binary-patch SHA-256 values, exact
  ten-path base diff, exact seven-path repaired-head diff, and clean candidate
  worktree: PASS.
- Manifest entries: 20/20 passed, comprising 15 Git blob/content identities
  and five filesystem content identities.
- Frozen F06A signature SHA-256:
  `cfe433e36d0670c344b29ab5107557842e7d4fc8358fba2713b8ff2ee107a3a1`.
- Superseded A08 manifest SHA-256:
  `49e1ef32b687b9095b6326d5019986e8ca7eb750d5dbb6d7444576e69b4c8904`.
- A08 report SHA-256:
  `9d4f126a93b4d3831ff8b345fcb88784d9bf78f06e758cd15aa8e4bea4545405`.

A08 and A10 bind identical candidate objects. Their first 19 locators and
content SHA-256 values are identical; A10 corrects only the malformed manifest
blob text and adds the authenticated A08 report as entry 20. No candidate or
pinned-source byte changed.

## Residual risk and accounting

Tests, Lean, Lake, builds, generation, and workflow validation were
intentionally not rerun. A08's authenticated substantive review remains the
applicable evidence. Executable downsizing and its runtime proof remain future
Lean work.

- Observed end: `2026-09-02T20:37:32.910015316Z`.
- Read-only shell invocations: 36.
- Writes, network, GitHub, credential access, and nested agents: 0.
- Token usage: `null`; collaboration does not expose per-session usage.
