# QPBT-037 / LPR-032 candidate binding

Session `i037-integrator-a17-pr032-bind` authenticated the immutable QPBT-037
candidate for no-byte-change adoption by `LPR-032`.

## Identity

| Item | Authenticated value |
| --- | --- |
| Canonical checkpoint | `4dec80aa8271efac036a4a3ad4a7eb51797f75d8` |
| Canonical checkpoint tree | `18d746ac4e0da742395a8697b7f9a9f70a5542b8` |
| Candidate base / sole parent | `c5f4b277c17c54f2bfff3eb02c1101d4f1e85b60` |
| Candidate head | `cdb83f4017cfc182eb2611be0fbc5cd3635fbf64` |
| Candidate tree | `239f65b911d5535bdd20bb442c6e9c61aa00f8ff` |
| Binary patch SHA-256 | `0292bed4a9457185b82b27db060091a766aa3f4b0719553da50eacd3d152d08d` |

The candidate branch and registered worktree both resolve to the exact head.
The head has the declared sole parent and exactly one changed path. The
candidate worktree is clean, and both `git diff --check` and
`git diff-tree --check` report no defect.

| Changed path | Git blob | File SHA-256 |
| --- | --- | --- |
| `MIPStarRE/QPBT/Basic/Pauli.lean` | `d183c3d440bdb49870ba55f8ad06cb029531743e` | `df003a117fb8495bd01bd7ceee45b7c58df5c9e4815bfb4e5a9e344da6b56e12` |

The committed candidate report
`workflow/reviews/qpbt-037-pauli-a15.md` has Git blob
`d3a030f073b4b93474c8d98757d70b4609156282` and SHA-256
`3cf308d7b65dd205752af172825e8eaa757a1f0a081e1f3670fc52f4b8629b9f`.

## Canonical binding

At the immutable canonical checkpoint above, `LPR-032` is a draft for
`QPBT-037` with base `c5f4b277c17c54f2bfff3eb02c1101d4f1e85b60`, head
`cdb83f4017cfc182eb2611be0fbc5cd3635fbf64`, branch
`issue/qpbt-037-pauli-a02`, and the sole changed path listed above. QPBT-037 is
in review, has the expected owner, and owns only that path.

All 6/6 registered checks are `passed` on the exact PR base/head pair:

| Check | Recorded result |
| --- | --- |
| `check-qpbt-037-auth` | Exact commit, tree, sole parent, one new 857-line file, and clean worktree authenticated |
| `check-qpbt-037-lean` | Scoped Lean elaboration passed in 7.43 seconds with zero diagnostics |
| `check-qpbt-037-target` | Affected target build passed in 27.07 seconds |
| `check-qpbt-037-full` | Private full build passed in 6.24 seconds across 8992 jobs |
| `check-qpbt-037-blueprint` | Default and pinned-source synchronization passed with 54 nodes |
| `check-qpbt-037-hygiene` | Exact imports, G09 phase/order, proof-debt, and diff hygiene passed |

## Authentication commands

The following read-only commands were run from the binding or candidate
worktree, as appropriate:

```text
git status --short --branch
git rev-parse HEAD HEAD^{tree} HEAD^
git diff-tree --no-commit-id --name-status -r <base> <head>
git ls-tree <head> MIPStarRE/QPBT/Basic/Pauli.lean
sha256sum MIPStarRE/QPBT/Basic/Pauli.lean
git rev-list --parents -n 1 <head>
git diff --binary <base> <head> | sha256sum
git diff --check <base> <head>
git diff-tree --check <base> <head>
jq '.pull_requests[] | select(.id == "LPR-032")' workflow/state/prs.json
jq '.issues[] | select(.id == "QPBT-037")' workflow/state/issues.json
python3 scripts/workflow.py validate
```

Their results were respectively: clean binding and candidate worktrees; exact
checkpoint/head/tree/parent identities; one added path; exact blob and file
hash above; one candidate parent; exact binary-patch hash above; no whitespace
defects; exact LPR-032 and QPBT-037 bindings; and a valid workflow containing
55 issues, 32 local PRs, zero planned sessions, 446 issued sessions, and seven
stages.

## Disposition and counters

Adopt exact head `cdb83f4017cfc182eb2611be0fbc5cd3635fbf64` in
`LPR-032` without changing candidate bytes, then obtain the required fresh
immutable mathematical/API review. This session made one report-file change
and zero candidate changes. It ran zero Lean/Lake/build/cache/materialization
actions, made zero network/GitHub/credential operations, and spawned zero
nested agents. Exact per-agent token usage is unavailable because the
collaboration backend does not expose it; no token value is estimated. The
root coordinator records lifecycle elapsed time from the issued session's
start and terminal timestamps.
