# QPBT Formalization Workflow Report

## Scope

This report records the formalization of the quantum Pauli basis test from
arXiv:2001.04383v3 in Lean 4 and the evolution of its local multi-agent workflow.
The record is observational: unavailable metrics are `null`, approximate timing
is labelled, and successful no-op reviews or scouts remain visible.

## Method

For every stage and issued session, record elapsed time, agent role and lineage,
subagent count, token usage when exposed, owned paths, accepted artifacts,
compile attempts and failures, cache hit/wait/build timing, review rounds and
findings, proof-debt delta, incidents, and active protocol revision. Canonical
machine-readable state is under `workflow/state/`; raw run data is ignored and
retained only locally.

## Stage summary

| Stage | Status | Start | End | Sessions issued | Token data | Key output |
| --- | --- | --- | --- | ---: | --- | --- |
| 1. Workflow skeleton | completed | 2026-08-30 09:31 +08 | 2026-08-31 01:25 +08 | 35 including root | 5 completed CLI sessions exposed usage; collaboration/root totals unavailable | protocols, ledgers, local tooling, frozen-review harness |
| 2. Source split | planned | - | - | 1 read-only design scout, plus the Stage 1 source audit | unavailable | pinned byte-split design |
| 3. Lean blueprint | planned | - | - | 2 read-only scouts | unavailable | proof graph, source gaps, Lean API map |
| 4A. Minimal skeleton | planned | - | - | 0 | - | - |
| 4B. Complete skeleton | planned | - | - | 0 | - | - |
| 4C. Proofs | planned | - | - | 0 | - | - |
| 5. Final audit | planned | - | - | 0 | - | - |

## Baseline observations

The mature MIPStarRE workflow evolved in response to four recurring classes:
paper-statement drift, stale Lean artifacts, duplicated review/build work, and
issue/automation races. Its current design moves fast integrity checks to local
hooks, reviews only after a successful build, keeps deterministic bookkeeping
out of model agents, and caches only main because per-PR caches exhausted the
GitHub budget.

TeXRA adds execution lineage, explicit plan-versus-call state, bounded fan-out,
fresh completion audits, and a third-occurrence rule for extracting abstractions.
Its campaign evidence identifies concurrency duplication as the leading
non-quality failure and treats zero-edit simplification as success.

The local protocol combines those lessons. The bootstrap has recorded 20
incidents so far, beginning with invalid empty Git metadata, hanging Git
transport, missing expected references, upstream documentation/pin drift, and
ambiguous paper-source redistribution rights. Later incidents came from state
and event-envelope gaps, review persistence and timeout boundaries, explicit
external-disclosure authorization, endpoint transport, and probe construction.
These were recorded before integration so protocol changes remain traceable to
evidence rather than hindsight.

## Stage 1 observations

The deterministic gate grew from the initial workflow checks to 83 tests after
adversarial fixes to cache identity and transactions, immutable review targets,
session/PR/state invariants, interrupt-safe subprocess bounds, and compact
frozen evidence. All current tests pass locally. The active protocol evolved
from `0.1.0` through `0.1.4`. Revision `0.1.1` compacted the review packet after
a small endpoint health probe succeeded but two full review packets produced no
model work. The second packet ran for 1,800.154375 seconds and contained 36,041
bytes; the integrity-preserving replacement is constant in manifest cardinality
and keeps the full manifest digest-bound in the isolated harness. Revision
`0.1.2` then separated instruction isolation from provider routing: the launcher
retains `--ignore-user-config` but supplies the authorized provider name, HTTPS
base URL, Responses wire API, and authentication mode as validated non-secret
overrides before `exec`. Revision `0.1.3` distinguishes frozen-core approval
from the terminal lifecycle and seal that can only be recorded after the
reviewer returns. It also canonicalizes that trusted phase record and binds the
captured core back to the reverified freeze after evidence capture.

Reviewer transport evidence is deliberately retained rather than averaged
away: A04 failed locally before thread creation in 10.292274 seconds; A05 was
manually interrupted after about 1,277 seconds and motivated the timeout
wrapper; A06 was rejected before launch pending explicit disclosure authority;
A07 timed out after 900.154354 seconds; A08 timed out after 1,800.154375
seconds; and compact A10 timed out after 900.152341 seconds. None conferred a
verdict. A10 ruled out packet size and exposed that reviewer isolation had also
disabled the custom provider routing used by the successful endpoint probe,
which took 15.196164 seconds and exposed 17,214 input, 19 output, and 17,233
total tokens. A repository-free canary using the corrected isolated routing
then completed in 15.787069 seconds and exposed 15,166 input, 11 output, and
15,177 total tokens. A12 then completed the first full isolated review in
80.312839 seconds, exposing 219,938 input, 1,878 output, and 221,816 total
tokens. Its blocked verdict identified an impossible pre-return lifecycle/seal
ordering rather than a frozen-core defect. The follow-up fix received two
adversarial trust-boundary findings, closed both, and passed fresh re-review.
The resulting A14 review approved with no findings in 101.945834 seconds after
independently matching all 59 frozen-core entries and all 66 captured files; it
exposed 391,459 input, 3,590 output, and 395,049 total tokens. Its approval was
superseded only because the later staged gate exposed the untracked whitespace
blind spot. A16 then approved the corrected protocol `0.1.4` snapshot with no
findings in 111.408903 seconds after matching all 61 frozen-core files and all
69 captured entries. It exposed 577,028 input, 3,288 output, and 580,316 total
tokens, of which 474,880 input tokens were cached. Other per-agent
token counts were unavailable and remain `null`.

After sealing A14's approved snapshot, the first staged-index check reported 14
new files with blank lines at EOF. The frozen `git diff --check` had inspected
no untracked files, so its recorded success did not cover the eventual root
commit. This concrete failed acceptance test reopened Stage 1, invalidated the
seal for commit purposes, and added a focused untracked-text hygiene gate before
the next freeze. Revision `0.1.4` now rejects a final empty logical line in every
frozen core text file. Its regression and aggregate gates pass 9/9 and 83/83,
respectively; disposable full-tree staging also passes the cached diff check
without touching the real index. An independent child reviewer verified the 14
edits as exact one-LF removals against the prior hashes and approved with no
findings.

The Stage 1 session tree has issued 34 subagents plus the root coordinator,
with observed peak concurrency four. A compact-packet fixer used one child
reviewer; the child requested five integrity properties and approved the
corrected shape. A transport fixer likewise used an independent child reviewer,
which approved the explicit-routing boundary with no findings. The bootstrap
ordering fixer was independently rejected once for helper-level authority
injection and a verification-to-capture race; its fresh re-review approved the
canonicalized, post-capture-bound result. The whitespace fixer also delegated a
fresh reviewer, while a separate read-only closeout audit reconciled the stale
A14 evidence and final allowlist before refreeze. Exact collaboration timing
and token usage were not exposed, so those records use bounded windows rather than
estimates. Three additional read-only scouts used the review wait to prepare
Stage 2 and Stage 3 without claiming writable ownership or changing their
deliverables.

The package-style focused unittest command also failed for the third time.
Rather than reopen accepted tooling for convenience, the recurrence is tracked
as `INC-017` and deferred to numbered issue `QPBT-011`.
