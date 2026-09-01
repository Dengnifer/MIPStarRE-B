# QPBT-026 final activation auditor A26 prelaunch failure

## Outcome

`failed before launch`

No reviewer agent was spawned, no external identity was assigned, and no
review verdict exists. The attempt cannot approve any object.

The issued record used base revision
`5c4401a4ec5d5bd78d44623a5539b1379547f878`, which is a syntactically valid
40-hex string but not the checkpoint commit. The actual clean registered
worktree is at
`5c4401aa3e80abcaff936aa1ff35f7a5b3a8663f`, tree
`d6009a227c190dbb5bfbb82c297abc8a09caaa75`.

Root detected the mismatch during the mandatory prelaunch identity check. The
recorded value had been formed by extending the displayed seven-character
abbreviation instead of resolving it with `git rev-parse`. Because
`base_revision` is immutable after issuance, A26 must be retired rather than
repaired in place.

## Superseded object

Before the mismatch was discovered, root constructed and fully validated
activation object `17415b8b00883962e64dbede1fe2c079f0654956`, tree
`0163c085d1c79189025742c59a3a3c3c2efa6c0e`, with ordered parents
`d6479f582639901fec0ada09091125b9dcc1dd99` and
`5bf6e086cc1656c3ce9ceb6527fe6ca657f9795a`.

That object passed the four-path identity gates, workflow 70/70, local-agent
63/63, aggregate 336/336 in 244.105 seconds, compileall, workflow validation,
workflow checker, blueprint 26/26 with the 48-node deterministic graph, and a
clean-worktree check. It was never reviewed and will not be activated. These
results remain failed-attempt provenance and cannot be relabelled as validation
of the replacement object.

## Recovery

Record incident INC-050, fail and archive A26, issue a fresh auditor attempt
whose base is copied from exact `git rev-parse HEAD`, commit that registration,
then construct and rerun every required gate on one replacement activation
object from the new frozen parent. The fresh reviewer alone may approve that
replacement object.

Token usage is `null`: no agent ran and the workflow backend exposes no token
accounting for the coordinator actions. Network, endpoint, GitHub, credentials,
Codex launch, Lean, Lake, and hot-cache actions were all zero.
