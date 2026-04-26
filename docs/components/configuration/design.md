# Configuration Component Design

## Purpose

The configuration component loads `agentkit.yml` and turns it into typed Python objects.

AgentKit's own configuration maps lifecycle modules explicitly. The current repo uses a `lifecycle` layer for `lifecycle.py` and `watch.py`, utility mappings for task state and receipt helpers, and guidance component mappings for the reminder sampler implementation.

## Owned Concepts

- docs configuration
- component mappings
- layer dependency rules
- review policy
- skill source and output locations
- maintainability budgets for repo-specific module size and responsibility limits

## Boundary

Configuration parsing should not perform checks. It should validate shape lightly and leave repository-specific checks to command functions.
