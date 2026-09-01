# QPBT-026 final activation A27 root validation

## Immutable target

- Commit: `8e2a645e272ba4de9d1218ca5a13bf86534b55fd`.
- Tree: `ccd2ecf221756b539242faea25490809d9527e90`.
- Ordered parent 1: `3c0e7c5675a7fca0bba925f016e8df39c0d444c0`.
- Ordered parent 2: `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.
- Unique parent merge base: `ea584e9e894391773e09ddad2ce4d082497c7913`.
- Validation completed: `2026-09-01T06:57:08.144293Z`.

The target is a commit object with exactly the ordered parents above, and the
second parent is its ancestor. The complete first-parent delta is exactly four
modified `100644` paths:

| path | exact result blob |
| --- | --- |
| `protocols/CHANGELOG.md` | `107c5eb147811e0d3909717c74e2f32eb43d1ac5` |
| `protocols/review.md` | `037b625f0f77cfef1997d793aa14d48893d91dc0` |
| `scripts/local_agent.py` | `25a5198e9b3c7e3ace8c6365b7064e8aa55dc506` |
| `tests/test_local_agent.py` | `f8b51e87f2e1d7ac5fc40d55b0c415b95cebf824` |

The protocol blobs exactly equal independently approved semantic prototype
`8ee49bcca504ccb02ffcb4852f63ca2d2f8fbbd4`. The Python blobs exactly equal
the LPR-016 candidate. Every other entry equals ordered parent 1. In
particular, QPBT-027 workflow/test blobs remain
`6b5271bc995066641319c4ee0fe880e37d74490e` and
`ac747a955a360cf6bb8b8d1124f4fd1bf1846dbe`, and the five shared QPBT-026
report blobs match across both parents and the target.

## Exact-object gates

| gate | result |
| --- | --- |
| workflow focused tests | PASS, 70/70 in 0.644 s |
| local-agent focused tests | PASS, 63/63 in 4.414 s |
| aggregate Python tests | PASS, 336/336 in 187.177 s |
| compileall with private `/tmp` cache | PASS |
| workflow state validation | PASS, 29 issues, 17 PRs, 0 planned, 349 issued, 7 stages |
| workflow checker `--skip-tests` | PASS |
| blueprint tests/check/graph | PASS, 26/26; 48 nodes, 12 chapters, acyclic and deterministic |
| parent/tree/blob/ancestry/preservation gates | PASS |
| marker and rejected-hunk scan | PASS, no matches |
| `git diff --check HEAD^1..HEAD` | PASS |
| target worktree final porcelain status | PASS, clean |

No Lean source, pin, declaration list, or build recipe changed. Lean, Lake,
and hot-main-cache actions were therefore zero. Network, endpoint, GitHub,
credentials, and Codex launches were zero.

Superseded object `17415b8b00883962e64dbede1fe2c079f0654956`
is not this target, was never reviewed, and will not be activated.
