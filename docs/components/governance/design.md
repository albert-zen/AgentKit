# Governance Component Design

Status: Draft

## Responsibility

The governance component covers AgentKit's own repository hygiene and dogfood baseline.

It owns:

- Git repository setup
- ignored generated files
- package-level metadata boundaries
- files that teach AgentKit how to govern itself

## Design Intent

AgentKit should be a real Git repository so its own `changed_paths`, `docs-impact`, and `review-guidance` commands operate in the same conditions they expect from user repositories.

Repository hygiene files such as `.gitignore` and package marker files should be mapped in `agentkit.yml` so future agents do not treat them as unrelated or unmapped changes.

AgentKit task state and receipts should be local runtime state, not durable product documentation. `.agentkit/` is ignored by Git so temporary task records and check receipts do not become repository history by accident.

Git hooks installed by AgentKit live under `.git/hooks/` and are local to the checkout. The durable intent is recorded in docs; the hook files are operational wiring.

Hook installation should ask Git for the hook path instead of assuming `.git` is a directory. This keeps AgentKit compatible with linked worktrees.

## Non-Goals

- AgentKit does not need a hosted repository or remote origin for the MVP.
- AgentKit does not need to manage release automation yet.
