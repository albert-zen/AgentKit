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
- finite named lifecycle rule policy and reminder selection
- versioned preset provenance
- repository format version, independent from package, preset, task-state, and
  managed-artifact versions

## Boundary

Configuration parsing should not perform checks. It should validate shape lightly and leave repository-specific checks to command functions.

`policy.py` owns the stable finite catalog of rule ids, reminder nodes, preset
provenance, and typed policy values. `config.py` parses against that catalog.
`presets.py` depends on the catalog and owns only versioned value sets plus
text-preserving materialization; it must not define the stable rule directory.

Lifecycle configuration is stricter than advisory path mappings: unknown
preset names/versions, rule ids, reminder nodes, or rule options must fail
clearly. Missing rule sections in an older repository select the compatibility
baseline; explicit `recommended-v1` values are materialized by `init`, not
looked up dynamically at evaluation time.

Preset application must preserve hand-written YAML comments and unrelated
configuration. Existing partial or conflicting policy sections fail with an
explicit migration instruction rather than being silently merged or
re-serialized.

Repository format v1 remains readable for compatibility and diagnosis; v2 is
the latest creation target. Unknown future formats fail clearly. Format
migrations must not round-trip mixed-ownership YAML through `safe_dump`:
controlled text edits preserve unknown fields, comments, ordering, quoting,
and project policy byte-for-byte outside an owned token.

Current managed-artifact markers live in `artifacts.py`. New templates and
historical migrations both depend on that stable contract; templates do not
depend on retained migration implementations.
