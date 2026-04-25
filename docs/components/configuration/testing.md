# Configuration Testing

## Strategy

Configuration tests should prove that representative `agentkit.yml` data parses into typed objects with stable defaults.

## Current Coverage

- component parsing
- layer parsing

AgentKit's own dogfood checks should also verify that new implementation modules are mapped to components and architecture layers in `agentkit.yml`.
