# ADR 0002: Repository Upgrade Preserves User Intent

Status: Accepted

Date: 2026-08-09

## Context

AgentKit evolves in two places. The Python package gains new behavior, while repositories contain an AgentKit-shaped operating environment: `agentkit.yml`, an AgentKit-managed section in `AGENTS.md`, plugin and skill wiring, hooks, and local runtime state.

Installing a newer package does not by itself update that repository environment. Re-running `agentkit init` is also insufficient: initialization is intentionally conservative and must not overwrite an existing repository's policy or human-authored content.

AgentKit therefore needs an explicit repository upgrade operation. The operation must make old AgentKit structure compatible with the installed package without resetting the project-specific associations, rules, design intent, or other content that users and agents have accumulated.

## Decision

AgentKit will provide `agentkit upgrade` as a sequential, versioned migration system for AgentKit-managed repository structure.

The governing invariant is:

```text
old AgentKit structure + user-owned intent
  -> new AgentKit structure + semantically unchanged user-owned intent
```

Upgrade changes the AgentKit envelope. It does not redesign the repository.

If AgentKit cannot prove that a migration preserves user-owned content and policy semantics, it must report a conflict and make no changes. It must not guess, silently reset values, or leave a partially upgraded repository.

## Version Boundaries

AgentKit keeps distinct version domains:

- the installed package version describes the released CLI implementation;
- the top-level `agentkit.yml` version describes the repository configuration format;
- preset provenance describes the versioned policy that was materialized;
- task-state schema versions describe `.agentkit/tasks/*.json`;
- managed artifact versions describe generated or AgentKit-owned text blocks such as the AgentKit section in `AGENTS.md`.

These versions may advance independently. Package installation does not silently advance any repository-owned version.

Repository configuration migrations are sequential. An upgrade from format 1 to format 3 executes the reviewed `1 -> 2` migration followed by `2 -> 3`; it does not infer a direct transformation dynamically.

## Ownership Model

Upgrade classifies repository content by ownership.

### AgentKit-Managed Structure

AgentKit may migrate:

- repository format and managed-artifact version markers;
- the AgentKit-managed section in `AGENTS.md` or `agents.md`;
- AgentKit plugin manifests, marketplace entries, and hook wiring;
- an unmodified generated AgentKit skill or other artifact whose prior managed version can be identified;
- internal `.agentkit` state representation through its own schema migration;
- missing structural defaults whose old semantics are known and can be preserved exactly.

### User-Owned Intent and Policy

Upgrade must preserve:

- component, code, document, testing, and architecture associations;
- layer and dependency policy;
- review rules, maintainability budgets, thresholds, severities, and explicit overrides;
- task statements, plans, focus context, blocked questions, and validation evidence;
- design documents, ADRs, component documents, and project-specific skills;
- content outside an explicitly AgentKit-managed text block;
- unknown configuration fields that the migration does not own.

Some files are mixed-ownership surfaces. `agentkit.yml` contains AgentKit schema together with project policy. `AGENTS.md` contains one AgentKit-managed block together with user instructions. Migration must edit only the managed structure inside those files.

Changing representation is permitted only when semantics remain equivalent. For example, a legacy `require_clean_tree: false` value may become a disabled `working_tree_clean` rule, but it may not be replaced by the recommended default of `true`.

## Managed Text Blocks

New AgentKit-managed text uses bounded, versioned markers:

```text
<!-- agentkit:agents-section version=2 -->
...managed content...
<!-- /agentkit:agents-section -->
```

Upgrade may replace a block automatically when it matches a known prior managed version. Content before and after the block is preserved byte-for-byte.

The initial migration may recognize the legacy unbounded AgentKit marker only when the content from that marker to its known boundary matches a shipped legacy template. If the section was modified or its boundary is ambiguous, upgrade reports a conflict instead of overwriting it.

Generated skills and similar mixed surfaces follow the same rule: replace a known unmodified managed artifact; preserve or conflict on user modification. File location alone is not proof that AgentKit owns the current content.

## Command Contract

`agentkit doctor` reports the repository format, installed target format, and whether an upgrade is available or blocked by a detectable conflict.

`agentkit upgrade --dry-run` computes and renders the complete migration plan without writing files. The plan includes:

- source and target repository format;
- ordered migration identifiers;
- files and managed blocks that would change;
- user-owned values explicitly preserved;
- conflicts and required human actions;
- validation that will run after migration.

`agentkit upgrade` applies the same plan. If no upgrade is needed, it succeeds without changing files. Re-running a completed upgrade is idempotent.

The initial command targets the latest repository format supported by the installed package. A later `--to` option may be added when multiple supported targets create a real use case; it is not required for the first implementation.

## Planning, Validation, and Atomicity

Upgrade has separate planning and application phases.

Planning reads every affected file, detects ownership and conflicts, computes final contents in memory, and validates the resulting configuration and managed artifacts. A planning conflict produces no writes.

Application writes only the previously validated plan. Individual files are replaced atomically. The upgrade operation retains original bytes until every planned write succeeds and restores them if a later write fails. Success is reported only after the installed AgentKit can load the new configuration and its deterministic repository checks complete successfully.

Migration must not depend on a hosted service or LLM judgment. Human or agent involvement is required only when a conflict prevents a provably lossless transformation.

## Initial Format Migration

The first upgrade implementation introduces the next repository format and must dogfood the migration on AgentKit itself.

The migration should cover at least:

- advancing the `agentkit.yml` repository format marker;
- preserving all existing component, layer, review, maintainability, rule, reminder, preset, and unknown values;
- materializing any missing lifecycle policy only when its values are semantically identical to the old implicit behavior;
- converting a known legacy AgentKit `AGENTS.md` section to a bounded, versioned managed block;
- updating known unmodified AgentKit skill/plugin managed artifacts needed by the new format;
- leaving task-state schema migration independent unless that schema itself requires an upgrade.

Fixtures representing old initialized repositories, customized repositories, partial policy configuration, modified managed blocks, and already-upgraded repositories are required acceptance tests.

## Relationship to Init and Presets

`agentkit init` creates the latest repository format for a repository that is adopting AgentKit. It does not serve as an implicit upgrade for an existing AgentKit installation.

`agentkit init --preset recommended-v1` materializes a selected policy. `agentkit upgrade` preserves the policy already chosen by the repository. Upgrade may materialize a formerly implicit default only when it is exactly equivalent to existing behavior; otherwise it must request a policy decision.

This separation prevents package evolution from being confused with project-policy adoption.

## Consequences

Positive consequences:

- repositories can adopt new AgentKit structure without manually recreating configuration;
- package upgrades do not silently change project intent;
- AgentKit-owned guidance can evolve through explicit, reviewable migrations;
- dry-run, conflicts, and idempotence make upgrades safe for agents and humans;
- old repositories become durable migration fixtures instead of accidental compatibility assumptions.

Costs and constraints:

- AgentKit must retain sequential migration code and known legacy templates;
- managed files require ownership markers or known-content detection;
- true all-or-nothing multi-file application requires rollback handling;
- some customized repositories will require an explicit human decision rather than automatic migration.

## Non-Goals

Repository upgrade does not:

- redesign components, documentation, architecture, or workflow policy;
- apply a newer recommended preset automatically;
- rewrite arbitrary user-authored Markdown or YAML;
- infer the intended meaning of unknown configuration;
- update application dependencies or source code outside AgentKit-managed surfaces;
- replace Git history, backups, or human review for ambiguous migrations.
