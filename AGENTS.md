# AGENTS.md

This repository uses AgentKit.

Before changing code:
- Run `agentkit start` with the relevant component, task, or changed paths.
- Read the durable intent sources and docs AgentKit recommends.
- Ask the human for design when AgentKit reports a design gap for a product, architecture, API, data model, workflow, or state-machine change.

After changing code:
- Run relevant tests.
- Run `agentkit check`.
- Update docs when behavior, architecture, public contracts, workflows, data models, or testing strategy changed.
- Run `agentkit review-guidance` for non-trivial work.
- Run `agentkit close --review-complete` before ending a reviewed task. If blocked, record the human question with `agentkit close --blocked-question "..."`.
