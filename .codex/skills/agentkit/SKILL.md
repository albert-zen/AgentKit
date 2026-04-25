---
name: agentkit
description: Use AgentKit to orient coding agents, enforce repository-local maintainability rules, check docs impact, and request clean-context review guidance.
---

# AgentKit Skill

This repository uses AgentKit.

## Start Of Task

Run:

```text
agentkit start
```

If you know the component, run:

```text
agentkit start --component <name>
```

Configured components: cli, configuration, docs, governance, guidance

## During Design

Use:

```text
agentkit intent-guidance --component <name> --change-type <type>
```

Write the actual design content yourself. AgentKit tells you where it belongs.

## Before Review

Run:

```text
agentkit check
agentkit review-guidance
```

If review is expected, spawn or request a clean-context reviewer with the guidance AgentKit returns.

## Close Task

Before ending the task, run:

```text
agentkit close --review-complete
```

If blocked on human input, run:

```text
agentkit close --blocked-question "..."
```
