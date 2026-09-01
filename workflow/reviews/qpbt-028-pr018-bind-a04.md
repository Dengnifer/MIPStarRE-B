# LPR-018 no-byte-change adoption A04

## Verdict

**PASS for formal adoption of the exact LPR-018 draft as a partial,
fail-closed dependency slice.** The frozen candidate and canonical records are
mutually consistent. They do not claim that QPBT-028 is complete and do not
enable production external review.

This is identity/provenance adoption, not a security review, PR approval,
integration approval, or QPBT-028 acceptance. LPR-018 still requires a fresh
independent immutable review before integration. QPBT-029 and QPBT-030 remain
required before QPBT-028 can close.

## Immutable Git identity

- LPR: `LPR-018`, canonical status `draft`.
- Base: `1799fbaf8175157a4aca6841a179fcbd43d7f4ed`.
- Head: `7e7fe07e776b44b98724605648a71e2d5f31580e`.
- Head tree: `398eaced83f0bfdf7b51364784d1a5211aab2e86`.
- Direct parent: `1799fbaf8175157a4aca6841a179fcbd43d7f4ed`.
- `merge-base(BASE, HEAD)` equals BASE; `BASE..HEAD` has one commit.
- Branch `issue/qpbt-028-content-isolation-a01` resolves to HEAD.
- `git diff --check BASE..HEAD` passed.
- The owned worktree was clean before validation and remained clean after all
  reproduced checks.

The exact seven-path inventory is:

| Status | Path | HEAD blob |
| --- | --- | --- |
| M | `protocols/CHANGELOG.md` | `561958d41c178fa822a9416080334a6fad0fb86d` |
| M | `protocols/review.md` | `79b4ee6f7dee9a91d139450fa22d582bf02c0268` |
| M | `scripts/local_agent.py` | `7d5448af405401c01535677101b3f2b349273ab8` |
| A | `scripts/review_isolation.py` | `32c2276168f691f695eb6e83645f756fcf6aa44a` |
| M | `tests/test_local_agent.py` | `c7396513ded0e93a96d92439836b8df2864c98e7` |
| A | `tests/test_review_isolation.py` | `a08310539144f2f0f1e41e79e9ce6073ca169e57` |
| A | `workflow/reviews/qpbt-028-content-isolation-a01.md` | `fec6970198e603e6e603ded9a0e1452f81e53877` |

All seven entries are ordinary mode `100644`; no rename inference was used.
The inventory exactly matches LPR-018 `changed_paths` and the orchestrator's
owned paths.

## Report authentication

- Candidate report SHA-256:
  `c756a8842089f385a175c49287a7a58fec51b989731d45ca84ad704371a278e5`
  (exactly the issue, session, and requested digest).
- A02 channel-matrix report SHA-256:
  `167085d8d8902c6e2c43290ee081ba271cf89459de77791cf39f2427dc763bcd`.
- A03 OS-isolation report SHA-256:
  `0738401dc1a4b78eba89ace547898b87eebe509b255e0f842e10c2cc9c8c660a`.

The two scout digests exactly match their archived canonical session records.
The scouts are design/capability evidence, not approval evidence.

## Registered checks

All six LPR-018 checks are registered as `passed` against the exact BASE and
HEAD above. Read-only reproduction on the frozen HEAD gave:

| Check | Reproduced result |
| --- | --- |
| `test_local_agent.py` | 65/65 passed in 4.526 s |
| `test_review_isolation.py` | 4/4 passed in 0.202 s |
| dependency-free aggregate | 342/342 passed in 226.049 s |
| Python `compileall` | passed with cache redirected to `/tmp/qpbt-028-pr018-bind-a04-pycache` |
| workflow validation | passed; candidate snapshot reports 29 issues, 17 PRs, 349 issued sessions, 7 stages |
| ancestry/tree/path/clean identity | passed; direct parent, one commit, seven paths, unchanged tree, clean worktree |

The canonical coordinator state also validated separately with 31 issues, 18
PRs, 354 issued sessions, and 7 stages. That newer state count does not alter
the frozen candidate's bytes or its exact-head check.

## Issue, PR, and session linkage

- LPR-018 links only QPBT-028, binds the exact BASE/HEAD above, records the
  seven paths and six checks, requests no external review, and says explicitly
  that QPBT-029/QPBT-030 and post-PR immutable review remain unexecuted.
- QPBT-028 is in `review`, owned by archived orchestrator
  `i028-orchestrator-a01-content-isolation`. Its candidate evidence binds
  LPR-018, HEAD/tree/report digest, records `acceptance_complete: false`, and
  records `production_enabled: false`.
- The PR provenance sessions are the archived A01 orchestrator and archived A02
  and A03 scouts. Their base revisions and report digests agree with the PR and
  candidate report.
- This running session, `i028-integrator-a04-pr018-bind`, is linked to QPBT-028
  and LPR-018 at exact HEAD. It is the post-PR no-byte-change adoption attempt;
  it does not replace the required independent reviewer.
- QPBT-029 is a QPBT-028 child for one-time exact-content capture/projection;
  QPBT-030 is a QPBT-028 child dependent on QPBT-029 for the pinned reviewer and
  credential-broker boundary. Their open gates cover the work omitted here.

## Scope-honesty assessment

The draft accurately describes a partial fail-closed slice:

- The candidate report says at lines 17-18 that it is not QPBT-028 acceptance
  and production external review remains disabled.
- Its gate table at lines 58-63 marks five gates open/open-fail-closed and one
  partial; lines 65-82 identify the two required dependency tracks and require
  QPBT-028 to remain open.
- `validate_review_disclosure_authorization_v2_structure` documents and performs
  structural validation only; it does not claim to compare declared entries
  with captured source or outbound bytes.
- The production preflight raises if the combined isolation capability is
  unavailable. Even if that capability becomes available, it raises again
  because the independently reviewed one-time projection coordinator is absent.
  Thus this candidate contains no production-review success path.
- The protocol and changelog use the same partial/fail-closed framing and do not
  convert the Landlock sentinel probe into a claim of complete descendant-egress
  isolation.

No contradictory completion or production-enabled claim was found in the seven
changed paths or canonical QPBT-028/LPR-018/session records.

## Action accounting

Repository edits, Git writes, endpoint requests, network requests, GitHub
operations, credential access, Codex launches, Lean/Lake/hot-main-cache actions,
and nested agents: zero. The only output is this `/tmp` report; compileall's
temporary bytecode stayed under the explicitly named `/tmp` directory. Per-session token
usage is unavailable from the collaboration backend and was not estimated.

Audit completed at `2026-09-01T07:56:21Z`.
