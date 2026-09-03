# QPBT-067 Reviewer A03 Preflight Recovery

The planned read-only reviewer was confirmed under an invalid manually
transcribed base identity before a worktree was provisioned. The supplied
value `d7a7d62f1d1b677bb4fffc0181bfbf6eabca7f11` is not the current Git object;
the authenticated resolution is `d7a7d62d6dcf41a295535ff003bfb1d52f92beae`.

The lease was never transitioned to running, no worktree was created, and no
repository, source, cache, network, or GitHub operation was performed by the
reviewer. The attempt is retained as failed provenance and will be retried with
the exact SHA emitted by `git rev-parse`.
