# QPBT-028 fail-closed v2/isolation slice A01

## Identity and scope

- Session: `i028-orchestrator-a01-content-isolation`
- Role: sole writable orchestrator for QPBT-028
- Immutable base: `1799fbaf8175157a4aca6841a179fcbd43d7f4ed`
- Base tree: `3f36e74e6b33402142cb9831162a0987ee8f3075`
- Owned implementation paths: `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/local_agent.py`, `scripts/review_isolation.py`,
  `tests/test_local_agent.py`, and `tests/test_review_isolation.py`
- Endpoint, network, credential, Codex CLI, GitHub, Lean, Lake, and hot-cache
  actions: zero

## Outcome

This is a smallest fail-closed dependency slice, not QPBT-028 acceptance.
Production external review remains disabled.

The launcher now recognizes an exact-key version-2 authorization structure and
validates its declared provider/model/target/policy identities, canonical
manifest digest, sorted unique channel records, Git modes/types/OIDs, sizes,
SHA-256 values, inert projection paths, credential exclusions, and derived-input
provenance. Version 1 retains its migration behavior and cannot launch.

The new isolation module executes a real Landlock probe in a disposable nested
process. The projection remains readable and a sibling unmanifested host
sentinel is denied after `no_new_privs` and the ruleset are applied. The policy
digest covers a canonical policy document containing the Landlock ABI floor,
handled/allowed access masks, `no_new_privs`, exact-clear-environment rule, and
private descendant-network requirement. A separate safe `unshare --net` probe
shows that this host cannot enforce the required network boundary. The combined
capability therefore returns unavailable and version-2 production preflight
fails before persistence/capability probes, harness/output creation, command
construction, lease, runner, or endpoint effects.

## Scout topology

Two bounded fresh read-only children ran in parallel with implementation:

- `i028-scout-a02-a10-channel-matrix`: complete A10 content/channel/schema/order
  audit, 230.301580 seconds, zero edits/network. Root-owned authenticated report:
  `workflow/reviews/qpbt-028-channel-matrix-a02.md`.
- `i028-scout-a03-os-isolation`: local OS substrate audit, zero edits/network.
  It found bubblewrap and unprivileged namespaces unavailable, while Docker is
  installed but lacks pinned reviewer/broker images, an attested internal network,
  and a single-connection credential broker. Root-owned authenticated report:
  `workflow/reviews/qpbt-028-os-isolation-a03.md`.

Both reports were inspected and accepted as design evidence, not approval.
Token usage is `null`; collaboration/runtime tools expose no per-session token
accounting, and no estimate was made.

## Acceptance-gate status

| QPBT-028 gate | Status |
| --- | --- |
| Version-2 authorization binds all actual outbound bytes | **Open.** Structural validation exists, but declared entries are not yet compared with one-time captured authority/request/Git/patch/manifest/prompt bytes. |
| One-time immutable evidence projection excludes all source/unrelated state | **Open.** The offline projection is reusable, but no production content-plan coordinator consumes v2 records. |
| Enforceable filesystem/environment/tool-egress boundary denies sentinel and fails closed | **Partial.** Real Landlock sentinel denial and exact minimal environment exist. Descendant network/tool egress is unavailable, so the complete capability fails closed. |
| Production validates exact manifest before endpoint and never exposes credentials | **Open/fail-closed.** No production endpoint or runner can be reached. Credential separation requires the broker deployment. |
| Complete A10 matrix and adversarial regressions | **Open.** Structural drift and sentinel/fail-close regressions were added; the complete capture, projection, TOCTOU, source-object, environment, and broker matrix remains in dependencies. |
| Fresh independent immutable security review | **Open.** It depends on a complete immutable candidate. |

## Required dependencies

1. One-time exact-content plan/projection coordinator: validate descriptors
   before reads; capture repository-confined task/context files no-follow and Git
   objects by exact OID exactly once; derive authority/request/prompt/patch/
   manifest only from captured bytes; compare the complete A10 manifest exactly;
   recursively verify and immediately recheck projection before a late lease and
   isolated spawn.
2. Digest-pinned Docker reviewer plus credential broker: reviewed reviewer and
   broker images, AppArmor/seccomp/argv/network identities, internal-only network,
   broker-only endpoint credential, one leased Codex transport connection, denial
   of descendant/second connections, and a real no-endpoint Docker integration
   proving sentinel, proc/fd, environment, projection-write, and direct-egress
   denial.

Root was sent exact proposals for canonical dependency issues QPBT-029 and
QPBT-030. QPBT-028 must remain open until both are discharged and a fresh
immutable security reviewer approves the assembled candidate.

## Validation and attempts

- `test_local_agent.py`: final focused pass 65/65 in 5.411 seconds; earlier
  post-edit passes were 63/63 and 65/65, with two failing attempts used to fix a
  test-placement error and an overclaimed structural mutation.
- `test_review_isolation.py`: final focused pass 4/4 in 0.158 seconds; all
  isolation-focused attempts passed.
- Aggregate Python suite: final post-review tree passed 342/342 in 186.915
  seconds. Earlier stable-tree passes were also 342/342 in 186.276, 199.988,
  and 191.448 seconds; they are compile attempts, not substituted final evidence.
- `compileall` with private `/tmp/qpbt-028-a01-pycache-final`: pass.
- `python3 scripts/workflow.py validate --json`: pass; 29 issues, 17 pull
  requests, 349 issued sessions, 7 stages.
- `git diff --check`: pass.
- Blueprint declaration checker attempt: unavailable because
  `scripts/check_blueprint_declarations.py` does not exist at this snapshot; no
  substitute command was guessed. No Lean declarations changed.

The candidate intentionally records no per-session token estimate. The final
commit/tree, exact changed-path inventory, canonical lifecycle elapsed time, and
this report's digest are reported out of band after the commit freezes these
bytes; embedding the commit's own identity here would be self-referential.
