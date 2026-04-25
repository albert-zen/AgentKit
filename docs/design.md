# AgentKit Design

Status: Draft

## Overview

AgentKit is a lightweight agent-first development harness for personal and small-team software work.

Its purpose is to define "the way you should work with agents" inside a repository. Modern coding agents can implement software very quickly, but speed without durable intent, feedback loops, and architectural guardrails can accumulate technical debt just as quickly. AgentKit helps keep agent work on the rail by turning human taste and design intent into repository-local artifacts that agents can read, execute against, and validate.

AgentKit is not meant to be a heavy enterprise platform. It starts as a CLI-first, file-based toolkit that can be adopted gradually in any repository.

## Product Thesis

Human developers increasingly work at a higher level of abstraction:

- define intent
- design system boundaries
- specify acceptance criteria
- shape feedback loops
- review and correct trajectory

Agents increasingly execute:

- implement features
- write tests
- update docs
- inspect code
- run validation
- respond to review

AgentKit exists to make this collaboration sustainable. It gives agents a legible operating environment and gives humans a way to inject intent into the agent's implementation trace.

The expected collaboration loop is documented in [workflow.md](workflow.md). That workflow is part of the product contract: AgentKit should support the way a human and coding agent move from outside-world requirements, to design discussion, to intent recording, to implementation, to review.

The concrete product mechanics are documented in [implementation-model.md](implementation-model.md). AgentKit should primarily provide guidance, routing, templates, and deterministic checks. The LLM agent remains responsible for semantic understanding and writing the actual design content.

## Maintainability Model

AgentKit's core value is maintainability for agent-built software.

A system is maintainable when future humans and future agents can safely change it by reading durable intent, following explicit boundaries, running meaningful checks, and understanding why past decisions were made.

AgentKit should treat maintainability as a product surface, not as an accidental side effect of documentation.

### 1. Durable Intent

Human intent should survive beyond a chat session.

Examples:

- product goals
- non-goals
- design decisions
- component responsibilities
- accepted tradeoffs
- rejected alternatives
- open questions

AgentKit supports this with structured docs, specs, ADRs, and intent placement guidance.

### 2. Explicit Boundaries

Future agents need to know where code belongs and what dependencies are allowed.

Examples:

- layer rules
- component ownership
- public contracts
- integration boundaries
- forbidden imports

AgentKit supports this with architecture docs, manifests, and dependency checks.

### 3. Executable Constraints

Important human preferences should eventually become executable checks.

Examples:

- TDD tests for behavior
- API contract tests
- state transition tests
- architecture lint
- docs-impact warnings

AgentKit should help teams promote repeated review comments into durable rules.

### 4. Documentation Freshness

Documentation only helps if future agents can trust it.

AgentKit should not demand documentation changes for every edit, but it should require agents to evaluate whether code changes affect documented behavior, architecture, data models, workflows, or tests.

The key requirement is not "always update docs"; it is "always account for docs impact."

### 5. Traceability

Future agents should be able to answer:

- What changed?
- Why was it changed?
- What human intent approved it?
- What tests prove it?
- What docs were updated?
- What risks remain?

AgentKit supports traceability through specs, ADRs, review guidance, and implementation summaries.

### 6. Reviewability

Changes should be easy for a clean-context reviewer to inspect.

The reviewer should have enough context to compare original intent against implementation without inheriting all of the implementing agent's assumptions.

AgentKit supports reviewability through review guidance, relevant-doc discovery, and consistent output expectations.

### 7. Reversibility and Locality

Maintainable changes should be scoped enough that future agents can understand, modify, or revert them safely.

AgentKit should encourage agents to:

- keep changes close to affected components
- avoid unrelated refactors
- record design impact when scope expands
- separate mechanical cleanup from behavioral changes

### 8. Skill Transfer

The repository should teach future agents how to work in it.

AgentKit supports this through root guidance, plugin-packaged skills, local commands, and repository-aware conventions.

### Maintainability Signals

AgentKit can gradually report maintainability signals:

- missing component docs
- code changes without docs-impact assessment
- architecture violations
- weak or missing tests for behavior changes
- stale generated references
- large unscoped diffs
- missing review for non-trivial changes
- missing ADR for cross-cutting decisions

Early versions should favor warnings and guidance over hard blocking.

## Core Beliefs

### Intent Must Be Durable

If an intention only exists in a chat thread or in someone's head, it will eventually be lost. Durable intent should be recorded in repository-local artifacts such as Markdown specs, architecture docs, ADRs, test contracts, and lint rules.

### AGENTS.md Is a Map, Not an Encyclopedia

The root agent instruction file should be short. It should tell agents where to look, how to decide what to read, and what rules are mandatory. Detailed knowledge should live in structured docs.

`agentkit init` should keep this surface small. It may create or append a low-level AgentKit section that explains the repository uses AgentKit for maintainable agent-led changes and points agents to the CLI entry points and AgentKit plugin skill. It should not put the full AgentKit workflow or product philosophy into `AGENTS.md`.

### Documentation Should Become Executable When It Matters

Some intentions can stay as prose. Important intentions should eventually become checks:

- architecture lint rules
- structural tests
- API contract tests
- generated documentation checks
- docs-impact checks

When an agent repeatedly violates a written rule, the rule should usually be promoted into tooling.

### TDD Reduces Long-Run Drift

Agent implementation should prefer test-first or test-anchored development. Tests convert intent into a feedback loop that can continuously correct the agent's trajectory.

### Agents Should Ask When Design Is Missing

Agents should not make broad product or architecture assumptions when the design is absent or ambiguous. If a task is not designed, the agent should ask for design help. If part of a task is blocked by ambiguity but other parts are clear, the agent should continue with the clear parts and isolate the blocked decision.

### Clean Review Context Matters

After implementation, review should be performed from a cleaner context than the implementing agent's context. A review agent should compare:

- original human intent
- relevant design docs
- implementation plan
- code diff
- tests and validation output

The reviewer should look for drift from intent, missing tests, architectural violations, and stale documentation.

The durable docs are the source of truth for human intent. Inline summaries in reviewer prompts are allowed only as convenience context; they should point back to specific repository paths and should not replace the design, component, spec, or ADR documents that carry the approved intent.

## Goals

- Scaffold repositories for agent-first development.
- Keep human design intent visible to agents.
- Help agents record design discussions and implementation intent in the right repository location.
- Define documentation structures that scale from solo projects to small teams.
- Map code areas to documentation areas.
- Detect likely stale documentation after code changes.
- Enforce architecture dependency rules with lightweight structural tests.
- Encourage TDD and review loops for agent-generated changes.
- Support clean-context review by a separate agent.
- Provide reusable skills or agent instructions that teach agents how to use AgentKit inside a repository.
- Make agent workflows traceable and auditable without requiring a heavy platform.

## Non-Goals

- Replace coding agents, IDEs, or project management tools.
- Become a full orchestration system like Symphony.
- Require a hosted SaaS control plane.
- Force every project into the same architecture.
- Require every source file to have a matching documentation file.
- Block all progress when documentation is imperfect.

## Target Users

- Solo developers working with coding agents.
- Small teams adopting agent-first development.
- Builders who want repository-local governance without enterprise process overhead.
- Projects that need durable design intent, architecture rules, and doc hygiene before they need a large platform.

## System Model

AgentKit treats a repository as an agent-readable operating environment.

The repository contains:

- a short root `AGENTS.md`
- structured documentation
- active and completed specs
- architecture rules
- component ownership metadata
- tests and lint rules
- optional agent skills
- optional review instructions

AgentKit provides:

- templates for these artifacts
- checks that validate their structure
- impact analysis over code and documentation changes
- prompts, skills, or instructions that guide agents through implementation and review

## Task Lifecycle Model

AgentKit should treat agent work as an explicit task lifecycle.

### 0. Repository Initialization

At repository setup time, the agent runs `agentkit init`.

The purpose of `init` is not only to create files. It should instruct the agent to improve the repository's long-term maintainability by configuring:

- documentation structure
- component-to-doc mappings
- architecture rules
- durable intent locations
- local skills
- deterministic hooks
- project-specific links and conventions

AgentKit should recommend a standard documentation system, while allowing the repository to configure its own docs, links, and hooks.

### 1. Start

At task start, the implementing agent runs `agentkit start`.

The start command should create or update a lightweight task record that captures:

- the task todo or task statement
- durable human intent source paths
- docs the agent should keep in working memory
- task focus notes from the human-agent discussion
- likely affected components
- likely code areas
- planned validation commands
- whether review is expected
- whether design appears missing
- the agent's current implementation plan, if one exists

`agentkit start` should build on `orient`; it should not replace the agent's own planning ability. Its job is to make the task's durable context explicit and recoverable.

The human and agent may discuss first and then start the task, or start early and refine the task focus later. Either way, the task's important intent and focus must be recorded before closeout.

### 2. Work

During implementation, the agent can return to the task record to recover context it may have forgotten.

The task record should help answer:

- What human intent am I implementing?
- Which docs are authoritative?
- Which files or components are in scope?
- What checks did I promise to run?
- Is review required?
- What is blocked on human input?

### 3. Close

Before ending a task, the implementing agent must run `agentkit close`.

The close command checks whether the task has been responsibly closed:

- relevant checks were run or intentionally skipped
- docs impact was addressed
- review loop was completed when required
- blocking questions were recorded if the work cannot continue
- git status is clean or the agent has committed/staged according to the local policy
- the final state is traceable to durable intent

If the task is blocked on human input, `agentkit close` should still allow closure after the agent records the question, current state, and next action needed from the human.

Close may end as `completed`, `needs_work`, or `blocked`. A blocked close is a traceable fallback path, not a bypass. It requires an existing task and a recorded human question.

### 4. Reminder

If a task has been started but not closed, an integration may re-activate the agent with a reminder:

```text
AgentKit found an open task that was not closed.
Are you done, still working, or blocked waiting for human input?
Run `agentkit close` before ending the task.
```

This reminder should be stateful, not noisy. Once the task is closed, it stops. If the task is blocked and closed with a recorded question, it should not keep nagging the agent until new input arrives.

AgentKit itself may provide the local state model and CLI commands. Runtime-specific reminders can be implemented by adapters, ProjectMan, Symphony, editor integrations, or future agent platform hooks.

AgentKit owns reminder truth, and it may also ship a lightweight local watcher for reminder delivery. It can record open task state, sample that state at any moment, decide whether a reminder is needed, and generate the reminder text. To wake a stopped agent or send a message into a running environment, AgentKit needs a delivery trigger: this can be an external adapter such as an agent runtime hook, ProjectMan, Symphony, an editor integration, or OS scheduler, or an AgentKit-owned `agentkit watch` process. The watcher should remain a local reminder adapter, not a general orchestrator.

The same state sampler should power `check`, `status`, `remind`, `watch`, and external integrations. `check` may include lifecycle reminders for convenience, but the reminder policy should live below the command layer so every entry point sees the same missing gates and fallback options.

## Intent Injection Channels

AgentKit uses several channels to inject human intent into agent work.

### 1. Startup Guidance

Agents receive concise initial guidance through `AGENTS.md`. This guidance should point to the right documents and explain the local development protocol.

Example responsibilities:

- read relevant component docs before editing
- follow layer dependency rules
- use TDD when implementing behavior
- update docs when public behavior changes
- ask questions when design is missing

### 2. Design and Specification Documents

Human intent is recorded in a structured docs tree.

Common document types:

- product design docs
- architecture docs
- component docs
- execution specs
- ADRs
- testing docs
- generated references

AgentKit should not need to own the planning experience itself. Many coding agents already have strong plan modes. AgentKit should instead make it easy to persist the result of that planning conversation into the correct docs, specs, component files, and ADRs.

### 3. Tests and Constraints

Important intent should be enforced mechanically.

Examples:

- dependency direction tests
- docs manifest tests
- API schema tests
- state transition tests
- naming and file-size lints
- generated docs freshness checks

### 4. TDD Workflow

For behavior changes, agents should prefer:

1. Read intent.
2. Write or update tests that express the desired behavior.
3. Run tests and observe failure.
4. Implement the smallest change that passes.
5. Refactor within the architecture rules.
6. Run the relevant checks.
7. Update docs or record why docs did not change.

### 5. Clean-Context Review

After an implementation pass, a separate reviewer should inspect the change with fresh context.

AgentKit's baseline responsibility is not to own every agent runtime. Instead, it should provide review guidance that tells the implementing agent when and how to ask a clean-context reviewer to compare the original intent against the implementation.

The review should receive:

- the original task
- relevant design docs
- implementation notes
- changed files
- test results

The reviewer should produce:

- findings ordered by severity
- missing tests
- documentation drift
- architecture violations
- suggested fixes

### 6. Agent Skills

When an agent platform supports skills, AgentKit should provide an AgentKit skill that teaches agents how to use the repository's AgentKit setup. For Codex, the preferred distribution shape is a repo-local plugin under `plugins/agentkit/` exposed through `.agents/plugins/marketplace.json`.

The skill is for agents using AgentKit inside a target repository. It is not the north-star product design for agents developing AgentKit itself.

Therefore the skill should focus on operational value:

- how AgentKit helps the current task
- which commands to run and when
- which docs to read before editing
- when to ask the human for missing design
- how to keep docs, checks, review, and closeout aligned
- how to interpret lifecycle reminders

The skill should not try to teach the full product philosophy, roadmap, or long-term architecture of AgentKit. Those belong in durable design docs such as this file, the workflow, implementation model, component docs, and roadmap.

The skill should explain:

- how to read `agentkit.yml`
- how to find component docs
- how to run AgentKit checks
- how to record design intent
- how to decide whether docs need updates
- how to request review guidance

This keeps the root `AGENTS.md` small while still giving agents detailed, reusable operating knowledge.

## Documentation Strategy

AgentKit separates docs by purpose and stability.

### Intent Layer

High-level, human-readable, relatively stable.

Examples:

- `docs/design.md`
- `docs/architecture/overview.md`
- `docs/core-beliefs.md`

### Contract Layer

Specific enough for agents to implement and validate.

Examples:

- `docs/architecture/layers.md`
- `docs/architecture/dependency-rules.md`
- `docs/components/<component>/design.md`
- `docs/components/<component>/api.md`
- `docs/components/<component>/testing.md`

### Execution Layer

Task-specific, allowed to evolve quickly.

Examples:

- `docs/specs/active/<spec>.md`
- `docs/specs/completed/<spec>.md`
- `docs/tech-debt.md`

### Decision Layer

Records why important choices were made.

Examples:

- `docs/decisions/0001-agent-first-docs.md`
- `docs/decisions/0002-layer-boundaries.md`

## Suggested Repository Structure

```text
AGENTS.md
agentkit.yml
docs/
  design.md
  core-beliefs.md
  architecture/
    overview.md
    layers.md
    dependency-rules.md
    data-flow.md
  components/
    <component>/
      design.md
      api.md
      testing.md
  decisions/
    0001-example.md
  specs/
    active/
    completed/
  generated/
  skills/
    agentkit/
      SKILL.md
```

This structure is a default, not a mandate. AgentKit should let projects customize it.

## Component and Layer Mapping

AgentKit should maintain a manifest that maps code areas to documentation areas.

Example:

```yaml
components:
  issues:
    code:
      - src/projectman/domain/issues.py
      - src/projectman/services/issues.py
      - src/projectman/api/routes/issues.py
    docs:
      - docs/components/issues/design.md
      - docs/components/issues/api.md
      - docs/components/issues/testing.md
```

This manifest enables docs-impact checks:

- if related code changed and docs did not, warn the agent
- if docs changed but referenced code does not exist, warn the agent
- if a component lacks required docs, warn the agent

## Architecture Rules

AgentKit should support configurable dependency rules.

Example:

```yaml
layers:
  domain:
    may_import: []
  schemas:
    may_import:
      - domain
  repositories:
    may_import:
      - domain
      - db
  services:
    may_import:
      - domain
      - schemas
      - repositories
  api:
    may_import:
      - schemas
      - services
```

The exact layers are project-specific. AgentKit provides the checking mechanism, not one universal architecture.

## Agent Decision Protocol

Agents should follow this protocol:

1. Identify the affected component.
2. Read the root `AGENTS.md`.
3. Read the relevant design, architecture, and component docs.
4. If the task has no design and affects product behavior or architecture, ask the human for design.
5. If only part of the task is ambiguous, isolate the ambiguity and continue with clearly designed work.
6. Prefer TDD for behavioral changes.
7. Implement within the architecture rules.
8. Run tests and AgentKit checks.
9. Update docs when public behavior, data models, architecture, workflows, or tests changed.
10. Request or run clean-context review for non-trivial changes.

## Proposed CLI

### `agentkit init`

Set up AgentKit in a repository.

This is a one-time or occasional setup command. It gives the repository an AgentKit-readable shape:

- `AGENTS.md`
- `agentkit.yml`
- docs skeleton
- starter architecture rules
- starter doc strategy

The value of `init` is not scaffolding for its own sake. It creates the durable surfaces that future agents can use:

- where project intent lives
- where component docs live
- how code maps to docs
- what architecture rules exist
- which local commands agents should run
- where an AgentKit skill should be generated

If `AGENTS.md` or `agents.md` already exists, `init` should add only a small low-level AgentKit entry section instead of overwriting the file or inserting a large workflow manual.

### `agentkit start`

Start or resume an AgentKit task.

This command makes the task's working context explicit:

- durable intent source paths
- relevant docs
- likely affected components
- likely changed code areas
- design gaps
- suggested checks
- review expectation
- optional implementation plan

`start` should call the same underlying analysis as `orient`, but it additionally writes a local task record so later commands can reason about whether the task was closed correctly.

### `agentkit orient`

Tell an agent what to look at before starting or continuing work.

This command is meant to provide immediate development value to the implementing agent. Given a task, changed paths, or an explicit component, it should answer:

- Which components are likely affected?
- Which design and component docs should I read first?
- Are any expected design docs missing?
- Does this look like a product, API, data model, architecture, workflow, or test-impacting change?
- Which architecture rules are relevant?
- What tests or checks should I consider?
- Should I ask the human for design before changing code?

`orient` does not design the feature. It gives the agent a repository-aware starting map so it does not begin from a blank context or rely only on chat history.

Example:

```text
agentkit orient --component orchestration
```

Expected output:

```text
Affected component:
- orchestration

Read first:
- docs/design.md
- docs/components/orchestration/design.md
- docs/components/orchestration/agent-run-lifecycle.md
- docs/architecture/dependency-rules.md

Potential design gap:
- No Symphony spawn design doc found.

Suggested checks:
- orchestration API tests
- agent run lifecycle tests
- architecture dependency lint
```

### `agentkit check`

Run all configured checks:

- manifest validity
- docs existence
- docs-impact checks
- architecture lint
- optional generated-doc freshness checks

`check` may also print lifecycle reminders sampled from the current task state. This makes the common command more useful without making `check` the only owner of reminder logic.

### `agentkit status`

Print the current task lifecycle state:

- open tasks
- completed, needs-work, or blocked state
- missing closeout gates
- stale check or review receipts
- recorded blocked human questions

### `agentkit remind`

Print agent-facing next actions derived from the same lifecycle state as `status`.

`remind` is useful when an agent wants guidance without running repository checks, and it gives `watch` and external adapters a stable reminder surface.

### `agentkit close`

Close the current AgentKit task.

This command is a workflow gate for agents before final response or task handoff. It should check:

- whether `agentkit check` has passed for the current diff
- whether docs impact was addressed
- whether review guidance was followed when review is expected
- whether review -> fix -> review happened for non-trivial work
- whether blocking human questions were recorded
- whether the working tree has uncommitted changes when local policy expects a commit

`close` should avoid infinite loops by using a task state file and diff fingerprint. If the diff has not changed since the last successful check or review receipt, AgentKit should not repeatedly ask for the same action. If the diff changes, related receipts become stale.

### `agentkit install-hooks`

Install repository-local Git hooks that invoke AgentKit checks automatically at Git boundaries.

The first hook should be a standard `pre-commit` hook that runs deterministic checks such as `agentkit check`. Agents and humans should not need to remember a separate manual `agentkit precommit` command.

The hook layer is for deterministic repository checks. It should not spawn reviewers or perform long-running LLM judgment.

### `agentkit watch`

Run a lightweight local reminder loop.

`watch` should repeatedly call the same status/reminder logic used by `status`, `remind`, and the lifecycle reminder section of `check`. It should deliver reminders while a task is open and missing gates, then stop once the task is completed or traceably blocked.

### `agentkit plan <name>`

Create a new active execution spec from a template when the user wants AgentKit to host the planning artifact.

This is optional because many coding agents already have their own plan mode. AgentKit's more important responsibility is to help persist the final human-approved intent and implementation approach.

### `agentkit intent-guidance`

Tell an agent where human-approved design intent should be recorded:

- active spec
- component design doc
- architecture doc
- ADR
- testing doc

AgentKit should not try to replace the LLM's semantic capture. The agent writes the content; AgentKit provides placement guidance, required headings, and templates.

### `agentkit docs-impact`

Inspect git changes and report which docs may need updates.

### `agentkit lint-architecture`

Validate import direction and forbidden dependencies.

### `agentkit review-guidance`

Return instructions that the implementing agent can use when spawning or requesting a clean-context reviewer.

The guidance should state:

- durable intent source paths
- relevant design docs, specs, and ADRs
- changed files
- implementation summary
- test and check results
- review focus areas
- expected output format

AgentKit may optionally emit a durable context summary for external systems, but the main path is guidance for the implementing agent.

### `agentkit doctor`

Explain repository readiness for agent-first development.

`doctor` should audit whether the repository has the AgentKit entry guidance, config, docs, valid mappings, plugin-packaged skill, and optional hook setup. It reports missing readiness items and optional improvements without changing files.

### `agentkit skill`

Generate or update an AgentKit usage skill for the current repository.

The skill should be concise and repository-aware. It should point agents to local docs, local commands, and local decision rules instead of restating the whole documentation tree. By default, it should live inside the AgentKit Codex plugin rather than only under a runtime-private `.codex/skills` path.

## Review Loop

AgentKit should support a standard implementation-review loop:

1. Human writes or approves intent.
2. Implementing agent creates or updates tests.
3. Implementing agent changes code.
4. Implementing agent runs local checks.
5. Implementing agent calls AgentKit for review guidance.
6. AgentKit tells the implementing agent whether review is expected and how to brief the reviewer.
7. The implementing agent requests or spawns a clean-context reviewer when the environment supports it.
8. Clean reviewer agent inspects the result.
9. Implementing agent fixes meaningful findings.
10. Implementing agent requests a second clean-context review after fixes.
11. Implementing agent repeats review -> fix -> review until no meaningful findings remain, or only low-value residual risks remain.
12. Human reviews only the remaining judgment calls.

One review pass is not a review loop. For non-trivial reviewed work, AgentKit should require at least review -> fix -> second review before normal closeout.

## Skill Strategy

AgentKit should treat skills as a first-class adoption mechanism.

A repository can contain a skill that teaches agents how to work in that specific repository. This skill should be generated from:

- root `AGENTS.md`
- `agentkit.yml`
- architecture rules
- docs manifest
- common commands
- review expectations

The skill should not replace docs or checks. It should be the agent-facing guide that explains how to use them.

The skill should be rich enough to shape another capable agent's behavior without relying on the original conversation. It should tell the agent the normal operating loop:

1. Start or resume the task with AgentKit.
2. Read the durable intent sources AgentKit returns.
3. Ask for human design when the design surface is missing or ambiguous.
4. Implement against tests and repo rules.
5. Run checks and read lifecycle reminders.
6. Request clean-context review when expected.
7. Fix meaningful findings.
8. Close the task as completed or blocked.

For deeper product intent, the skill should point to the repository docs instead of restating them.

Mock-agent adoption tests should be used to calibrate this surface. If a clean agent can read the skill and explain when to start, ask for design, run checks, request review, and close, then the skill is carrying useful operational knowledge. If the agent cannot read the skill because of runtime permissions, AgentKit should fail gracefully through CLI guidance and root docs, but the runtime integration should still grant read access to the plugin skill.

## Relationship to Other Tools

### ProjectMan

ProjectMan manages projects, issues, documents, revisions, and agent run records.

AgentKit manages repository-local agent development discipline.

### Symphony

Symphony orchestrates coding agent execution across issues, workspaces, retries, and concurrency.

AgentKit provides the repository rules and checks those agents should follow while working.

### Coding Agents

AgentKit does not replace coding agents. It gives them a clearer environment and stronger feedback loops.

## Initial MVP

The first useful version should include:

- `agentkit init`
- `agentkit start`
- `agentkit check`
- `agentkit orient`
- `agentkit docs-impact`
- `agentkit lint-architecture`
- `agentkit intent-guidance`
- optional `agentkit plan`
- `agentkit review-guidance`
- `agentkit close`
- `agentkit install-hooks`
- `agentkit skill`
- default templates for `AGENTS.md`, docs, specs, and ADRs
- a simple YAML manifest
- Python import graph checks

The lifecycle-focused iteration adds `agentkit status` and `agentkit remind` as first-class ways to sample task state. A lightweight `agentkit watch` command provides a local reminder adapter on top of the shared sampler.

## Open Questions

- Should AgentKit start as a Python CLI, a TypeScript CLI, or both?
- How strict should docs-impact checks be by default?
- Should AgentKit optionally write durable review context summaries, or keep review guidance ephemeral by default?
- Should AgentKit integrate directly with ProjectMan issue documents, or keep that as an adapter?
- Should TDD be a hard requirement or a recommended mode?
- How should projects define "non-trivial change" for clean-context review?
- Which non-Codex plugin formats should AgentKit generate after the Codex plugin surface is stable?

## Design Principle

AgentKit should be useful before it is comprehensive.

It should start as a small set of repository-local tools that make agent collaboration more legible, intentional, and recoverable. The product should grow only where repeated human-agent friction proves that more structure is needed.
