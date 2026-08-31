# QPBT-024 protocol-scope audit (a03)

## Conclusion

The bounded QPBT-024 repair does **not** change a normative protocol, provided
the candidate remains within the issue's exact contract: full archive identity
before Lake; post-build package-source verification that projects out only a
validated package-root `.lake/build` subtree; rejection of every mutation
outside that subtree and every malformed boundary; unchanged verification
order; and full `.lake` artifact inventory/READY binding.

Therefore QPBT-024 requires its already-recorded fresh independent immutable
code review, but it does **not** require edits to `AGENTS.md`, `protocols/`,
`protocols/CHANGELOG.md`, or `research/metrics/protocol_changes.jsonl`, and it
does not require a separate protocol reviewer. No protocol revision should be
created for this correction.

This conclusion is bounded. Excluding all of package-root `.lake`, accepting an
arbitrary exclusion list, weakening/removing/moving the post-build verifier,
stopping full archive verification, or ceasing to inventory generated output
would exceed QPBT-024 and materially alter the security contract. Such a change
would require explicit protocol evolution, changelog and protocol-change
evidence, validation, and independent protocol review.

## Evidence

- Audited Git `HEAD` is the required exact base
  `38dc1b9be719ce6b9e3eb9b57ecabc40b9a624fe`.
- `QPBT-024` is explicitly an implementation issue. Its gates retain the full
  pre-Lake identity check and narrow only the post-build comparison to the exact
  validated `.lake/build` subtree. Its orchestrator owns only
  `scripts/materialize_lake_packages.py`,
  `tests/test_lake_package_materialization.py`, and
  `tests/test_hot_main_cache.py`; its issued validation contract expressly
  forbids protocol edits.
- `protocols/local-development.md:45-48` already separates the generated
  artifact authority from source identity: the complete `.lake` tree is
  content-inventoried and bound by READY, then deeply verified during seed.
  The repaired source projection leaves that authority unchanged.
- `protocols/orchestration.md:201-206` requires source to be checked again
  immediately before publication and rejects missing, dirty, or mismatched
  source. QPBT-024 preserves that rule by checking every package path except
  the one exact generated-output subtree; it changes the implementation's
  erroneous source domain, not the normative requirement.
- Resolved finding `F-LPR005-001` requires an identity-bound post-build package
  verification so build-time source mutation cannot enter READY. A17 explicitly
  says not to reopen or rewrite that finding: its resolution remains true
  because the verifier exists and failed closed. QPBT-024 preserves the second
  verifier and its location.
- A15 identifies the observed 169 additions exclusively under
  `.lake/build`, calls the mismatch an identity-boundary bug, and prescribes the
  narrow projection while retaining full archive hashing, all paths outside
  `.lake/build`, special-object rejection, and the later full `.lake` inventory
  (`qpbt-018-plausible-drift-a15.md:91-129`). This matches the issue gates.
- A16 agrees that source and generated artifacts need distinct authorities and
  that READY inventory continues to bind generated artifacts
  (`qpbt-018-hotcache-verify-order-a16.md:89-91`), but proposes excluding the
  broader top-level `.lake` tree. The canonical QPBT-024 acceptance gate resolves
  that report-level disagreement in favor of A15's weaker, exact
  `.lake/build` boundary. The implementation must follow the issue, not broaden
  the exclusion from A16's prose.
- A16 also states that the materializer is already a hot-cache identity input,
  so no recipe-version edit is needed merely to obtain a changed key
  (`qpbt-018-hotcache-verify-order-a16.md:130-135`).
- A17 makes separate protocol review conditional: it is needed only "if the
  normative package-verification rule changes." The bounded repair does not
  trigger that condition. A17 otherwise requires ordinary immutable review of
  the successor head and one changed-hypothesis post-integration warm.
- `AGENTS.md:127-130` and `protocols/meta.md:80-94` govern actual protocol
  evolution. INC-044 is a new class at count 1, and this issue is a mechanical,
  durable boundary correction under existing source/READY authorities. A new
  protocol mechanism or rule is neither needed nor justified.
- `workflow/state/protocols.json` keeps revision `0.1.4` active. The current
  protocol-change metric has entries only through `0.1.4`; the bounded repair
  supplies no before/after normative revision to record.

## Scope and accounting

- Logical session: `i024-scout-a03-protocol-scope`
- Role/topology: one read-only scout under
  `i024-orchestrator-a01-source-projection`; 0 subagents; topology depth 1 from
  the issue orchestrator (depth 2 from the root coordinator)
- Issued start: `2026-08-31T16:00:25.644366Z`
- Evidence cutoff: `2026-08-31T16:02:25.788526414Z`
- Elapsed through report drafting: `120.144` seconds (agent measured from the
  canonical issued start; checksum verification followed)
- Token usage: JSON `null`; availability reason: collaboration backend does not
  expose per-agent token usage. No estimate was made.
- Subagent calls: 0
- Tests, workflow validation, Lean/Lake, builds, warm, seed, cache actions, and
  network actions: 0
- Repository, canonical state, metrics, runtime, cache, reference, and Git-ref
  edits: 0. The checkout already had coordinator-owned canonical-state changes;
  this scout did not modify them.
- Authored output: only `/tmp/qpbt-024-protocol-scope-a03.md`

## Evidence checksums

- `AGENTS.md`: `c7d985dfc145599045cfc75881250ff242d17db47ebd5d70bf82738e6ac8755c`
- `protocols/CHANGELOG.md`: `94f983ca1bb2fc11c161ec4ac18eed38fbad97239838c31a26f044c2daa61380`
- `workflow/state/issues.json`: `ed146f7ab0b74d9843912286421585bf5041fef8e6caf358a8b31f9be0a5879a`
- `workflow/state/prs.json`: `c3914db9e35ea8e0e286beee5bed7c5991729dd7207d38db31a40f53cf8b73d5`
- `workflow/state/protocols.json`: `00bba5cd9a9d94371552a918702e481840a0844882a02f405009d6ff05c0d641`
- A15: `922943b7ac0866f8aa96e7eae9a8048c07d2eecd0ae774428093cd7dedf42b63`
- A16: `263275da4d0b2312619bd1fec81b92d50993556202c219abc3ad535fd0302b9c`
- A17: `538c83d046b4377c92de8322628df7e61e60569f9c8a3cddf07c8f0f7a632d67`
- Protocol-change metric: `ebb18b3c289a3cbc342bcf1456c4badb4e90f856568ed61462e9371e1c140068`
- Report SHA-256 is necessarily supplied out of band after finalization.
