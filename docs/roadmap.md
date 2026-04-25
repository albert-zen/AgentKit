# AgentKit Roadmap

Status: Draft

## Purpose

This roadmap describes how AgentKit can grow from a lightweight repository harness into a durable maintainability system for agent-built software.

The roadmap is intentionally staged. AgentKit should be useful early without pretending to automate everything.

## Current Constraints

### 1. Agent Runtime Diversity

Different coding agents expose different ways to spawn sub-agents, use skills, run tools, inspect diffs, and persist state.

AgentKit should not depend on one runtime as the only path. It should provide portable artifacts first:

- Markdown guidance
- YAML configuration
- CLI output
- generated skills
- repository-local checks

Runtime-specific integrations can come later.

### 2. Intent Is Hard To Infer Reliably

AgentKit cannot perfectly infer human intent from code changes.

Early versions should ask agents to record or identify intent explicitly instead of pretending to reconstruct it automatically.

### 3. Documentation Freshness Is Probabilistic

A docs-impact check can identify likely affected docs, but it cannot always know whether docs truly need updates.

Early versions should produce warnings and require a docs-impact assessment rather than hard-failing every code-only change.

### 4. Architecture Rules Are Project-Specific

There is no universal correct architecture.

AgentKit should provide a configurable checking mechanism and starter templates, not a fixed framework.

### 5. Review Automation Depends On Agent Capabilities

Some environments allow sub-agent spawning. Others do not.

AgentKit should return review guidance that an implementing agent can follow. Direct review-agent orchestration is optional and later.

### 6. Too Much Process Can Hurt Small Projects

The first version must stay light.

AgentKit should make the right thing easy, not bury solo builders in enterprise ceremony.

## What Is Technically Achievable Now

These features are feasible with local files, git, and a CLI.

### Repository Initialization

Create a default structure:

- `AGENTS.md`
- `agentkit.yml`
- `docs/design.md`
- `docs/workflow.md`
- `docs/architecture/*`
- `docs/components/*`
- `docs/decisions/*`
- optional skill skeleton

Initialization should also guide the agent to finish repository-specific maintainability setup:

- choose or adapt the documentation structure
- configure doc links and durable intent locations
- map components to docs
- configure architecture rules
- install deterministic Git hooks when appropriate

### Task Lifecycle State

Track a lightweight task record for agent work:

- task id
- task todo
- durable intent sources
- focus docs and focus notes
- relevant docs
- affected components
- expected checks
- review requirement
- diff fingerprints
- close status
- blocked human question, when applicable

### Manifest Validation

Check that `agentkit.yml` references existing docs and code paths.

### Docs-Impact Warnings

Use `git diff` and the manifest to report likely affected docs.

Example:

```text
Changed code:
- src/projectman/services/orchestration.py

Likely affected docs:
- docs/components/orchestration/design.md
- docs/components/orchestration/agent-run-lifecycle.md

Update docs or record why no docs update was needed.
```

### Architecture Import Checks

For Python projects, parse imports and enforce configurable layer rules.

Later versions can add deterministic check adapters for TypeScript or other ecosystems where useful. This is not because LLMs need help understanding those languages; it is because AgentKit's own lint checks need parsers or analyzers to enforce boundaries reliably.

### Intent Placement Guidance

Tell the implementing agent where human-approved intent should be recorded.

The early version can provide placement guidance and templates. The LLM agent remains responsible for semantic capture and writing the content.

### Review Guidance

Return instructions for the implementing agent:

- whether review is expected
- what design docs to read
- what changed files to inspect
- what risks to check
- how to instruct the clean-context reviewer

### Git Hook Installation

Install standard Git hooks that run deterministic AgentKit checks at Git boundaries.

The early version should focus on `pre-commit` running `agentkit check`. AgentKit does not need a separate user-facing `agentkit precommit` workflow; Git is the trigger.

### Skill Generation

Generate a repository-local AgentKit skill that teaches agents:

- how to use the repo's AgentKit setup
- where docs live
- how to run checks
- when to ask humans
- how to request review guidance

## Phased Roadmap

## Phase 0: Design and Dogfood

Goal: Use AgentKit's own docs to clarify the product before building too much.

Deliverables:

- product design doc
- workflow doc
- review guidance doc
- maintainability model
- roadmap
- example `agentkit.yml` for AgentKit itself
- draft AgentKit skill

Success criteria:

- A future agent can read the docs and explain the intended product.
- We can use the docs to guide the first implementation.

## Phase 1: Lightweight CLI MVP

Goal: Provide useful repository-local guidance with minimal automation.

Commands:

- `agentkit init`
- `agentkit start`
- `agentkit check`
- `agentkit orient`
- `agentkit docs-impact`
- `agentkit lint-architecture`
- `agentkit intent-guidance`
- `agentkit review-guidance`
- `agentkit close`
- `agentkit install-hooks`
- `agentkit skill`

Capabilities:

- create docs skeleton
- guide repository maintainability setup during init
- create and close lightweight task records
- record task todo and focus context at start
- validate manifest
- orient agents at task start or continuation
- warn on likely stale docs
- check Python import layering
- generate intent placement guidance
- generate review guidance
- verify closeout requirements before final handoff
- support blocked close with human question as fallback
- install deterministic Git hooks
- generate a local skill

Success criteria:

- AgentKit can be installed and run in ProjectMan.
- A coding agent can use AgentKit output to decide which docs to read and update.
- Docs-impact and architecture checks catch real issues without being too noisy.

## Phase 1.5: Lifecycle Usability

Goal: Make the repo/task lifecycle easier for agents to follow without adding a heavy control plane.

Vision issues:

- `init` should become a repo readiness audit, not only a scaffold command.
- `init` should report whether docs, component mappings, architecture rules, hooks, and skills are present.
- `start` should support explicit task updates, such as focus notes, focus docs, task ids, and refined plans.
- `close` should explain missing gates in a way agents can act on immediately.
- task state should distinguish current focus, original task todo, human-approved constraints, receipts, and blocked handoff notes.
- reminders should be generated from open task state, not from chat memory.
- a lightweight `agentkit watch` process is acceptable as an AgentKit-owned local adapter for delivering reminders on one machine.

Success criteria:

- A new repo can run `agentkit init` and receive a clear maintainability readiness report.
- A task can be started before or after discussion and later refined without losing the human-approved focus.
- `agentkit close` gives a precise next action whenever it returns `needs_work`.

## Reminder Automation Model

AgentKit can own reminder state and reminder logic, but it cannot always own wakeup delivery.

AgentKit can do these things by itself:

- record open tasks in `.agentkit/`
- determine whether a task is `completed`, `needs_work`, or `blocked`
- compute whether receipts are stale for the current fingerprint
- generate a reminder message for an open task
- expose commands such as a future `agentkit remind` or `agentkit status`
- run a lightweight local `agentkit watch` process that periodically checks open task state
- run deterministic checks from Git hooks

AgentKit usually needs a trigger to deliver reminders after an agent has stopped. That trigger may be external, or it may be AgentKit's own local watcher.

Possible triggers:

- AgentKit's own `agentkit watch` process
- an agent runtime post-run hook
- ProjectMan or Symphony monitoring an agent run
- an editor integration
- an OS scheduled task
- a CI job or local background service

The key design boundary:

- AgentKit owns the repo-local truth: task state, receipts, rules, and reminder text.
- Delivery adapters own delivery: when and how to wake or message an agent. The adapter may be external, or it may be AgentKit's local watcher.

AgentKit should be allowed to ship a lightweight local watcher. That watcher should stay small: it reads AgentKit state, emits reminders, and optionally calls configured local notification mechanisms. It should not become a general job orchestrator or agent runner.

## Phase 2: ProjectMan Dogfood Integration

Goal: Use AgentKit while adding Symphony-style agent spawning and board features to ProjectMan.

Capabilities:

- create a ProjectMan-specific `agentkit.yml`
- map ProjectMan code areas to docs
- add orchestration component docs
- add architecture tests for ProjectMan
- use `review-guidance` before human review

Success criteria:

- AgentKit helps guide a real feature implementation.
- The workflow identifies missing docs or tests before human review.
- We learn which warnings are useful and which are noise.

## Phase 3: Deterministic Check Adapters

Goal: Add deterministic check adapters where they provide real maintainability value.

Capabilities:

- TypeScript import graph checks
- frontend component mapping
- package boundary rules
- generated API docs checks
- OpenAPI freshness checks

Success criteria:

- AgentKit can enforce configured boundaries across ProjectMan backend and frontend.
- Additional language support only ships where the checks are reliable and useful.

## Phase 4: Better Intent Guidance

Goal: Reduce the cost of placing design intent correctly.

Capabilities:

- suggest affected docs from task text plus git diff
- suggest ADR creation for cross-cutting decisions
- generate testing checklist from design docs
- provide templates for missing component docs

Important constraint:

AgentKit should not treat inferred intent as authoritative. The LLM agent and human own semantic intent. AgentKit routes, reminds, and templates.

Success criteria:

- Recording intent becomes easier without pretending AgentKit understands the human better than the agent does.

## Phase 5: Review Guidance Adapters

Goal: Make review guidance easier to use in different agent environments.

Capabilities:

- runtime-specific reviewer spawn instructions
- optional durable review context summaries for external systems
- optional review result parsing
- integration with systems like Symphony or ProjectMan agent runs
- post-agent reminder adapters that detect open tasks and ask the agent to run `agentkit close`

Success criteria:

- The implementing agent can reliably perform one review-fix loop before human attention.
- Review outputs consistently focus on intent drift, tests, docs, and architecture.
- Open tasks are not silently abandoned when the runtime supports reminders.

## Phase 6: Maintainability Reports

Goal: Provide agent-readable maintainability signals without making a dashboard the product.

Capabilities:

- component documentation coverage
- docs-impact history
- architecture violation trends
- stale generated references
- unreviewed non-trivial changes
- missing ADR signals

This should start as CLI or machine-readable output. A dashboard belongs in a project management or observability product, not AgentKit's core.

Success criteria:

- An agent can quickly see where the repository is becoming harder to change safely.
- Other tools, such as ProjectMan, can consume these signals if they want to show a board or dashboard.

## Long-Term Direction

As models become stronger, AgentKit should become less about compensating for model weakness and more about preserving project memory and engineering taste.

Long-term value should come from:

- durable intent
- shared repository memory
- executable governance
- review protocols
- traceable decisions
- tool-agnostic agent onboarding

AgentKit should remain useful even when agents are much better at reasoning, because maintainability is not just a reasoning problem. It is also a memory, coordination, validation, and governance problem.

## Product Risks

### Too Much Ceremony

If AgentKit requires too many files or steps, users will ignore it.

Mitigation:

- warnings before hard failures
- templates that can be adopted gradually
- optional strict mode

### Noisy Checks

If docs-impact warnings are too broad, agents will learn to dismiss them.

Mitigation:

- component manifest tuning
- severity levels
- allow explicit "no docs update needed" notes

### Runtime Lock-In

If AgentKit depends too heavily on one agent platform, it loses portability.

Mitigation:

- keep CLI and docs as the core
- treat skills and runtime integrations as adapters

### False Confidence

Passing AgentKit checks does not prove the product is correct.

Mitigation:

- describe checks as maintainability signals
- keep human judgment in the loop for design decisions

## Near-Term Product Questions

- Should the first implementation be Python CLI because ProjectMan is Python-backed?
- What should the first `agentkit.yml` schema look like?
- How should a code change record "docs checked, no update needed"?
- Should `review-guidance` inspect git diff automatically or rely on explicit changed paths?
- Where should generated skills live by default?
- What should strict mode enforce versus warn?
- Should `agentkit orient` be path-based only in MVP, or accept free-form task text too?
