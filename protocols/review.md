# Local Review Protocol

## Gate order

Model review starts only after deterministic validation succeeds. Code review
and blueprint/prose review are separate fresh sessions because their failure
modes differ. A completion auditor checks the assembled outcome after both.

Reviewer sessions are intended to run read-only and receive a trusted prompt
from the reviewed base plus an untrusted diff/context artifact. External
dispatch is currently disabled because read-only execution does not confine
reads to authorized evidence. The deterministic offline path constructs a
projected evidence repository and invokes only an injected non-`codex` test
double; it does not establish a production isolation boundary. Reviewers may
inspect paper sources,
blueprint entries, definitions, callers, and build logs. They may not edit,
commit, launch fix agents, change state, or approve their own work.

## Execution bounds

Every local Codex run has an explicit wall-clock bound. The default is 1,800
seconds; a stage may choose a smaller positive value and records it in the run
envelope. On timeout, the wrapper terminates the complete Codex process group,
escalates to a forced kill after a short grace period, and preserves any partial
stdout and stderr. It writes a failed result envelope even when no thread ID,
usage event, final message, or verdict was exposed.

A timeout is terminal evidence for that attempt, not a review verdict. The
session is archived or retired according to the exposed thread evidence, the
incident is recorded, and any retry receives a new stable alias. A timed-out
attempt never confers approval and cannot be resumed as the approving reviewer.

## External disclosure preflight

Transport trust and content-disclosure authorization are separate decisions.
Official OpenAI transport and `https://api.finite-dimensional.space` are
standing trusted transports, but that trust authorizes no repository content.
Never record an API key or authentication token. Changing endpoint, model,
profile, revision, or evidence content requires a new authorization decision.

The legacy version-1 JSON record binds endpoint origin, model, `wire_api`,
immutable `base_sha`, `head_sha`, and `tree_sha`, plus the sorted changed paths
and true `exclude_credentials`/`exclude_unrelated_contents` controls. The
wrapper still resolves exact clean commits, preserves both rename endpoints,
screens normalized paths, and validates every version-1 field. Raw and
normalized authorization mappings remain internal and never enter targets,
prompts, envelopes, or logs.

Version 1 is not production-launch authority. Path names do not bind unchanged
authority, request/context, patches, Git objects, command output, environment,
or the transitive host read surface. Even a matching version-1 record therefore
fails closed for missing exact-content authorization and enforceable filesystem
isolation. Production entry points reject before task/context reads, persistence
or capability probes, evidence preparation, lease claim, command construction,
or runner invocation. Uncommitted targets also remain non-launchable.

Version 2 is a distinct exact-key schema. Its structural validator compares the
declared transport profile, model, committed target kind, immutable base/head/tree,
the reviewed isolation-policy digest, and a canonical sorted content manifest.
Every Git entry records sorted channels, revision role, normalized path, object
type, mode, object identity, inert representation, byte size, SHA-256, and
projected evidence path. Logical entries record sorted channels, a host-path-free
logical identity, byte size, and SHA-256; derived entries additionally require a
sorted nonempty list of input digests as provenance. The canonical manifest
digest covers every authorization field except the digest field itself. Unknown,
missing, duplicate, unsorted, malformed, credential-like, or mismatched fields
fail before probes, output, lease, command construction, or runner invocation.

Structural schema validation does not prove that the declared entries are
complete or match source, projection, request, authority, or prompt bytes, and
therefore does not authorize a launch. Production additionally
requires one-time no-follow capture from the validated object/input identities,
exact projection and prompt reconstruction from only those captured bytes, an
immediate pre-spawn inventory recheck, and an independently reviewed isolation
capability. Until that coordinator exists, even an exact version-2 record fails
closed without contacting an endpoint.

The local isolation probe uses Landlock in a disposable child and demonstrates
that an allowlisted projection remains readable while a randomized unmanifested
host sentinel is denied to the child and its descendants. This host cannot create
a private network namespace, so the complete capability is unavailable: a
reviewer process and its model-directed descendants would not yet have a proven
single-destination egress boundary. A future production boundary must use a
digest-pinned, credential-free reviewer container plus a separate credential
broker whose one leased transport connection is the only network path. Missing
images, policy digests, internal network, broker lease, second-connection denial,
or sentinel proof fails closed. An asserted Boolean, a fake test runner, or
filesystem isolation without descendant egress isolation is never sufficient.

Path screening distinguishes private containers from ordinary public
certificate material: `.pem`, `.key`, `.p12`, `.pfx`, `.jks`, `.keystore`, and
`.kdbx` fail closed, while `.crt` and `.cer` are not rejected merely by
extension. High-signal credential dot-directories, service-account artifacts,
`.npmrc`, and `.pypirc` are rejected without treating generic `keys`, `auth`,
`private`, or `certs` directories as credentials by themselves.

Any future reviewer transport remains a mandatory, explicit, non-secret
all-or-none profile: the model-provider key, provider display name, HTTPS base
URL, `responses` wire API,
and the provider's `requires_openai_auth` boolean. The wrapper keeps
`--ignore-user-config` and injects the validated profile as top-level CLI
configuration overrides before `exec`; no current production review reaches
that command construction. Authentication must remain outside reviewer-readable
evidence and is never read or recorded by the wrapper. Provider
keys must be safe dotted-config components, and endpoint URLs with userinfo,
credentials, queries, fragments, or non-HTTPS schemes fail before evidence
dispatch. Omitting the profile never means local execution: it would inherit an
unknown user-configured destination, so the wrapper rejects it before loading
authorization, task, or context files, probing persistence, or claiming a lease.

Library tests may opt into `offline_test_mode` only with an injected runner and
an injected Codex capability record. The record is copied and its required
fields are validated before repository inspection, harness/output creation,
lease claim, or runner invocation; a falsey record never falls back to a Codex
probe. That mode substitutes a non-`codex` executable marker, accepts no
transport or authorization data, skips persistence probing, and has no CLI
switch. A committed offline harness is a fresh Git repository with no source
objects or remote. It contains only inert base/head bytes for changed endpoints,
an exact derived patch, and a manifest recording path, revision role, Git
type/mode/object identity, size, and SHA-256.

Every Git operation used for source inspection or harness construction receives
the same fixed minimal process environment: a system-default executable path, C
locale, disabled system/global configuration and prompting, and no inherited
repository, worktree, index, object, alternate, namespace, replacement, shallow,
discovery, quarantine, ceiling, or template selector. Only the fixed author and
committer dates needed for deterministic harness commits may extend it; identity
itself is command-local. The injected offline runner is handed that same minimal
environment. Tests must plant a source-object alternate and confirm that the
unmanifested source head remains unresolved, the harness reports no alternate,
and the child sees none of the selector variables. This closes ambient Git
selection; it does not turn the in-process test double into OS-enforced host
filesystem isolation.

The offline packet projection also binds the inline request, final prompt,
unchanged base authority blobs, harness manifest, and derived evidence. It
explicitly records `external_launchable: false` and
`host_isolation: not-enforced`. This is the deterministic exact-content success
regression, not authorization or proof of a production read boundary.

There is no module-global preflight token and no independently callable
post-persistence production helper. Offline state therefore cannot be replayed
into production or across targets, models, or profiles, and duplicate
consumption is inapplicable because no authorization capability exists.

The configured Stage 1 bootstrap transport profile is
`gpt-5.6-sol` over the Responses protocol at
`https://api.finite-dimensional.space`. Transport trust is not content
authorization. Version-1 authorization does not bind an uncommitted snapshot,
so the current launcher refuses that external dispatch.
Bootstrap harness behavior remains testable only through the non-transmitting
offline mode until a separately reviewed immutable-snapshot authorization schema
exists; ignored paper payloads, runtime files, and credentials remain excluded.

Before spending a frozen full-evidence attempt, a minimal read-only prompt must
receive a complete response through that exact endpoint/model profile within
the configured health window. The probe gets its own stable session and metric,
contains no repository contents, and is archived. A connection, fallback, or
reconnect-only stream fails closed and blocks the large review until a later
probe succeeds. Use a disposable empty Git repository for the probe so Codex's
trusted-repository preflight remains enabled without exposing project files.

The health canary proves transport availability only; prompt construction has
an independent bounded-payload gate. A frozen prompt includes trusted authority,
selectors, revisions, status hashes and counts, the evidence digest, and a
fixed-shape manifest summary whose numeric counters grow only logarithmically.
It references `evidence/manifest.json` inside
the isolated harness rather than duplicating its per-file entries. The wrapper
verifies both the exact file-byte digest and the parsed manifest's logical
digest immediately before launch, while the full manifest remains in the
harness and result envelope. Tests must demonstrate that manifest cardinality
does not make the prompt grow linearly. Record exact UTF-8 prompt bytes for each
attempt; if this gate fails, fix the packet before spending a full reviewer
session rather than treating a tiny successful canary as evidence that a large
prompt will complete.

The offline unborn Stage 1 harness passes `--bootstrap-snapshot-digest` with the
exact digest printed by the freeze tool. Harness construction accepts this phase
contract only with `--uncommitted` while `HEAD` is unborn. It independently runs
the bootstrap verifier, matches the digest, requires an unsealed Stage 1 manifest,
and compares the manifest's terminal-evidence contract with the tool's fixed
allowlist and rule. After evidence capture it repeats verification, byte-matches
the copied freeze manifest, and binds every captured core path and hash to the
verified freeze before invoking the offline test double. The trusted phase
record has an exact key set and constant values; extra, missing, or changed
fields fail before prompt
serialization. Only then does built-in trusted prompt text explain the
unavoidable ordering: the current reviewer's terminal lifecycle fields, final
report, and seal are completed after an approving reviewer returns, so their
pre-return state is not a finding by itself. Manifest prose remains evidence
and is never interpolated into reviewer authority.

## Code and mathematical review

Review only the local PR delta, but inspect enough surrounding code to verify it.
Priorities are:

1. mathematical truth and exact paper-statement fidelity;
2. soundness, forbidden assumptions, proof holes, and quantifier/domain drift;
3. Lean type/API correctness and downstream behavior;
4. reproducible source/build behavior and cache isolation;
5. maintainability issues that materially affect future proofs.

For every changed source-labelled theorem, compare paper and Lean assumptions,
conclusion, quantifier order, parameter bounds, normalizations, and error terms.
Boundary hypotheses must be justified. A load-bearing proof-obligation input is
a blocker even if the declaration compiles.

Findings are ordered by severity and cite `path:line`. Each states the concrete
failure, evidence, impact, and smallest reasonable fix. Do not manufacture
comments, repeat an existing unresolved finding, or lead with style nits.

## Blueprint/prose review

Check source citations, exact definitions, dependency edges, notation,
cross-references, declared encoding choices, and `\leanok` truthfulness. Verify
the blueprint explains every mathematically load-bearing boundary introduced by
the formal encoding. A readable but inaccurate blueprint fails review.

## Findings ledger

Each review round is tied to one head SHA. Findings have stable IDs, severity,
path/line when available, body, status, and disposition. The implementer may
mark `fixed` or `rejected` with evidence; only a fresh reviewer confirms
`resolved`. A changed head invalidates approval.

Resolution evidence is permanent. Once a finding is resolved, its status,
disposition, disposition evidence, and `resolved_by_review_id` are immutable.
If the PR head later advances, an approving fresh review may be appended to the
finding's optional `confirmation_review_ids`; absence of that field means no
later confirmations. Each confirmation ID is unique, is later than the original
resolution and every preceding confirmation, and names an existing formal
review on the same PR whose read-only reviewer is independent and terminal.
Review lists and per-finding confirmation lists are append-only.

An `approved` or `merged` PR requires every finding to be resolved and requires
either its original resolution review or an appended confirmation review to
bind the exact current base/head. A later head therefore preserves all prior
dispositions and confirmations but invalidates approval until another current
approving review is appended where needed. A `request_changes` round may be the
original resolution review for one finding while introducing another; it is not
an approving reconfirmation.

Verdicts are `approve`, `request_changes`, or `blocked`. Any blocker or
unresolved correctness finding yields `request_changes`. Reviewer failure,
timeout, or unavailable evidence yields `blocked`, never implicit approval.

## Completion audit

A fresh read-only auditor inspects the issue gates, child reports, diff, git
state, builds, reviews, source links, remaining TODO/proof debt, metrics, and
protocol incidents. It returns one of: stop; one concrete next action; at most
five bounded options; or a necessary user question. Its report does not mutate
state.
