# QPBT Stage 2 integration-order scout A07

## Verdict

Integrate LPR-017 first, using its eventual A05 head as an immutable second
parent of a true merge commit. Then checkpoint canonical activation of the
QPBT-027 ledger contract. Integrate exact approved LPR-016 head
`5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a` second, again with a true merge.
Do not rebase, replay, squash, or cherry-pick either candidate: those operations
would replace the reviewed candidate identity instead of preserving it in the
merge ancestry.

The two candidate ranges independently merge cleanly with checkpoint
`e5c078e25fa2633d0e4a836ca7cca8872d78af6f`, but that does **not** prove the
second merge is conflict-free after the first. The likely sequential conflicts
are `protocols/CHANGELOG.md` and `protocols/review.md`. Resolve each as a
semantic union, retaining all QPBT-027 finding-reconfirmation text and all
QPBT-026 fail-closed disclosure/offline-isolation text. Because this produces a
new combined tree whose bytes were not the approved tree of either candidate,
the resolved integration merge requires fresh independent read-only review
before main advances to it.

## Immutable evidence

- Scout checkpoint: commit
  `e5c078e25fa2633d0e4a836ca7cca8872d78af6f`, tree
  `754dc024c35a463a55f296eba459a573128480e5` (both exactly matched).
- LPR-017 reviewed A01: base
  `506ac7a7b57a2318e0764acfc2558dc62f9e50f0`, head
  `44ecdce96e5536407f89266b2be59820be56f01c`; merge-base with checkpoint is
  exactly its base; range length 1. Its five-path range is the two protocol
  files, `scripts/workflow.py`, `tests/test_workflow.py`, and
  `workflow/reviews/qpbt-027-finding-reconfirm-a01.md`.
- LPR-016: base `ea584e9e894391773e09ddad2ce4d082497c7913`, approved head
  `5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`; merge-base with checkpoint is
  exactly its base; range length 5. Its manifest is exactly nine paths: two
  protocol files, `scripts/local_agent.py`, `tests/test_local_agent.py`, and
  five QPBT-026 reports.
- The checkpoint is five commits beyond LPR-017 A01 and eight commits beyond
  LPR-016. This is stale-base integration, not candidate-head drift.
- Classic read-only `git merge-tree BASE CHECKPOINT CANDIDATE` reported only
  `merged` results for both candidates, with no `changed in both`, `added in
  both`, or conflict marker. Candidate `git diff --check` was clean for both.

## Add/add and content analysis

There are six apparent report add/add cases against main, but they are
byte-identical and should collapse without resolution:

| report | checkpoint blob | candidate blob | result |
|---|---|---|---|
| `qpbt-027-finding-reconfirm-a01.md` | `06e0c36a...` | `06e0c36a...` | identical |
| `qpbt-026-capability-schema-a19.md` | `80d15f96...` | `80d15f96...` | identical |
| `qpbt-026-disclosure-preflight-a01.md` | `2923e68d...` | `2923e68d...` | identical |
| `qpbt-026-disclosure-preflight-a05.md` | `0ccf818f...` | `0ccf818f...` | identical |
| `qpbt-026-disclosure-preflight-a11.md` | `da1e5c1c...` | `da1e5c1c...` | identical |
| `qpbt-026-offline-isolation-a17.md` | `ea20399f...` | `ea20399f...` | identical |

Independent virtual merges also preserve candidate protocol blobs directly:
LPR-017 yields `f5fcf6d0...` and `84b5c607...`; LPR-016 yields `86c14327...`
and `6582dadc...`. Sequentially, however, both candidates prepend changelog
material at the same top-of-file anchor. In `protocols/review.md`, QPBT-027
inserts the new resolution/confirmation rules immediately after the findings
ledger paragraph while QPBT-026 rewrites a broad surrounding review protocol
range. Expect content conflicts in exactly these two overlapping protocol
paths. There is no code-path overlap between the candidates.

Resolution requirements:

1. Changelog: retain the complete QPBT-027 candidate entry and every QPBT-026
   dated entry, ordered coherently; do not choose either side wholesale.
2. Review protocol: retain QPBT-026's production-dispatch fail-closed and
   offline-test boundary, plus QPBT-027's immutable resolution evidence,
   append-only `confirmation_review_ids`, chronological/current-head checks,
   and approval/merge semantics.
3. Confirm all six report blobs above remain unchanged after the merges.
4. Confirm the A05 delta is exactly its promised three paths relative to
   `44ecdce...`; its inherited protocol/report bytes must remain those already
   reviewed unless A05 explicitly changes them (which would violate scope).

## Canonical checkpointing

Before any merge, run workflow validation, record the actual A05 head and its
review/approval in canonical state, validate again, and commit that state-only
checkpoint. Do not rewrite the immutable `base_sha`/`head_sha` fields to current
main. A05 must be a direct descendant of `44ecdce...`, and its parent delta must
be exactly:

```
scripts/workflow.py
tests/test_workflow.py
workflow/reviews/qpbt-027-stale-append-fix-a05.md
```

After the reviewed LPR-017 merge is activated, make a separate canonical
checkpoint setting LPR-017 merged with its merge commit SHA and QPBT-027 done;
retain its original candidate base/head and review ledger. This activation is
needed before validating LPR-016 approval/reconfirmation under the repaired
ledger contract. Then create and independently review the LPR-016 integration
merge. After activation, checkpoint LPR-016 as merged with its own integration
SHA and reconcile QPBT-026 status/closure gates. Run validation immediately
before and after every canonical state mutation. Never mix state reconciliation
into either immutable candidate head.

## Executable integration sequence

The coordinator should substitute `A05` and generated integration SHAs only
after resolving them exactly.

```sh
python3 scripts/workflow.py validate
git rev-parse A05 A05^ A05^{tree}
git merge-base --is-ancestor 44ecdce96e5536407f89266b2be59820be56f01c A05
git rev-list --count 44ecdce96e5536407f89266b2be59820be56f01c..A05
git diff --name-status --no-renames 44ecdce96e5536407f89266b2be59820be56f01c..A05
git diff --check 44ecdce96e5536407f89266b2be59820be56f01c..A05
```

Expected: ancestor success, count `1`, and exactly the fixed three-path A05
delta. Bind/review/approve that exact A05 SHA, checkpoint canonical state, then
create a no-fast-forward true merge on an integration branch. Verify its
parents are `(current-main-before-merge, A05)` and preserve A05 as an ancestor.
Run the QPBT-027 gates below and obtain fresh review if the merge resolved any
bytes rather than taking candidate blobs unchanged. Activate the reviewed merge
and checkpoint LPR-017/QPBT-027 state.

Next create a no-fast-forward true merge of `5bf6e08...` on an integration
branch. Resolve only the two protocol files as the union specified above. Its
parents must be `(post-LPR-017-main, 5bf6e08...)`; `5bf6e08...` must remain an
ancestor. Review the exact resolved merge commit independently, activate it
only after approval, then checkpoint LPR-016/QPBT-026 state.

## Exact post-merge validation

Run after LPR-017 integration and again after the combined LPR-016 integration;
the local-agent focused test is mandatory after LPR-016:

```sh
python3 scripts/workflow.py validate
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflow.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_agent.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPYCACHEPREFIX=/tmp/qpbt-stage2-integration-pycache python3 -m compileall -q scripts tests
python3 scripts/check_workflow.py
make -C blueprint test check graph
git diff --check
git status --porcelain
```

Also verify ancestry/parents and report identity:

```sh
git show --no-patch --format='%H%n%P%n%T' LPR017_INTEGRATION
git show --no-patch --format='%H%n%P%n%T' LPR016_INTEGRATION
git merge-base --is-ancestor A05 LPR016_INTEGRATION
git merge-base --is-ancestor 5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a LPR016_INTEGRATION
git ls-tree -r LPR016_INTEGRATION -- workflow/reviews
```

No Lean source, declaration list, pin, or build recipe changes occur in either
manifest. Therefore no new Lean compile/cache operation is justified by these
merges; the aggregate workflow and blueprint synchronization gates above cover
the affected surfaces. If repository policy nevertheless requires the global
pre-review build, use the elected hot-main-cache protocol once, never a shared
writable build directory.

## Review boundary and residual risks

- Candidate approvals remain evidence about their immutable heads, not about a
  manually combined protocol tree. Fresh review is mandatory for the LPR-016
  resolved merge; it should check protocol semantics and combined workflow and
  local-agent tests. If LPR-017's merge is mechanically clean and its code blobs
  equal A05 exactly, candidate review can remain sufficient, subject to the
  project's integration-review gate. Any manual byte resolution triggers fresh
  review there too.
- A05's SHA is unknown. No integration should start until its direct ancestry,
  one-commit distance, exact three-path delta, validation, and independent
  approval are recorded.
- Classic three-way previews cannot exactly materialize the sequential merge
  tree without writing Git objects; the two-file sequential conflict forecast
  is therefore evidence-based but not an observed second-merge result.
- Canonical state evidence added after this scout can alter merge context.
  Re-run read-only merge previews from the actual pre-merge main and inspect
  every resolved path before committing.

## Session metrics

- Stable session: `i027-scout-a07-integration-order`
- Mode/topology: one read-only scout; no subagents
- Repository/Git writes: 0; refs created: 0; merges/rebases/checkouts: 0
- Tool batches: 6; observed read-only Git subcommand executions: 35
- Compile/build/cache/network/endpoint attempts: 0
- Exposed tool wall time: approximately 1.6 seconds across command calls;
  end-to-end session elapsed was not exposed
- Token usage: `null` (runtime did not expose per-session token accounting)
- Findings: 1 required fresh-review boundary; 2 likely sequential content
  conflicts; 6 byte-identical apparent add/add reports
