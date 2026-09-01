# LPR-018 immutable security review A05

## Verdict

**REQUEST CHANGES** on the exact LPR-018 partial fail-closed slice. Production
external review is still disabled, so none of the findings is an active endpoint
disclosure path. They are defects in the security primitives this slice proposes
to land for QPBT-029/QPBT-030.

This is not a QPBT-028 completion verdict. QPBT-028 remains open and
QPBT-029 (one-time exact capture/projection) plus QPBT-030 (pinned reviewer and
single-connection credential broker) remain required even after these findings
are fixed.

## Findings

### F-LPR018-001 - High - v2 structural validation accepts malformed and internally contradictory authority

`scripts/local_agent.py:786` compares JSON control fields with ordinary Python
equality, so `2.0` is accepted as schema version 2 and integer `1` is accepted
for every required Boolean. The model can also be `null`, restoring an unbound
default model that version 1 explicitly rejected. At `scripts/local_agent.py:822`,
Git fields are checked independently but not structurally coupled: a `commit`
object can claim regular-file mode `100644`, `inert-object-bytes`, an
`outbound-prompt` channel, and an evidence path unrelated to its source path.
Distinct entries may also target the same `evidence_path`; derived provenance
digests need not identify any manifest input; logical IDs are not canonically
normalized. All of these records receive a valid canonical manifest digest and
are returned as structurally valid.

This contradicts the exact-key/malformed-field fail-closed contract in
`protocols/review.md` and allows malformed authority to reach the isolation
probe at `scripts/local_agent.py:1046`. The unconditional coordinator failure
still prevents launch today, but QPBT-029 must not build on a validator that has
already accepted ambiguous channel, object, and projection identities.

Exact reproductions executed from the detached worktree both printed
`ACCEPTED`:

```bash
python3 -c 'import sys; sys.path.insert(0,"scripts"); import local_agent as m; p={"model_provider":"OpenAI","provider_name":"OpenAI","base_url":"https://api.finite-dimensional.space","wire_api":"responses","requires_openai_auth":True}; e={"kind":"logical","channels":["outbound-prompt"],"logical_source_id":"prompt:packet","size":0,"sha256":"0"*64}; a={"schema_version":2.0,"authorized":1,"endpoint_origin":p["base_url"],"model":"m","model_provider":"OpenAI","provider_name":"OpenAI","wire_api":"responses","requires_openai_auth":1,"target_kind":"base","base_sha":"1"*40,"head_sha":"2"*40,"tree_sha":"3"*40,"entries":[e],"manifest_sha256":"0"*64,"isolation_policy_sha256":m.review_isolation.POLICY_SHA256,"exclude_credentials":1,"exclude_unrelated_contents":1,"exclude_source_repository":1}; a["manifest_sha256"]=m._canonical_manifest_sha256(a); print("ACCEPTED",m.validate_review_disclosure_authorization_v2_structure(a,transport_profile=p,model="m",target_kind="base",base_sha="1"*40,head_sha="2"*40,tree_sha="3"*40))'
python3 -c 'import sys; sys.path.insert(0,"scripts"); import local_agent as m; p={"model_provider":"OpenAI","provider_name":"OpenAI","base_url":"https://api.finite-dimensional.space","wire_api":"responses","requires_openai_auth":True}; e={"kind":"git","channels":["outbound-prompt"],"revision_role":"base","path":"a.txt","object_type":"commit","mode":"100644","object_id":"4"*40,"representation":"inert-object-bytes","size":0,"sha256":"0"*64,"evidence_path":"evidence/base/not-a.txt"}; a={"schema_version":2,"authorized":True,"endpoint_origin":p["base_url"],"model":None,"model_provider":"OpenAI","provider_name":"OpenAI","wire_api":"responses","requires_openai_auth":True,"target_kind":"base","base_sha":"1"*40,"head_sha":"2"*40,"tree_sha":"3"*40,"entries":[e],"manifest_sha256":"0"*64,"isolation_policy_sha256":m.review_isolation.POLICY_SHA256,"exclude_credentials":True,"exclude_unrelated_contents":True,"exclude_source_repository":True}; a["manifest_sha256"]=m._canonical_manifest_sha256(a); print("ACCEPTED",m.validate_review_disclosure_authorization_v2_structure(a,transport_profile=p,model=None,target_kind="base",base_sha="1"*40,head_sha="2"*40,tree_sha="3"*40))'
```

Smallest fix: require exact JSON scalar types and a nonempty model; define and
enforce per-kind channel, mode/type/representation, revision/evidence-path, and
provenance relationships; canonicalize logical identities; reject projection
path collisions; add adversarial tests for every relationship before retaining
the structural-validator claim.

### F-LPR018-002 - Medium - the isolation capability checker accepts fabricated success evidence

`scripts/review_isolation.py:228` checks only six policy/result values. It does
not require `filesystem_probe_returncode == 0`, validate either evidence digest,
or enforce exact scalar types and cross-field consistency. Consequently an
ordinary caller-created mapping with success Booleans, return code `999`, and
non-digest evidence is accepted. This directly conflicts with the protocol's
statement that an asserted Boolean is never a sufficient isolation capability.

The current preflight obtains the mapping immediately from the real probe, so
this does not bypass the unconditional production failure. It nevertheless
makes `require_production_isolation` unsafe as the reusable boundary advertised
by the slice and leaves tests named “schema and policy are exact” materially
incomplete.

Exact reproducer; output begins `ACCEPTED`:

```bash
python3 -c 'import sys; sys.path.insert(0,"scripts"); import review_isolation as r; c={"schema_version":1,"policy_id":r.POLICY_ID,"policy_sha256":r.POLICY_SHA256,"filesystem_enforced":True,"sentinel_denied":True,"environment_mode":"exact-clearenv","minimal_environment_credential_names_present":False,"descendant_network_egress_denied":True,"available":True,"filesystem_probe_returncode":999,"filesystem_probe_stderr_sha256":"not-a-digest","network_probe_evidence":"not-a-digest"}; print("ACCEPTED",r.require_production_isolation(c))'
```

Smallest fix: do not accept a caller-constructible result mapping as a
production capability. Keep probe and requirement in one non-injectable
production operation (or mint a process-local opaque result), validate exact
types and all evidence/Boolean relationships, and add the forged-record
regression above.

### F-LPR018-003 - Medium - the no-follow projection-root check is ineffective

`scripts/review_isolation.py:100` resolves the supplied path before line 101
checks `root.is_symlink()`. A resolved path is no longer a symlink, so a live
symlink naming any readable directory is accepted as the Landlock allowlist
root despite the function's “real directory” contract. There is also a path
resolution/open interval rather than one descriptor-bound no-follow capture.

The checked probe creates its own private real directory, so the reported
sentinel denial remains genuine. The helper itself, however, cannot be adopted
as a safe projection boundary: a swapped or aliased root can authorize a
different subtree than the caller named.

Exact reproducer; it printed `returncode 0 root_is_symlink True`:

```bash
python3 -c 'import pathlib,subprocess,sys,tempfile; d=tempfile.TemporaryDirectory(dir="/tmp",prefix="qpbt-a05-symlink-"); root=pathlib.Path(d.name); real=root/"real"; real.mkdir(); (real/"allowed.txt").write_text("ok"); link=root/"projection-link"; link.symlink_to(real,target_is_directory=True); sentinel=root/"sentinel"; sentinel.write_text("deny"); p=subprocess.run([sys.executable,"scripts/review_isolation.py","--probe-child",str(link),str(sentinel)]); print("returncode",p.returncode,"root_is_symlink",link.is_symlink()); d.cleanup()'
```

Smallest fix: open the named root once with descriptor-relative no-follow and
directory checks, bind the rule to that verified descriptor, and ensure any
pre-restriction probe read uses the same pinned identity. Add final-component,
ancestor-symlink, and swap regressions.

## Verified properties

- CLI review loads and parses authorization and runs production preflight before
  `_packet_from_arguments`, so task/context files are not read on the checked
  production failure path.
- Both bound and unbound library paths preflight before persistence/capability
  probes, harness/output preparation, command construction, lease claim, and
  runner invocation.
- Version 1 always fails after validation. Version 2 either fails isolation or,
  on a capable host, reaches the unconditional missing-coordinator failure.
- Offline mode has no CLI switch, requires an injected runner/capability, uses a
  non-`codex` executable marker, and rejects transport and authorization data.
- The real local probe returned `filesystem_enforced=true`,
  `sentinel_denied=true`, `descendant_network_egress_denied=false`, and
  `available=false`. Thus the host's network-egress gate is unavailable and
  production remains fail-closed.

## Identity and source authentication

- Detached clean head: `7e7fe07e776b44b98724605648a71e2d5f31580e`.
- Tree: `398eaced83f0bfdf7b51364784d1a5211aab2e86`.
- Direct base/unique merge base: `1799fbaf8175157a4aca6841a179fcbd43d7f4ed`.
- Commit count: 1.
- Exact diff: seven paths, all mode `100644`, no renames; inventory matches
  LPR-018.
- A01 SHA-256: `c756a8842089f385a175c49287a7a58fec51b989731d45ca84ad704371a278e5`.
- A02 SHA-256: `167085d8d8902c6e2c43290ee081ba271cf89459de77791cf39f2427dc763bcd`.
- A03 SHA-256: `0738401dc1a4b78eba89ace547898b87eebe509b255e0f842e10c2cc9c8c660a`.
- A04 SHA-256: `a9f0d575f9e988f9997c17c9057541680d028bce24bb9979b5f56945e5d726d5`.

## Validation

- `test_local_agent.py`: 65/65 passed; unittest 4.494 s, wall 4.69 s.
- `test_review_isolation.py`: 4/4 passed; unittest 0.223 s, wall 0.31 s.
- `compileall`: passed, wall 0.65 s; cache redirected to
  `/tmp/qpbt-028-pr018-review-a05-pycache`.
- `python3 scripts/workflow.py validate --json`: passed, wall 0.16 s; 29
  issues, 17 PRs, 349 issued sessions, 7 stages in the frozen candidate.
- `git diff --check`: passed.
- Required 342-test aggregate reruns: 0, as instructed; the authenticated A01
  and A04 evidence records the existing 342/342 pass.
- Targeted adversarial reproductions: 4 commands, all reproduced the stated
  acceptance defects.

## Session accounting

- Session: `i028-reviewer-a05-pr018-immutable`.
- Role/topology: one fresh read-only reviewer under the root coordinator;
  nested agents/subagents: 0.
- Review clock start observation: `2026-09-01T08:55:52Z`.
- Evidence-complete observation: `2026-09-01T09:03:14Z`.
- Report-freeze observation: `2026-09-01T09:05:21Z`.
- Evidence collection elapsed: `442` seconds; total measured review elapsed:
  `569` seconds.
- Token usage: `null`; the collaboration/runtime interface exposes no
  per-session token accounting, and no estimate was made.
- Repository edits/commits/Git writes: 0. The sole durable output is this `/tmp`
  report; compile bytecode was redirected to the named `/tmp` cache.
- Endpoint requests, external network requests, GitHub operations, credential
  reads, Codex launches, Lean/Lake/hot-cache actions, nested-agent launches: 0.
- Findings: 3 new; approvals: 0; fixes/actions taken: 0.
- Report SHA-256: reported out of band after immutable file freeze to avoid a
  self-referential digest.
