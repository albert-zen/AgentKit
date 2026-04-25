# Governance Testing

Status: Draft

## Checks

Governance changes should run:

- `git status --short`
- `agentkit check`
- `pytest -q`

## Expected Signals

After Git initialization and component mapping, `agentkit check` should report no unmapped changed paths for ordinary AgentKit source, docs, tests, package metadata, or repository hygiene files.
