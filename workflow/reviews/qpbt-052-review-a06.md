# QPBT-052 / LPR-025 Release Contract Review A06

Verdict: `request_changes`

## Findings

### F-LPR025-A06-001 (blocker): a null terminal identity disables the marked release contract

At `scripts/workflow.py:1541`, marked issuance identity is checked only by
equality with the issued-session row. For a terminal collaboration row,
`sessions.json` permits `external_id: null`, so a marked issuance with a
missing/null `external_id` passes because `None == None`. Then
`scripts/workflow.py:1554-1562` includes the truthiness of the session identity
in `release_required`, which disables the release requirement entirely for
that same marked lifecycle.

An independent full-store hostile probe constructed a schema-valid archived
`codex-collaboration` row with `external_id: null` and the ordered log
`session.issued(release_contract="post-confirmation-v1", no external_id)`,
`session.finished`, `session.archived`,
`session.released(external_id=null)`. `validate_documents` and
`WorkflowStore.validate()` both returned success. The same no-release form was
also accepted for schema-valid `finished`, `failed`, and `archived` rows.

This is a concrete bypass of both required properties: the marked issuance has
no immutable backend identity, and terminal/archive progression does not
require release (or can precede a later release). It leaves
F-LPR025-A04-001 and F-LPR025-A04-002 unresolved.

Required change: for every issuance payload containing `release_contract`,
require the corresponding session `external_id` to be a non-empty string and
require the issuance value to equal it. Once the supported marker is present,
make `release_required` depend on the marker and collaboration backend, not on
identity truthiness. Add terminal and archived regressions where both identity
copies are null/missing, including release-after-terminal/archive.

## Open Finding Dispositions

- `F-LPR025-A03-001`: **resolved on this head**. The markerless archived legacy
  lifecycle regression passes, the full canonical workflow validation accepts
  all 407 issued sessions, and the compatibility boundary is limited to
  issuance records without a `release_contract` field.
- `F-LPR025-A03-002`: **resolved on this head**. The CLI issued-session path
  selects lock-held pre/post event validation and rollback through
  `WorkflowStore.mutate`; the local-agent claim path does the same through
  `_session_transaction`. Independent end-to-end probes for both paths rejected
  pre-release transition without changing state/event bytes, then accepted
  `issued -> release -> running` and passed full store validation.
- `F-LPR025-A03-003`: **resolved on this head**. Lifecycle order is compared as
  `(timestamp, event line)`. The equal-timestamp release-before-issuance probe
  is rejected, while issuance-release-running is accepted.
- `F-LPR025-A04-001`: **not resolved**. Ordinary-time and equal-time
  terminal/archive-before-release cases with a non-empty identity are now
  rejected, but F-LPR025-A06-001 shows that a marked null-identity terminal or
  archived lifecycle disables the gate and validates.
- `F-LPR025-A04-002`: **not resolved**. Wrong or missing issuance identity
  against a non-empty session identity, wrong backend, and unsupported contract
  are rejected. When the terminal session identity is also null, equality
  accepts the missing issuance identity and the marked lifecycle validates.

## Authentication

- Formal PR base: `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`
  (authenticated commit and ancestor of the head).
- A05 comparison base and sole parent:
  `40d3e565426f74a0e3c60798ec7e2b5f7e35cfbf`.
- Head: `2310617ed6df56730f1fa267a9b19aec47be6e37`.
- Head tree: `d8a0402804ed6066b4c7143285446815925ce267`.
- Commit subject: `fix(workflow): bind marked release lifecycles`.
- Exact A05 changed paths: `scripts/workflow.py`,
  `tests/test_workflow.py`.
- A05 sorted newline-delimited changed-path manifest SHA-256:
  `ed1d478437c5e52e80e2828ca3439138c7483235b51c49ffbff7f24a30cb8184`.
- Prior cumulative candidate manifest SHA-256:
  `9c8a5a2e835d5afd3363d708be5298a8141a64aac52b3652083754aef1e57e6e`.
- `scripts/workflow.py` SHA-256:
  `ada39132d3c837e86aa1e4d5849b277dd111976dd88d2560c15a2b660882aa1d`.
- `tests/test_workflow.py` SHA-256:
  `1cd151ffd44b02a0bf03a49dc826dc1e0d194fa08c0b12cf810f78cc25832e5a`.
- A05 repair report SHA-256:
  `fb5aec95306545c793bae05449b36c14c8585136c51860ef9dcd6e012863ccd8`.
- A04 review SHA-256:
  `e4d2cafe70963d59ebb68ba4854a60d31bdeefbb43ee49f43cf354c7ae7e7036`.
- `AGENTS.md` SHA-256:
  `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c`.
- Authentication was repeated after all checks. The candidate remained a clean
  detached worktree at the exact head.

## Commands And Results

| Check | Result |
| --- | --- |
| Six focused workflow regressions (A03/A04 lifecycle, identity, backend, compatibility, CLI rejection) | 6/6 passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py` | 84/84 passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_local_agent.py` | 65/65 passed |
| Independent governed CLI issuance/release/running probe | pre-release rejected with exact byte preservation; post-release running accepted |
| Independent governed local-agent claim probe | pre-release rejected with exact byte preservation; post-release claim accepted |
| Independent null-identity terminal/archive hostile probe | unexpectedly accepted; finding A06-001 |
| `compileall` on the two scripts and two suites with a temporary external pycache | passed |
| `python3 scripts/workflow.py --root . validate` | valid: 52 issues, 24 PRs, 407 issued sessions, 7 stages |
| `python3 scripts/check_workflow.py --root . --skip-tests` | `workflow state: valid` |
| `git diff --check` for formal-base-to-head and A05-base-to-head | passed |
| Final `git diff --exit-code HEAD --` and detached status | clean |

No Lean/Lake build, cache action, network action, GitHub action, credential
access, repository edit, or candidate-worktree edit was performed. The only
persistent review write is this report.

## Residual Risk

The supported dispatch, release, CLI transition, and local-agent paths preserve
a non-empty confirmed identity, so the bypass requires malformed or corrupted
terminal state/history. That is still within the validator's fail-closed
integrity boundary and directly contradicts the marked issuance/release
contract. Integration should remain blocked until the null-identity case is
rejected and independently re-reviewed.

The final report SHA-256 is supplied out of band after these bytes are frozen;
self-embedding the ordinary digest would change the file being hashed.
