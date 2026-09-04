# QPBT-057 post-integration cache evidence A18

The approved LPR-035 candidate was integrated byte-for-byte at main commit
`735a419a0f58fb531eaff04c62bd05e8e846f01e` (tree
`1362a781beeb4e93a7aafa7c5a2381977b3b8386`). One singleton recipe-v7 warm
built and atomically published that exact snapshot.

## Result

- Cache key: `e6767da55a90639333fdfbeb2abf87aa45118cc20c18117b55d8de0a0c15bb47`
- Result: built; immediate status recheck: hit
- Full build: 8,992 jobs passed
- Build time: 635.032752 seconds
- End-to-end warm time: 774.399684 seconds
- Lock wait: 0.0 seconds; elected builders: 1; duplicate builders: 0
- Materialization: 3.867079 seconds
- Package materialization: 22.053009 seconds
- Package verification: 19.012763 seconds
- Dependency cache: 60.112309 seconds

## Integrity

- Artifact inventory: 124,925 files, 4,147 directories, 3 symlinks,
  10,097,592,794 bytes
- Artifact inventory SHA-256:
  `6b2e6027083bd45115842f103aa313319df28742c29c3eb8e5e3969e94f7fec9`
- Authored QPBT inventory: 7 files, 182,257 bytes, SHA-256
  `f132250ce47e8abf893b1b56ee869ab799624998c8d0b1de8d81750c1e52d142`
- Manifest SHA-256:
  `87afa0a68976a184b84175d38cffa1f55690eb10b86a4dd680fbb8b809fdf7cf`
- READY SHA-256:
  `7b5819448e3117ba6b5f4289265ab712b3afb828a2e7685ace4e43149d2ce018`

The first invocation omitted the required Mathlib source selector and failed
closed in 0.064 seconds before materialization or build. `INC-079` records the
preflight error. The successful invocation used the authenticated offline
Mathlib, upstream MIPStarRE, and eight pinned Lake-package archives.

Lean/Lake builds: 1. Cache publications: 1. Network, endpoint, GitHub,
credential, and nested-agent actions during the warm: 0. Token usage is
`null`; the root session does not expose per-operation token usage.
