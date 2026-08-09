# AgentKit Configuration Schema

## Root Fields

- `version`: repository configuration format; supported values are legacy `1`
  and current `2`
- `docs`
- `components`
- `layers`
- `review`
- `skills`
  - `source`: canonical skill source path, defaulting to `plugins/agentkit/skills/agentkit/SKILL.md`
  - `output`: skill output path, defaulting to `plugins/agentkit/skills/agentkit/SKILL.md`
- `maintainability`
  - `budgets`: repo-local file budgets for keeping modules readable and scoped
- `preset`
  - `source`: `agentkit`
  - `name`: currently `recommended-v1`
  - `version`: currently `1`
- `rules`: supported named lifecycle rules and their finite options
- `reminders`: supported lifecycle reminder-node booleans

## Lifecycle Rules

Repository format is not the package version, preset version, task-state schema
version, or managed-artifact version. Those domains advance independently.
Format v2 requires a bounded AgentKit agents block; it does not change the
shape or semantics of the policy fields below.

Supported rule ids are:

- `working_tree_clean`
- `check_receipt_current`
- `review_addressed`
- `blocked_question_recorded`

Every rule supports `enabled` and `severity` (`error` or `warning`).
`review_addressed` also supports `allow_skip`. Missing rules use the existing
compatibility behavior. Unknown rule ids or options are errors.

Supported reminder keys are `open_task`, `ready_to_close`, and
`stale_terminal`. Each value is boolean.

When `preset` provenance is present, all supported rule ids and reminder keys
must be materialized explicitly. Omitting one is an incomplete preset error;
repositories override a default by editing its value, not by deleting it.

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
