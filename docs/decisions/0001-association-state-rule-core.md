# ADR 0001: Association, State, and Rule Form the AgentKit Core

Status: Accepted

Date: 2026-08-09

## Context

AgentKit currently exposes repository mapping, task lifecycle, deterministic checks, reminders, review guidance, and runtime integrations. These behaviors are useful, but their governing model is spread across configuration, command orchestration, lifecycle sampling, task JSON, receipts, and adapters.

The product needs a smaller architectural vocabulary before it adds more configuration. That vocabulary must explain both the current recommended workflow and future project-specific workflows without turning AgentKit into a general agent orchestrator or an arbitrary workflow programming language.

## Decision

AgentKit's stable core consists of three concepts: **Association**, **State**, and **Rule**.

The core evaluation model is:

```text
Evaluation = Rules(Associations, State)
```

An evaluation produces explainable results: relevant context, satisfied and unsatisfied conditions, next actions, reminders, and permitted lifecycle transitions.

### Association

An association describes a repository-local relationship between artifacts or concerns. Examples include code paths belonging to a component, components referring to design or testing documents, files belonging to architecture layers, and change categories requiring particular checks.

Associations answer: **what repository knowledge is relevant to this task or change?**

Associations are declarative, repository-local, inspectable, and project-specific. AgentKit may supply conventional structures and matching mechanisms, but it does not own a universal component model or architecture.

### State

State represents facts used during evaluation. It includes:

- persisted task context, such as the task statement, plan, focus documents, focus notes, and blocked question;
- observed repository facts, such as HEAD, changed paths, and working-tree cleanliness;
- asserted facts, such as a human- or agent-recorded persistence decision;
- evidence, such as the result of a deterministic check or acknowledged review.

Evidence is a kind of state, not a separate core concept. Evidence that applies to code must be bound to the relevant repository fingerprint. When HEAD or the diff changes, evidence for an older fingerprint does not satisfy rules for the new state.

Persisted source facts and derived status must remain distinct. AgentKit should recompute lifecycle readiness from current facts whenever practical instead of persisting a second, independently mutable version of the same conclusion.

### Rule

A rule evaluates associations and state to produce an explainable result. Rules cover:

- contextual guidance, such as which documents should be read;
- validation, such as whether a current check receipt exists;
- reminders and next actions;
- lifecycle transition requirements, including completion and blocked handoff.

Evidence requirements and gates are therefore rules. A gate is not a separate product capability; it is a rule controlling whether a transition is permitted.

Rules must initially be finite, named, and composable. Every evaluated rule must expose a stable identifier, pass/fail or applicable/not-applicable outcome, an explanation, and an actionable next step when one exists.

AgentKit will not initially provide arbitrary expressions, user-defined executable rule code, or a general workflow DSL. New configurability should be driven by demonstrated repository needs.

## Fixed Invariants and Configurable Policy

AgentKit owns the following system invariants:

- evaluation is deterministic for the same associations and state;
- evidence is scoped to the repository state it validates;
- stale evidence cannot silently satisfy a current rule;
- unknown presets, rules, and invalid configuration fail clearly rather than being ignored;
- lifecycle adapters do not duplicate or override core evaluation policy;
- a completed or blocked transition is explainable from evaluated rules and recorded state;
- repository configuration and durable intent remain inspectable and version-controlled;
- task update operations cannot directly forge derived status or validation evidence.

Repositories may configure policy within those invariants, including:

- artifact and component associations;
- which supported named rules are enabled;
- warning versus blocking behavior where the rule supports it;
- review applicability and permitted low-risk review skips;
- maintainability thresholds;
- reminder content or selection at supported lifecycle points;
- the versioned preset used to initialize these values.

The distinction is intentional: projects choose their development policy, while AgentKit preserves the integrity and explainability of evaluating that policy.

## Recommended Preset

The current AgentKit workflow becomes the versioned `recommended-v1` preset.

Applying a preset must materialize its effective configuration into the repository. The repository records the preset name and version for provenance, but runtime behavior is governed by the checked-in materialized configuration, not by a mutable upstream preset definition. Upgrading AgentKit must not silently change the lifecycle policy of an existing repository.

Users can inspect and edit the materialized configuration. A future preset upgrade must be an explicit repository change that can be reviewed like any other policy change.

`agentkit init` without an explicit preset remains compatible with existing behavior during the migration period. `agentkit init --preset recommended-v1` is the explicit path for importing the recommended policy. The implementation may later make a versioned preset the default only through a documented compatibility decision.

## Task Update Semantics

Starting and updating a task are different operations.

`agentkit start` creates or resumes lifecycle tracking and establishes the initial task context. `agentkit update` changes only explicitly requested task-context fields.

Update operations use domain-level semantics:

- `set` replaces a scalar value;
- `add` inserts a value without duplication;
- `remove` removes the requested value and is safe when the value is already absent.

Updating task context must not reset unrelated fields, fabricate check or review evidence, reopen a terminal task implicitly, or change derived lifecycle status directly. Arbitrary JSON patching and event sourcing are outside the initial scope.

Persisted task state receives an explicit schema version. Existing unversioned task JSON must remain readable and migrate safely without requiring users to discard current work.

## Adapter Boundary

The CLI, Git hooks, Codex hooks, local watcher, CI integrations, and future runtime integrations are adapters. They may observe state, invoke core operations, render evaluation results, and deliver reminders. They must not maintain independent copies of lifecycle rules.

This boundary allows AgentKit to remain runtime-portable: the repository holds associations, state, and rules; adapters determine when and where results are delivered.

## Compatibility and Implementation Order

The existing lifecycle behavior is the compatibility baseline. Implementation should proceed by:

1. adding characterization tests for current lifecycle outcomes;
2. introducing an explicit, versioned task-state model and `agentkit update`;
3. extracting shared named rule results used by `status`, `remind`, and `close`;
4. materializing the existing recommended policy as `recommended-v1`;
5. opening additional rule configuration only where behavior is deterministic and tested.

Refactoring must not make an existing repository silently stricter or weaker. Any intentional behavior change requires a separate documented decision.

## Consequences

Positive consequences:

- AgentKit gains a small vocabulary that covers mapping, lifecycle, evidence, reminders, and gates.
- Current behavior can become a preset rather than remaining implicit command logic.
- Status, reminder, close, and runtime adapters can share one explainable evaluation.
- Projects can customize policy without replacing the integrity rules of the core.
- Stronger future agents do not reduce the value of repository-local state and governance.

Costs and constraints:

- Existing command logic and task dictionaries require careful compatibility migration.
- Preset materialization creates configuration that AgentKit must validate and document.
- Named rules are intentionally less expressive than an arbitrary DSL.
- Association matching remains advisory where semantic meaning cannot be determined mechanically.

## Non-Goals

This decision does not introduce:

- a hosted control plane;
- a general agent runner or task orchestrator;
- arbitrary user-authored workflow code;
- automatic inference of authoritative human intent;
- an event-sourced task history;
- a guarantee that passing AgentKit checks proves product correctness.
