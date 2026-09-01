# QPBT-026 / LPR-016 supplemental review A04

- Logical session: `i026-reviewer-a04-pr016-supplemental`
- Verdict: `request_changes`
- Scope: supplemental finding F-004 only; this is not a rewrite of the frozen
  A03 review record.
- Base: `ea584e9e894391773e09ddad2ce4d082497c7913`
- Head: `5d6164e949a32c906557a136c7e49558ea13d7ae`
- Tree: `7af3fb789c5a4438482599b25e0d42a2088bbba6`
- Repository edits: none.
- Network/endpoint/GitHub/credential/Lean/Lake/build/cache actions: none.

## Finding

### F-004 (high): credential-path rejection is basename-only and incomplete

The documented contract says credential or secret-looking paths are rejected
(`protocols/review.md:50-52`), but `scripts/local_agent.py:642-643` applies
`DISCLOSURE_FORBIDDEN_PATH_RE` only to `Path(path).name`. The pattern has no
rules for common key/credential paths such as `keys/id_rsa`,
`.ssh/authorized_keys`, `private/private_key.pem`, `certs/client.pem`, or
`.aws/config`; all of these can therefore be accepted if they are changed
paths and listed in an otherwise valid authorization. With the candidate
implementation their contents enter the frozen harness and external prompt
while `exclude_credentials` remains true. This is a direct credential-leakage
gap, not merely a naming-style concern.

Smallest fix: reject sensitive directory components and established private-key
or credential filenames/extensions, or use a reviewed allowlist for files that
may be disclosed. Add focused regressions for representative nested and
extension-based names. Keep explicit authorization in addition to this
fail-closed filter.

## Provenance

This finding was discovered after the first A03 report bytes had already been
frozen in the PR ledger. During that later A03 continuation, a read-only regex
smoke check showed that the candidate expression returns no match for
`keys/id_rsa`, `private/private_key.pem`, `.ssh/authorized_keys`,
`certs/client.pem`, `.aws/config`, and `credentials/config`. Those are literal
test strings; no credential file or credential content was read.

Validation provenance is inherited from A03 and was not rerun for this A04
evidence-preservation follow-up:

- Focused `test_local_agent.py` suite: passed 51/51 in 4.036 seconds (4.216
  seconds command wall time).
- `compileall`: passed; its later measured wall time was 0.04 seconds.
- Workflow validation: passed with `valid=true`; its later measured wall time
  was 0.11 seconds.
- `git diff --check`: passed; its later measured wall time was 0.02 seconds.
- Base/head ancestry, exact head/tree identity, five-path diff identity, and
  clean worktree checks: passed.

No new tests or validation commands were run for A04. Session-level A04 elapsed
time is unavailable because the collaboration runtime exposes individual tool
wall times but no logical-session start/stop duration; no estimate is made.
Token usage is unavailable because the local tools expose no model token data;
no estimate is made.
