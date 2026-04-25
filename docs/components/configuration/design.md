# Configuration Component Design

## Purpose

The configuration component loads `agentkit.yml` and turns it into typed Python objects.

## Owned Concepts

- docs configuration
- component mappings
- layer dependency rules
- review policy
- skill output location

## Boundary

Configuration parsing should not perform checks. It should validate shape lightly and leave repository-specific checks to command functions.
