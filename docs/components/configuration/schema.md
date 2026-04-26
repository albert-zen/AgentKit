# AgentKit Configuration Schema

## Root Fields

- `version`
- `docs`
- `components`
- `layers`
- `review`
- `skills`
  - `source`: canonical skill source path, defaulting to `plugins/agentkit/skills/agentkit/SKILL.md`
  - `output`: skill output path, defaulting to `plugins/agentkit/skills/agentkit/SKILL.md`
- `maintainability`
  - `budgets`: repo-local file budgets for keeping modules readable and scoped

## Components

Each component can define:

- `description`
- `code`
- `docs`
- `required_docs`
- `keywords`

## Layers

Each layer can define:

- `paths`
- `may_import`

Layer rules are project-specific. AgentKit provides a checking mechanism, not a universal architecture.

AgentKit's own repo uses the same schema to express the lifecycle sampler boundary:

- utility helpers such as task state and receipts sit below lifecycle policy
- lifecycle policy may use utilities
- command functions may use lifecycle policy
- CLI routing may use commands and the watch adapter

This is an example of the existing schema, not a new schema version.

## Maintainability Budgets

Each maintainability budget can define:

- `name`
- `paths`
- `max_lines`
- `max_functions`
- `max_classes`
- `mode`: `warn` or `fail`
- `guidance`

Budgets are repository-specific maintainability reminders. They are not a replacement for language-level tools such as Ruff, Pylint, or formatters. AgentKit uses them to preserve human taste about module size and responsibility boundaries in `agentkit.yml`.

Example:

```yaml
maintainability:
  budgets:
    - name: commands-orchestration
      paths:
        - src/agentkit/commands.py
      max_lines: 900
      max_functions: 35
      max_classes: 0
      mode: warn
      guidance: "Prefer extracting templates or lint helpers before adding more behavior."
```
