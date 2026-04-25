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
- `agentkit status`
- `agentkit remind`
- `agentkit docs-impact`
- `agentkit lint-architecture`
- `agentkit check`
- `agentkit review-guidance`
- `agentkit close`
- `agentkit install-hooks`
- `agentkit watch`
- `agentkit skill`

## Lifecycle Commands

`start` and `close` are lifecycle gates for agent work.

`start` captures durable task context and writes a task state file. `close` verifies whether the task is completed, still needs work, or is blocked on a recorded human question.

`close` accepts `--review-complete` after a required review loop and `--skip-review-reason` for low-risk work where review is intentionally skipped.

`status` and `remind` expose the current lifecycle state without changing it. `status` should print facts about open tasks, missing gates, stale receipts, and blocked handoffs. `remind` should print agent-facing next actions derived from those facts.

`check` may include lifecycle reminders in its output, but the CLI should still route status/reminder computation through shared guidance logic instead of implementing reminder policy itself.

## Hook Commands

`install-hooks` installs Git-triggered deterministic hooks. It should not create a separate manual pre-commit workflow for agents.

## Watch Command

`watch` runs a lightweight local reminder loop. It should call the same status/reminder logic as `status`, `remind`, and `check`, then deliver the resulting reminder text while it is running.

The CLI should expose interval and output options when needed, but it should not turn `watch` into an agent runner or job scheduler.

The first implementation supports `--once` for tests and for agents that want a one-shot reminder through the same watch entry point.
