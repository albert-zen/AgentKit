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
- `agentkit start`
- `agentkit orient`
- `agentkit intent-guidance`
- `agentkit docs-impact`
- `agentkit lint-architecture`
- `agentkit check`
- `agentkit review-guidance`
- `agentkit close`
- `agentkit install-hooks`
- `agentkit skill`

## Lifecycle Commands

`start` and `close` are lifecycle gates for agent work.

`start` captures durable task context and writes a task state file. `close` verifies whether the task is completed, still needs work, or is blocked on a recorded human question.

`close` accepts `--review-complete` after a required review loop and `--skip-review-reason` for low-risk work where review is intentionally skipped.

## Hook Commands

`install-hooks` installs Git-triggered deterministic hooks. It should not create a separate manual pre-commit workflow for agents.
