# Configuration Testing

## Strategy

Configuration tests should prove that representative `agentkit.yml` data parses into typed objects with stable defaults.

## Current Coverage

- component parsing
- layer parsing
- skill source and output defaults

AgentKit's own dogfood checks should also verify that new implementation modules are mapped to components and architecture layers in `agentkit.yml`.

When default configuration is used, skill paths should point at the Codex plugin skill under `plugins/agentkit/skills/agentkit/SKILL.md`.
