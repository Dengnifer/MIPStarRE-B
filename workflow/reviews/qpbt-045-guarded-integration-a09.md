# QPBT-045 / LPR-024 guarded integration A09

Guarded integration completed in the authorized detached worktree. The approved
candidate was merged with `--no-ff` onto current base, then non-owned canonical
paths were restored from current base. No workflow state or metrics files were
changed.

## Authenticated integration

| Item | Value |
| --- | --- |
| Current base | `b06c948c4d64c0f38c4e6ad677385f6bfdfe3027` |
| Candidate head | `39c9ee0d74c929cbd4a1fc98be970f4d6c6c8a16` |
| Integration commit | `47b0bf444d9f29e82e03e51a6d2c89ff5958e6d5` |
| Integration tree | `c0c42f87501a820c5438cd7471dc1835032455cb` |
| Integration parents | `b06c948c4d64c0f38c4e6ad677385f6bfdfe3027`, `39c9ee0d74c929cbd4a1fc98be970f4d6c6c8a16` |
| Candidate tree | `105854b569b76a6c2103ac2c22e512454afe0c53` |
| Three-path manifest SHA | `11ee7fbec15a1bda08bcfc94da37232a191f48ac19a94f29af1c8299bc006c6b` |

The seven candidate paths were checked against candidate `39c9ee0`; every
indexed blob matched exactly. The resulting base-to-integration diff has five
paths because A05 and A07 report blobs were already present on current base:

```text
protocols/CHANGELOG.md
protocols/local-development.md
scripts/hot_main_cache.py
tests/test_hot_main_cache.py
workflow/reviews/qpbt-045-hot-main-preservation-a01.md
```

## Validation

| Command | Result | Time |
| --- | --- | ---: |
| `python3 tests/test_hot_main_cache.py` | 60/60 passed | 12.253 s |
| `python3 tests/test_mipstarre_materialization.py` | 11/11 passed | 0.457 s |
| `python3 -m compileall -q scripts tests` | passed | <0.1 s |
| `python3 scripts/workflow.py validate --json` | valid (51 issues, 24 PRs, 406 issued sessions, 7 stages) | <0.1 s |
| `python3 scripts/check_workflow.py --skip-tests` | valid | <0.1 s |
| `python3 tests/test_check_workflow.py` | 3/3 passed | 0.003 s |
| `git diff --cached --check` and authentication checks | passed | <0.1 s |

No warm, seed, build, Lean/Lake, network, endpoint, GitHub, credential, or
nested-agent actions were run. Token usage is JSON `null` because the backend
does not expose per-agent token data; no estimate was made. Final worktree was
clean after this report commit.
