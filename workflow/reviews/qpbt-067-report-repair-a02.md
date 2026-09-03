# QPBT-067 Report Repair (A02)

The QPBT-067 cache-layout audit was corrected for findings F-067-A02-001 and
F-067-A02-002. The original measured values, hashes, source anchors, design
recommendation, and no-deletion boundary are unchanged.

- Isolation wording now distinguishes observed `.lake/build` hard-link absence
  from whole-`.lake` privacy. It records the observed absolute symlink
  `.workflow-runtime/worktrees/qpbt-037-pauli-a01/.lake/packages/mathlib` to
  `/home/drx/.cache/mipstarre-dev/hot-main/repo/.lake/packages/mathlib`, whose
  resolved target was mode `775` and writable at review time. Target ownership,
  read-only status, and realpath containment remain required gates.
- Recovery wording now distinguishes implemented live exception rollback from
  process-crash recovery. A SIGKILL in the two-rename gap can leave the target
  without `.lake`; automatic recovery is not implemented and is explicitly a
  future requirement with subprocess SIGKILL tests.

No cache, worktree, source, state, metrics, or protocol bytes were mutated.
