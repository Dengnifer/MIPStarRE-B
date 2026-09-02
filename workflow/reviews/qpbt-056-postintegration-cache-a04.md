# QPBT-056 / LPR-033 post-integration cache A04

The root coordinator authenticated and built the exact guarded merge commit,
then atomically published its recipe-v7 hot-main cache. This is the sole
post-integration build for QPBT-056.

| Field | Result |
| --- | --- |
| Integration commit | `20745fe45450276db3c2130d2631d863e8346ba3` |
| Integration tree | `c8be3a058203b155491847bac50caface74a8fb0` |
| Parents | `23e619f1f24f2e9b5f31082527faf56180e5ab8f`, `c1bfd95226e0c068f7d818689f56ab41088ff545` |
| Cache key | `333328233009df561dab57c57c4b05d74e61d217c62c8d429bfef2130c8b37be` |
| Result | built and published |
| Builder election | elected owner; no lock wait |
| Full build | 8,992 jobs passed |
| Total | 766.973942 seconds |
| Foundation materialization | 3.976608 seconds |
| Package materialization | 19.725329 seconds |
| Package verification | 20.467013 seconds |
| Dependency cache | 40.741921 seconds |
| Build | 647.356712 seconds |

The authored QPBT inventory was identical before materialization, after
materialization, after dependency retrieval, after build, and before
publication: 7 files, 147,146 bytes, SHA-256
`f6b58573384a6dbbf2922a643e0616ebce189d559c17544a9826c2cf625ad592`.

The published artifact inventory contains 124,925 files, 4,147 directories,
3 symlinks, and 10,097,592,794 bytes. Its inventory SHA-256 is
`3dc96ef9585f1cf00475ce2d1ecf235473a3e99d557f40dd25f8d95e971410eb`.
The manifest SHA-256 is
`1793994452f499eaa7e60803cfc7b95ab6fe26905e6f216cb147894234c7a867`;
the `READY` file contains that digest and has SHA-256
`0873ae6ce82cc37086f95f5f1227d62c37f7819200729baab4252f351a2bf038`.
The build log SHA-256 is
`e6d611bff23fba4252c8796d9255558dcdd0a7f831e94fb9eb1ffa1761139ffc`.

All authenticated inputs were local. The warm used no network, had no retry or
failure, and did not compete with another builder. Token usage for this root
operation is unavailable and is not estimated.
