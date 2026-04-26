from __future__ import annotations


AGENTKIT_AGENT_SECTION_MARKER = "<!-- agentkit:agents-section -->"

AGENTKIT_AGENT_SECTION = f"""### AgentKit

{AGENTKIT_AGENT_SECTION_MARKER}
This repository uses AgentKit to keep agent-led changes tied to durable intent, checks, review, and closeout. For implementation, documentation edits, hook/plugin updates, or any repository-changing task, start with `agentkit start --task "..."`, use `agentkit check` plus `agentkit status` or `agentkit remind` while working, and finish with `agentkit close`. For read-only exploration, codebase orientation, or answering questions without edits, do not create an AgentKit task unless the work becomes long-running or the human asks for lifecycle tracking. For the full operating guide, read the AgentKit plugin skill.
"""

DEFAULT_AGENT_MD = f"""{AGENTKIT_AGENT_SECTION}
"""


DEFAULT_AGENTKIT_YML = """version: 1

docs:
  root: docs
  design: docs/design.md
  workflow: docs/workflow.md
  decisions: docs/decisions

components:
  core:
    description: Core product behavior.
    code:
      - src/**
    docs:
      - docs/design.md
    required_docs:
      - design
    keywords:
      - core

layers: {}

review:
  require_for:
    - public_api
    - data_model
    - architecture
    - orchestration
  default: warn

skills:
  source: plugins/agentkit/skills/agentkit/SKILL.md
  output: plugins/agentkit/skills/agentkit/SKILL.md

maintainability:
  budgets: []
"""

DEFAULT_SKILL_MD = """---
name: agentkit
description: Preserve human intent and project maintainability by guiding agents to read durable intent files and persist meaningful design, docs, and test changes.
---

# AgentKit Skill

This repository uses AgentKit.

## What AgentKit Gives You

AgentKit keeps your work tied to durable repo intent. Use it to:

- find the docs and components relevant to a task
- remember the task's closeout gates
- check docs impact and architecture rules
- get lifecycle reminders while you work
- ask for clean-context review before human attention
- close the task as completed or blocked

The skill is an operating guide. For deeper product or architecture intent, read the durable docs that AgentKit returns.

## When To Start A Task

Use the AgentKit task lifecycle for implementation work, documentation edits, hook/plugin changes, generated files, commits, or any task that changes repository state.

Do not start a task for read-only exploration, codebase orientation, answering architecture questions, or lightweight audits with no edits. In those cases, read the relevant docs directly and use `agentkit status` or `agentkit remind` only if you need to inspect an already-open task.

If read-only exploration turns into repository-changing work, start or resume the task before making edits so closeout gates apply to the change.

## Repository-Changing Operating Loop

1. Start or resume the task with `agentkit start`.
2. Read the durable intent sources in the output.
3. If design is missing or ambiguous for product behavior, API, data model, workflow, architecture, or state transitions, ask the human before implementing that part.
4. Implement against tests and the repo's architecture rules.
5. Run `agentkit check` and read any lifecycle reminder it prints.
6. Run `agentkit review-guidance` and request clean-context review when expected.
7. Fix meaningful reviewer findings.
8. Run `agentkit close --review-complete`, or close as blocked with a recorded human question.

## Start Of Task

For repository-changing work, run:

```text
agentkit start
```

`start` writes repository-local task state under `.agentkit/`. In a read-only audit, orientation pass, or question-answering task, do not run `start`; read this skill and use read-only commands such as `agentkit status` or `agentkit remind` only when they help inspect existing state.

If you know the component, run:

```text
agentkit start --component <name>
```

After discussion clarifies the task, preserve the focus:

```text
agentkit start --task "<refined task>" --focus-note "<human-approved focus>" --focus-doc <path>
```

Use `agentkit start --component <name>` when you already know the component. Otherwise, include the task text and let AgentKit infer affected components.

## During Design

Use:

```text
agentkit intent-guidance --component <name> --change-type <type>
```

Write the actual design content yourself. AgentKit tells you where it belongs.

Useful change-type values include `architecture`, `data_model`, `public_api`, `orchestration`, `workflow`, `tests`, and `docs`.

For docs-only wording tasks, ask the human for design only when the wording changes product meaning, command semantics, public behavior, workflow expectations, or accepted terminology. For local copyedits that preserve meaning, proceed with focused docs checks and review expectations from AgentKit.

## Before Review

Run:

```text
agentkit check
agentkit review-guidance
```

If review is expected, spawn or request a clean-context reviewer with the guidance AgentKit returns.

Do not treat review as a transcript storage task. AgentKit only needs the main agent to acknowledge that the review loop was completed for the current diff. If review reveals durable design, risk, or testing knowledge, record that in the repository docs.

For low-risk docs-only wording changes, review may still be expected by local policy. Use `agentkit review-guidance` to decide. If the change is truly low risk, close with `agentkit close --skip-review-reason "..."` only when AgentKit allows it.

## Lifecycle Reminders

Use:

```text
agentkit status
agentkit remind
```

`status` shows task facts and missing gates. `remind` shows the next action. `agentkit check` may also include lifecycle reminders.

For a local reminder loop, use:

```text
agentkit watch
```

For Codex Stop-hook reminders, install explicit hook wiring:

```text
agentkit install-codex-watchdog --repo-local
```

If a Stop hook does not appear to run, check `.agentkit/codex-stop-hook.log`. No log usually means Codex did not invoke the hook.

## Close Task

Before ending the task, run:

```text
agentkit close --review-complete
```

If blocked on human input, run:

```text
agentkit close --blocked-question "..."
```

Use blocked close when continuing would require an unsupported assumption. Include the human question clearly.
"""

DEFAULT_CODEX_PLUGIN_JSON = """{
  "name": "agentkit",
  "version": "0.1.0",
  "description": "Preserve human intent and project maintainability by guiding agents to read durable intent files and persist meaningful design, docs, and test changes.",
  "skills": "./skills/",
  "hooks": "./hooks.json",
  "interface": {
    "displayName": "AgentKit",
    "shortDescription": "Preserve human intent and project maintainability through durable intent files.",
    "longDescription": "AgentKit guides coding agents to read durable intent files before work and persist meaningful design, documentation, and test changes after work.",
    "developerName": "AgentKit",
    "category": "Productivity",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": [
      "Use AgentKit to start this task and follow the repository closeout workflow.",
      "Use AgentKit to check whether this task is ready for review and closeout."
    ]
  }
}
"""

DEFAULT_CODEX_PLUGIN_HOOKS_JSON = """{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "agentkit codex-stop-hook",
            "timeout": 30,
            "statusMessage": "Checking AgentKit task closeout"
          }
        ]
      }
    ]
  }
}
"""

DEFAULT_CODEX_MARKETPLACE_JSON = """{
  "name": "agentkit-local",
  "interface": {
    "displayName": "AgentKit Local"
  },
  "plugins": [
    {
      "name": "agentkit",
      "source": {
        "source": "local",
        "path": "./plugins/agentkit"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
"""
