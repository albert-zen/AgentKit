---
name: agentkit
description: Use AgentKit to orient coding agents, enforce repository-local maintainability rules, check docs impact, and request clean-context review guidance.
---

# AgentKit Skill

This repository uses AgentKit.

## Start Of Task

Run:

```text
agentkit orient
```

If you know the component, run:

```text
agentkit orient --component <name>
```

Configured components: cli, configuration, docs, guidance

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
