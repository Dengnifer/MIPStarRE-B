# QPBT-026 / LPR-016 credential-path scout A07

- Logical session: `i026-scout-a07-credential-paths`
- Role: read-only security scout
- Candidate worktree: `/tmp/qpbt-026-pr016-review`
- Required head: `5d6164e949a32c906557a136c7e49558ea13d7ae`
- Observed head: `5d6164e949a32c906557a136c7e49558ea13d7ae`
- Observed tree: `7af3fb789c5a4438482599b25e0d42a2088bbba6`
- Candidate worktree status: clean
- Verdict on supplemental F-004: confirmed; a narrowly scoped fix is available
- Repository edits: none
- External endpoint, GitHub, credential-file, Lean, Lake, build, and cache actions: none

## Finding

### F-004 (high, confirmed): only the basename is screened

`scripts/local_agent.py:633-645` validates that the authorization's path list
exactly equals the committed changed-path set, but line 642 applies
`DISCLOSURE_FORBIDDEN_PATH_RE` only to `Path(path).name`. Consequently sensitive
parent components are discarded before screening. The supplemental examples
`keys/id_rsa`, `private/private_key.pem`, `.ssh/authorized_keys`,
`certs/client.pem`, `.aws/config`, and `credentials/config` all evade the
candidate predicate.

The source of the expected path set is otherwise appropriate:
`scripts/local_agent.py:691-694` obtains the immutable target tree and decodes a
NUL-delimited Git changed-path list. Authorization comparison is exact and the
committed source must be clean, at the declared HEAD, with the declared base as
an ancestor (`scripts/local_agent.py:660-694`). The filter should therefore
classify repository-relative Git paths; it should not call `resolve`, inspect a
filesystem object, or follow a symlink.

A literal in-memory regex check reproduced the gap. It returned false for all
six supplemental examples. It also exposed existing false positives: the raw
substring expression returns true for `src/tokenizer.py`,
`docs/passwordless-auth.md`, `src/secretary.py`, and
`MIPStarRE/ApiKey.lean`.

## Recommended policy

Use a small predicate such as `_disclosure_path_is_forbidden(path: str)` rather
than applying one regex to a basename or to the joined path.

1. Preserve the original Git spelling for exact authorization comparison and
   evidence. Create a separate screening form only.
2. For screening, treat both `/` and `\` as separators and case-fold every
   component. Git emits `/`, but treating a literal backslash as a separator
   also rejects Windows-looking credential names committed on POSIX.
3. Reject empty, absolute, `.`/`..`, or NUL-bearing screening components rather
   than normalizing them away. Keep the existing exact-scope validation too.
4. Reject these exact sensitive directory components wherever nested:
   `.ssh`, `.aws`, `.azure`, `.gnupg`, `.kube`, `.docker`, `.gcloud`,
   `credentials`, `.credentials`, `secrets`, and `.secrets`. Also reject the
   component sequence `.config/gcloud`.
5. Reject established exact artifacts, case-insensitively:
   `.env`, every `.env.*`, `.envrc`, `.netrc`, `_netrc`, `.git-credentials`,
   `.npmrc`, `.pypirc`, `authorized_keys`, `id_rsa`, `id_dsa`, `id_ecdsa`,
   `id_ed25519`, `kubeconfig`, `application_default_credentials.json`,
   `service-account.json`, and `service_account.json`.
6. Reject private-container suffixes `.pem`, `.key`, `.p12`, `.pfx`, `.jks`,
   `.keystore`, and `.kdbx`. Do not reject `.pub`, `.crt`, or `.cer` merely by
   extension; those normally carry public material. Blanket `.pem` rejection
   is intentionally conservative because a path-only check cannot distinguish
   a public certificate from the private key in the supplemental `client.pem`
   case.
7. If generic credential words are retained, match whole delimiter-bounded
   markers, not arbitrary substrings. High-signal markers include
   `credential(s)`, `secret(s)`, `password`, `passwd`, `api_key`, `api-key`,
   `private_key`, `private-key`, `access_token`, `refresh_token`, `auth_token`,
   and `client_secret`. This catches `deploy/client-secret.prod.json` without
   treating `tokenizer`, `passwordless`, or `secretary` as secrets.

Do not use raw directory terms `key`, `keys`, `auth`, `config`, `private`,
`cert`, or `certs`. They are common source-tree vocabulary: for example,
`src/keys/map.py`, `src/auth/session.py`, `config/build.py`, and
`docs/private-api.md`. Do not use the candidate's unbounded
`token|secret|password|credential|api[_-]?key` expression over a full path; it
would extend the existing false positives from basenames to every parent
component. Even delimiter-bounded credential words can reject ordinary tools
such as `scripts/credential_parser.py`; that tradeoff should be explicit rather
than hidden in a regex.

The smallest implementation is two frozen sets (sensitive directory
components and exact filenames), one suffix tuple, and one optional
delimiter-bounded marker expression. Apply it to the expected Git path set
before accepting authorization, and optionally also to the supplied list for a
clear early error. Exact equality remains the authority; the screening form
must never replace the recorded path strings.

## Rename and configuration hardening

Changed-path extraction should be configuration-independent and include both
sides of a rename. Use:

```text
git diff --name-only -z --no-renames BASE HEAD
```

With rename detection disabled, a rename is a deletion plus an addition, so a
sensitive old path renamed to a benign destination is still screened. This is
important because the review diff can expose the old bytes. Add `--no-renames`
at path-set derivation even if the presentation diff continues to display a
rename. The existing `_git_bytes` wrapper already disables hooks, fsmonitor,
system config, and global config; explicitly pinning rename behavior avoids
depending on Git defaults or repository-local configuration.

## Exact regression matrix

All cases should call the path predicate directly. A second integration test
should pass the same list as both `private_file_paths` arguments to
`validate_review_disclosure_authorization`, proving rejection is not merely an
exact-scope mismatch.

| Expected | Repository-relative test path | Rule exercised |
| --- | --- | --- |
| deny | `keys/id_rsa` | established private-key filename under ordinary parent |
| deny | `private/private_key.pem` | bounded marker and private container |
| deny | `.ssh/authorized_keys` | sensitive top-level directory |
| deny | `a/b/.SSH/Config` | nested directory and case folding |
| deny | `certs/client.pem` | conservative PEM container rule |
| deny | `CERTS/CLIENT.P12` | suffix case folding |
| deny | `.aws/config` | cloud credential/config directory |
| deny | `nested/credentials/config` | sensitive nested directory |
| deny | `a/.config/gcloud/application_default_credentials.json` | component sequence and exact artifact |
| deny | `deploy/.env` | exact environment file |
| deny | `deploy/.ENV.production` | `.env.*` and case folding |
| deny | `.netrc` | established credential artifact |
| deny | `home/.git-credentials` | established credential artifact |
| deny | `deploy/client-secret.prod.json` | bounded compound marker |
| deny | `deploy/refresh_token.txt` | bounded compound marker |
| deny | `.ssh\authorized_keys` | alternate separator in screening only |
| deny | `nested\credentials\config` | alternate separator and nesting |
| allow | `src/tokenizer.py` | no substring false positive |
| allow | `docs/passwordless-auth.md` | no substring false positive |
| allow | `src/secretary.py` | no substring false positive |
| allow | `src/key_value_store.py` | generic `key` is not denied |
| allow | `src/keys/map.py` | generic `keys` directory is not denied |
| allow | `src/auth/session.py` | generic `auth` directory is not denied |
| allow | `config/build.py` | generic `config` directory is not denied |
| allow | `docs/private-api.md` | generic `private` is not denied |
| allow | `certs/ca.crt` | public-certificate extension is not denied |
| allow | `certs/client.cer` | public-certificate extension is not denied |

Add these behavioral tests around the complete preflight:

1. Commit one harmless sentinel at `nested/.ssh/config`, bind an otherwise
   exact authorization to it, and require a credential-path error before
   persistence probing or harness creation.
2. Rename a harmless sentinel from `nested/.ssh/config` to `src/config.txt`;
   require the old path to remain in the computed scope and the preflight to
   fail.
3. Change a symlink blob whose repository path is `keys/id_rsa`; require path
   rejection without reading its target.
4. Change a benign symlink blob; require harness preparation to record only the
   Git link target text and never dereference it. No focused candidate test
   presently covers committed symlinks.
5. Keep the existing `credentials.json` extra-scope case, but add an exact
   sensitive-scope case. The existing test at `tests/test_local_agent.py:1256`
   fails even without credential screening because the authorization also
   mismatches the actual path set; it does not prove that a changed credential
   path is rejected.

## Symlink and scope assessment

The committed harness clones without checkout, checks out the trusted base,
then constructs a synthetic commit directly from the exact target tree
(`scripts/local_agent.py:2314-2385`). A changed symlink therefore remains a Git
blob in the target diff and is not followed by path classification or target
tree construction. This is the correct behavior for the proposed predicate.

Residual boundary: the trusted base is checked out in the harness, and the
focused tests contain no committed-harness symlink regression. A pre-existing
base symlink may therefore be traversable by a reviewer depending on sandbox
filesystem policy. Also, only changed paths are screened; a path-name filter
cannot prove that a benignly named changed file lacks a credential in its
contents. Neither limitation is repaired by a larger regex. Explicit human
authorization remains necessary, and any promise that unrelated repository
contents are mechanically inaccessible requires separate harness/sandbox
hardening.

## Validation and provenance

Read-only commands and results:

- `sed -n '1,260p' AGENTS.md`: read canonical instructions; success.
- `git rev-parse HEAD`: exact requested head; success.
- `git rev-parse 'HEAD^{tree}'`: exact supplemental tree
  `7af3fb789c5a4438482599b25e0d42a2088bbba6`; success.
- `git status --short` and `git status --porcelain=v1 -z | wc -c`: clean, zero
  status bytes.
- `rg` plus numbered `sed` reads of `scripts/local_agent.py`,
  `tests/test_local_agent.py`, and `protocols/review.md`: success.
- Read `/home/drx/MIPStarRE-auto/workflow/reviews/qpbt-026-review-a04-supplemental.md`:
  confirmed exact source finding and inherited 51/51 focused-test result.
- `git diff --name-status` and `git diff --stat` for the pinned base/head:
  confirmed the documented five-path PR scope.
- `git diff --check BASE..HEAD`: success, no output.
- `git ls-tree -r --name-only HEAD`: 227 tracked paths; no current tracked path
  matched the proposed high-confidence deny inventory. Only path names were
  inspected.
- Literal in-memory regex smoke check: success after one import attempt failed
  harmlessly because `bootstrap_manifest` was not on the standalone import
  path. No repository or credential file was opened by that attempt.
- `sha256sum` over `git show HEAD:scripts/local_agent.py` and
  `git show HEAD:tests/test_local_agent.py`: success; digests
  `31ff77ad00c5f994028cddf90c96d780731ada3a3e52c088827da8cef5db9218` and
  `f6fc2413d957206f745072b47485d63434b25a867902a832976a37795c2f6f71`.

The tool exposed command-batch wall times of approximately 0.2 seconds for
each inspection batch; individual commands generally reported under 0.01
seconds. Logical-session start/stop elapsed time is not exposed, so no total is
estimated. Model token usage is unavailable because the collaboration/runtime
tools expose no token counter; no estimate is made. No subagents were spawned.
No tests, workflow validation, endpoint calls, builds, or cache operations were
run in this scout session.

Actionable recommendations were messaged during the session to
`/root/i026_fixer_a05_disclosure_preflight`.
