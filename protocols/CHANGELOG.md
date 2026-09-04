# Protocol Changelog

## 0.1.15 candidate (QPBT-085) - 2026-09-04

The owner assigned Track B three concurrent Codex sessions from a ten-session
account budget shared with Track A. The root coordinator consumes one slot, so
Track B may run at most two external workers. This direct operational authority
supersedes the collaboration fan-out and 5-second/three-retry procedure from
0.1.14: Track B now uses leaf `codex exec` workers only, disables their
multi-agent feature, counts live scoped workers and surviving collaboration
threads before each launch, waits 30 seconds between worker starts, and runs no
more than one reviewer at a time. A full allocation waits 60 seconds before
recounting; HTTP 429 waits 120 seconds and retries the same stable session once,
then leaves the task queued instead of looping.

The protocol explicitly excludes Track A's checkout, development cache, and
tmux session. The stage ledger records the total ceiling of three, while
dispatcher calls use the two-worker non-coordinator ceiling. This is a direct
owner requirement rather than an inference from INC-087; independent review is
still required before QPBT-085 closes.

## 0.1.14 candidate (QPBT-081) - 2026-09-04

INC-087 records nine HTTP 429 failures across seven stable collaboration
sessions while the root and nested orchestrators were filling capacity or
resuming work. Five canonical issued rows account for seven failures; the
QPBT-075 handoff authenticates two more first-turn failures in its parallel
read-only children. Exact ledger times identify successful issuance and running
transitions, not the rejected requests themselves, so the evidence supports a
concurrent unstaggered transport burst but not a claimed provider rate window
or literally simultaneous rejected-request timestamps.

QPBT-081 adds one root-owned launch-class admission lane for bootstrap creation,
task release, and resume across the complete collaboration tree. New-session
admission is sequential from exact dry-run through bootstrap, confirmation, and
task release, with no interleaved launch or resume. Launch-class requests have a
5-second minimum stagger. A 429 keeps the lane and the same stable attempt,
permits at most three retries using 10/20/40-second exponential base delays plus
deterministic `[0, 5)`-second SHA-256-derived jitter, and ends no later than a
120-second episode deadline. Exhaustion stops automatic requests, preserves
planned bytes or the existing thread and worktree, and requires root escalation
and explicit retry accounting; no sibling launch-class request runs before the
quiet window ends. A later authorized episode reuses the same stable identity
rather than inventing a replacement attempt.

The restriction applies only to launch-class control traffic. Successfully
admitted agents and ordinary running-turn communication remain parallel under
the unchanged aggregate capacity, so useful steady-state concurrency is not
reduced. This is a procedural candidate: the repository can enforce preflight,
identity, confirmation, capacity, and no-mutation behavior, but no current local
launcher wraps collaboration creation and resume calls. A dispatcher sleep
would occur after the bootstrap transport and miss nested resumes, so QPBT-081
adds no misleading partial code or test. Independent review remains required
before activation.

## 0.1.13 candidate (QPBT-068 A32) - 2026-09-04

Fresh reviews A29 and A30 found that the A28 description mixed cooperative
workflow guarantees with adversarial same-identity claims. A same-identity
process can link a producer's `O_TMPFILE` descriptor or relocate an ancestor
between syscalls, and a recursive inventory releases nested authority before
the enclosing traversal returns. Those counterexamples are accepted; the
stronger confinement and exact-snapshot claims are withdrawn, not presented as
implementation fixes.

The supported boundary is cooperating repository agents that obey target locks
and do not concurrently mutate owned source, target, staging, transaction, or
retained-evidence trees. Monitors and repeated descriptor-relative checks detect
observed interference. Recursive inventory is a non-atomic monitored traversal
record, and a single-link requirement rejects aliases present when a file is
visited. For regular outputs, this program populates, metadata-finalizes, and
fsyncs a zero-link `O_TMPFILE` before making its own `linkat`, then performs no
later payload or metadata write. This order is not same-identity access control.

Dry seed and prepare remain non-mutating with respect to detached-file
publication: their output now says `detached_file_publication_checked: false`
because dry admission does not create an `O_TMPFILE` or exercise either
`linkat` route. Live failure regressions cover `O_TMPFILE` refusal and ordered
failure of both direct and `/proc/self/fd` publication routes in the cache and
materializer. Each case preserves the existing destination and retains partial
staging or transaction evidence. Cache publication wraps the combined
two-route error in the public `CacheError` contract.

## 0.1.13 candidate (QPBT-044) - 2026-09-03

INC-050, INC-058, and INC-059 are the three occurrences of
`session-base-full-sha-guessed-from-abbreviation`: a displayed abbreviation was
manually extended into a syntactically valid but nonexistent 40-hex value.
INC-078 independently reached the third occurrence of the same transcription
failure at a read-only candidate comparison. The prior manual preflight rule
did not prevent recurrence.

QPBT-044 adds one Git identity resolver to workflow admission. Every dispatch
dry-run and confirmation resolves the planned base in its registered worktree,
proves the full commit and exact root-tree object and type, compares an optional
expected tree, and records the resolved commit/tree pair. A guessed SHA,
missing object, or tree mismatch blocks the complete requested batch before
session/event mutation. The resolver deliberately keeps a PR review base
distinct from a detached candidate worktree `HEAD`. Collaboration confirmation
and atomic rollback are unchanged, and governed CLI rows retain their null-ID
issue-first lease behavior.

Independent reviews A02 and A03 identified three remaining admission gaps, all
fixed in the candidate. Unqualified symbolic names now require exactly one
canonical ref match, while fully qualified refs remain explicit authority.
Symlinked worktree components are rejected; the canonical root's device/inode
is checked around each Git process and again at the dispatch publication
boundary, with byte-exact rollback on replacement. Git also runs with
`GIT_NO_LAZY_FETCH=1`, so a missing promisor object fails locally without
invoking the repository's configured transport or credential path.

Independent reviews A06 and A07 then reproduced one remaining high-severity ABA
gap: pre/post pathname inode checks did not determine the working directory
used by a Git child while an attacker swapped and restored the repository
between those checks. The resolver now acquires the worktree component-wise
with no-follow `openat`, runs every Git child from the retained descriptor via
`/proc/self/fd`, and keeps that descriptor live through dispatch publication or
rollback. Dispatch-scoped cleanup closes every proof on every exit path. New
deterministic resolver and dispatch regressions swap in a repository with a
different commit/tree only while each subprocess runs; Git remains bound to the
original directory object, and a substitute expected tree is rejected with
byte-identical session and event ledgers.

Independent regression review A10 found that one descriptor-close failure
aborted cleanup of later proofs after session and event publication had already
committed, leaking a later descriptor and reporting failure for durable success.
Proof cleanup now attempts every retained close and propagates the first error.
Dispatch performs that cleanup inside its publication rollback boundary, so a
reported close failure has byte-identical pre-dispatch ledgers; successful
publication cannot subsequently become an exceptional caller result due to
proof cleanup. The deterministic two-proof regression injects the first close
failure, proves both
real descriptors closed and exact rollback, then proves a clean retry commits.

Independent regression review A13 found that the syntactic direct-object test
accepted either supported hash width without consulting the repository, so Git
could expand a 40-hex prefix in a SHA-256 repository. Direct hexadecimal
identities are now admitted only when their width matches an input object format
advertised by the bound repository. Resolver and dispatch regressions reject a
40-hex SHA-256 prefix without mutation and accept the exact 64-hex commit.

Independent reviews A15 and A16 found two further path/authority gaps. The
object-format query could rediscover a transient substitute `.git` directory
before later resolution returned to the authentic SHA-256 repository, and
lexical normalization could erase a symlink followed by `..` before the
no-follow walk. The resolver now rejects lexical parent components before
normalization and authenticates one retained repository authority before any
Git operation. Ordinary `.git` directories and linked-worktree gitfiles,
gitfile targets, `commondir` files, and common-directory targets are opened
without following symlinks and retained through dispatch publication. Every Git
child receives the same worktree, Git-directory, and common-directory
descriptors explicitly. Direct object input must additionally equal the full ID
returned by Git. Exact resolver and workflow regressions swap a SHA-1 `.git`
directory into a SHA-256 worktree only during the format child, reject the
40-hex prefix with an expected tree and no ledger mutation, and still accept
the authentic 64-hex ID. Companion regressions reject a symlink/`..` path before
Git runs and prove linked-worktree gitfile/common-directory resolution.

Focused regressions cover symbolic and exact refs, branch/tag ambiguity,
nonexistent full-looking SHAs, object/tree authentication, expected-tree
mismatch, detached-head review semantics, symlink retargeting, root
rename/replacement, publication-boundary rollback, partial-clone missing-object
behavior, exact issued/event identity, governed launch behavior, and
byte-identical atomic rejection. The partial-clone checks use a sentinel
transport and prove that neither dry-run nor confirmation invokes it. The
QPBT-045 contract is exercised without a cache implementation change: an
invalid exact main reaches zero warm/build, publication, and metric actions.
The focused resolver suite passes 18/18 and the workflow module passes 94/94.
The single dependency-free aggregate run passed 416/418; its two unrelated
Unix-socket cases were denied by the managed sandbox with `EPERM`, then both
passed in a bounded unsandboxed follow-up. The canonical checker, compileall,
and canonical workflow validation pass. A fresh immutable independent review
remains required before activation.

## 0.1.12 (2026-09-03)

The user-authorized repository mirror is now explicit. The root coordinator may
push each validated coherent local checkpoint to the attached
`Dengnifer/MIPStarRE-B` `github` remote with bounded retries. Local issue, PR,
review, and session ledgers remain authoritative; child sessions cannot push,
and the umbrella repository, MIPStarRE-A, runtime caches, credentials, and
unrelated remotes remain out of scope. This change resolves the earlier
local-only wording without changing the singleton build or exact-review rules.

## 0.1.11 candidate (QPBT-051) - 2026-09-03

INC-065 is the third `hot-cache-input-preflight-omission`. INC-070 records a
seeded writer worktree that still lacked ignored foundation sources, and
INC-071 is the third manual omission of the materializer preservation flag.
Canonical warm now authenticates the complete Mathlib, MIPStarRE, and eight
Lake-package input tuple before a hit or builder election without changing the
cache key. The new `prepare` path combines deep private seed with mandatory
replacement-mode foundation materialization, authored-QPBT preservation, and
final verification without invoking Lean or Lake.

Security review A03 found that preflight reopened mutable verifier/pin bytes,
`prepare` returned an authored inventory captured before verification, and its
seed lock/backup lifetime ended before materialization. The repair captures
every identity input with bounded no-follow reads, authenticates it against the
cache identity, and executes or parses only the captured verifier, pin, and
manifest bytes. `prepare` now holds one target lock and replacement rollback
boundary through final deep identity checks, compares initial, verifier, and
post-verifier authored evidence, and returns only the final inventory.

Follow-up review A05 found that captured pins and manifests still crossed
mutable temporary pathnames and that replacement rollback ended before a
fallible success-metric append. The follow-up repair passes authenticated bytes
through exact-path in-memory verifier adapters, restores temporary module hooks,
catches interruptions across seed replacement, and retains the old `.lake`
through successful metric publication. Post-commit backup cleanup is
best-effort and cannot turn a successful preparation into a failure.

Review A07 retained the replacement finding because a failed first
old-to-backup rename could withdraw the untouched destination, publisher return
preceded caller rollback ownership, and standalone `seed` discarded its backup
before its metric append. The transaction now records old-moved and
new-published states separately in caller-owned state, so both `seed` and
`prepare` cover publication through the success metric. Only post-commit backup
and rollback-staging cleanup are nonfatal.

## 0.1.10 candidate (QPBT-045) - 2026-09-02

INC-060 is the second occurrence of
`integrated-source-materializer-replace-existing-omission`. The recipe-v5 warm
for exact main `a648a7d6d2d24489e393e39c4d1cc7b7f1292ec8`, cache key
`3d5cb99499071dc935470d5c4dc0cd236bedd1baf867a720041648cbec9d9793`,
authenticated two authored QPBT files (5,319 bytes; inventory SHA-256
`0578da860a522b58b69c2c16df366c7eee3abd97c425900401e4e83c992803ed`)
but omitted `--replace-existing`. The materializer rejected the existing
output before dependency retrieval or Lean compilation. Its retained
`failure.json` and `build.log` are under the matching key in
`.workflow-runtime/cache/failures/`.

QPBT-045 first bumped the deterministic canonical recipe to v6 and added the
existing authenticated replacement flag. The materializer remains the sole
owner of atomic upstream replacement and reserved-tree copying; the cache now
also binds and rechecks the exact authored path-and-byte inventory before
materialization, after materialization, after dependency retrieval, after the
build, and immediately before publication.

Immutable review A03 then reproduced three fail-open gaps: the lexical walker
could follow a substituted root or child directory, exact hard-linked authored
files passed because link count was absent from identity, and unreadable
generated subtrees plus exit-zero Git diagnostics could be omitted. The repair
bumps the canonical recipe to v7 so no v6 snapshot remains addressable. It
recurses from no-follow directory descriptors, verifies root and child lexical
incarnations before and after use, fails on every scan/stat/open/recheck error,
and requires single-link regular files with strong before/after descriptor and
name identity including `st_nlink`. Nonempty Git cleanliness diagnostics also
fail closed. Deterministic regressions cover root/nested substitution, helper
and complete-warm hard links, unreadable generated subtrees, no snapshot or
`READY`, zero/nonzero inventories, replacement, and version-only cache-key
determinism. Focused and aggregate gates plus a fresh immutable review are
required before integration; only then may a single lock-elected current-main
warm publish recipe v7.

## 0.1.9 candidate (QPBT-034) - 2026-09-01

INC-053 records three `agent thread limit reached` rejections after the local
QPBT-019 ledger admitted a third non-coordinator session while two
collaboration workers were visible. The caller-supplied aggregate capacity and
the backend's effective live admission limit had drifted, and the old ordering
durably issued a session before it knew whether an external thread existed.

QPBT-034 changes `codex-collaboration` admission to a spawn-first,
confirm-at-dispatch boundary. A deterministic `dispatch --dry-run` preflights
one exact candidate without changing canonical bytes. The backend then receives
only a bootstrap prompt. Rejection produces no confirmation call and therefore
no session/event mutation. Success returns the immutable external thread ID,
which the root coordinator must pass explicitly through `--confirm-launched`;
the legacy wrapper uses `--launched-external-id`. Generic dispatch JSON cannot
serve as confirmation. The locked confirmation transaction reruns every local
admission check, binds the ID into the active record and issuance event, and
retains the state/event transaction across any append or audit failure. A
post-spawn confirmation failure requires immediate interruption of the inert
bootstrap thread before deterministic retry.

Only collaboration issuance requires the prelaunch confirmation, and active
collaboration rows enforce the invariant during schema validation. Governed
`codex-cli` rows remain capacity-gated but are issued with a null ID; their
launch lease claims authority before running and imports the actual runner-returned
ID without invention. Terminal legacy rows remain compatible. Nested parents
and children each consume one
non-coordinator slot, and nested launch uses the same root-confirmed bootstrap
sequence. Focused regressions cover the
three-rejection ordering class through a no-confirmation backend rejection,
exact state/event byte preservation, deterministic preflight retry, generic-ID
bypass rejection, queued confirmation drift, identity-bound issuance, nested
slot accounting, parser failures, and preservation of the prior transaction
rollback test. Aggregate evidence and independent immutable review remain
required before activation.

The A03 repair resolves the first immutable review's two findings. A governed
fake-runner integration covers null-ID CLI dispatch, claim, execution, and
terminal ID import. Dispatch rollback now catches `BaseException`, restores the
exact sessions/event snapshots, and re-raises. `KeyboardInterrupt` regressions
exercise publication of `sessions.json`, each of two `session.issued` events,
the `sessions.dispatched` summary, and the post-publication audit; every case
validates exact bytes and the same deterministic retry plan.

## 0.1.8 candidate (QPBT-027) - 2026-09-01

The QPBT-026 A15 critical-path audit
(`workflow/reviews/qpbt-026-stage2-critical-path-a15.md`, SHA-256
`266bd04517a5214d5a63c2058b685350268c56707ecafcd96acdccfa5295a17f`)
exposed a contradictory finding-ledger contract: approval required every
resolved finding's resolution review to match the current head, while the
update guard permanently fixed that review ID after the first resolution.
LPR-016 demonstrates the failure with resolutions on multiple historical heads
and another required repair head still pending.

QPBT-027 preserves every original finding identity and resolution field and
adds one backward-compatible, optional `confirmation_review_ids` list. Entries
are unique, chronological references to fresh independent terminal formal
reviews on the same PR, and only approving reviews may reconfirm a disposition.
Both the PR review ledger and each confirmation list remain append-only.
Approval and merge accept the immutable original resolution when it is current,
or an appended approving confirmation bound to the exact current base/head;
historical confirmations never authorize a later head.

Focused regressions cover head advancement after one finding is resolved and a
later finding is introduced, approval with and without current confirmation,
duplicate, non-string, unknown, wrong-head, and non-approving confirmations,
plus immutable resolution fields and confirmation removal/replacement. Existing
records need no migration because an absent confirmation list is the empty
history. The independent read-only A02 contract audit found and drove closure
of malformed-value crashes in this exact confirmation/reviewer/update surface;
its final 26-case replay had no unexpected result
(`workflow/reviews/qpbt-027-reconfirm-contract-a02.md`, SHA-256
`148c9e1596e8bab2fdc5071c4c57dc8f1cc337ce81005be12c2b926bacb9d5e2`).
Focused tests pass 8/8, the workflow module passes 67/67, and the dependency-free
aggregate passes 320/320. Fresh immutable PR review remains required before this
candidate is activated.

## 2026-09-01

- QPBT-026 A17 closes A14's two offline-isolation findings. Injected Codex
  capability evidence is now copied and field-validated before repository,
  harness, output, lease, or runner effects; empty mappings cannot invoke the
  real capability probe. Local Git operations and the injected offline runner
  receive a fixed minimal environment rather than ambient process state. It
  excludes repository/worktree/index, object/alternate, namespace/replacement,
  shallow, discovery/quarantine, ceiling, template, and config-injection
  selectors. The adversarial regression plants the source object database as an
  ambient alternate and proves that the projected harness still has zero local
  objects, reports no alternate, and cannot resolve the unmanifested source
  head. Production dispatch remains fail-closed at the earlier exact-content
  and filesystem-isolation boundary.

- QPBT-026 A11 closes the remaining disclosure replay and readable-scope
  findings by disabling production review dispatch at the boundary that cannot
  yet prove exact content authorization and OS-enforced read isolation. A
  matching version-1 changed-path record is now structural validation only and
  fails before task/context reads, Codex persistence/capability probes, evidence
  creation, lease claim, or runner invocation. The module-global singleton and
  independently callable post-probe production helper were removed, leaving no
  offline/production, cross-target, cross-profile/model, direct-attribute, or
  duplicate-consumption capability surface. Committed offline tests now use a
  fresh evidence repository with no source objects or remote, inert base/head
  endpoint bytes, an exact patch, and path/object/mode/size/SHA-256 records. A
  complete offline packet projection also binds request, unchanged authority,
  harness manifest, derived evidence, and final prompt, while explicitly
  declaring that host isolation is not enforced and external launch is not
  authorized. This deterministic success reconciles the exact-content test gate
  without representing the offline harness as a production security boundary.

- QPBT-026 A05 addressed four pre-integration disclosure findings. At that
  revision, every model-backed review required an explicit transport profile and
  field-exact version-1 changed-path validation before packet loading,
  persistence probing, or lease claim; inherited/default provider configuration
  was no longer treated as local. Authorization validation returned only an
  opaque internal preflight token, and no raw or normalized authorization
  mapping entered a target, prompt, envelope, persisted result, or log. Commit
  target and declared-head resolution shared one preflight/capture
  implementation, so drift failed before lease claim.
  Full normalized repository paths were screened for sensitive directories and
  common key, credential, and private certificate/container forms, with rename
  detection disabled so both sides of a rename remain in scope. A library-only
  offline test mode required injected runner/capability records, substituted a
  non-`codex` executable marker, accepted no transport data, and had no CLI flag.
  Version-1 authorization remained committed-target-only; uncommitted bootstrap
  dispatch failed closed pending a separately reviewed snapshot schema.
  Official OpenAI and `https://api.finite-dimensional.space` are standing
  trusted Codex transports, but transport trust grants no content permission:
  every external review still requires its own exact immutable manifest and
  matching credential-excluding disclosure authorization. A11 later established
  that version 1 does not provide that manifest and disabled production dispatch.
  Public `.crt`/`.cer` material and generic `keys`/`auth`/`private`/`certs`
  paths remain allowed; high-signal credential dot-directories, service-account
  artifacts, `.npmrc`, `.pypirc`, and private-container suffixes fail closed.

## 0.1.7 candidate (QPBT-021) - 2026-08-31

QPBT-021 makes the pinned Mathlib source a first-class hot-cache input. The
canonical recipe accepts exactly one authenticated local Git worktree or the
audited shallow-repository archive at commit
`81a5d257c8e410db227a6665ed08f64fea08e997` and tree
`5ea66b811b8461daae82f14d356fed2a287d7c40`. Source paths remain outside the
cache key; the elected singleton validates the source, emits a deterministic
sorted `LAKE_PKG_URL_MAP`, rechecks the source before publication, and never
publishes an archive extraction. Missing, dirty, mismatched, malformed, or
conflicting inputs fail closed without `READY`. Git validation strips inherited
Git configuration, disables system/global configuration and executable command
hooks, and accepts only inert structural keys in the repository's local config.
It also rejects symlinked or special Git metadata, external common directories,
and index visibility flags that could hide worktree changes.

The pinned archive is 51,938,317 bytes with SHA-256
`c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7`; its
decompressed tar is 147,712,000 bytes with SHA-256
`ad9a60b01736070112fbc1008ea98c67e68fa045c5b69e66873e0b9444ddd3ba`. Focused
hot-cache tests pass 42/42, including a real archive extraction, malformed
archive and symlink-chain rejection, alternate source paths with one cache key,
an executable `core.fsmonitor` trap, exact Lake command/environment
construction, and an explicit Reservoir `cache get` failure. Reservoir artifact
retrieval remains a separate network/cache policy: a local Mathlib source does
not claim a fully offline warm.

## 0.1.6 candidate (QPBT-022) - 2026-08-31

The hot-main cache now derives its omitted runtime root from the primary
non-bare Git worktree. Linked issue worktrees consequently contend on one
filesystem lock and cannot duplicate a build for the same cache key. An
explicit `--runtime-dir` retains its prior absolute/relative path semantics;
the default skips prunable/unresolvable worktree records and fails closed with
an explicit override when the repository root or primary cannot be resolved. A
two-process linked-worktree regression exercises the election and records one
build with one waiter, while CLI regressions cover missing roots and resolution
failures. Canonical revision state and independent review remain with QPBT-022
integration.

## 0.1.5 - 2026-08-31

QPBT-019 adds a locked, capacity-aware dispatch boundary for local session
creation. The explicit `dispatch --capacity N` limit is compared with active
non-coordinator `issued`/`running` sessions; planned IDs are sorted and
reported across all backends in the selected local scope as dispatchable,
queued, or blocked after dependency, stage, and writable-path
checks. Capacity-only queueing issues the sorted available prefix atomically and
leaves the remainder planned; any blocked selected member leaves the requested
batch unchanged. Cross-candidate materialization checks apply to the admitted
prefix; queued rows are revalidated on a later attempt, while ownership checks
remain conservative across the selected set. `--dry-run` has no state effect.
The `backend_scope: all` value denotes one local-service ceiling: active counts
are summed across every backend and the explicit capacity is never multiplied
into per-backend quotas.
Unknown capacity now defers its rejection until dependency and writable-path
checks have produced deterministic diagnostics; the operation still fails closed
without changing state or events.
The stage `max_concurrency` counter remains an observed metric. Capacity does
not permit parallel Lean/Lake builds: callers still wait for the singleton
hot-main cache builder. The four-slot collaboration ceiling is recorded only as
the current environment observation, never as a hard-coded default.

Focused dispatch regressions cover explicit/unknown capacity, coordinator
exclusion, deterministic queue and block reasons, cross-candidate validation,
ownership conflicts, dry-run behavior, and atomic event/state updates.
The legacy `issue-session` command now routes through the same planner and
requires an explicit capacity, so authority-changing additions cannot bypass
dependency, ownership, or admission checks; successful calls retain the
historical issued-record JSON shape while queued/blocked calls return the
planner envelope. Admission reserves one orchestrator slot per issue (planned
or active duplicates are blocked), and mixed single-record/keyed override
objects are rejected.
The writer snapshots the sessions bytes and event offset and rolls both back
when an event append or post-append audit fails; crash-recovery journaling is
deferred to QPBT-020.

## 0.1.4 - 2026-08-31

The first full-tree staging attempt after A14's approval failed
`git diff --cached --check`: fourteen new files ended with an extra blank line.
The frozen `git diff --check` result was truthful but incomplete because an
unborn repository exposes no unstaged diff for untracked files.

Bootstrap core text hygiene now rejects a final empty logical line and records
`blank_line_at_eof_paths` alongside the existing trailing-whitespace and ASCII
checks. A focused regression covers `text\n\n`; the fourteen reported files
were changed by exactly one final LF each. An independent reviewer verified
those byte deltas against the prior frozen hashes and found no terminal-evidence
or unrelated edits. Focused tests pass 9/9, the aggregate gate passes 83/83,
and a disposable full-tree index passes `git diff --cached --check` while the
real bootstrap index remains empty.

## 0.1.3 - 2026-08-31

A12 proved that the nested Codex session and custom-provider boundary now work:
the isolated reviewer completed in 80.313 seconds and returned valid structured
evidence. It nevertheless blocked because its launch snapshot necessarily showed
its own session as nonterminal and the bootstrap seal as null. Both fields can
only be completed after the reviewer returns, so asking for them beforehand made
the acceptance gate circular.

Bootstrap reviews now pass an exact frozen-core digest through a dedicated,
validated phase contract. Fixed trusted text distinguishes review of that core
from the narrow lifecycle/report/seal evidence populated after return. The
launcher accepts this mode only for an unborn uncommitted repository, verifies
the unsealed Stage 1 manifest and exact terminal allowlist, rejects noncanonical
trusted phase fields, and never imports manifest prose as authority.

Independent review then found and closed two further safety defects: helper-level
callers could add keys to the trusted phase mapping, and source contents could
change between initial verification and evidence capture. The final launcher
canonicalizes the phase record and, after capture, reverifies the freeze,
byte-matches the copied manifest, and binds every captured core path and hash to
the frozen manifest before prompt construction or model dispatch. Focused tests
pass 30/30, the aggregate gate passes 82/82, and fresh re-review approved with no
findings.

## 0.1.2 - 2026-08-31

Compact A10 ruled out request-envelope size as the root transport cause. The
installed CLI documents that `--ignore-user-config` disables the entire user
configuration, not only instructions. That erased the custom provider URL,
Responses wire setting, and `requires_openai_auth` mapping used by the
successful health probe.

Nested reviewers now keep `--ignore-user-config`, `--ignore-rules`, read-only
sandboxing, and the isolated evidence harness, while receiving an explicit
all-or-none non-secret transport profile before `exec`. The wrapper validates
the provider config key, display name, HTTPS base URL, exact `responses` API,
and auth-mode boolean. URLs with credentials, userinfo, queries, fragments, or
non-HTTPS schemes fail closed. Authentication values remain in Codex's auth
store and are never accepted, read, copied, or recorded by the wrapper.

An empty-repository control first reached the authorized endpoint and returned
the expected 401 without the auth mapping. Adding only
`requires_openai_auth=true` then returned the exact requested response in
15.787 seconds. Focused tests pass 26/26, the aggregate gate passes 78/78, and a
fresh read-only child reviewer approved with no findings.

## 0.1.1 - 2026-08-30

Two full frozen-review attempts reached their wall-clock bounds without model
work even though the exact endpoint and model completed a tiny health probe.
The second failed packet was 36,041 bytes and redundantly inlined every
untracked manifest entry. Frozen prompts now carry only a fixed-shape target
summary, the exact manifest-file digest, and its logical digest. The full
manifest remains in the isolated harness and result envelope and is reverified
immediately before dispatch. Prompt byte length is recorded, and regression
tests require prompt growth to be independent of manifest cardinality.

Endpoint liveness and local packet-size construction are separate gates. Files
already present in frozen evidence are inspected there rather than copied into
caller context. The current packet is about 4,136 bytes before task-specific
text, down from 36,041 bytes for A08.

The user also closed the Stage 1 scope: after an acceptance gate passes, only a
failed acceptance test, concrete safety issue, or direct user requirement may
change that stage. Every other improvement is deferred to a numbered issue.

## 0.1.0 - 2026-08-30

Initial local-first protocol, derived from:

- `LionSR/MIPStarRE` at `507e81220d95266ff3d589d125b2f87c7300a9fb`;
- `LionSR/TeXRA` at `039757e8b076ac6bf43c5b7623b61cd8543d7b64`;
- the initial QPBT source audit of arXiv:2001.04383v3.

It replaces GitHub state with versioned issue/PR/session records, GitHub Actions
artifacts with a locked atomic hot-main cache, and mention-triggered review bots
with fresh read-only local Codex reviewers. It adds explicit session lineage,
honest token-availability fields, cache timing, incident classes, and the
third-occurrence evolution trigger that the source workflows lacked as a single
research ledger.

Adversarial bootstrap review hardened the initial revision before its first
commit. The cache now binds its canonical recipe, rechecks source state, and
deeply verifies artifact inventories before seeding. Review targets and trusted
authority are isolated and content-addressed. State transitions enforce
immutable session authority, SHA-bound PR evidence, independent reviewers,
fresh finding resolution, worktree-aware ownership, and formalization
orchestrators. Canonical events are chronological and reconciled with session
lifecycle, and the aggregate gate reconciles incidents, protocol changes, and
terminal-session metrics. `protocols.json` itself now participates in canonical
state validation. A failed real-review preflight further separated host-level
Codex session persistence from the reviewer model sandbox: the host wrapper may
need approved filesystem access, while the nested reviewer remains read-only in
an isolated evidence repository. A subsequent host-enabled review stalled for
more than 21 minutes without exposing intermediate events, which added a
bounded, interrupt-safe reviewer timeout and structured partial-result evidence
to the bootstrap hardening scope. The same boundary was applied to execution,
archive, and capability probes. A later 503 during an agent's final report was
recovered by a no-edit report-only retry under the same session identity.
The first subsequent external reviewer launch was rejected before execution,
which made disclosure consent an explicit precondition: sending a frozen local
repository snapshot to the Codex service requires separate user authorization,
and a rejected launch receives a terminal alias rather than a workaround.
The user subsequently authorized `gpt-5.6-sol` at
`https://api.finite-dimensional.space`; the non-secret endpoint/model/wire
profile and evidence scope are now bound into the review record.
The first authorized attempt then exposed endpoint transport failure rather
than a review finding: WebSocket and HTTPS requests both failed for 900 seconds.
The protocol now requires a minimal successful endpoint/model health prompt
before another full frozen-evidence attempt.
The first such probe selected plain `/tmp` and was rejected locally by Codex's
Git trust check. Repository-free health probes now use a disposable empty Git
repository rather than disabling that check.
The corrected empty-repository probe returned the exact requested response in
15.196 seconds with complete usage evidence and archived successfully, clearing
the endpoint-health gate for the next frozen review.

Revision 0.1.0 is re-evaluated after three completed issue workflows and must be
superseded if it permits duplicate main builds, overlapping writable ownership,
or review state that cannot be tied to an immutable SHA or bootstrap manifest.
## 2026-08-31

- QPBT-026: external reviewer dispatch now has a strict opt-in disclosure
  preflight. A version-1 non-secret authorization record binds endpoint origin,
  model, wire API, immutable base/head/tree, and changed private-file path names
  while requiring credential and unrelated-content exclusion. The check
  runs before packet/evidence preparation, persistence probing, or issued-lease
  claim, and rejects missing, drifted, duplicate, or credential-looking paths.
  This is the smallest protocol response to INC-045 and does not authorize any
  endpoint, model, or repository contents by itself.
  QPBT-026 A11 subsequently established that this record is not exact content
  authorization and disabled production dispatch pending enforceable isolation.

- Added issued-session launch leases with locked authority checks, exactly-once
  terminal envelope imports, and explicit idempotent interruption recovery.
- Remediated the initial candidate after pre-review: governed exec and review
  now bind complete authority, all post-claim failures terminate the lease,
  imports and recovery are byte-idempotent under the real WorkflowStore, and
  archive retries cannot silently invoke Codex again.
- Hardened the lease boundary after independent review: claims now verify the
  live clean Git `HEAD` and tree against the issued base, lifecycle rollback
  covers interrupts, terminal paths are normalized and bound to the issued
  result envelope, and recovery emits archiveable evidence with exact-once
  reuse.
- Hardened runtime publication after LPR-009: Git claim/status probes isolate
  inherited configuration and disable repository hooks/fsmonitor; governed
  terminal imports transactionally publish or roll back their result artifact;
  archive aliases use no-follow runtime confinement, strict envelope reuse,
  atomic directory publication, interruption cleanup, and same-alias locking.
- Closed the remaining launch/archive race window after immutable review:
  governed exec/review repeat canonical worktree identity checks immediately
  before child spawn, and archive retries verify stdout/stderr byte counts and
  SHA-256 digests against the recorded log files before reusing an envelope.
