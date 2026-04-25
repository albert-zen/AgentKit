# CLI Component Design

## Purpose

The CLI is the primary interface for agents and humans. It routes commands to deterministic AgentKit behaviors and prints agent-readable guidance.

## Owned Concepts

- command names
- argument parsing
- repository root selection
- process exit codes

## Boundaries

The CLI should stay thin. It should parse arguments and delegate behavior to command functions. It should not contain configuration parsing, path matching, architecture lint logic, or git diff logic.

## Public Commands

- `agentkit init`
- `agentkit orient`
- `agentkit intent-guidance`
- `agentkit docs-impact`
- `agentkit lint-architecture`
- `agentkit check`
- `agentkit review-guidance`
- `agentkit skill`
