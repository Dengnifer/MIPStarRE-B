# GitHub PR-029 Review Repairs A02

## Identity

- Canonical issue: GitHub #31
- Pull request: GitHub #29
- Stable orchestrator session: `i031-orchestrator-a02-pr29-safety-repairs`
- Orchestrator external ID: `/root/i031_orchestrator_a02_pr29_safety_repairs`
- Reviewer session: `i031-reviewer-a02-pr29-repairs`
- Reviewer immutable external ID: `/root/i031_reviewer_a02_pr29_repairs`
- Reviewed base SHA: `4a6683795a71712d6a5c52b7539c2f532fd39f71`
- Reviewed head SHA: `682513ac07f8f600886555d06ea9ccfa421bd15b`
- Review artifact SHA-256:
  `078b55d141fd47e3a8a3f813f03b3245798d07d6a0a952841a1d5a2a038adf8f`
- Reviewer verdict before repair: `request_changes`

## Finding Dispositions

### R2-F1: Post-cutover event append followed a leaf swap

Resolved. A post-cutover publication now opens the verified `workflow/`
directory with `O_DIRECTORY | O_NOFOLLOW`, opens `events.jsonl` relative to
that descriptor with `O_NOFOLLOW | O_APPEND` and without `O_CREAT`, and binds
both filesystem identities before state publication. The same open descriptors
and exact byte snapshot remain live through timestamp selection, append,
post-append event validation, and rollback. Every use rechecks the addressed
directory and leaf against their bound `(st_dev, st_ino)` identities.

If the leaf is swapped or removed after state publication, append fails. The
rollback restores the held event inode, atomically replaces only the addressed
leaf through the anchored directory descriptor, verifies exact bytes through a
fresh no-follow descriptor, and leaves a symlink target untouched. The session
state rollback and event rollback share this publication failure boundary.
Pre-cutover event creation retains its existing `O_CREAT` behavior.

Two temp-only regressions inject the change on the first event `os.write`:

- `test_github_cutover_event_symlink_swap_rolls_back_bound_append` requires a
  failure, byte-exact restoration of every state file and canonical events,
  restoration of the displaced original inode, and no write to the alternate
  symlink target.
- `test_github_cutover_event_removal_rolls_back_bound_append` requires a
  failure and byte-exact restoration of every state file and a regular,
  non-symlink canonical event log.

### R2-F2: Exact cutover integers accepted booleans and floats

Resolved. The irreversible indicator now requires
`type(schema_version) is int` and `type(repository.database_id) is int` before
checking their values. One strict-schema regression rejects `true`, `1.0`, a
boolean repository database ID, and a numerically equal floating-point
database ID.

## Validation

- Focused repair and compatibility selection: `6/6` passed in `0.248s`
  (`0.38s` wall).
- `python3 tests/test_workflow.py`: final `126/126` passed in `2.381s`
  (`2.60s` wall). The expected argparse usage text comes from the existing
  missing-capacity regression.
- `python3 -m unittest discover -s tests -p 'test_workflow.py'`: `126/126`
  passed in `2.476s` (`2.64s` wall).
- The requested literal command `python3 -m unittest tests.test_workflow`
  cannot load this repository's non-package `tests/` directory on this host:
  an installed site-package named `tests` is selected first. It failed at
  import with `ModuleNotFoundError: tests.test_workflow` before running project
  code. The direct-file and discovery commands above exercised the same suite.
- `PYTHONPYCACHEPREFIX=/tmp/i031-a02-pycache python3 -m compileall -q
  scripts/workflow.py tests/test_workflow.py`: passed.
- `python3 scripts/check_workflow.py --root . --skip-tests`: passed in `0.19s`.
- `git diff --check`: passed.

The first focused iteration exposed a missing test-module `os` import; the
tests now use the already imported `workflow.os` reference, and the corrected
focused and full runs above pass. No Lean/Lake build, network operation, GitHub
mutation, push, canonical state/metrics edit, or subagent dispatch was
performed.

## Residual Risks

- Descriptor-backed validation uses `/proc/self/fd`, `dir_fd`, and Linux
  `O_NOFOLLOW` behavior. This matches the workflow store's existing explicit
  dependence on Linux directory `flock`; it is not portable to a non-Linux
  host without a separate stream-based validator.
- An external process that replaces the entire `workflow/` directory causes a
  fail-closed directory-identity error. This repair restores tested leaf swaps
  and removals but does not attempt to reconstruct an externally replaced
  directory tree.
- Filesystems do not provide one atomic commit across `sessions.json` and
  `events.jsonl`. The guarded failure path restores and fsyncs byte-exact final
  contents; power loss between the two filesystem operations remains the
  pre-existing crash-consistency boundary.
