# QPBT-028 A10 channel matrix scout A02

## Identity

- Session: `i028-scout-a02-a10-channel-matrix`
- Role: fresh read-only security scout; not an approving review
- Base: `1799fbaf8175157a4aca6841a179fcbd43d7f4ed`
- Tree: `3f36e74e6b33402142cb9831162a0987ee8f3075`
- Worktree creation/start proxy: `2026-09-01T07:17:42.924114074Z`
- Report freeze: `2026-09-01T07:21:33.225694410Z`
- Measured elapsed: `230.301580` seconds
- Initial and final worktree: detached, clean, exact base/tree
- Verdict: QPBT-028 needs one consolidated production coordinator. The existing offline projection is reusable capture/verification machinery, but it is not a v2 authorization plan or an OS isolation boundary.

## Current boundary

Production remains intentionally disabled:

- Schema constants are version 1 and path-only at `scripts/local_agent.py:46`.
- Exact-key v1 loading and validation occur at `scripts/local_agent.py:653` and `scripts/local_agent.py:667`.
- `_review_disclosure_target` derives only changed names with `--no-renames --name-only` at `scripts/local_agent.py:817`.
- `_preflight_external_disclosure` validates v1 and unconditionally rejects production at `scripts/local_agent.py:843`.
- Unbound and bound library entry points reject before probes, harness, output, runner, or lease at `scripts/local_agent.py:3002` and `scripts/local_agent.py:3066`.
- CLI validates the profile, loads authorization, and rejects before `_packet_from_arguments` at `scripts/local_agent.py:3840`.
- The former singleton token and post-probe production helper are absent, guarded by `tests/test_local_agent.py:1628`.

## Complete channel matrix

| A10 channel | Current function/site | Current identity | Required v2 identity and disposition |
| --- | --- | --- | --- |
| Prompt authority | `load_trusted_review_authority`, `scripts/local_agent.py:2126`; `build_trusted_review_prompt`, `scripts/local_agent.py:1239` | Base revision, path, blob OID, SHA-256, UTF-8 content; offline projection adds channel/size at `scripts/local_agent.py:2560` | One record per authority blob: `channel=prompt-authority`, `revision_role=base`, normalized path, Git type/mode/OID, size, SHA-256. Built-in contract/persona also needs a stable logical ID, size, digest, and channel or explicit non-private trusted-code version binding. Capture from prevalidated OID once; omitted authority must not load. |
| Prompt request | `build_review_request`, `scripts/local_agent.py:1094`; CLI reads at `_packet_from_arguments`, `scripts/local_agent.py:3762` | Assignment, context contents/labels, gates, issue/session metadata, declared SHAs; final request gets only aggregate size/SHA-256 offline at `scripts/local_agent.py:2546` | Separate records for inline task, task file, each context, private gates/metadata, and final encoded request. Use normalized logical source IDs, channel, size, SHA-256; task/context files must be repo-confined regular no-follow captures. Generate solely from captured bytes. |
| Prompt path metadata | `build_review_request`, `scripts/local_agent.py:1108`; `_packet_from_arguments`, `scripts/local_agent.py:3765` | Source cwd is now `"."`; context labels are resolved repository-relative | Keep `"."` or omit cwd. Bind every logical label/path in v2. Reject absolute paths, traversal, symlink aliases, duplicate normalized IDs, and any host path in final prompt. |
| Outbound final prompt | `build_trusted_review_prompt`, `scripts/local_agent.py:1239`; `_offline_content_projection`, `scripts/local_agent.py:2553` | Final UTF-8 prompt size/SHA-256 is measured only after construction | Bind `channel=outbound-prompt`, stable logical ID, exact size/SHA-256. Recompute immediately before isolated spawn and compare to the sealed plan. |
| Base/head endpoint bytes | `_prepare_committed_harness`, `scripts/local_agent.py:2683` | Both sides of every no-renames changed name; revision role, path, type, mode, OID, inert representation, size, SHA-256, evidence path | Retain these fields, but derive endpoint metadata before capture and compare exact canonical records to authorization. Modifications need both records; additions head only; deletions base only; renames preserve both endpoints; mode-only, binary, symlink, and gitlink cases explicit. |
| Base checkout / synthetic head | `_prepare_committed_harness`, `scripts/local_agent.py:2711` | Already replaced by regular projected evidence; no source checkout or synthetic full tree | Preserve this design. Never materialize live symlinks or source commits/trees. Authorized symlink targets and gitlinks remain inert regular payload/metadata. |
| Git object database, refs, remotes, alternates | `_prepare_committed_harness`, `scripts/local_agent.py:2711`; `_verify_committed_harness_manifest`, `scripts/local_agent.py:2493` | Fresh empty repository; verifier rejects object files, alternates, remotes, extra evidence, and live evidence symlinks | Extend recursive verification to exact allowed `.git` metadata, no resolved refs/logs, no source path strings, no worktree/object selectors, no replacement/shallow state. Unrelated/orphan/other-ref OIDs must be unresolvable. |
| Derived patch | `_prepare_committed_harness`, `scripts/local_agent.py:2715` | `channel=derived-patch`, logical evidence path, size, SHA-256 | Authorize exact derived-record identity or deterministically derive it from the already authorized captured endpoints and require its record/digest to match v2 before spawn. |
| Evidence manifest | Construction at `scripts/local_agent.py:2783`; verification at `scripts/local_agent.py:2493`; compact prompt reference at `scripts/local_agent.py:1135` | Offline schema 1; file digest/size and logical digest; explicitly non-launchable/not isolated | Production v2 manifest must be a separately authorized exact immutable record. File bytes and logical canonical digest must both match immediately before spawn. Never mutate the offline schema into production authority. |
| Model-directed filesystem/process reads | Offline runner at `scripts/local_agent.py:3369` | Harness cwd and minimal environment, but no host read isolation | Launch Codex and every descendant through a verified OS isolator. Only projected harness readable; deny source/workspace, `/home`, shared `/tmp`, host `/proc`, sibling worktrees, user config, and unmanifested sentinel. Fail before endpoint request if unavailable. |
| Child environment | `_git_environment`, `scripts/local_agent.py:1860`; runner call at `scripts/local_agent.py:3369` | Minimal Git environment is passed to offline fake runner | Define and attest an exact production environment allowlist. No secret or repository selector may reach reviewer tool processes. Authentication/control-plane material must remain outside the tool-readable namespace. |
| Capability/parser probe | `inspect_codex_review_capability`, `scripts/local_agent.py:2172` | Probe uses `Path.cwd()`; production currently never reaches it | If retained, run in an empty isolated disposable repository with scrubbed environment and no evidence. Parser probe must cause no endpoint request. Bind probe/isolator capability into the sealed launch plan. |
| Persistence probe | `_probe_codex_persistence`, `scripts/local_agent.py:1394` | Production currently rejects before it | Run only after v2 authorization, one-time capture, sealed-manifest comparison, and isolator verification. Its filesystem/control-plane state must not become tool-readable evidence. |
| Lease/session claim | `run_review`, `scripts/local_agent.py:3118` | Production preflight precedes claim | Preserve ordering: claim only after all disclosure and isolation gates. Bound and unbound calls must use the same coordinator; bound mode adds only this late lease step. |
| Command/profile construction | `_review_transport_config_arguments`, `scripts/local_agent.py:632` | Validated non-secret provider overrides; production never reaches construction | Bind provider key/name/base URL/wire API/auth boolean/model in v2. Construct only after sealed plan and isolator capability validate. Never record credentials. |
| Command/tool output | `_run_bounded` call and output persistence, `scripts/local_agent.py:3369` | Fake runner output is stored locally; no production channel exists | Treat all descendant stdout/stderr/tool output as potentially outbound. The OS boundary must prevent any unmanifested byte from entering it; persisted envelopes continue to exclude raw authorization and credentials. |
| Local prompt/events/stderr/result | `scripts/local_agent.py:3363` onward | Local only in offline mode | Not authorization channels by mere persistence, but output paths must be outside reviewer visibility and records must contain hashes/metadata, never credentials or raw authorization. |

## Exact v2 schema

Use a new exact-key schema; retain v1 parsing only for deterministic migration failure.

Recommended top-level exact fields:

```text
schema_version
authorized
endpoint_origin
model
model_provider
provider_name
wire_api
requires_openai_auth
target_kind
base_sha
head_sha
tree_sha
entries
manifest_sha256
exclude_credentials
exclude_unrelated_contents
```

Every top-level field is mandatory. `schema_version` is exactly `2`; booleans require actual Boolean values. Endpoint origin is the normalized validated HTTPS origin. SHAs are full immutable OIDs. `target_kind` is committed `base` or `commit`; bootstrap/uncommitted remains production-disabled.

Each entry has an exact shape selected by kind:

- Git content: `kind`, sorted unique `channels`, `revision_role`, normalized `path`, `object_type`, `mode`, `object_id`, `representation`, `size`, `sha256`, `evidence_path`.
- Non-Git prompt content: `kind`, sorted unique `channels`, `logical_source_id`, `size`, `sha256`.
- Derived content: `kind`, sorted unique `channels`, `logical_source_id`, `size`, `sha256`, with deterministic provenance from captured entries.

Canonical ordering is by `(kind, logical path/source ID, revision_role, object_type, mode, object_id, channels)`, with no duplicate identity. Channels themselves are sorted unique. JSON digest input uses the exact manifest payload with sorted object keys and compact separators, excluding only the `manifest_sha256` field. SHA-256 is lowercase 64-hex; sizes are nonnegative integers excluding Boolean values. Authorization must byte/logically match the separately constructed manifest, not merely contain a compatible subset.

The exact schema should reject unknown fields, absent fields, unsorted/duplicate records, inconsistent endpoint presence, unrecognized channels/roles/types/modes, absolute evidence paths, and records whose channel does not match where bytes are placed. Credential screening occurs on all Git and request logical paths before capture.

## One-time plan and ordering

The smallest sufficient production flow is one immutable internal `ReviewDisclosurePlan`:

1. Parse structural arguments; validate the complete transport/model profile; load the non-secret v2 control record.
2. Resolve canonical source root and clean immutable target; derive raw endpoint metadata and normalize/screen every path.
3. Validate exact v2 keys, destination, target, descriptors, record shape, ordering, and manifest digest before task/context contents, probes, output/harness creation, command construction, lease, or runner.
4. Capture each authorized Git object by prevalidated OID exactly once. Capture request files once through confined, no-follow regular-file descriptors; verify size/digest. Do not call `_packet_from_arguments` afterward.
5. Generate request, authority, endpoint projection, patch, and final prompt solely from captured bytes. Compare the completed exact manifest to authorization and seal the plan.
6. Verify a real isolator capability and exact policy.
7. Run any persistence/parser probes in an empty isolated repository.
8. Build and recursively verify the projection; recheck manifest and prompt digests immediately before spawn.
9. Claim a bound-session lease, if applicable.
10. Launch exactly once through the isolator.

Any failure through step 8 must assert zero packet rereads, probes where not yet permitted, harness/output creation, lease claims, command construction, runner calls, and endpoint requests.

## Required adversarial regressions

Implement every A10 case:

- Same names but different base/head bytes or OID.
- Missing base or head half of a modification.
- Addition, deletion, rename, mode-only, binary, symlink, and gitlink endpoint semantics.
- Omitted or drifted unchanged base authority.
- Missing/drifted/outside-repository/symlink/special/swapped task or context input; prove no second read.
- Exact inline/file request succeeds without absolute labels.
- Unchanged secret, orphan blob, other branch/tag/ref, commit message, and unrelated OID remain absent/unresolvable.
- Authorized symlink/gitlink is inert and nontraversable.
- `git show`/`cat-file` cannot recover source objects.
- Reads of source, sibling worktree, home, shared `/tmp`, host `/proc`, and injected secret environment are denied by a real nested process.
- Extra harness file/object/ref/alternate/remote/source path fails immediately before spawn.
- Probe uses empty isolated cwd and scrubbed environment; parser probe makes no model request.
- Offline-to-external and external-to-offline replay fail before side effects.
- Drift in target, manifest, model, endpoint, wire API, profile, runner, or isolator capability fails.
- Production CLI missing profile, v2 authorization, or isolator fails before request capture/probe/lease.
- Bound and unbound successful plans share identical manifest logic; claim is late.
- Tampering between harness verification and spawn is detected by the immediate digest/inventory recheck.
- Isolator unavailable, policy incomplete, or sentinel readable fails closed with zero endpoint requests.

Existing useful regressions include early CLI failures around `tests/test_local_agent.py:1095`, production isolation ordering at `tests/test_local_agent.py:1144`, exact v1 migration/fail-closed behavior at `tests/test_local_agent.py:1327`, replay removal at `tests/test_local_agent.py:1628`, projection tamper rejection at `tests/test_local_agent.py:1684`, credential paths at `tests/test_local_agent.py:1763`, sensitive rename endpoints at `tests/test_local_agent.py:1837`, and projected committed evidence at `tests/test_local_agent.py:1910`. They do not establish v2 capture or OS confinement.

## Smallest sufficient change

Required files remain:

- `scripts/local_agent.py`
- `tests/test_local_agent.py`
- `protocols/review.md`
- `protocols/CHANGELOG.md`
- Normal QPBT-028 implementation/review reports

Reuse `_resolve_committed_review_target`, path normalization/screening, minimal Git environment, inert endpoint projection, recursive evidence verification, bounded runner, and output parsing. Replace v1 target/schema validation and add the sealed one-time capture plan, exact v2 comparison, production coordinator, and reviewed isolator interface. Keep offline mode a separate injected-runner/fake-isolator path that accepts no transport or authorization.

Do not claim completion by only relabeling the offline manifest, adding a policy Boolean, or enabling the current subprocess runner.

## Validation and metrics

- Commands: initial and final `git rev-parse HEAD`, `git rev-parse HEAD^{tree}`, `git status --short`; final `git diff --check`; static `rg`, `sed`, and `nl` reads.
- Results: exact identity, clean worktree, diff check passed.
- Attempts: identity checks 2; diff-hygiene checks 1; static-read batches 7.
- Edits: 0; commits: 0.
- Subagents: 0; topology: one read-only scout under the QPBT-028 orchestrator.
- Token usage: `null`.
- Availability reason: collaboration/runtime tools expose no per-session token accounting; no estimate was made.
- Network/endpoint/GitHub/Codex CLI/Lean/Lake/hot-cache actions: 0.

## Residual risk

This was a static design scout, not an implementation or approving security review. The proposed schema names and canonical ordering remain design guidance until implemented, exercised by the complete adversarial matrix, and approved on an exact immutable manifest. The current production path correctly remains disabled; enabling it before a real descendant-process filesystem/environment/tool-egress boundary is independently demonstrated would expose unmanifested host-readable content despite the evidence-only harness.
