# GitHub PR Claim Identity Repair A03

- Session: `i030-fixer-a03-claim-pr-identity`
- Collaboration task: `/root/i030_fixer_a03_claim_pr_identity`
- Canonical issue: GitHub #30
- Model requested: `gpt-5.6-sol`
- Owned paths: `scripts/local_agent.py`, `tests/test_local_agent.py`
- Subagents: 0
- Point timing and token usage: unavailable from the collaboration backend
- Lean/Lake builds: 0
- GitHub operations: 0

Claim admission now authenticates stored migrated PR legacy/number pairs and
their exact base/head refs and SHAs against the cutover manifest. A canonical
number belonging to a migrated PR cannot omit its legacy half. Unbound
GitHub-only PRs retain `pr_id: null` and must carry a structurally exact
immutable base/head tuple; freshness comes from the two live dispatch reads,
not from a claim-time network operation. Config and manifest digests remain
bound through publication.

Validation: local-agent tests `77/77`, Python compilation, and diff hygiene
passed. Seven focused PR claim tests cover valid migrated and unbound rows plus
byte-exact rejection of mismatch, omitted legacy identity, absent migration,
malformed base/head identity, and manifest conflicts.
