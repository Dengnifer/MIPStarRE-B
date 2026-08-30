# Workflow State

This directory replaces GitHub issues, pull requests, review threads, and agent
run status with local versioned records.

## Canonical files

- `state/issues.json`: issue hierarchy, dependencies, acceptance gates, owners.
- `state/prs.json`: local PR base/head revisions, checks, reviews, findings.
- `state/sessions.json`: planned roles and actual issued attempts.
- `state/stages.json`: top-level project stage measurements and outputs.
- `state/protocols.json`: active protocol revision and evolution history.
- `events.jsonl`: append-only canonical lifecycle events.
- `prompts/`: trusted role contracts passed to fresh Codex sessions.

Raw Codex JSONL, prompts assembled for a specific issue, build logs, cache data,
and result envelopes live under ignored `.workflow-runtime/`. Only the root
coordinator imports compact, inspected evidence into canonical files.

## Commands

```bash
python3 scripts/workflow.py validate
python3 scripts/workflow.py ready
python3 scripts/workflow.py show --help
python3 scripts/workflow.py add --help
python3 scripts/workflow.py update --help
python3 scripts/workflow.py transition --help
python3 scripts/workflow.py issue-session --help
python3 scripts/hot_main_cache.py status
python3 scripts/local_agent.py --help
python3 scripts/bootstrap_manifest.py --help
```

Run validation before dispatch, after any state edit, before review, and after
integration. The aggregate gate also reconciles canonical event lifecycles,
incident references, protocol-change evidence, and terminal-session metrics.
State writes are locked and atomically renamed. Do not hand-edit canonical JSON
while another coordinator command is active.
