# QPBT-062 Fresh Workflow-Policy Review A02

Verdict: **REQUEST_CHANGES**

The immutable packet authenticated successfully, so this is not a `BLOCKED`
review. The candidate must not be integrated at the reviewed head. In
particular, the missing protocol `0.1.13` changelog entry is an integration
prerequisite and must be included in a new immutable candidate head, validated,
and freshly reviewed.

## Findings

### High - The policy does not make the GitHub mirror timely

`protocols/branch-lifecycle.md:42` makes freshness a property of the local
`main` commit age, while `protocols/branch-lifecycle.md:94` merely reports the
remote ahead/behind count. `protocols/branch-lifecycle.md:144` restricts who may
push and mentions bounded retries, but it defines neither a mandatory push
deadline, a retry bound/backoff, nor a blocking/escalation state when local
`main` remains ahead. The candidate can therefore report a fresh heartbeat
while the visible remote remains arbitrarily stale. The candidate's own
snapshot demonstrates this permitted state at
`workflow/reviews/qpbt-062-branch-lifecycle-a01.md:41`: local `main` is fresh
but 82 commits ahead of `github/main`.

Define a deterministic remote-sync due time and outcome, including exact retry
bounds and the canonical incident/blocking action after failure. A local
checkpoint must not count as a timely mirror heartbeat merely because its own
commit age is below 3,600 seconds.

### High - Claimed branch/worktree admission checks are not representable or enforced

`protocols/branch-lifecycle.md:17` calls the issued session the ownership
authority but does not bind a branch field; nevertheless,
`protocols/branch-lifecycle.md:29` says admission rejects duplicate writable
branches and worktrees. The listed validator's immutable session fields at
`scripts/workflow.py:71` likewise contain no branch, and its required session
shape at `scripts/workflow.py:1028` contains a worktree but no branch. Its only
cross-session guard at `scripts/workflow.py:1238` rejects overlapping owned
paths in the same ownership scope; two writers with the same worktree and
disjoint paths are accepted, and duplicate branch use cannot be detected.

The exact two-path patch changes no validator or focused test. The prose command
list at `protocols/branch-lifecycle.md:107` is not a deterministic parser or
admission gate. This does not satisfy the focused duplicate branch/worktree
validation required by `workflow/state/issues.json:3245`. Bind the branch/ref in
canonical authority and add a mechanically validated admission/topology rule,
or weaken the claim to an explicitly manual, evidence-recorded coordinator
check and supply focused counterexample evidence.

### High - Adding `0.1.13` during integration would mutate the reviewed surface

The exact reviewed changelog begins with `0.1.12` at
`protocols/CHANGELOG.md:3`; it has no `0.1.13` entry. Both `AGENTS.md:129` and
`protocols/meta.md:91` require a changelog entry for a protocol change, and the
QPBT-062 acceptance gate requires the revision in the changelog at
`workflow/state/issues.json:3246`.

`workflow/reviews/qpbt-062-branch-lifecycle-a01.md:107` instead tells the root
coordinator to append the entry during canonical integration. That would change
the exact two-path reviewed head, contrary to the immutable-head rule at
`protocols/meta.md:33` and the freeze/review/integrate order at
`protocols/orchestration.md:197`. The entry must be part of a new candidate head;
all checks and review must bind that new head before merge.

### Medium - The A01 topology artifact does not conform to the proposed contract

`protocols/branch-lifecycle.md:51` says each audit contains the displayed object,
including array-valued `candidate_reachability` and a `commands` array. It also
requires exact argv, exit status, and duration at
`protocols/branch-lifecycle.md:109`. The purported snapshot uses a prose string
for `candidate_reachability` at
`workflow/reviews/qpbt-062-branch-lifecycle-a01.md:55` and omits `commands`
entirely. Its validation section at
`workflow/reviews/qpbt-062-branch-lifecycle-a01.md:77` lists commands but no
exit statuses or durations, runs none of the required Git topology commands,
and labels outcomes as "Expected result" rather than recorded results.

Thus A01's deterministic-topology claim is unsupported by its own proposed
schema. Emit a conforming audit with per-candidate ancestry results and complete
command envelopes, then validate its shape and semantics mechanically.

### Medium - Commit retention is asserted but not guaranteed

`protocols/branch-lifecycle.md:133` requires preservation of candidate commits,
yet `protocols/branch-lifecycle.md:139` accepts missing refs or objects as merely
unavailable evidence. No protected archival ref, bundle/object retention rule,
verification cadence, or incident is defined, and the meanings and storage of
`retain`, `supersede`, and `archive` are unspecified. Avoiding destructive
deletion in the audit itself is sound, but it does not preserve an unreferenced
commit against later ref removal and Git object pruning.

Define the durable, reversible retention mechanism and where classification,
owner, reason, timestamp, and reachability evidence are recorded. Object loss
must be an exceptional finding/incident, not a normal completion state.

### Medium - Stale integration and terminal-session semantics are ambiguous

`protocols/branch-lifecycle.md:47` says stale/unknown local `main` blocks guarded
integration until the coordinator "records a real next action," but it defines
neither that record nor how it changes the stale predicate. Recording prose
does not refresh `main`, while an empty refresh commit is correctly forbidden;
the guard can therefore be cleared arbitrarily or remain circular when the
needed real action is the integration itself.

Separately, `protocols/branch-lifecycle.md:134` names `cancelled` as a terminal
session state, but `scripts/workflow.py:60` and
`scripts/workflow.py:152` permit only `finished` or `failed` before `archived`.
Specify an evaluable stale-state transition and use the canonical session
statuses (or make and test the corresponding schema transition).

## A01 Claim Audit

- Exact diff scope: verified; only `protocols/branch-lifecycle.md` and
  `workflow/reviews/qpbt-062-branch-lifecycle-a01.md` changed.
- Candidate bytes and patch: verified against every manifest digest.
- Root-only push, child no-push, and umbrella/runtime/credential/unrelated-remote
  exclusions: present in `protocols/branch-lifecycle.md:142`; these boundaries
  are not weakened by the candidate text.
- No destructive branch/worktree deletion: explicitly preserved at
  `protocols/branch-lifecycle.md:138`, subject to the retention finding above.
- A01 deterministic audit: not conforming, as described above.
- A01 validation: the listed session ledger records `workflow_validate` and
  `diff_check` as passed, but A01 itself contains only expected outcomes. Per the
  review packet, no test or validation command was rerun.
- A01 live-topology/scout claims: the listed session summaries corroborate the
  reported 82-ahead observation and zero write/network counters. The underlying
  `/tmp` scout reports were not manifest-listed and were not read, so the full
  historical topology snapshot was not independently replayed.

## Immutable Authentication

- Manifest: `/home/drx/MIPStarRE-auto/.workflow-runtime/manifests/i062-reviewer-a02-branch-lifecycle.json`
- Manifest SHA-256: `1234ba2cc39058ff033411e7f0263e6ddf5cb4c6f268618eaeea8c85f8810009`
- Base: `08b12a8cc7e9f0464f1842d0074884c96ddff832`
- Base tree: `87afa4967f7b4129bcb12539c9883280e069097b`
- Head: `889e7f8f16b09e5c6de23b3348508a48c2bc14c6`
- Head parent: `08b12a8cc7e9f0464f1842d0074884c96ddff832`
- Head tree: `04cad9b46835ab529b849510c853a07b2c8bce27`
- Patch SHA-256: `cfc57ff7a6b7f4542dc09e06c2b1f50a6e66881be8204943a07c573ab9a13557`
- Worktree: clean and detached at exact head (`git status --porcelain=v1` empty;
  `git rev-parse --abbrev-ref HEAD` = `HEAD`).

Listed object SHA-256 values, all verified:

| Git object | SHA-256 |
|---|---|
| `889e7f8:protocols/branch-lifecycle.md` | `71e64509c9fb91e3c0f1ff74c05c9f2a19de21f5c79cf6392de2310be695120f` |
| `889e7f8:workflow/reviews/qpbt-062-branch-lifecycle-a01.md` | `fc8c515d300b2bfe7d7c3f171afd56df8cd599f2fcd9de91f49d1773c84e2795` |
| `08b12a8:AGENTS.md` | `3df95336eaf3b504a7e537b04703e66c0daf6311e511e9dca3b49b1a67b3e339` |
| `08b12a8:protocols/orchestration.md` | `c017d8add3277267fa97fa57b598b1c5bda334c805d28fe120afc19f00d45701` |
| `08b12a8:protocols/meta.md` | `04525efbfbf1074c84497d26d6de6173bd3c63567898dafab1252cd6d24516c8` |
| `08b12a8:protocols/README.md` | `7a64d940c0ebb8f70d7ec94195b9feda67a41d430e569ae41750464e191543eb` |
| `08b12a8:protocols/CHANGELOG.md` | `b35c3930e70b9a61fd3d85926a760edf6d261bffa18687c95aa18a250a818fb1` |
| `08b12a8:scripts/workflow.py` | `04e0d92a5f52949322a4c5089269cc9f223b0e32f3ca36c3b6b6651ded0b02ab` |
| `08b12a8:workflow/state/issues.json` | `803ca262f7006009665e79a10cbd32225ba05714d4dc55d64e70eae5521a46e8` |
| `08b12a8:workflow/state/prs.json` | `bdc4d957b995eb57bb176d5c6d759bcbe1c911f2925c1e8501671331351cc28c` |
| `08b12a8:workflow/state/sessions.json` | `1a816009a291d949c359e2e7b9658335d85ae964e97896740f513e03af041c72` |

## Timing, Counters, and Residual Risk

- Review window: `2026-09-03T12:36:53Z` to `2026-09-03T12:40:25Z`
  (`212` seconds, runtime-measured wall clock).
- Token usage: `null`; the collaboration backend does not expose per-agent token
  usage.
- Subagents/nested agents: `0`; topology: one fresh read-only reviewer only.
- Repository writes: `0`; Git writes: `0`; state writes: `0`; metric writes: `0`.
- Report writes: `1`, only `/tmp/i062-review-a02-branch-lifecycle.md`.
- Tests/builds/compile attempts/cache actions: `0/0/0/0`, prohibited and not
  needed for this document-policy review.
- Network calls/endpoint calls/GitHub writes/credential reads: `0/0/0/0`.
- New issues/incidents/PR actions: `0/0/0`.

Residual risk: live refs, worktrees, remote state, and transport were not queried,
and the candidate's claimed validation was not rerun, exactly as required by the
packet. Review conclusions are limited to the authenticated Git objects listed
above. The textual no-destructive-deletion and authority exclusions are clear;
the material residual risks are enforcement, durable retention, and remote-sync
timeliness.
