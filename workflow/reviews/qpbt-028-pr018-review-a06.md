# LPR-018 authority-correction security review A06

## Verdict

**REQUEST CHANGES.** F-LPR018-001 through F-LPR018-003 are independently
confirmed on the exact immutable LPR-018 head. They are defects in the v2 and
isolation primitives proposed for later reuse. They are not an active endpoint
disclosure path because production external review remains unconditionally
disabled.

This is not approval or completion of QPBT-028. The one-time exact-content
capture/projection work proposed as QPBT-029 and the digest-pinned reviewer plus
single-connection credential broker proposed as QPBT-030 remain required,
followed by a fresh immutable security review. At this frozen head those IDs are
recorded as required proposals in
`workflow/reviews/qpbt-028-content-isolation-a01.md:65`, not yet as canonical
objects in `workflow/state/issues.json`.

## Findings

### F-LPR018-001 - High - malformed and contradictory v2 authority is accepted

`scripts/local_agent.py:786` uses ordinary Python equality for JSON control
fields. Consequently schema version `2.0` equals integer `2`, integer `1`
equals Boolean `true`, and a null model is accepted when the caller also passes
`model=None`. At `scripts/local_agent.py:822`, Git mode, object type,
representation, and evidence path are validated independently rather than as a
coherent identity. A record claiming regular blob/object bytes with gitlink mode
`160000` is accepted and receives a valid canonical manifest digest.

The focused reproductions returned `ACCEPTED` for a single authority containing
`schema_version: 2.0`, `authorized: 1`, and the contradictory Git tuple, and
returned `ACCEPTED_MODEL None` for a null model. This contradicts the
malformed-field fail-closed contract at `protocols/review.md:71`. Today the
record can reach the isolation probe but cannot cross the coordinator stop at
`scripts/local_agent.py:1051`.

Required repair: enforce exact JSON scalar types and a nonempty model; enforce
per-kind channel, mode/type/representation, revision/evidence-path, provenance,
logical-identity, and projection-collision invariants before QPBT-029 consumes
this validator.

### F-LPR018-002 - Medium - fabricated isolation success evidence is accepted

`scripts/review_isolation.py:227` checks six asserted values but does not bind
the mapping to the probe that produced it. It also ignores the required
relationship between those assertions, `filesystem_probe_returncode`, and the
two evidence fields. A caller-created mapping with all success Booleans,
return code `999`, and `network_probe_evidence: "fabricated"` was accepted and
returned unchanged by `require_production_isolation`.

The current preflight obtains the mapping directly from the local probe, and the
later unconditional stop still blocks launch. The helper nevertheless does not
meet the reusable production-capability contract stated at
`protocols/review.md:90`.

Required repair: make probe and requirement one non-injectable production
operation or return an opaque process-local capability; validate exact types,
evidence syntax, return code, and every cross-field relationship. Retain the
forged-record case as a regression.

### F-LPR018-003 - Medium - projection-root no-follow check is ineffective

`scripts/review_isolation.py:102` resolves the supplied root before
`root.is_symlink()` is evaluated at line 103. Resolution removes the final
symlink from the `Path`, so the advertised real-directory rejection cannot fire.
A disposable child accepted a live projection-root symlink and exited `0` after
installing the Landlock rule.

The built-in probe creates its own real private directory, so its observed
sentinel denial is genuine. The reusable `restrict_reads_to` boundary is still
unsafe for a caller-selected projection because path resolution and descriptor
opening are not one no-follow, identity-pinned operation.

Required repair: open the named root once with descriptor-relative no-follow
checks, verify it is a directory, and bind the Landlock rule and any pre-probe
reads to that same descriptor. Cover final-component, ancestor-symlink, and
swap cases.

## Fail-Closed Status

The real local probe returned `filesystem_enforced=true`,
`sentinel_denied=true`, `descendant_network_egress_denied=false`, and
`available=false`. Thus `scripts/local_agent.py:1046` rejects on this host.

A separate bounded control-flow case replaced the probe result with the forged
all-success mapping and replaced earlier source/structure work with inert test
doubles. Preflight still returned:

```text
BLOCKED production review requires the independently reviewed one-time projection coordinator
```

That is the unconditional failure at `scripts/local_agent.py:1051`. Both
unbound and bound production entry paths call this preflight before their review
runner paths (`scripts/local_agent.py:3220` and `scripts/local_agent.py:3296`).
No endpoint, Codex process, lease, output directory, or production harness was
reached during this review.

`workflow/reviews/qpbt-028-content-isolation-a01.md:58` keeps exact-byte binding,
one-time projection, production manifest validation, the complete adversarial
matrix, and final independent review open. Its required dependencies at line 65
are the work proposed as QPBT-029 and QPBT-030; both remain necessary after the
three findings above are repaired.

## Immutable Identity

- Detached clean head: `7e7fe07e776b44b98724605648a71e2d5f31580e`.
- Tree: `398eaced83f0bfdf7b51364784d1a5211aab2e86`.
- Exact base and sole parent/merge base:
  `1799fbaf8175157a4aca6841a179fcbd43d7f4ed`.
- Commit count from base to head: `1`.
- Exact seven-path manifest, with no rename and mode `100644` throughout:
  `protocols/CHANGELOG.md`, `protocols/review.md`,
  `scripts/local_agent.py`, `scripts/review_isolation.py`,
  `tests/test_local_agent.py`, `tests/test_review_isolation.py`, and
  `workflow/reviews/qpbt-028-content-isolation-a01.md`.
- A01 SHA-256:
  `c756a8842089f385a175c49287a7a58fec51b989731d45ca84ad704371a278e5`.
- Final pre-report repository status: clean; this review made no repository or
  Git changes.

Identity commands and results:

```text
git status --short --branch
  -> ## HEAD (no branch)
git rev-parse HEAD HEAD^{tree}
  -> 7e7fe07e776b44b98724605648a71e2d5f31580e
     398eaced83f0bfdf7b51364784d1a5211aab2e86
git merge-base 1799fbaf8175157a4aca6841a179fcbd43d7f4ed 7e7fe07e776b44b98724605648a71e2d5f31580e
  -> 1799fbaf8175157a4aca6841a179fcbd43d7f4ed
git rev-list --parents -n 1 7e7fe07e776b44b98724605648a71e2d5f31580e
  -> 7e7fe07e776b44b98724605648a71e2d5f31580e 1799fbaf8175157a4aca6841a179fcbd43d7f4ed
git rev-list --count 1799fbaf8175157a4aca6841a179fcbd43d7f4ed..7e7fe07e776b44b98724605648a71e2d5f31580e
  -> 1
git diff --name-status 1799fbaf8175157a4aca6841a179fcbd43d7f4ed..7e7fe07e776b44b98724605648a71e2d5f31580e
  -> four M entries and three A entries; exactly the seven paths above
git diff --check 1799fbaf8175157a4aca6841a179fcbd43d7f4ed..7e7fe07e776b44b98724605648a71e2d5f31580e
  -> exit 0, no output
```

## Focused Validation

The existing aggregate, compileall, workflow, and identity evidence was not
duplicated. The authenticated candidate records 65/65, 4/4, 342/342,
compileall, workflow validation, and identity checks. This review ran only
bounded authority/isolation cases.

Exact focused test command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_local_agent.RuntimeTests.test_v2_authorization_structure_binds_declared_fields_and_policy test_local_agent.RuntimeTests.test_v2_production_fails_before_side_effects_when_complete_isolation_is_unavailable test_review_isolation.ReviewIsolationTests.test_capability_schema_and_policy_are_exact test_review_isolation.ReviewIsolationTests.test_landlock_child_denies_unmanifested_host_sentinel
```

Run from `tests/`: exit `0`; 4/4 passed; unittest time `0.189s`; observed wall
time `0.275748877s`. One earlier invocation from the repository root used the
incorrect package-qualified names, exited `1`, and ran 0 tests because `tests`
is not a Python package. The command was corrected without any code change.

Adversarial commands were Python `-c` processes with
`PYTHONDONTWRITEBYTECODE=1` and imports pinned to this worktree's `scripts/`:

1. Construct v2 authority with `schema_version=2.0`, `authorized=1`, and Git
   tuple `object_type=blob`, `mode=160000`,
   `representation=inert-object-bytes`; recompute `_canonical_manifest_sha256`;
   call `validate_review_disclosure_authorization_v2_structure`.
   Result: exit `0`, `ACCEPTED` with the contradictory record.
2. Construct otherwise-shaped v2 authority with `model=None`; recompute the
   manifest digest; call the same validator with `model=None`.
   Result: exit `0`, `ACCEPTED_MODEL None`; observed wall `0.013455141s`.
3. Construct a complete isolation mapping with the policy constants, asserted
   success values, `filesystem_probe_returncode=999`, a zero digest, and
   `network_probe_evidence=fabricated`; call
   `require_production_isolation`.
   Result: exit `0`, `ACCEPTED` with the fabricated mapping unchanged.
4. In a `TemporaryDirectory`, create a real projection, a live directory
   symlink naming it, and a sibling sentinel; invoke
   `python3 scripts/review_isolation.py --probe-child SYMLINK SENTINEL`.
   Result: child return `0`, symlink still live, empty stderr; temporary content
   removed automatically.
5. Run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/review_isolation.py`.
   Result: exit `0`; filesystem/sentinel true, descendant network/available
   false; observed wall `0.011565482s`.
6. Patch only `_review_disclosure_target`, the v2 structure validator, and
   `probe_production_isolation` in one disposable Python process, supplying the
   accepted forged capability to `_preflight_external_disclosure`.
   Result: exit `0` with the `BLOCKED ... one-time projection coordinator`
   message above; observed wall `0.040433483s`.

Exact primary finding reproducers:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import sys; sys.path.insert(0,"scripts"); import local_agent as l; z="0"*40; d="0"*64; p={"base_url":"https://api.example.invalid","model_provider":"OpenAI","provider_name":"OpenAI","wire_api":"responses","requires_openai_auth":True}; e={"kind":"git","channels":["outbound-prompt"],"revision_role":"base","path":"x","object_type":"blob","mode":"160000","object_id":z,"representation":"inert-object-bytes","size":1,"sha256":d,"evidence_path":"evidence/base/x"}; a={"schema_version":2.0,"authorized":1,"endpoint_origin":p["base_url"],"model":"m","model_provider":p["model_provider"],"provider_name":p["provider_name"],"wire_api":p["wire_api"],"requires_openai_auth":True,"target_kind":"base","base_sha":z,"head_sha":z,"tree_sha":z,"entries":[e],"manifest_sha256":d,"isolation_policy_sha256":l.review_isolation.POLICY_SHA256,"exclude_credentials":True,"exclude_unrelated_contents":True,"exclude_source_repository":True}; a["manifest_sha256"]=l._canonical_manifest_sha256(a); print("ACCEPTED", l.validate_review_disclosure_authorization_v2_structure(a,transport_profile=p,model="m",target_kind="base",base_sha=z,head_sha=z,tree_sha=z))'
```

Result: exit `0`; printed `ACCEPTED` and the contradictory record.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import sys; sys.path.insert(0,"scripts"); import review_isolation as r; d="0"*64; c={"schema_version":r.ISOLATION_SCHEMA_VERSION,"policy_id":r.POLICY_ID,"policy_sha256":r.POLICY_SHA256,"filesystem_enforced":True,"sentinel_denied":True,"environment_mode":"exact-clearenv","minimal_environment_credential_names_present":False,"descendant_network_egress_denied":True,"available":True,"filesystem_probe_returncode":999,"filesystem_probe_stderr_sha256":d,"network_probe_evidence":"fabricated"}; print("ACCEPTED", r.require_production_isolation(c))'
```

Result: exit `0`; printed `ACCEPTED` and the forged mapping unchanged.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import pathlib,subprocess,sys,tempfile; s=pathlib.Path("scripts/review_isolation.py").resolve(); t=tempfile.TemporaryDirectory(); r=pathlib.Path(t.name); real=r/"real"; real.mkdir(); (real/"allowed.txt").write_text("allowed\n"); link=r/"projection"; link.symlink_to(real,target_is_directory=True); sentinel=r/"sentinel"; sentinel.write_text("denied\n"); c=subprocess.run([sys.executable,str(s),"--probe-child",str(link),str(sentinel)],capture_output=True,text=True,env={"PATH":"/usr/bin:/bin","LC_ALL":"C","LANG":"C"}); print("RETURN",c.returncode,"SYMLINK",link.is_symlink(),"STDERR",c.stderr.strip()); t.cleanup()'
```

Result: exit `0`; printed `RETURN 0 SYMLINK True STDERR`.

Read-only inspection used `cat AGENTS.md`, targeted `rg`, numbered `nl` ranges,
and exact-base `git diff`/`git diff-tree`; no aggregate or unrelated suite was
run.

## Session Accounting

- Session: `i028-reviewer-a06-pr018-authority`.
- Topology: root coordinator -> one fresh read-only A06 reviewer; nested agents
  or subagents: `0`.
- Required `AGENTS.md` first-read timestamp:
  `2026-09-01T09:12:46.057417042Z`, recovered exactly from its unchanged
  filesystem access time after the read.
- Evidence-complete clock observation:
  `2026-09-01T09:16:17.462829840Z`.
- Report-freeze clock observation:
  `2026-09-01T09:18:21.524768156Z`.
- Exact measured first-read-to-evidence interval: `211.405412798s`.
- Exact measured first-read-to-report-freeze interval: `335.467351114s`.
- Token usage: `null`; the collaboration/runtime interface exposes no
  per-session token accounting, and no estimate was made.
- Repository edits/commits/Git writes: `0`; state edits: `0`; metric edits: `0`;
  protocol edits: `0`. The sole durable output is this `/tmp` report.
- Endpoint requests: `0`; external network requests: `0`; GitHub operations:
  `0`; credential reads: `0`; Codex launches: `0`; Lean commands: `0`; Lake
  commands: `0`; hot-cache actions: `0`; nested-agent launches: `0`.
- Aggregate-suite reruns: `0`; compileall reruns: `0`; workflow-validator
  reruns: `0`; compile attempts: `0`; cache hits/misses/waits: `0/0/0`.
- Focused test invocations: `2` (`1` command-selection failure, `1` pass);
  targeted adversarial cases: `6`; retries after code changes: `0`.
- Findings confirmed: `3`; new finding IDs: `0`; approvals: `0`; fixes/actions
  taken: `0`; new issues opened: `0`.

Report SHA-256 is intentionally reported out of band after the file is frozen,
avoiding a self-referential digest.
