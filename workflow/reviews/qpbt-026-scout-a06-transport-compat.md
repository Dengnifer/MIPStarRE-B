# QPBT-026 / LPR-016 transport-compatibility scout A06

- Session: `i026-scout-a06-transport-compat`
- Mode: logical read-only scout; no repository files edited
- Immutable worktree: `/tmp/qpbt-026-pr016-review`
- Required head: `5d6164e949a32c906557a136c7e49558ea13d7ae`
- Observed head: `5d6164e949a32c906557a136c7e49558ea13d7ae`
- Observed tree: `7af3fb789c5a4438482599b25e0d42a2088bbba6`
- Base: `ea584e9e894391773e09ddad2ce4d082497c7913`
- Frozen inputs read: `workflow/reviews/qpbt-026-review-a03-pr016-immutable.md` and `workflow/reviews/qpbt-026-review-a04-supplemental.md`

## Outcome

The smallest coherent behavior is to require all three of these for every
model-backed review dispatch, including calls that currently omit a custom
transport profile:

1. a complete explicit transport profile;
2. a nonempty explicit model; and
3. an exact committed-target disclosure authorization.

An absent profile cannot mean "local": this wrapper still constructs and runs
`codex ... exec` (`scripts/local_agent.py:2908-2945`), and it injects an explicit
destination only when `transport_profile` is non-null (`:2917-2918`). Without
that profile the wrapper does not know the actual endpoint or wire protocol, so
it cannot compare the authorization with the transport that will receive the
evidence. Deriving the expected endpoint from the authorization alone would
bind a declaration, not the actual dispatch destination.

Keep `validate_review_transport_profile`'s all-or-none parsing behavior if API
compatibility matters (`scripts/local_agent.py:498-565`), but make
`_preflight_external_disclosure` reject the returned `None` with an explicit
"review requires an explicit transport profile" error. This is narrower than
changing the reusable validator's return contract and still closes every public
dispatch path.

## Findings

### 1. Blocker: absent-profile dispatch is the primary bypass

`_preflight_external_disclosure` returns success immediately for a missing
profile (`scripts/local_agent.py:697-704`). Both direct/unbound review
(`:2606-2618`) and bound review (`:2686-2696`) accept that result. The bound path
then claims the issued lease at `:2697-2701`; the unbound path probes persistence
at `:2622-2633`; both can reach command construction and the model-backed runner.
The CLI has the same problem in its bound preflight (`:3475-3484`) and unbound
preflight (`:3499-3524`).

This is not only a review finding: the issue's canonical gate requires refusal
when any destination or model field is absent
(`workflow/state/issues.json:1144-1147`). The implementation report's statement
that no-profile reviews are "local-only" and remain unchanged is therefore
incorrect (`workflow/reviews/qpbt-026-disclosure-preflight-a01.md:49-53`). No
execution-mode branch proves that a no-profile Codex process is offline.

Required API behavior:

- Every `run_review` call, bound or unbound and native-selector or generic-exec,
  must fail before persistence probing, packet/context loading, harness creation,
  lease claim, capability probing, or child execution when the profile, model,
  or authorization is absent.
- The CLI may leave flags syntactically optional for useful diagnostics, but
  runtime preflight must require `--model`, all five transport fields, and
  `--disclosure-authorization-file` before `_packet_from_arguments`.
- `dry_run` should follow the same validation contract as current profiled dry
  runs; current code already preflights before its dry-run branch
  (`scripts/local_agent.py:2613-2620`, `:3501-3509`).

### 2. Blocker: authorization must remain transient and absent from all artifacts

The validated authorization is added to `target` at
`scripts/local_agent.py:2883-2886`. `_compact_review_target_for_prompt` begins
with a shallow copy of the whole target (`:982-988`), and
`build_trusted_review_prompt` serializes that packet at `:1077` and
`:1100-1104`. The same target is expanded into `target_record` at `:2948-2960`
and returned in the dry-run envelope at `:2961-2980` or persisted in the normal
result envelope at `:3048-3069` and `:3087`.

Remove the assignment at `:2885-2886`. Do not replace it with the raw record, a
sanitized field-by-field copy, or the path to the authorization file. Validation
may keep the mapping transiently on the Python stack. The already-recorded
`transport_profile`, resolved target SHAs/tree, and prompt digest independently
provide the non-secret execution evidence.

As defense in depth, `_compact_review_target_for_prompt` should reject or remove
the reserved `disclosure_authorization` key. It is directly unit-tested and can
be called with caller-constructed target mappings (`tests/test_local_agent.py:277`),
so removing only the current producer leaves an easy future reintroduction into
the prompt. The normal target builder remains responsible for keeping the key
out of `target_record` and envelopes.

No other Python consumer in the frozen tree reads this envelope field. The only
consumer is the contrary assertion at `tests/test_local_agent.py:1293-1296`.
Its removal is therefore a narrow output-schema change, with no executable
downstream migration outside this test.

### 3. High: commit `head_sha` drift must be rejected in the pre-claim resolver

For `target_kind == "commit"`, `_review_disclosure_target` resolves
`target_value` but ignores a supplied `head_sha`
(`scripts/local_agent.py:681-688`). Authorization can therefore bind commit A
while the call declares `head_sha=B`. Bound `run_review` accepts the preflight
and claims at `:2691-2701`. Only the post-claim target resolver compares the
declared head at `:2771-2784`, after which recovery marks the lease failed
(`:2716-2720`).

In the commit branch of `_review_disclosure_target`, resolve a non-null
`head_sha` with `require_full=True` and require it to equal `resolved_head`
before returning the authorization scope. Preserve the current optionality: an
omitted commit `head_sha` is not drift because `target_value` itself supplies the
resolved authorized head. Prefer sharing this check with the later target
resolver so their error and full-SHA rules cannot diverge again.

### 4. High: the post-persistence internal dispatcher is an accidental bypass

`_run_review_after_persistence_probe` is an internal but directly callable
dispatcher (`scripts/local_agent.py:2724-2744`). It accepts
`disclosure_authorization=None`, never validates it, prepares the harness, and
can execute Codex. The unbound CLI calls it directly at `:3524-3542`; it passes
the raw authorization rather than the value returned by the preflight at
`:3501-3506`. Existing CLI tests mock this internal boundary
(`tests/test_local_agent.py:1039`, `:1730`).

The normal public paths currently preflight first, but a later internal caller
can bypass the gate by calling this helper. Small coherent options are:

- consolidate all command-capable paths behind one preflighted dispatcher; or
- pass a private, non-sensitive preflight result into the helper and fail if it
  is absent, while re-resolving the immutable target immediately before harness
  creation.

A raw authorization mapping should not serve as the proof marker. It is both
sensitive scope metadata and not proof that validation occurred. If the helper
instead defensively re-runs validation, public callers must still run the first
preflight before persistence/packet/lease operations to preserve gate order.

### 5. Compatibility hazard: the new committed-only gate conflicts with legacy bootstrap behavior

The new protocol says uncommitted targets cannot be externally disclosed
(`protocols/review.md:42-52`), and `_review_disclosure_target` rejects every
non-committed target (`scripts/local_agent.py:689-690`). Requiring preflight for
no-profile calls therefore intentionally disables all current uncommitted
review dispatches. However, the same protocol still specifies an external
unborn Stage 1 `--uncommitted` launch (`protocols/review.md:64-68`, `:92-99`).
These statements cannot both describe the current authorization schema, which
requires immutable base/head/tree fields.

Do not retain the absent-profile bypass to preserve bootstrap tests. The
smallest QPBT-026 fix is committed-only dispatch and an explicit note that the
legacy Stage 1 launch is unavailable under this gate. Restoring it requires a
separate design: either a genuinely non-network local executor or a versioned
authorization schema binding the verified uncommitted snapshot/manifest
digests. That is larger than the three reviewed repairs.

## Call-site audit

The frozen executable tree has no production caller outside
`scripts/local_agent.py`; all other Python callers are in
`tests/test_local_agent.py`.

| Entry/call site | Current ordering | Required adjustment |
| --- | --- | --- |
| `_run_review_unbound` (`scripts/local_agent.py:2582-2652`) | validates profile, optional preflight, then persistence | reject null profile/model/auth; pass only a non-sensitive proof onward |
| public `run_review`, unbound/dry (`:2655-2682`) | delegates to unbound path | inherits strict preflight |
| public `run_review`, bound (`:2683-2704`) | optional preflight, claim, then repeats unbound preflight | strict target/profile/auth preflight and commit head equality before `claim_issued_session` |
| CLI bound (`:3456-3498`) | loads auth/profile, optional preflight before packet, then public bound call | require complete values; preserve pre-packet and pre-claim order |
| CLI unbound (`:3499-3542`) | optional preflight, persistence, packet, direct internal dispatch | require complete values and pass non-sensitive preflight proof to guarded helper |
| `_run_review_after_persistence_probe` (`:2724-3088`) | no disclosure validation; copies auth into artifacts | require proof/revalidation; remove authorization argument from target construction/output |
| prompt compactor (`:982-1049`) | copies arbitrary target keys | defensively omit/reject reserved authorization key |

## Exact test migration

Existing tests already supplying a complete profile and authorization:

- `test_generic_review_is_persistent_read_only_and_records_exact_target`
  (`tests/test_local_agent.py:828-909`): keep success behavior; add assertions
  that `disclosure_authorization`/`private_file_paths` are absent from the prompt,
  returned envelope, and persisted `result.json`.
- `test_review_transport_overrides_precede_exec_and_retain_isolation`
  (`:1075-1141`): keep; it covers both native/generic command transport.
- `test_external_disclosure_preflight_is_exact_and_precedes_evidence`
  (`:1205-1296`): replace the contrary equality assertion at `:1293-1296`
  with absence assertions for prompt and envelope.

Committed success/output tests that must receive a shared exact profile/auth
fixture so they still reach the behavior they intend to test:

- ordinary provider failure (`tests/test_local_agent.py:1048-1073`);
- timeout evidence (`:1298-1336`);
- native selector/synthetic diff (`:1352-1382`);
- malicious-head authority isolation (`:1384-1413`); and
- bound worktree revalidation (`:1924-1962`).

Target-validation negative tests at `tests/test_local_agent.py:1338-1350` and
`:1415-1459` must at least supply a complete profile so the target error remains
the first failure. Where the target reaches authorization comparison, use a
fixture matching that exact revision. Do not weaken the new preflight merely to
preserve old error ordering.

Persistence/CLI ordering tests must become committed exact-scope fixtures:

- persistence failure before evidence (`tests/test_local_agent.py:911-942`);
- CLI failed/single persistence probes (`:944-1046`); and
- CLI bootstrap-digest wiring (`:1706-1737`), unless it is moved to a parser or
  argument-forwarding unit that mocks the disclosure preflight explicitly.

The following uncommitted dispatch-success tests cannot receive a valid version-1
authorization and should be refactored to lower-level harness/manifest/prompt
units or changed to assert fail-closed rejection:

- unborn bootstrap isolation (`tests/test_local_agent.py:1461-1505`);
- tampered harness manifest (`:1507-1537`);
- bootstrap post-capture revalidation (`:1539-1582`); and
- native uncommitted selector (`:1584-1610`).

Add these focused regressions:

1. `test_review_without_transport_profile_rejects_before_probe_or_evidence`:
   use a clean committed target and otherwise valid authorization; omit all
   transport fields and assert no persistence probe, packet read, harness, runner,
   or claim.
2. A CLI equivalent proving missing destination/model/auth rejects before
   `_packet_from_arguments` and `_probe_codex_persistence`.
3. `test_commit_head_drift_rejects_before_bound_lease_claim`: authorize commit A,
   pass `target_value=A` and full `head_sha=B`, and assert
   `claim_issued_session` and the child runner are never called (or the real
   issued record remains `issued`, not recovered `failed`).
4. `test_authorization_is_not_prompted_or_persisted`: exercise a real fake-runner
   success, then inspect prompt bytes, the returned envelope, and `result.json`;
   assert the reserved key and the unique `private_file_paths` marker are absent.
5. `test_internal_post_probe_dispatch_requires_preflight`: direct invocation of
   `_run_review_after_persistence_probe` without its proof must fail before
   harness creation/runner execution.
6. Preserve the existing exact mismatch matrix at
   `tests/test_local_agent.py:1249-1275`, and add a case for an otherwise valid
   authorization paired with no transport profile. The exact-key validation at
   `scripts/local_agent.py:613-615` should also have an explicit missing-field
   regression to match the issue gate.

## Residual observations

- The target is re-resolved after claim (`scripts/local_agent.py:2746-2826`), so
  source drift after a valid preflight is detected before harness preparation;
  bound failure is then recovered. The reviewed defect is specifically caller-
  declared commit head drift that was already knowable before claim.
- Transport profile recording in the envelope (`scripts/local_agent.py:2976`,
  `:3065`) is not authorization leakage. Endpoint/model/wire are required audit
  facts and also appear independently in the executed command. The forbidden
  material is the authorization record, particularly its exact private path
  scope and consent controls.
- The supplemental credential-path F-004 remains independently valid. It is not
  repaired by the three changes audited here.

## Commands and results

All commands were read-only with respect to the repository. No endpoint,
network, GitHub, credential, Lean, Lake, build, or cache action was used.

- `git rev-parse HEAD` in the immutable worktree: passed; exact required head;
  tool wall time was part of a 0.2-second parallel inspection batch.
- `git log -1 --format='%H%n%T%n%P%n%s'`: passed; observed head/tree/base and
  subject `feat(review): require exact disclosure preflight`; 0.3-second
  parallel batch.
- `git diff --name-only BASE..HEAD`: passed; exactly five candidate paths;
  0.3-second parallel batch.
- Read-only `rg`, `awk`, `sed`, `nl`, and `git show/diff` call-site/source scans:
  passed; individual parallel batches ranged from 0.1 to 0.4 seconds.
- `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p
  test_local_agent.py`: passed 51/51; unittest reported 4.325 seconds, tool wall
  time 4.338 seconds.
- `git diff --check BASE..HEAD`: passed; 0.2-second parallel batch.
- Final immutable-worktree `git status --short`: empty.

Session-level elapsed time is unavailable because the collaboration runtime
exposes tool-call wall time but not a logical-session timer; no estimate is
made. Token usage is unavailable because the collaboration runtime does not
expose per-agent model token counts; no estimate is made. Subagents: 0.
