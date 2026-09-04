# QPBT-058 private-cache seed evidence A03

The QPBT-058 worktree at exact base
`937ea218133cc21afb16313076ce2278fbe9260e` was seeded from the compatible
post-integration cache for main `735a419a0f58fb531eaff04c62bd05e8e846f01e`.
The intervening checkpoint changes only workflow evidence; the seed verified
the cache's authored QPBT inventory before publication.

## Result

- Cache key: `e6767da55a90639333fdfbeb2abf87aa45118cc20c18117b55d8de0a0c15bb47`
- Result: seeded; cache hit: 1; cache miss: 0; builds: 0
- Lock wait: 0.0 seconds
- Elapsed: 87.083277 seconds
- Target: `.workflow-runtime/worktrees/qpbt-058-typed-a01/.lake`
- Existing target replaced: false
- Files: 124,925; logical bytes: 10,097,592,794; symlinks: 3
- Reflinked files: 0; byte-copied files: 124,925

The seed preserves private writable build output and avoids recompilation, but
this host/filesystem did not provide reflink deduplication. The observed full
byte-copy fallback is material evidence for QPBT-067: the long-term layout must
share authenticated immutable dependency/package layers while keeping mutable
build output private, or use another verified copy-on-write mechanism.

Cache seeds: 1. Builds, network, endpoint, GitHub, credential, and nested-agent
actions: 0. Token usage is `null`; the root session does not expose
per-operation token usage.
