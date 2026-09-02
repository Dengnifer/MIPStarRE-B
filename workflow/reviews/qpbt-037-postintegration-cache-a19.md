# QPBT-037 post-integration hot-main cache (A19)

The root coordinator ran exactly one authenticated recipe-v7 warm after the
reviewed Pauli integration and ledger closure.

| Field | Result |
| --- | --- |
| Main commit | `cc9194ad4a38aaf4971db871bdae34f10b447230` |
| Cache key | `93555a48b1efbf80003411ec9d39de51baeeccbc0e2c310cbab2157225e05ab3` |
| Result | built; subsequent status is `hit` |
| Builder election | elected owner; no lock wait |
| Builds | 1 |
| Full build | 8,992 jobs passed |
| Total | 720.471731 seconds |
| Foundation materialization | 3.502080 seconds |
| Package materialization | 17.763569 seconds |
| Package verification | 18.740119 seconds |
| Dependency cache | 38.852885 seconds |
| Build | 613.197937 seconds |

The authored QPBT inventory was identical before materialization, after
materialization, after dependency retrieval, after build, and before
publication: 6 files, 113,326 bytes, SHA-256
`54fdca3911c90b0566d00c2450d83b907088accbf3f3e7c201a7b3f2da49b62f`.

The published artifact inventory contains 124,925 files, 4,147 directories,
3 symlinks, and 10,097,592,576 bytes; its inventory SHA-256 is
`6c2cc55824a5d6469f7637004c678b55fed31f65630aca0a72949d51b92f8153`.
The manifest SHA-256 is
`db278509a4af29e0d968944c9a41fe88470ef7e7a0c8e03abbe56fd9914c8443`,
and the bound `READY` SHA-256 is
`6dec6f6aa0e7042e434280510f8b62201a11e3ae088a74fed41c9504dd0ed837`.

Authenticated inputs were local. The warm used no network, had no retry or
failure, and did not compete with another builder. Token usage for this root
operation is unavailable and is not estimated.
