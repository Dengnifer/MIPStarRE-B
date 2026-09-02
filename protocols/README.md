# Workflow Protocols

These protocols combine canonical GitHub issue/PR coordination with local,
versioned execution evidence. All GitHub objects belong to exactly
`Dengnifer/MIPStarRE-B`.

| Concern | Authority |
| --- | --- |
| Issues, sub-issues, dependencies, and status | GitHub Issues in `Dengnifer/MIPStarRE-B` |
| Pull requests and review threads | GitHub PRs in `Dengnifer/MIPStarRE-B` |
| Agent execution | named Codex sessions recorded in `workflow/state/sessions.json` |
| CI | scoped local checks followed by a full integration gate |
| Latest-main build artifact | locked hot-main cache under `.workflow-runtime/cache/` |
| Review bots | fresh read-only Codex reviewer sessions |
| Workflow telemetry | `research/metrics/` |

`workflow/state/issues.json` and `workflow/state/prs.json` survive as legacy or
derived compatibility projections. They are never an independent source of
truth. Only the root coordinator writes GitHub, every writing `gh` command names
`--repo Dengnifer/MIPStarRE-B`, and PR creation also names `--base main` until
the repository default branch is fixed.

Read the protocols in this order:

1. [meta.md](meta.md): authority, invariants, and evidence-driven evolution.
2. [orchestration.md](orchestration.md): issues, PRs, agents, and session lifecycle.
3. [local-development.md](local-development.md): worktrees, builds, cache, and gates.
4. [formalization.md](formalization.md): paper, blueprint, Lean, and proof debt.
5. [review.md](review.md): independent review and finding disposition.

`AGENTS.md` is the concise executable constitution. These files provide the
operational detail. If they disagree, stop and return an exact workflow-issue
payload for the root coordinator to create in `Dengnifer/MIPStarRE-B`; resolve
the conflict before implementation continues.
