# QPBT-026 / LPR-016 exact-scope and preflight-capability design

## Session identity

- Logical session: `i026-scout-a10-scope-token-design`
- Role: fresh read-only security/design scout; this is not an approving review
- Candidate worktree: `/tmp/qpbt-026-pr016-review-a08`
- PR base: `ea584e9e894391773e09ddad2ce4d082497c7913`
- Candidate head: `94c0e630b5f2697f678c400da082f108bde89471`
- Candidate tree: `4188a6d959cb145b945c9618789f96cd98165d02`
- Observed head/tree: exact match
- UTC start: `2026-09-01T03:02:21Z`
- UTC end: `2026-09-01T03:08:33Z`
- Measured elapsed: 372 seconds

## Outcome

Both reported blockers are real. The smallest coherent repair is not another
check around the existing singleton. Production dispatch must move to one
closed launch coordinator that (1) validates a version-2 content manifest, (2)
captures each authorized byte exactly once, (3) constructs an evidence-only
harness with no source clone or full Git tree, (4) proves an OS-level read
boundary, and only then (5) probes persistence, claims a lease, and launches.
The split helper/token API should be removed. If it must temporarily remain,
the replacement capability must be fresh, single-use, and bound to every
launch-relevant identity described below.

The current `--sandbox read-only` is a write policy, not evidence confinement.
Because the Codex child is a host process with inherited environment and can be
asked to execute read commands, exact content scope requires OS-level isolation.
Removing the source path from the prompt and projecting the harness are
necessary, but are not an enforcement boundary by themselves. Production must
fail closed if that isolation capability is unavailable or unverified.

## Concrete evidence

1. The authorization schema records only `private_file_paths`
   (`scripts/local_agent.py:46-59`), and validation compares that list only with
   changed path names (`scripts/local_agent.py:644-687`). `_review_disclosure_target`
   derives exactly those names from `git diff --no-renames --name-only`
   (`scripts/local_agent.py:794-817`). It records neither the base-side blob nor
   the head-side blob, mode, size, or a collision-resistant content digest.

2. Five unchanged base files are independently read from Git and their full
   contents are returned as trusted authority (`scripts/local_agent.py:110-116`,
   `scripts/local_agent.py:2043-2104`). `build_trusted_review_prompt` embeds all
   those contents and the persona in the outbound prompt
   (`scripts/local_agent.py:1184-1230`). None is included in the current
   authorized changed-path set.

3. `_packet_from_arguments` reads arbitrary task and context files after the
   first CLI preflight and embeds their complete contents in the request
   (`scripts/local_agent.py:3487-3531`). It also exposes resolved file labels and
   `build_review_request` emits the source working directory
   (`scripts/local_agent.py:1087-1098`). The unbound CLI ordering is preflight,
   persistence probe, packet read, then direct helper
   (`scripts/local_agent.py:3606-3649`); the bound branch likewise performs an
   early preflight and then reads the packet (`scripts/local_agent.py:3582-3605`).

4. `_clone_without_checkout` clones the complete local repository, including
   unrelated reachable objects and repository metadata
   (`scripts/local_agent.py:2195-2209`). `_prepare_committed_harness` then checks
   out the complete base tree and creates a synthetic commit whose tree is the
   complete head tree (`scripts/local_agent.py:2446-2517`). Thus the child can
   read every base file and can resolve every head file and unrelated reachable
   object with Git. A local clone also exposes refs, commit metadata, path names,
   object packs, and an origin/config path, even if no such file is checked out.

5. The prompt explicitly discloses the original absolute source path and tells
   the reviewer to use `git show` for surrounding head files
   (`scripts/local_agent.py:1238-1245`). The actual subprocess inherits the
   caller environment when `environment=None` (`scripts/local_agent.py:1644-1681`),
   and the Codex command is merely given `--sandbox read-only` and the harness
   cwd (`scripts/local_agent.py:3011-3049`, `scripts/local_agent.py:3095-3101`).
   Therefore the original repository, other host-readable files, `/tmp`, process
   metadata, and potentially credential-bearing environment/config paths remain
   externally accessible through model-directed tool reads. The capability
   probe also runs Codex from `Path.cwd()` with copied host environment
   (`scripts/local_agent.py:2107-2192`) and must not execute in the source scope.

6. `_DISCLOSURE_PREFLIGHT_TOKEN` is one module singleton
   (`scripts/local_agent.py:103-104`). Both offline and production preflight
   return it (`scripts/local_agent.py:820-846`), and the post-probe helper checks
   only identity (`scripts/local_agent.py:2864-2888`). An offline caller can
   obtain the singleton with an injected fake runner, then invoke the helper
   with `offline_test_mode=False`, `runner=_subprocess_run`, and
   `transport_profile=None`; command construction selects `codex` and accepts no
   destination overrides (`scripts/local_agent.py:3011-3023`). This is a direct
   cross-mode replay.

## Outbound and externally accessible content channels

| Channel | Current content | Why current authorization misses it | Required disposition |
| --- | --- | --- | --- |
| Prompt authority | Built-in contract, base persona, and full contents of up to five unchanged base authority files | Scope is changed path names only | Manifest each Git blob/version/mode/size/SHA-256 and authorize it, or omit it |
| Prompt request | Inline task or task-file bytes, every context-file byte, acceptance gates, issue/session metadata, base/head declarations | Packet is built after preflight; arbitrary files are not in scope | Bind all private prompt inputs; capture once after structural authorization and before any probe/lease |
| Prompt path metadata | Absolute source cwd and resolved context labels | Path names themselves are disclosed | Remove host paths; use normalized logical repository labels covered by the manifest |
| Base checkout | Complete base tree, including unchanged files and live symlinks | Only changed names are authorized | Do not checkout the source tree; materialize only inert authorized evidence |
| Synthetic head | Complete head tree resolvable through `git show` | Full head content is accessible regardless of diff | Do not import the head tree; use a projected evidence package |
| Git object database | All reachable blobs, trees, commits, tags, refs, logs/config/path metadata copied by clone | Object reachability is broader than path list | Never clone; initialize a new empty repository only if Codex requires Git trust |
| Git-derived diff/patch | Text/binary content and path/mode metadata for changed objects | Path list does not bind exact bytes | Treat patch as derived authorized evidence; record its SHA-256 and size |
| Model-directed reads | Original repo/host filesystem, `/tmp`, process data, Codex persistence and possibly credential paths | Read-only sandbox does not mean read-confined | OS mount/PID boundary; only projected harness visible to reviewer tools |
| Child environment | Full inherited environment | Not represented by file scope; may contain secrets or host paths | Minimal allowlist and a credential/control-plane design not inherited by reviewer tool processes |
| Capability/parser probe | Codex process launched from ambient cwd/config environment | Happens after initial preflight but outside projected harness | Run locally in an empty isolated root with no repository evidence and no network-capable prompt path |
| Command/tool output | Any readable content returned by reviewer shell/Git tools is relayed to the model | Accessibility equals potential disclosure | Enforce the same OS evidence root for every descendant process |

Local result envelopes, prompt/event/stderr files, and review JSON are not
outbound merely because they are persisted, but they must continue to omit raw
authorization. The endpoint sees the prompt and every subsequent tool result;
that full transitive read surface is the authorization boundary.

## Required repair

### 1. Replace path-only version 1 with content-bound version 2

Do not reinterpret schema version 1. Introduce a version-2 exact-key record and
reject version 1 for every production launch with a migration error. At minimum
the authorization binds:

- normalized endpoint origin, model, provider/profile identity, and wire API;
- normalized target kind plus immutable base, head, and head-tree OIDs;
- one canonical, sorted evidence record per disclosed content unit;
- a canonical manifest digest and explicit authorization/exclusion booleans.

Each Git-backed record should contain `channel` or a sorted channel set,
`revision_role` (`base` or `head`), normalized repository path, Git object type
and mode, blob/gitlink OID, byte length, and SHA-256. A modification normally
requires separate base and head records. Additions have a head record; deletions
have a base record; renames have both endpoint paths/records. Mode-only changes,
symlinks, gitlinks, binary blobs, and absent endpoints must be explicit. Git OID
alone is not sufficient; retain SHA-256 over the exact exposed bytes.

Non-Git prompt inputs need records too: inline assignment, task file, every
context file, and any private acceptance-gate text. Use logical source IDs and
SHA-256/size, never an absolute host path. Present authority files are ordinary
base Git records with an `authority` channel; being trusted as instructions does
not implicitly authorize their disclosure.

The mandatory lower bound is both sides of every changed entry plus every
content-bearing prompt input. Explicitly authorized unchanged surrounding files
may be added. Omitted surroundings remain inaccessible; the reviewer must report
that scope limitation rather than discover arbitrary files. Credential screening
applies to every authorized Git/request path before its bytes are captured.

### 2. Compute, authorize, and capture in one fail-closed plan

Create one internal immutable `ReviewDisclosurePlan`, owned by one launch
coordinator. The order should be:

1. Parse only structural CLI/library arguments. Validate a complete normalized
   destination profile/model and load the non-secret authorization control
   record. Select production mode; CLI has no offline mode.
2. Resolve the canonical source root and immutable target; require clean exact
   HEAD/ancestry/tree. Derive changed endpoint metadata with raw Git diff/tree
   plumbing, not `--name-only`. Normalize and credential-screen all paths.
3. Validate the authorization's exact key set, destination, target identity,
   requested logical input descriptors, and canonical manifest shape before
   generic packet/context loading, Codex/persistence probing, or lease claim.
4. Capture each authorized byte once. For Git records, address the prevalidated
   object OID directly and verify type/mode/path. For request files, confine them
   to the repository (or require inline text), reject symlinks/special files,
   read through a no-follow descriptor, and compare size/SHA-256 from the
   authorization. Store the captured bytes in private memory/staging. Do not
   call `_packet_from_arguments` to reread them; that would reopen a TOCTOU gap.
5. Compare the completed canonical path+content manifest exactly with the
   authorization and seal the plan with its manifest digest. Generate the
   request and authority packet only from captured bytes. A mismatch fails
   before persistence probe, capability probe, harness preparation, or lease.
6. Verify OS-isolator availability and policy. Then perform the local
   persistence/capability probes in an empty isolated repository. Only after all
   disclosure gates pass may a bound launch claim a reviewer lease.
7. Build and recursively verify the evidence-only harness, recheck the sealed
   manifest immediately before spawn, and launch through the isolator.

Reading a request file to verify its authorized hash is necessarily a local
read. It must be part of guarded preflight capture, after its logical descriptor
is authorized, and the captured bytes must be the only bytes later packetized.
There must be no unguarded second packet/context load.

### 3. Make the committed harness evidence-only

Delete the committed use of `_clone_without_checkout`. The simplest safe
committed harness is a new empty Git repository (only to satisfy Codex trusted
repository checks) plus regular files such as:

- `evidence/manifest.json` containing the canonical authorized records;
- `evidence/base/<encoded logical path>` and
  `evidence/head/<encoded logical path>` containing only authorized regular-file
  bytes, with symlink targets/gitlinks represented as inert metadata or regular
  payload files rather than live filesystem objects;
- an exact derived patch/diff whose digest is recorded in the manifest;
- authorized authority/request material, either in those projections or in the
  prompt, never both without declaring both channels.

Use generic `codex exec` for this projected harness. Native `exec review
--commit` is not required for correctness and currently encourages a complete
Git tree. If a minimal synthetic Git history is retained, create every object
from captured authorized bytes in a fresh object database, import no source
commit/tree/ref/config/alternates, checkout no symlink, and prove unrelated and
orphan source OIDs are unresolvable. The generic evidence package is smaller
and easier to audit.

Remove both source-cwd emissions (`build_review_request` and the trusted prompt)
and the instruction to inspect the synthetic full tree. The prompt should name
only logical evidence paths and state that absent files are intentionally out of
scope.

### 4. Enforce host read isolation

An evidence-only harness does not prevent a host Codex process from reading the
original source path. Production must execute Codex and every model-directed
descendant in a reviewed OS isolation boundary (for example a dedicated
container/mount namespace with an allowlisted filesystem), with:

- only the projected harness mounted read-only for reviewer tools;
- no source repository, workspace root, general `/home`, shared `/tmp`, host
  `/proc`, Git object store, or user config mounted;
- a minimal scrubbed environment;
- no reviewer-tool access to authentication material;
- network/control-plane behavior constrained so tool commands cannot route
  disclosed bytes to a destination other than the authorized review transport.

Codex authentication/persistence may require an outer broker or narrowly
mounted private control-plane state that is not visible inside reviewer tool
processes. If the implementation cannot demonstrate that separation, the
external launch must remain disabled. A unit-test fake isolator is adequate for
offline tests; production cannot treat an asserted boolean as proof. It needs a
capability returned by the reviewed isolator after checking the actual launch
policy.

### 5. Remove the replayable helper/token seam

Preferred design: remove `_DISCLOSURE_PREFLIGHT_TOKEN` and make
`_run_review_after_persistence_probe` unreachable as an independently callable
dispatch surface. One coordinator should own preflight, one-time capture, probe,
optional lease, harness, isolation, and spawn. Separate public entry points may
construct either a production request or an offline-test request, but they must
not exchange a token and boolean mode across a helper boundary.

This is simpler and safer than inventing a security protocol inside one Python
module. It also removes current duplicate preflights in bound/CLI paths and
makes the required ordering directly testable.

If short-term compatibility requires a capability, it must be a fresh instance
per successful preflight, not a module singleton. It should contain no raw
authorization or captured secrets and be bound to:

- an enum launch mode (`external` or `offline_test`);
- canonical source identity and normalized target kind/base/head/tree plus the
  sealed evidence-manifest digest;
- normalized model and complete destination-profile fingerprint;
- the exact runner identity and isolator capability; offline mode additionally
  binds the injected capability-record digest and the offline executable marker;
- a random/process-local nonce and a private constructor seal.

Consumption must occur atomically at helper entry, before any source read,
capability probe, directory creation, command construction, or runner call.
Any consumption attempt burns the nonce, including a binding mismatch. Reject
copy, pickle, JSON, and reconstruction; never serialize it into prompt/envelope
or accept one from arguments. A lock-protected process-local live-capability
registry makes reuse/concurrent double consumption fail. External mode must
also require the production runner/isolator identities; `transport_profile=None`
can never match an external capability. This is non-forgeable by accidental
call-site reuse, though no Python object protects against actively malicious
code executing in the same interpreter. Consolidating the launch remains the
better final boundary.

## Focused adversarial regression matrix

| Case | Expected gate |
| --- | --- |
| Same changed paths, different base or head blob bytes/OID | Reject before packet/probe/lease |
| Modification lacks either base or head record | Reject exact manifest |
| Addition, deletion, rename, mode-only change, binary blob | Exact endpoint records and digests; no implicit content |
| Changed-path list matches, unchanged base authority omitted | Reject before authority load/prompt |
| Authorized authority blob hash/size drifts | Reject; prompt never built |
| Task/context absent from manifest, hash drifts, is outside repo, is a symlink, or is swapped after open | Reject before probe/lease; no second read |
| Exact authorized inline task/context | Success from captured bytes; no absolute label in prompt |
| Unchanged secret file, orphan blob, other branch/tag, commit message, or ref exists in source | Fake reviewer cannot resolve/read it in harness |
| Base/head contains an authorized symlink target | Exposed only as inert metadata/payload; no traversable symlink in harness |
| Fake reviewer runs `git show`/`git cat-file` for unrelated OID | Object absent |
| Fake reviewer tries original source path, sibling worktree, host home, shared `/tmp`, `/proc`, or injected secret environment variable | OS isolation returns unavailable/denied; no value reaches tool output |
| Harness inventory includes any extra private file/object/alternates/remote/source path | Reject immediately before spawn |
| Capability/parser probe runs | Empty isolated cwd, scrubbed environment, no repository content, no model dispatch on parser probe |
| Offline capability/request replayed as external | Reject before probe/harness/runner |
| External capability/request replayed as offline | Reject before side effect |
| Capability target, manifest digest, model, endpoint, wire API, profile, runner, isolator, or injected capability changes | Reject and burn capability |
| Same capability consumed twice or concurrently | Exactly one consumption; second fails before launch |
| Capability copied, pickled, JSON encoded, or passed across process | Not serializable/not accepted |
| Direct post-probe helper call without valid bound capability | Reject before source/harness/command access |
| Production CLI omits profile, version-2 authorization, or isolator | Reject before task/context capture, persistence probe, or lease |
| Bound and unbound exact-scope success | Same coordinator and manifest logic; bound claim occurs only after all gates |

Tests should instrument call order and assert zero calls to packet rereads,
persistence/capability probes, harness preparation, lease claim, and runner on
every early failure. One integration-style offline isolator test should run a
real nested read command against a synthetic host secret; mocking a policy flag
does not prove filesystem confinement.

## Compatibility implications

- **Committed-only version 1:** retain parsing only to issue a deterministic
  migration failure. It cannot authorize production because path equality does
  not bind content or all channels. Regenerate existing records as version 2.
- **Uncommitted/bootstrap:** remains production-disabled. Version 2 in this
  repair is committed-only; immutable-snapshot support is a separate reviewed
  schema.
- **Offline tests:** preserve deterministic harness/envelope coverage through a
  separate offline-only entry point with injected runner, capability record,
  and fake isolator. It accepts no destination/authorization and can never
  construct the `codex` executable. Existing helpers need migration, not a
  shared mode boolean/token.
- **CLI:** no offline flag. Load structural authorization first, then invoke the
  single production coordinator. `--task-file`/`--context-file` must be
  repository-confined and content-recorded; inline values are digest-recorded.
- **Bound/unbound library calls:** use the same coordinator. Bound mode adds a
  lease step after disclosure/isolation gates; it must not preflight, claim, and
  then recursively enter the unbound path. Dry-run still validates version 2
  and produces only projected local evidence; it launches no Codex process.
- **Native review selector:** committed production reviews should temporarily
  use existing generic-exec fallback. Re-enabling native review requires proof
  that a projected minimal Git database is complete enough and leaks nothing.

## Smallest implementation boundary

Required files are `scripts/local_agent.py`, `tests/test_local_agent.py`,
`protocols/review.md`, and `protocols/CHANGELOG.md`, plus the issue's normal
fixer/review evidence report. In `local_agent.py`, replace the version-1 schema,
path-only target, clone-based committed harness, source-bearing prompt text, and
singleton/helper flow as one change. Splitting only the token fix while leaving
full-tree disclosure does not satisfy QPBT-026; projecting the harness without
OS isolation likewise cannot claim exact scope.

## Required repair versus later hardening

Required for QPBT-026 closure:

- version-2 path+content/channel manifest covering Git endpoints, authority,
  task/context, and derived evidence;
- guarded one-time capture and exact comparison before probes/lease;
- evidence-only harness with no clone/full tree/live symlink/source path;
- verified OS read/environment/tool-egress isolation or production fail-closed;
- consolidated dispatch with no replayable singleton, plus the adversarial tests
  above and corrected protocol/changelog claims.

Later hardening, not substitutes for the repair:

- cryptographic provenance/signatures for who issued the non-secret
  authorization record;
- content secret/DLP scanning in addition to exact explicit authorization;
- uncommitted snapshot schema;
- native-review support over a formally projected Git graph;
- stronger endpoint certificate/pinning and audit telemetry beyond the existing
  normalized destination binding.

## Acceptance commands for the fixer/reviewer

No commands below were run by this scout.

```text
python3 -m unittest discover -s tests -p 'test_local_agent.py'
python3 -m compileall -q scripts/local_agent.py tests/test_local_agent.py
python3 scripts/workflow.py validate
git diff --check
git diff --name-status ea584e9e894391773e09ddad2ce4d082497c7913..NEW_HEAD
```

The focused unittest suite must include the matrix above, especially a real
offline OS-isolation read-denial test and full harness inventory/OID checks. A
fresh read-only reviewer must inspect the exact new head and the actual
isolation launcher, not accept mocked unit evidence alone. No Lean/Lake build is
needed for this Python/protocol-only repair.

## Metrics and safety

- Exposed token usage: `null`.
- Token availability reason: the collaboration/runtime interface exposes no
  per-session model token accounting; no estimate was made.
- Subagents spawned: 0.
- Agent topology: one read-only scout; no delegation.
- Files written: only `/tmp/qpbt-026-scope-token-design-a10.md`.
- Repository/canonical-state/metrics/Git writes: 0.
- Tests run: 0.
- Compile attempts: 0.
- Lean commands: 0.
- Lake commands: 0.
- Full or scoped builds: 0.
- Cache warm/seed/status commands: 0.
- External endpoint contacts: 0.
- Network requests: 0.
- GitHub reads/writes: 0/0.
- Credential reads/uses: 0/0.
- Incidents or workflow issues opened: 0.
