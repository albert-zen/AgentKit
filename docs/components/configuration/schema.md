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
