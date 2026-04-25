# AgentKit Configuration Schema

## Root Fields

- `version`
- `docs`
- `components`
- `layers`
- `review`
- `skills`

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
