# Governance Testing

Status: Draft

## Checks

Governance changes should run:

- `git status --short`
- `agentkit check`
- `pytest -q`

## Expected Signals

After Git initialization and component mapping, `agentkit check` should report no unmapped changed paths for ordinary AgentKit source, docs, tests, package metadata, or repository hygiene files.

Hook and task-state checks should verify:

- `.agentkit/` is ignored by Git
- generated task state does not appear in `git status --short`
- check receipts do not appear in `git status --short`
- installed Git hooks are local operational files, not tracked docs
- the AgentKit repository's v1-to-v2 dogfood changes only planned managed
  envelope bytes and leaves `.agentkit` task/receipt bytes unchanged
- package metadata and `agentkit.__version__` remain synchronized
