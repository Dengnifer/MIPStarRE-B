# QPBT-023 / LPR-019 immutable binding (A07)

## Identity and ancestry

- Session: `i023-integrator-a07-pr019-bind`.
- Issue: `QPBT-023`; local PR: `LPR-019`.
- Base commit/tree: `942f9438b991ece8942815db16c019b92d9cdd8e` / `09123f4b25c892a146aabaa77d73cf0c5f35a0c6`.
- Candidate head/tree: `70fb1f484b0b94522b81082342b528b2fd39b707` / `59b1ca4351e91d1317c870d9e6da820a2b8cbf9f`.
- `git merge-base --is-ancestor BASE HEAD`: exit 0.
- Candidate worktree status: clean before this report-only write.

## Combined immutable manifest

`git diff --name-only BASE..HEAD` returned exactly 22 paths:

```text
blueprint/README.md
blueprint/check.py
blueprint/generated/graph.dot
blueprint/generated/graph.json
blueprint/metadata/gaps.json
blueprint/metadata/nodes.json
blueprint/src/generated/chapter-02-entries.tex
blueprint/src/generated/chapter-03-entries.tex
blueprint/src/generated/chapter-04-entries.tex
blueprint/src/generated/chapter-05-entries.tex
blueprint/src/generated/chapter-06-entries.tex
blueprint/src/generated/chapter-07-entries.tex
blueprint/src/generated/chapter-08-entries.tex
blueprint/src/generated/chapter-09-entries.tex
blueprint/src/generated/chapter-10-entries.tex
blueprint/src/generated/chapter-11-entries.tex
blueprint/src/generated/chapter-12-entries.tex
blueprint/src/generated/gaps.tex
blueprint/tests/test_check.py
docs/paper-gaps/self-dual-normal-basis.md
workflow/reviews/qpbt-023-leaf-contract-a04.md
workflow/reviews/qpbt-023-readme-sync-a05.md
```

No candidate file was modified by this adoption session.

## Registered evidence

The six required checks are bound to the immutable head: checker unit tests
(28/28), checker with pinned source root (51 nodes/12 chapters), checker
without source root (same), workflow validation, `git diff --check`, and the
blueprint PDF render (35 pages/160 identifiers). A04 report SHA-256:
`45dfbb3142df500eff3260d89055c4763c543036d62fad2ff3b32c9b036b0f0f`.
A05 report SHA-256: `f3b1f37e714d4157bad4c2ea04108538fdd2721fc12e97da434327d3b0ea407a`.
Reviewer report hashes: `9f8770d68bceb4f4a8da150b399c2c8999fd0a8d1e0db671156de391807df1c4` and
`402137288821e9a283af2e67db57493e4aee020dbbf8dfd1422402ddd2052838`.

## Action accounting

- Repository content writes: 1 (this report only); Git refs/index: 0.
- Lean/Lake/build/cache/network/endpoint/GitHub/credentials/nested agents: 0.
- Retries/incidents/new issues: 0.
- Token usage: `null` (collaboration backend does not expose it; no estimate).
- Binding inspection: less than one minute wall-clock; exact lifecycle timing
  is recorded by the coordinator.

Disposition: immutable binding accepted for coordinator-side LPR-019 transition
and integration. This report is not implementer/orchestrator approval.
