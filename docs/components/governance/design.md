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

## Non-Goals

- AgentKit does not need a hosted repository or remote origin for the MVP.
- AgentKit does not need to manage release automation yet.
