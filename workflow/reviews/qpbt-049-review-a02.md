# LPR-025 Immutable Review A02

Verdict: `request_changes`

Integration gate: **blocked**. The candidate does not yet enforce the task-release lease at the governed local-agent launch boundary, and its event-log validator does not fully bind release attestations to the issued collaboration identity.

## Findings

### F-LPR025-001 (blocker, open)

`scripts/local_agent.py:381` calls `workflow_state._transition_record("issued-session", record, "running")` directly from `claim_issued_session`. The candidate's release check exists only inside `scripts/workflow.py:3170-3183`, in the CLI `transition` command. Consequently a real governed launcher can claim an issued `codex-collaboration` row and transition it to `running` without any `session.released` event. A direct immutable-module replay of `_transition_record` confirms that an issued collaboration record becomes running without rejection; the production `claim_issued_session` path reaches that call. This defeats the core acceptance gate. Fix the actual lease path (and add a local-agent regression), or move the check into a shared transition/claim API that every launcher uses.

Disposition: `open`.

### F-LPR025-002 (blocker, open)

`scripts/workflow.py:1482` classifies `session.released` as a lifecycle phase, while `scripts/workflow.py:1507` only counts and orders releases. The validator never verifies the payload `external_id` against the issued session's immutable identity, never rejects a release event attached to a non-collaboration session, and never requires a release for a collaboration session whose durable status is already `running`. An in-memory replay with an issuance for `thread-good` followed by a release carrying `thread-BAD` is accepted by `validate_event_log`; a running collaboration record with only its issuance event is also accepted. This permits malformed or manually altered canonical histories to validate and leaves the durable fail-closed contract incomplete. Bind and validate the release payload, enforce the backend/status scope, and require exactly one valid release before running/terminal progression as appropriate.

Disposition: `open`.

## Checks

- Immutable object authentication: base `b0d5c83f7aa215a3c37372a962cb82019ceefa2d`; head `d202aca7c352d5480bff3726539a3354d5176b52`; head tree `b9987862ab36204033cc4f63e5b6f465a1214d92`; parent `b9ca40aa590b99c903cc4a8385e229e7d6a2e594`; ancestry verified; exact changed paths are the five paths in the issued manifest.
- Supplied five-path manifest SHA-256: `a8c3ba182170da1f550612b3118fa76509359e6e709a3d8af43b28f302a7575e`.
- Candidate report object SHA-256: `5d195c0c3f912208000395b056b36b58ea8df748c170a0073e644271255413de`; recomputed from `workflow/reviews/qpbt-049-task-release-a01.md`.
- Candidate `scripts/workflow.py` and `tests/test_workflow.py` compiled directly from immutable Git blobs.
- Candidate workflow test source executed in memory against the immutable workflow module: `78/78` passed.
- `python3 tests/test_check_workflow.py`: `3/3` passed.
- `git diff --check b0d5c83f7aa215a3c37372a962cb82019ceefa2d d202aca7c352d5480bff3726539a3354d5176b52`: passed.
- No Lean/Lake build, cache operation, network, endpoint, GitHub, credential, repository, or candidate-worktree mutation performed.

## Authentication and metrics

- Reviewer identity: `/root/i049-reviewer-a02-task-release`.
- Review mode: fresh, read-only, immutable candidate review.
- Token usage: `null` for input/output/total; collaboration backend does not expose per-agent token counters.
- Topology: subagents `0`; nested agents `0`.
- Compile attempts: `2` (in-memory candidate blobs; both passed).
- Workflow/checker test attempts: `2` (`78/78`, `3/3`; passed).
- Cache/build attempts: `0`.
- Network/endpoint/GitHub/credential actions: `0`.
- Repository/candidate edits: `0`; report-only output written to `/tmp/qpbt-049-review-a02.md`.
- Timing: runtime measured by tool calls; no token timing exposed.
