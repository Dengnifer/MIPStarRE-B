# QPBT-026 / LPR-016 immutable review A03

- Verdict: `request_changes`
- Base: `ea584e9e894391773e09ddad2ce4d082497c7913`
- Head: `5d6164e949a32c906557a136c7e49558ea13d7ae`
- Tree: `7af3fb789c5a4438482599b25e0d42a2088bbba6`
- Exact changed paths: 5
- Repository was clean at review start and remained clean; no files in the
  repository were edited. No endpoint, GitHub, credential, Lean, Lake, build,
  or cache command was used.

## Findings

### F-001 (blocker): authorization contents are copied into prompt and result envelope

`scripts/local_agent.py:2885-2886` adds the validated authorization mapping to
the `target` object. That object is serialized into the trusted review prompt
at `scripts/local_agent.py:1100-1104` and into the result envelope at
`scripts/local_agent.py:2969`/`3069`. The mapping contains the endpoint,
model, immutable revisions, and every `private_file_paths` entry. This directly
violates the new protocol contract at `protocols/review.md:48-52`, which says
authorization contents are never copied into prompts, envelopes, or logs.
It also creates an unnecessary disclosure of the private scope to the external
reviewer and to persisted runtime artifacts. The focused regression currently
asserts this contrary behavior at `tests/test_local_agent.py:1292-1296`.

Smallest fix: remove the authorization mapping from `target`/`review_target`
and from prompt construction. If an audit marker is required, use only a
constant non-sensitive boolean or digest whose semantics are explicitly added
to the protocol; do not retain the endpoint/path/revision mapping.

### F-002 (blocker): no custom transport profile bypasses the required disclosure gate

`scripts/local_agent.py:697-704` returns success (`None`) whenever
`transport_profile is None`. Both the unbound path (`:2613-2618`) and the bound
path (`:2691-2697`) therefore skip disclosure authorization; the bound path
then claims the issued lease at `:2697` and the execution path eventually runs
the model-backed `codex ... exec` command at `:2908-2945`. The CLI repeats the
same optional gate at `:3501-3506` before persistence probing. There is no
local/offline execution mode here: this command invokes Codex, and with no
override it inherits the user's configured provider/destination.

This is a disclosure bypass for default/user-configured external providers,
contrary to `protocols/review.md:35-40`, which requires an exact endpoint,
model, wire protocol, evidence scope, and explicit user authorization before
any external model-backed reviewer starts. It also fails the QPBT-026 gate
that dispatch refuses before lease issuance when destination/model/scope is
absent. Existing no-profile tests exercise the bypass (for example
`tests/test_local_agent.py:1307-1320`).

Smallest fix: require a validated transport profile and matching disclosure
authorization for every model-backed review dispatch, or add and enforce a
genuinely local/offline mode that cannot send evidence externally. Do not use
presence of a custom profile as the definition of “external.”

### F-003 (high): commit-target `head_sha` drift is detected only after lease claim

For `target_kind == "commit"`,
`scripts/local_agent.py:681-688` resolves the commit from `target_value` but
does not compare the supplied `head_sha` to that resolved commit. In the bound
review path, preflight returns and the issued lease is claimed at
`scripts/local_agent.py:2691-2700`; only later does
`_run_review_after_persistence_probe` reject a mismatching `head_sha` at
`scripts/local_agent.py:2779-2784`. Thus a caller can present a valid
authorization for commit A while passing `target_value=A, head_sha=B`; the
authorization preflight succeeds and a lease is claimed before the revision
drift is rejected/recovered.

This violates the required fail-closed ordering in `protocols/review.md:46-50`
and QPBT-026's “before lease issuance” revision gate. Smallest fix: in the
commit branch, require a supplied `head_sha` (when present) to resolve exactly
to `resolved_head` during `_review_disclosure_target`, and make the preflight
and final target resolver share that check.

## Validation and identity checks

- `python3 -m unittest discover -s tests -p 'test_local_agent.py'`: passed,
  51 tests in 4.036 seconds (wall command time 4.216 seconds).
- `python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py`:
  passed.
- `python3 scripts/workflow.py validate`: passed, `valid=true` (27 issues,
  15 pull requests, 308 issued sessions, 7 stages).
- `git diff --check`: passed.
- `git merge-base --is-ancestor BASE HEAD`: passed.
- `git rev-parse HEAD`: exactly `5d6164e949a32c906557a136c7e49558ea13d7ae`.
- `git rev-parse HEAD^{tree}`: exactly
  `7af3fb789c5a4438482599b25e0d42a2088bbba6`.
- `git diff --name-only BASE HEAD`: exactly the five paths declared by LPR-016.
- Worktree status count: 0.

No Lean/Lake/full build or hot-main cache was run, as required by the review
assignment. Token usage is unavailable from the local tools; no estimate is
made. Measured review elapsed time (from first repository inspection through
report write): approximately 11 minutes; command-level timings above are the
authoritative timings exposed by the tools.
