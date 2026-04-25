# AgentKit Workflow

Status: Draft

## Purpose

This document describes the intended way a human developer and coding agents work together in an AgentKit-enabled repository.

The workflow is intentionally lighter than an industrial automation harness. It assumes a human may still sit at the computer and collaborate with agents directly, while still borrowing the discipline of automated systems: durable intent, tests, checks, review loops, and traceable decisions.

## Workflow Summary

```text
External requirement
  -> agentkit start
  -> human-agent design discussion
  -> intent recording in repository docs
  -> derived tests and checks
  -> implementation, preferably TDD
  -> docs and maintenance updates
  -> clean-context review
  -> fixes
  -> agentkit close
  -> human attention
```

## 0. Task Start

When an agent begins a task in an AgentKit-enabled repository, it should run:

```text
agentkit start
```

The start step should establish the task's durable context:

- human intent source docs
- docs to keep in working memory
- affected components
- likely code areas
- expected validation commands
- review expectation
- design gaps or blocked decisions
- current implementation plan, when available

This gives the agent a stable reference it can return to during long-running work. It also gives AgentKit enough state to tell whether the task was closed responsibly.

## 1. Requirement Intake and Design Discussion

The work usually starts outside the repository.

Examples:

- office documents
- notes
- GitHub issues
- ProjectMan issues
- conversations
- user feedback
- production problems

The human brings the requirement to a coding agent and discusses:

- what the user really needs
- whether the current system design already covers it
- which component owns the work
- whether a new component or feature area is needed
- what tests should prove the behavior
- what docs should change
- what risks or open questions remain

The output should be a shared implementation direction, not necessarily a formal plan owned by AgentKit.

Many coding agents already have plan modes. AgentKit should work with those modes instead of replacing them.

## 2. Intent Recording and Documentation Placement

After the design discussion, the important result should be recorded inside the repository.

AgentKit should help the agent place the record in the right location:

- component design docs for component-local decisions
- architecture docs for cross-cutting structure
- active specs for task-specific implementation plans
- ADRs for meaningful long-term decisions
- testing docs for validation strategy
- `AGENTS.md` only for short, durable agent behavior rules

The goal is not to record every word of the conversation. The goal is to preserve the human intent that future agents must respect.

### Intent Recording Rules

Agents should record intent when a task changes:

- product behavior
- public API
- data model
- architecture boundaries
- workflow or state transitions
- testing strategy
- agent operating rules

Agents may skip persistent intent recording for:

- tiny mechanical fixes
- formatting-only changes
- obvious typo fixes
- local refactors that do not change documented behavior

When skipping, the agent should be able to explain why.

## 3. Derived Tests, Checks, and Guardrails

Once intent is recorded, the agent should derive validation from it.

Possible derived artifacts:

- unit tests
- integration tests
- API contract tests
- architecture import tests
- docs-impact rules
- state transition tests
- generated reference checks
- review checklist items

AgentKit does not need to auto-generate all of these on day one. Its first job is to remind the agent to consider them and provide templates or suggestions.

Over time, repeated human corrections should become checks.

Example:

```text
Human correction:
  "API routes should not directly contain persistence logic."

Promote to:
  docs/architecture/dependency-rules.md
  agentkit.yml layer rule
  tests/test_architecture_imports.py
```

## 4. Implementation, Preferably TDD

For behavioral work, the preferred path is test-first or test-anchored development.

Recommended sequence:

1. Read relevant intent and component docs.
2. Write or update tests that express the intended behavior.
3. Run tests and confirm the meaningful failure.
4. Implement the smallest change that passes.
5. Refactor while preserving tests.
6. Run relevant checks.

TDD should be strongly encouraged, but not treated as ceremony for every tiny task.

TDD is most important for:

- new behavior
- state machines
- API contracts
- data model changes
- orchestration logic
- bug fixes with clear reproduction steps

TDD can be optional for:

- simple copy edits
- style-only changes
- local renames
- one-line internal cleanups

## 5. Delivery and Maintenance

When implementation is complete, the agent should update maintenance artifacts.

The agent should check:

- Did public behavior change?
- Did an API change?
- Did a data model change?
- Did a workflow or state transition change?
- Did architecture boundaries change?
- Did tests or validation commands change?
- Did the user-facing behavior change?

If yes, update the relevant docs.

If no, record that no docs update was needed.

The agent should also run AgentKit checks:

```text
agentkit check
agentkit docs-impact
agentkit lint-architecture
```

The exact commands may vary by repository.

## 6. Autonomous Review and Fix Loop

Before the human spends attention on the result, the implementation should pass at least one review loop for non-trivial work.

The reviewer should ideally have a cleaner context than the implementing agent.

The reviewer receives:

- original task or requirement
- recorded human intent
- relevant design and component docs
- implementation summary
- changed files
- test output
- AgentKit check output

The reviewer checks:

- Does the implementation satisfy the original intent?
- Did the agent invent unsupported assumptions?
- Are tests meaningful?
- Are docs stale?
- Are architecture rules violated?
- Is the change too broad?
- Are there hidden failure modes?

The implementing agent should fix meaningful findings before asking for human review.

AgentKit does not need to directly spawn the reviewer in every environment. Its baseline responsibility is to remind the implementing agent when clean-context review is expected and return instructions for how to brief a reviewer.

See [review-guidance.md](review-guidance.md) for the review guidance contract.

Review means a loop, not a single pass. For non-trivial work, the implementing agent should perform review -> fix -> review until no meaningful reviewer findings remain, or only low-value residual risks are left for the human.

## 7. Human Attention Policy

Human attention should be spent on judgment calls, not preventable hygiene.

Before involving the human, the agent should have already handled:

- obvious test failures
- lint failures
- formatting
- stale docs warnings
- missing review guidance
- straightforward reviewer findings

The agent should ask the human when:

- design is missing
- requirements conflict
- the task would change product direction
- the implementation has multiple reasonable architecture choices
- a decision blocks the remaining work
- continuing would require an unsupported assumption

If one part is blocked but other parts are clear, the agent should continue with the clear work and isolate the blocked decision.

## 8. AgentKit Responsibilities in This Workflow

AgentKit should help with:

- starting and closing agent tasks with repository-local state
- creating a maintainable documentation system when introduced to a project
- mapping code components to documentation components
- reminding agents to record human-approved intent
- telling agents where that intent should be recorded
- suggesting tests and structural checks from design docs
- checking likely stale documentation
- checking architecture boundaries
- generating review guidance for the implementing agent
- reminding agents to close open tasks through runtime adapters where available
- generating or updating an AgentKit skill for the repository

AgentKit should not need to:

- replace an agent's built-in plan mode
- become a project management system
- run all implementation work itself
- force heavyweight ceremony on small tasks

## 8.1 Task Close

Every non-trivial task should end with:

```text
agentkit close
```

The close step checks whether the work is ready to hand back to the human or whether it should continue.

`agentkit close` should check:

- tests and AgentKit checks were run or intentionally skipped
- docs impact was addressed
- review loop was completed when required
- meaningful reviewer findings were fixed
- any blocking human question was recorded
- git status is clean or the local policy explains what remains uncommitted

If the agent is blocked waiting for human input, close should allow a blocked closure after the agent records:

- the question
- why it blocks progress
- what work is already complete
- what the next action should be after the human responds

This gives the agent a sanctioned pushback path instead of forcing it to guess.

In the MVP, successful `agentkit check` runs write local receipts keyed by the current diff fingerprint. `agentkit close` uses those receipts to avoid falsely completing work that has not passed the configured checks.

## 8.2 Hooks And Reminders

AgentKit should support two different hook layers.

Git hooks are deterministic repository gates. `agentkit install-hooks` can install a standard `pre-commit` hook that runs `agentkit check`. This hook runs because Git invokes it; agents do not need to remember a separate pre-commit command.

Agent lifecycle hooks are runtime integrations. When an environment supports a post-agent hook, scheduler, or ProjectMan/Symphony-style monitor, it can check for open AgentKit tasks and remind the agent to close them.

Reminder behavior must be stateful:

- no open task means no reminder
- a closed task means no reminder
- a blocked task with a recorded human question should wait for new input
- the same unchanged diff should not trigger the same warning forever

## 9. Skill Considerations

Skills are an important adoption path.

An AgentKit-enabled repository should be able to provide a local skill that tells agents:

- what AgentKit is
- where the repository's intent docs live
- how to inspect `agentkit.yml`
- how to choose relevant component docs
- how to run local checks
- how to update docs
- when to ask the human for design
- how to request and follow review guidance

The skill should be generated from repository-local configuration and docs, so it stays aligned with the project.

The skill should be concise. It should teach agents how to navigate the system, not duplicate all project documentation.

## 10. First MVP Interpretation

For the first version, AgentKit does not need to automate the whole workflow.

It should provide enough structure for agents and humans to follow the workflow manually:

- project initialization templates
- task start records
- documentation placement rules
- component-to-doc manifest
- docs-impact warnings
- architecture lint suggestions
- review guidance generation
- task closeout checks
- blocked-task recording
- deterministic Git hook installation
- repository-specific skill generation

This lets AgentKit become useful immediately while leaving room for deeper automation later.
