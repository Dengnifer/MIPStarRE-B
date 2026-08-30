# Stage 2 Split Design Reconnaissance

- Session: `i002-scout-a01-split-design`
- Issue: `QPBT-002`
- Backend: Codex collaboration, read-only
- Workspace edits: none

The scout recommends a pinned, manifest-driven byte slicer rather than a
general TeX parser. It must verify the arXiv archive before extraction, admit
only the expected regular `.tex` and `.bbl` members, preserve CRLF and trailing
bytes, slice audited inclusive line ranges, verify output hashes, and publish
under a lock through a staging directory. The full-document partition and the
QPBT/dependency excerpt partition are both gap-checked by tests.

The source archive is 233,859 bytes with SHA-256
`d645cd51dd26cae59195e61aeeb5c886a254ef4adf15da7e5657ad90c7ec2174`.
Important hazards are archive traversal and links, text-mode newline changes,
indented appendix headings, inline labels, fragments that are not standalone
documents, the missing `.bib`, and the nondeterministic `\today` date.

Recommended issue order: finish `QPBT-010` acquisition/cache resilience, then
implement and review `QPBT-002`. External reviewers must not receive ignored
author source without a separately expanded disclosure authorization.

Exact elapsed time and token usage were not exposed by the collaboration
backend; the canonical session records the coordinator-observed time window.
