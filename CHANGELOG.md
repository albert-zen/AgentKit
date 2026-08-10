# Changelog

## 0.2.0 - 2026-08-10

AgentKit 0.2.0 is the first release intended for installation from the GitHub
tag `v0.2.0`. It requires Python 3.11 or newer and is not published on PyPI.

### Added

- Established Association, State, and Rule as the stable core for explainable
  repository context, lifecycle facts, validation, reminders, and transitions.
- Added the versioned `recommended-v1` preset, which materializes auditable
  lifecycle rules and reminder policy without silently changing repositories
  when the package is updated.
- Added `agentkit update` for explicit, duplicate-safe task, plan, focus, and
  component updates without forging lifecycle status or validation evidence.
- Added repository format v2 and `agentkit doctor`, `agentkit upgrade
  --dry-run`, and `agentkit upgrade` support for existing repositories.

### Safety And Compatibility

- Upgrade changes only proven AgentKit-managed structure and preserves user
  configuration, policy, rules, documentation, instructions, task state, and
  receipts.
- Ambiguous ownership or a transformation that cannot be proven lossless is a
  conflict with zero writes. Multi-file application validates before and after
  replacement and rolls back AgentKit's writes on failure.
- Package, repository-format, preset, task-state, and managed-artifact versions
  are independent; updating the CLI never silently migrates a repository or
  reapplies a preset.

### Fixed

- Fixed recursive glob expansion on Python 3.11 when a configured pattern ends
  in `/**`, including repository-upgrade fixtures and deterministic checks that
  exercise those paths.
