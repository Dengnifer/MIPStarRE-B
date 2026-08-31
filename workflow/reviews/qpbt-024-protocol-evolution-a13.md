# QPBT-024 second post-build verifier failure: protocol-evolution audit (a13)

## Verdict

**No protocol revision is justified now, and the third-occurrence rule is not
triggered. HOLD any further QPBT-024 implementation until the exact
`proofwidgets` delta and its producer are identified.**

The retained `9c9b495` / `9b6ccb7` envelope proves a second independently
executed warm reached the post-build package verifier and failed its archive-tree
comparison, this time at `proofwidgets`. It does not preserve or enumerate the
changed paths. Calling the cause a second legitimate generated-output boundary
is therefore provisional, not an established forensic fact. The safe count is:

- canonical `INC-044` remains at recorded count 1 until root imports classified
  evidence;
- if the `proofwidgets` delta is legitimate Lake-generated state misclassified
  as source, this is `INC-044` occurrence 2;
- if it is a different cause, it is occurrence 1 of a new class, not occurrence
  2 of `INC-044`;
- neither branch reaches three.

Do not count INC-031, individual generated files, two SHA comparisons in one
verifier invocation, or multiple affected package names as extra occurrences.
INC-031 was the absence of a post-build verifier plus a lock-incarnation defect;
both failed warms here had the verifier present and failing closed. A17 expressly
classified INC-044 as distinct from INC-031.

This audit is the required evidence-based evaluation; its result is zero
protocol edits. A second occurrence permits earlier consideration, but
`AGENTS.md` mandates an issue/evaluation only on the third occurrence. The
earlier-intervention allowance in `protocols/meta.md` permits a safety change;
it does not require a new protocol mechanism when the existing authority is
sufficient.

## What the evidence proves

### First occurrence: c0de/dba1

The retained failure is bound to main
`c0de0900a01724c2a515311424dcbe5e7526ebd4` and key
`dba1d9c8846d98a7804aaf972c0aa284a3ed7c9500aa7c79b70cfdf871e50276`.
Its build completed 8,992 jobs, then reported:

```text
error: materialized archive tree differs for plausible
```

A15 identified 169 ordinary build artifacts below
`plausible/.lake/build/**`; A16 traced the verifier's forced whole-tree staging.
The canonical incident is `INC-044`, count 1.

Retained evidence SHA-256:

```text
6585f5226a1163527193dafb0dd49d6614e7917dfdc14d08600bd8f37b6ed401  failure.json
7fcc04ad7e13187dfa3159f1495c2981fdb47d0fa5a253249e69573e691b92bf  build.log
```

### Second failed hypothesis: 9c9/9b6

The retained failure is bound to integrated main
`9c9b49548fabdd6b01916787d7dc17a4bca36513` and key
`9b6ccb722e8943a7790b94f839edca0b6bed53f720284ea2a3f6762a9fba1f36`.
The materializer input changed from SHA-256 `73bc42...` to the repaired
`3325a1...`. Its build again completed 8,992 jobs, then reported:

```text
error: materialized archive tree differs for proofwidgets
```

Retained evidence SHA-256:

```text
a97fa0f97189d1e704808d1ea5e0aa209d269d915b6c5b293b7e117f9d536c48  failure.json
ed0f4d6e2f05f52e175723aac2d69b60230b50962c706c67098d81c665e1fe45  build.log
```

The error names a package, not a path or producer. The retained failure
directory contains only the envelope and build log. No claim about
`.lake/lakefile.olean`, barrel files, or any other particular path is supported
by this evidence.

### What QPBT-024 actually implemented

`scripts/materialize_lake_packages.py:990-1049` validates and projects only the
exact package-root `.lake/build` subtree. Both verifier comparisons use that
projection at `:1926-1954`. Archive inspection separately forbids an upstream
archive from containing `.lake/build` at `:822-825`.

`tests/test_lake_package_materialization.py:361-470` intentionally requires
`.lake/not-build`, `.lake/build-sibling`, and `src/.lake/build` to remain
authenticated. Thus broadening the projection now would contradict a deliberate
acceptance boundary; it is not a mechanical completion that can be inferred
from the package name.

## A01-A10 disposition

- A01 implemented and validated the exact `.lake/build` projection on
  `9c9b495`; it did not claim a successful governed warm.
- A02 deliberately superseded A16's broader package-root `.lake/**` proposal
  and required all paths outside `.lake/build` to remain authenticated.
- A03 correctly classified that bounded, already-specified correction as
  implementation work rather than protocol evolution. Its conclusion does not
  prove that an unidentified second path should be ignored.
- A04 bound the immutable candidate and LPR-014; A06 held the integration/warm
  lifecycle; neither supplied post-build success.
- A05 found compatible legacy `.lake/build` output for all eight packages, but
  explicitly said the legacy snapshot was not a byte-for-byte reproduction and
  that the governed warm was definitive. The `proofwidgets` failure activates
  that residual risk.
- A07 appropriately approved conformance to the stated gate. The later failed
  acceptance test shows the gate/diagnosis was incomplete, not that the review
  silently approved a different source projection.
- A08's failure branch requires provisional same-class treatment only until
  evidence classifies the cause, forbids an unchanged retry, and says to
  increment INC-044 only for a confirmed same-class failure.
- A09 froze an evidence procedure and expressly made acceptance conditional; it
  was not a warm-success report.
- A10 correctly keeps all Lean writers held. Its QPBT-017 lane is later,
  independent protocol synchronization debt, not a way to bypass QPBT-024.

## Existing protocol authority

The current rules already require the properties that matter:

- `AGENTS.md:49-60` requires one elected builder, a content-bound recipe and
  inventory, private seeds, and recorded cache evidence.
- `protocols/local-development.md:38-63` requires atomic publication only after
  success, an inventory of the entire root `.lake`, deep seed verification, and
  no publication of failed staging output.
- `protocols/orchestration.md:196-206` requires source rechecking immediately
  before publication and does not permit READY to hide dirty source.
- `INC-044.protocol_effect` already states the operational split: authenticate
  immutable package source while READY inventory binds permitted generated
  artifacts.

The package source/generated projection is an implementation of those
authorities. A new path-specific protocol clause before path diagnosis would be
speculative and would create a second authority beside QPBT-024's acceptance
gate. Conversely, removing post-build verification, accepting arbitrary ignore
lists, or ceasing to inventory generated output would be a protocol change and
is forbidden.

`protocols/meta.md:46-52` and `protocols/CHANGELOG.md:159-161` allow an accepted
Stage 1 surface to change only for a failed acceptance test, concrete safety
issue, or direct user requirement. This failure is both a failed acceptance gate
and a cache-integrity safety concern, so a smallest necessary change is
permitted. That exception is a scope ceiling, not evidence that documentation
must change. The direct gate therefore supports the repair below but does not
alter this no-revision verdict.

## Smallest action now: implementation diagnosis and correction

Keep QPBT-024 open and do not retry exact `9c9b495` / `9b6ccb7`. Before any
writer is dispatched, produce immutable evidence that identifies:

1. every path included in the `proofwidgets` observed tree but absent from its
   pinned archive tree;
2. object kind, mode, link count, and content identity for each path;
3. the exact Lake/build command or package declaration that produces it;
4. why the path is generated state rather than authenticated package source;
5. whether the rule is package-independent or truly package-specific.

Only after that classification may root update the unique incident record and
amend QPBT-024's acceptance gates. If it is same-class generated drift,
monotonically update INC-044 to count 2; preserve the first occurrence and append
the second session/evidence. If different, follow A08's new-class/new-dependency
branch. Canonical state and metric edits remain root-only.

If the diagnosis proves another legitimate generated boundary, the smallest
writable implementation surface remains exactly:

```text
scripts/materialize_lake_packages.py
tests/test_lake_package_materialization.py
tests/test_hot_main_cache.py
```

Required implementation gates:

1. Preserve complete pre-Lake archive identity and structural rejection of
   generated paths in authenticated archives.
2. Accept the exact observed legitimate output through a structured,
   non-caller-controlled projection; do not add an arbitrary ignore list.
3. Retain the existing `.lake/build` regressions.
4. Reject source files, `lakefile.*`, `lake-manifest.json`, symlinks, special
   objects, multiply-linked regular files, sibling/lookalike paths, and every
   path not established by the diagnosis.
5. Preserve both archive-tree and Gitlink-reconstructed comparisons, package
   materialize/verify/deps/build/verify order, no-READY on drift, and full root
   `.lake` inventory/READY binding of excluded generated artifacts.
6. Run the focused materializer suite, focused hot-cache suite, full serial test
   aggregate, workflow checker/validation, compileall, and SHA-bound diff
   hygiene on one exact candidate.
7. Obtain a fresh immutable **code** review after the head changes.
8. After integration, authorize exactly one newly changed-hypothesis warm; close
   only on verified status/READY/deep-inventory success.

No separate protocol reviewer is required for that implementation-only branch.

## Conditional protocol scope if diagnosis proves a normative gap

Do not take this branch merely because the second warm failed. Take it only if
the exact diagnosis shows the current protocol cannot determine which authority
owns the observed path, or if the repair changes the normative source/inventory
contract rather than implementing it.

The smallest textual/test surface would then be:

```text
protocols/local-development.md
protocols/CHANGELOG.md
tests/test_cache_protocol.py        # new; currently absent
```

`protocols/orchestration.md` should remain unchanged unless the diagnosed rule
changes its publication ordering or source-recheck authority. The local
development clause should state one source authority and one artifact authority:
the exact authenticated package-source projection; the exact Lake-owned
generated boundary proven by the diagnosis; fail-closed boundary validation;
post-build source reverification; and full `.lake` inventory/READY binding of
generated output. It must not enumerate an unobserved path or introduce a
general ignore mechanism.

The new `tests/test_cache_protocol.py` must be omission-sensitive: deleting the
source projection, generated-artifact authority, post-build verification, or
inventory/READY clause from an in-memory copy must make the test fail. A mere
substring-presence test without a negative omission case is insufficient.

Protocol-branch gates would be:

1. motivating exact-path evidence and a root-authorized protocol revision;
2. focused `python3 tests/test_cache_protocol.py` success plus a demonstrated
   negative omission case;
3. the implementation gates above and aggregate workflow validation;
4. a changelog entry and root-owned protocol revision/metric reconciliation;
5. a fresh adversarial read-only **protocol** reviewer independent of the
   implementer/orchestrator, followed by the ordinary immutable code review.

QPBT-017 already plans edits to these same three paths for recipe-documentation
synchronization and depends on QPBT-004, while QPBT-004 depends on QPBT-024.
Therefore QPBT-024 must not depend on QPBT-017, and no overlapping QPBT-017
writer may run in parallel. If this conditional branch becomes necessary, root
must explicitly add/deconflict the three paths under the active QPBT-024 repair
worktree; QPBT-017 can later rebase and complete its distinct recipe-enumeration
gates after QPBT-004. A planned lane is not an issued session.

## Accounting and provenance

- Logical session: `i024-scout-a13-protocol-evolution`.
- Start: `2026-09-01T01:19:58.401273441+08:00`.
- End: `2026-09-01T01:30:55.554494570+08:00`.
- Elapsed: `657.153221129` seconds.
- Token usage: JSON `null`; availability reason: the collaboration backend does
  not expose per-session token usage. No estimate was made.
- Subagents: 0; topology: root coordinator -> one read-only scout.
- Repository edits, state/Git writes, tests, builds, warm, seed, Lean/Lake,
  network, and cache-runtime mutation: 0.
- Authored output: only `/tmp/qpbt-024-protocol-evolution-a13.md`.

Primary inspected SHA-256 values:

```text
c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c  AGENTS.md
3b111e8a95025270bf24c7fd7d8601ca5000b6cc37582ca1bf3bff487c7c874a  protocols/local-development.md
389d2211b0c847069e158b1355f577fce66aee0225f9545c93417a2036ec21f9  protocols/orchestration.md
04525efbfbf1074c84497d26d6de6173bd3c63567898dafab1252cd6d24516c8  protocols/meta.md
94f983ca1bb2fc11c161ec4ac18eed38fbad97239838c31a26f044c2daa61380  protocols/CHANGELOG.md
4d4e6b079ed00d8feab474d7c7141e4ff351c7aac5f1fe52e2129533791209ec  research/metrics/incidents.jsonl
52412542f91f0e80c8a9ed3a092dd8a9da9cfd1e7982baa48b7b999bc5c4a538  workflow/state/issues.json
3325a1ad523f4fb84bedc6957218fcd412fd7af2c0a9c19e23c799523c69c243  scripts/materialize_lake_packages.py
d17364aa5e08ee7dc796a4bf14d1d90e2944bce5ee0cf0324c3a7a7f6736be1d  tests/test_lake_package_materialization.py
235c7466c66d2acb9ef7a3a8658d20c693e2410fad2e5f760157e92c870d41fe  tests/test_hot_main_cache.py
```

QPBT-024 report SHA-256 values A01-A10, in order:

```text
3f0bc92b995e74f2b57330d431db395c3bcc670ccafa497fcc803a664b1e4677
2997a94dd93733bbd699393828e619bdd29366decb6a4c9c7c785be5eef6ebdc
caad36e3d544878e52733100b5f66e1dcc87ad25800f3b02dee8a26e41ef4917
68380edb4d53066c533c617150b6849650736588d30366c772edaf10279bb072
771bdbc6b3a03de0a6ed75831dbfaaead42b8bb41bcbd588651ba4355f99564e
0ebd23e030a4b5f5a642aa2099830557c3adb8eb91edbd94adfe1c16ccc9f85b
c71a8dee299ca7437b20f1d9874d82dab2da10cfdfcd605fd3476f76ce625141
7f3793e65081f9c0b539715ebc36a3f575a9dc8e68e5a8052717bca892f0b0fd
cf8d984a7ae916baa216265f7625d06d70fc41fc3b2cfb47d838f865585d1b09
af993c21ac14546290bcacba1dc9496796d22b88d5d7b86511742cdc67433a09
```
