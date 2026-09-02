# MIPStarRE QPBT

Lean 4 formalization of the quantum Pauli basis test (QPBT) used in
`MIP* = RE` (arXiv:2001.04383v3).

This repository continues the workflow evolved in
[LionSR/MIPStarRE](https://github.com/LionSR/MIPStarRE). The mathematical
source, blueprint, and Lean implementation have a strict source-of-truth order:

1. `references/` contains the pinned paper sources and provenance.
2. `blueprint/` contains the dependency-tracked formalization design.
3. `MIPStarRE/` contains the Lean declarations and proofs.

GitHub Issues and pull requests in
[Dengnifer/MIPStarRE-B](https://github.com/Dengnifer/MIPStarRE-B) are canonical
for planning, status, integration, and review. Local state remains authoritative
for agent sessions, metrics, build-cache evidence, and fresh independent
reviewer identities; the old local issue and PR JSON files are retained only as
legacy or derived compatibility data. See [protocols/README.md](protocols/README.md)
and [workflow/README.md](workflow/README.md).

## Project stages

1. Establish the local workflow and research instrumentation.
2. Split the QPBT reference source into one TeX file per chapter or section.
3. Build a paper-traceable Lean blueprint.
4. Implement a minimal theorem skeleton, the complete declaration skeleton,
   and then all proofs through dependency-ordered GitHub issues.

Every implementation issue has one orchestrator. Provers, scouts, reviewers,
and simplifiers are bounded child sessions. A fresh read-only reviewer must
return an approving verdict for each immutable GitHub PR head after its
validation gate passes. The reviewer never writes GitHub; the root coordinator
posts the exact report and status while preserving the reviewer's immutable
identity.

## Current status

Canonical issue and PR status lives on GitHub in `Dengnifer/MIPStarRE-B`.
Authoritative local session state lives in `workflow/state/`, and research
measurements live in `research/metrics/`. Stage and execution evidence is not
duplicated in this overview.
