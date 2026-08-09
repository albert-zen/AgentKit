# Configuration Testing

## Strategy

Configuration tests should prove that representative `agentkit.yml` data parses into typed objects with stable defaults.

## Current Coverage

- component parsing
- layer parsing
- skill source and output defaults
- maintainability budget parsing
- recommended preset provenance, materialization, and idempotent overrides
- preservation of existing YAML comments/unrelated text and refusal of partial policy rewrites
- refusal of matching preset provenance with incomplete rule/reminder materialization
- named lifecycle rule defaults and supported options
- clear failures for unknown presets, rules, options, and invalid severities

AgentKit's own dogfood checks should also verify that new implementation modules are mapped to components and architecture layers in `agentkit.yml`.

When default configuration is used, skill paths should point at the Codex plugin skill under `plugins/agentkit/skills/agentkit/SKILL.md`.
