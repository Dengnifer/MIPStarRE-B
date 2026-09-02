# QPBT-036 / LPR-027 no-byte-change formal adoption A03

## Findings and verdict

No blocking, high, medium, or low findings. **PASS for formal adoption and
guarded-integration readiness of the exact A02-approved LPR-027 head.** The
candidate identity, ancestry, one-path manifest, writer report, approval
report, canonical PR chronology, exact implementer binding, and clean detached
worktree all match the released packet.

This is an identity/provenance and PR-authority attestation. It is not an
independent mathematical review, a second PR approval, a rerun of candidate
checks, a merge, or QPBT-036 closure. Mathematical and source-fidelity approval
remains the work of the fresh A02 reviewer. At the evidence cutoff, canonical
LPR-027 still had status `changes_requested` because its recorded unexecuted
gate was PR-bound adoption followed by guarded integration. This report supplies
the adoption evidence without mutating canonical state; the root coordinator
retains the guarded current-main integration and post-integration gates.

## Canonical authority and chronology

- QPBT-036 existed in canonical `workflow/state/issues.json` with status
  `review`, owned path exactly
  `MIPStarRE/QPBT/Basic/Polynomial.lean`, and the four F02 acceptance gates.
- LPR-027 was created at `2026-09-01T23:08:47.942383Z`, before this session's
  task release at `2026-09-02T00:02:40.625752Z` and start at
  `2026-09-02T00:03:27.122404Z`. The PR therefore existed 54 minutes
  39.180021 seconds before this session started.
- All six registered candidate checks are `passed` on exact base
  `358cd108db045d13f4e0095a2948dd4037be2b54` and exact head
  `8467454fefefdbac7478a2df8f8c1e2d9c25fcf5`. Their completion timestamps run
  from `2026-09-01T23:06:00Z` through `2026-09-01T23:06:50Z`.
- A02 started at `2026-09-01T23:16:14.065124Z`, 9 minutes 24.065124 seconds
  after the last registered candidate check, and completed at
  `2026-09-01T23:53:38.593869Z`. Its formal verdict is `approve` on the same
  exact base/head pair and manifest, with `finding_ids: []`.
- Canonical LPR-027 has exactly one review and `findings: []`; there is no open
  finding to resolve. The head approved by A02 is unchanged at this adoption
  cutoff.
- Canonical LPR-027 names exactly
  `i036-integrator-a03-pr027-bind` in `implementer_session_ids`. The issued
  session has `pr_id: LPR-027`, external identity
  `/root/i036_integrator_a03_pr027_bind`, the packet worktree, and sole owned
  path `workflow/reviews/qpbt-036-pr027-bind-a03.md`.

Chronology verdict: the PR predates this session; every candidate check predates
the A02 review; A02 approved the unchanged exact head before this session was
released; and the canonical implementer binding identifies this exact session.

## Immutable candidate binding

- Formal base and exact sole parent:
  `358cd108db045d13f4e0095a2948dd4037be2b54`.
- Base tree: `49177ed572a18951d9bcccfcc079bd2ed1728609`.
- Candidate head: `8467454fefefdbac7478a2df8f8c1e2d9c25fcf5`.
- Candidate tree: `50fec3a3a7611f63aacff2f15568812e123ca29d`.
- Merge base: exact formal base; commit count in `base..head`: `1`.
- Exact no-renames diff: one added path,
  `MIPStarRE/QPBT/Basic/Polynomial.lean`.
- Path mode and Git blob: `100644`,
  `6bf62ea13a192aa08065512275b2bbaa180963e6`.
- Blob size: `4,812` bytes. Hashing the worktree file as a Git object reproduced
  the same blob.
- Filesystem SHA-256:
  `cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c`.
- Manifest SHA-256 over the exact newline-terminated record
  `MIPStarRE/QPBT/Basic/Polynomial.lean cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c`:
  `0e7fd38a46b63c7ee660fa14fb828e19331233b0c983a687b1a38d0a2ceb3725`.
- Writer report
  `workflow/reviews/qpbt-036-polynomial-a01.md` SHA-256:
  `2bc560658677218f5c4f040246a145b75d4a0a231d9338bedf1c4d4354eb604b`.
- A02 approval report
  `workflow/reviews/qpbt-036-review-a02.md` SHA-256:
  `24986875977e8e8e5cab4a80a98d66b9c321c102414fe338cf31cdb73106d50e`.
- `git diff --check BASE HEAD` passed with no output.
- The worktree was detached at exact HEAD and had no tracked, staged, or
  untracked changes before report creation. The report path did not exist.

The canonical PR's administrative `changed_paths` also names the writer and
review reports. Those reports live in the coordinator snapshot and were hashed
there. The immutable candidate commit itself has exactly the one code path
above, matching the packet manifest.

## Commands and results

All authentication commands were read-only. `AGENTS.md` was read first with
`sed -n '1,260p' AGENTS.md`. The two upstream reports were read in full with
`sed -n '1,320p'` from the canonical coordinator worktree.

The complete canonical cross-record predicate was run as:

```text
jq -e -s '(.[0].pull_requests[] | select(.id == "LPR-027")) as $pr | (.[1].issued[] | select(.id == "i036-integrator-a03-pr027-bind")) as $session | ($pr.created_at < $session.task_released_at) and ($pr.created_at < $session.started_at) and ($pr.base_sha == "358cd108db045d13f4e0095a2948dd4037be2b54") and ($pr.head_sha == "8467454fefefdbac7478a2df8f8c1e2d9c25fcf5") and ($pr.implementer_session_ids == ["i036-integrator-a03-pr027-bind"]) and ($session.pr_id == "LPR-027") and ($session.external_id == "/root/i036_integrator_a03_pr027_bind") and ($pr.checks | length == 6) and all($pr.checks[]; (.status == "passed") and (.base_sha == $pr.base_sha) and (.head_sha == $pr.head_sha) and (.completed_at < $pr.reviews[0].started_at)) and ($pr.reviews | length == 1) and ($pr.reviews[0].verdict == "approve") and ($pr.reviews[0].formal_pr_review == true) and ($pr.reviews[0].base_sha == $pr.base_sha) and ($pr.reviews[0].head_sha == $pr.head_sha) and ($pr.reviews[0].completed_at < $session.task_released_at) and ($pr.reviews[0].finding_ids | length == 0) and ($pr.findings | length == 0)' workflow/state/prs.json workflow/state/sessions.json
```

Result: `true`, exit 0, both on the initial audit and at the final canonical
cutoff. This proves the pre-existing PR, exact session binding, six passed
base/head-bound checks before A02, unchanged approved head, and zero findings.

| Command | Exact result |
| --- | --- |
| `git rev-parse HEAD 'HEAD^{tree}' HEAD^ 'HEAD^^{tree}'` | head, head tree, exact parent/base, and base tree listed above |
| `git rev-list --parents -n 1 8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` | head followed only by exact base |
| `git merge-base 358cd108db045d13f4e0095a2948dd4037be2b54 8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` | exact base |
| `git rev-list --count 358cd108db045d13f4e0095a2948dd4037be2b54..8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` | `1` |
| `git diff --name-status --no-renames 358cd108db045d13f4e0095a2948dd4037be2b54 8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` | `A MIPStarRE/QPBT/Basic/Polynomial.lean` only |
| `git diff --check 358cd108db045d13f4e0095a2948dd4037be2b54 8467454fefefdbac7478a2df8f8c1e2d9c25fcf5` | exit 0, no output |
| `git ls-tree 8467454fefefdbac7478a2df8f8c1e2d9c25fcf5 -- MIPStarRE/QPBT/Basic/Polynomial.lean` | exact mode, blob, and path listed above |
| `git cat-file -s 6bf62ea13a192aa08065512275b2bbaa180963e6` | `4812` |
| `git hash-object MIPStarRE/QPBT/Basic/Polynomial.lean` | exact blob above |
| `sha256sum MIPStarRE/QPBT/Basic/Polynomial.lean` | exact filesystem SHA-256 above |
| `perl -MDigest::SHA=sha256_hex -e 'print sha256_hex("MIPStarRE/QPBT/Basic/Polynomial.lean cb69673911da3c259a822cbb8bc643e38acee18dedec2c808468f78c4d63a05c\n"), "\n"'` | exact manifest SHA-256 above |
| `sha256sum workflow/reviews/qpbt-036-polynomial-a01.md workflow/reviews/qpbt-036-review-a02.md` | exact writer and A02 digests above |
| `git status --short --branch --untracked-files=all` | `## HEAD (no branch)` and no paths before report creation |
| `git status --porcelain=v1 --untracked-files=all` | exit 0, no output before report creation |
| `git diff --quiet` and `git diff --cached --quiet` | both exit 0 before report creation |
| `test ! -e workflow/reviews/qpbt-036-pr027-bind-a03.md` | exit 0 before report creation |

At the final canonical cutoff, whole-file SHA-256 values were:

- `workflow/state/issues.json`:
  `6e2ba021d717de1ca7bdfc5fca7fd37a8461f458eb50315451ad472ab0f27636`;
- `workflow/state/prs.json`:
  `c006b52a88974530175295a9b4ef549e3ae3b46a06eb607de2453c11b38b89d5`;
- `workflow/state/sessions.json`:
  `e0e976e4bee1f8ee2b3a8fc68af4e6ae405c4471bdce6081186c8dc7b1eb79cd`.

Concurrent unrelated canonical activity can change whole-file hashes; the
LPR-027/session predicate above was rerun successfully against these cutoff
bytes.

## Scope preservation and metrics

- Stable session: `i036-integrator-a03-pr027-bind`.
- External identity: `/root/i036_integrator_a03_pr027_bind`.
- Topology: root coordinator -> one PR-bound adoption integrator; nested agents:
  `0`.
- Durable task release: `2026-09-02T00:02:40.625752Z`.
- Canonical session start: `2026-09-02T00:03:27.122404Z`.
- Final pre-report evidence cutoff: `2026-09-02T00:14:22.432644979Z`.
- Elapsed canonical start through evidence cutoff: `655.310241` seconds.
- Timing quality: canonical durable start plus agent UTC evidence sample.
- Token usage:
  `{"input":null,"output":null,"total":null,"availability_reason":"Collaboration backend does not expose per-agent token usage"}`;
  no estimate was made.
- Authentication counters: issues `1`; PRs `1`; bound sessions `1`; registered
  checks `6/6`; formal reviews `1/1`; open findings `0`; head/tree/base/parent/
  merge-base/commit-count bindings `6`; candidate paths `1/1`; blob matches
  `1/1`; filesystem hashes `1/1`; manifest hashes `1/1`; upstream report hashes
  `2/2`; canonical predicate passes `3/3`.
- Findings `0`; gate retries `0`; read-only query selector corrections `2`
  (the initial exploratory PR/session array selectors did not match the JSON
  envelope and exited without mutation); incidents `0`; protocol changes `0`.
- Candidate/repository/source edits `0`; canonical state/event/metrics/research
  edits `0`; Git/index/ref/object writes `0`; commits `0`; branches changed `0`.
- Report files edited `1`; the sole physical write is this authorized report.
- Test executions `0`; compile attempts `0`; Lean attempts `0`; Lake attempts
  `0`; target builds `0`; full builds `0`.
- Cache warm/seed/publish/other actions `0`; network requests `0`; endpoint
  requests `0`; GitHub operations `0`; credential access `0`; nested-agent or
  Codex launches `0`.
- Protocol revision evidence: `AGENTS.md` SHA-256
  `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c`.

The final SHA-256 of this report is supplied out of band to the root coordinator
because embedding a file's own digest would change that digest.
