# AgentKit Workflow

Status: Draft

## Purpose

This document defines the intended lifecycle for using AgentKit in an agent-built repository.

AgentKit is not only a set of checks. It is a workflow harness that keeps agent work tied to durable human intent, repository-specific maintainability rules, and explicit closeout gates.

The workflow has four stages:

1. Repository initialization
2. Task start
3. Task execution and checks
4. Exception handling and feedback

Only after a task reaches a valid closed state should the agent end the work.

## Workflow Summary

```text
Repository setup
  -> agentkit init
  -> configure maintainability docs, links, rules, hooks, and skills

Concrete task
  -> human-agent discussion and/or agentkit start
  -> record task intent, todo, focus docs, code scope, and plan
  -> implement against durable intent
  -> run tests, AgentKit checks, docs-impact, and review loop
  -> agentkit close
  -> completed, needs_work, or blocked with human question
```

## 1. Repository Initialization

Initialization happens at the repository level.

The command is:

```text
agentkit init
```

The purpose of `init` is to tell the agent:

- this repository should become more maintainable for long-running agent work
- human intent must live in durable repository artifacts
- the repo should have a legible documentation system
- code areas should map to docs and ownership boundaries
- deterministic checks and hooks should encode important constraints

`init` should recommend a standard structure, while allowing the project to configure its own docs, links, rules, and hooks.

Recommended initialized surfaces:

- `AGENTS.md`
- `agentkit.yml`
- `docs/design.md`
- `docs/workflow.md`
- `docs/architecture/`
- `docs/components/<component>/`
- `docs/decisions/`
- `docs/specs/active/`
- `docs/specs/completed/`
- `.codex/skills/agentkit/SKILL.md`
- optional Git hooks through `agentkit install-hooks`

The initialized repo should answer:

- Where does human intent live?
- Which docs are authoritative?
- Which code paths belong to which components?
- Which architecture rules are enforced?
- Which checks must agents run?
- Which hooks are installed automatically by Git?
- How should future agents start and close tasks?

The `init` command should not pretend to fully configure the repo by itself. Its job is to guide the agent to complete the maintainability setup.

If the repository already has a documentation system, AgentKit should adapt to it through configuration instead of forcing a full replacement.

## 2. Task Start

Task start happens for each concrete unit of work.

The command is:

```text
agentkit start --task "<task todo>"
```

Every task should have a task todo or task statement.

`start` creates or updates the task record that later gates `close`.

The task record should capture:

- task todo
- durable human intent source paths
- focus docs for this task
- likely affected components
- likely code areas
- expected checks
- review expectation
- design gaps or blocked decisions
- implementation plan, when available
- known human-approved constraints

There are two valid ways to use `start`.

### Option A: Discuss First, Then Start

The human and agent first discuss the requirement, design direction, risks, and implementation plan.

Then the agent runs `agentkit start` with the agreed task todo and plan.

This works well when the task needs design thinking before any execution begins.

### Option B: Start First, Then Refine Focus

The agent runs `agentkit start` early with the initial task todo.

After discussion or investigation clarifies the task, the agent updates the task context.

The MVP path is to rerun `agentkit start` for the current task with the refined task todo, plan, and focus notes. The current CLI uses the default `current` task id; a future version should expose explicit arguments such as:

```text
agentkit start --task-id current --task "<refined task todo>" --focus-note "<human-approved focus>"
```

Until those explicit flags exist, the implementing agent must preserve refined focus in the task plan text or in the relevant durable docs, then rerun `agentkit start` so the current task state reflects the updated context.

This works well when the agent needs AgentKit's orientation before the design is fully clear.

AgentKit must support the second path because agents often learn important scope information after the first pass.

The important rule is this:

Human intent and task focus must be written into a durable task context before implementation closes. They cannot live only in chat memory.

## 2.5. Task State And Reminder Sampling

After `start`, AgentKit maintains repository-local task state under `.agentkit/`.

This state is the source for lifecycle reminders. At any moment, AgentKit should be able to sample the state and answer:

- what task is open
- which durable intent sources matter
- which gates have been satisfied
- which gates are still missing
- whether the task is blocked with a recorded human question
- what the agent should do next

Commands can use this same sampling model in different ways:

- `agentkit check` runs deterministic repository checks and may also show the current lifecycle reminders.
- `agentkit status` should expose the sampled task state and missing gates.
- `agentkit remind` should format the sampled state into action-oriented instructions for the agent.
- `agentkit watch` should repeatedly sample the state and deliver reminders while it is running.

The important product rule is that reminders are derived from durable state, not from chat memory. If the task reaches a valid completed or blocked state, reminders stop. If the task is open and closeout gates are missing, reminders continue until the agent either completes the gates or records a legitimate blocked fallback.

## 3. Task Execution And Checks

During execution, the agent implements against the task record and the durable docs it references.

The agent should repeatedly ask:

- Am I still implementing the recorded task todo?
- Are the focus docs still the right source of truth?
- Did the affected components change?
- Did I introduce a new design decision?
- Did this change require docs updates?
- Do tests and checks still cover the intended behavior?

For behavioral work, the preferred implementation style is test-first or test-anchored development.

Recommended execution sequence:

1. Read durable intent sources and focus docs.
2. Record missing design questions before implementing ambiguous parts.
3. Write or update tests that express the intended behavior.
4. Implement the smallest change that satisfies the intent.
5. Run project tests.
6. Run `agentkit check` and read any lifecycle reminders it reports.
7. Run `agentkit review-guidance`.
8. Spawn or request a clean-context reviewer when review is required.
9. Fix meaningful reviewer findings.
10. Repeat review -> fix -> review until no meaningful findings remain.
11. Run `agentkit close`.

AgentKit should not allow a task to close as completed if required gates are missing.

Examples of missing gates:

- no task state from `agentkit start`
- no successful check receipt for the current diff fingerprint
- docs impact not addressed
- required review loop not acknowledged
- meaningful reviewer findings unresolved
- working tree still dirty when local policy requires commit
- blocked human question not recorded

If the main agent stops while the AgentKit task is still open, an integration may re-activate it with a reminder:

```text
AgentKit found an open task that was not closed.
Are you done, still working, or blocked waiting for human input?
Run `agentkit close` before ending the task.
```

This reminder is part of the lifecycle, not a one-off nag.

The task should continue receiving reminders until it reaches a valid closed state.

## 4. Exception Handling And Feedback

Sometimes the agent cannot complete the normal path.

Examples:

- human intent is missing
- requirements conflict
- design choices are ambiguous
- a check cannot run in the current environment
- review cannot be completed because required context is missing
- continuing would require an unsupported assumption

In these cases, the agent should not silently end the task.

The fallback path is:

1. Explain the problem.
2. Record the human question or blocker.
3. Record what work is complete.
4. Record what checks were not run and why.
5. Run `agentkit close --blocked-question "..."`.

Blocked close is a valid closed state only when it is traceable.

It must include:

- the human question
- why it blocks progress
- current task state
- open changes, if any
- the next action needed after human input

Blocked close must not create a task from scratch. The task must have been started with `agentkit start`.

If a check or review is intentionally skipped, the agent must provide a reason. That reason should be visible to the human and should be stored in the task state or related task documentation.

## 5. Close States

`agentkit close` should end in one of three states.

### `completed`

The task is complete.

Required signals:

- task was started
- checks passed for the current diff fingerprint
- docs impact was addressed
- required review loop was completed
- low-risk work that does not require review has an explicit skip reason
- no blocking human question remains
- local git policy is satisfied

If review is required but cannot be performed, the task should close as `blocked`, not `completed`.

### `needs_work`

The task cannot close yet.

Examples:

- missing task state
- missing check receipt
- missing review acknowledgement
- unresolved open changes
- docs impact still missing

The agent should continue working.

### `blocked`

The task cannot responsibly continue without human input.

Required signals:

- task was started
- human question is recorded
- blocker is explained
- current state is preserved
- next action is clear

The task should not keep nagging the agent until new human input arrives.

## 6. Hooks

AgentKit supports Git hooks and agent lifecycle hooks as separate layers.

### Git Hooks

`agentkit install-hooks` installs deterministic Git-triggered checks.

The first hook is:

```text
.git/hooks/pre-commit -> agentkit check
```

This is not a separate manual `agentkit precommit` workflow. Git is the trigger.

Git hooks should only run deterministic checks. They should not spawn reviewers or require long-running LLM judgment.

### Agent Lifecycle Hooks

Runtime integrations may provide post-agent or monitor hooks.

Those integrations can detect open AgentKit tasks and re-activate the agent if the task has not been closed.

AgentKit can determine that a reminder is needed and generate the reminder text from local task state. Delivering that reminder to a stopped agent requires a trigger, which may be an external integration or AgentKit's own lightweight local watcher.

An `agentkit watch` process is an acceptable reminder adapter. It should poll or subscribe to local AgentKit task state, emit reminders for open tasks, and stay bounded to reminder delivery. It should not become a general agent orchestrator.

Reminder behavior must be stateful:

- no open task means no reminder
- completed task means no reminder
- blocked task waits for new human input
- unchanged acknowledged warnings should not repeat forever
- changed fingerprints invalidate old receipts

`watch` should not invent its own policy. It should call the same status/reminder logic used by `check`, `status`, and `remind`.

## 7. Human Attention Policy

Human attention should be spent on judgment, not preventable hygiene.

Before asking the human for final review, the agent should have already handled:

- obvious test failures
- AgentKit check failures
- stale docs warnings
- missing review loop
- straightforward reviewer findings
- uncommitted changes when local policy expects a commit

The agent should ask the human when:

- design is missing
- product direction is unclear
- requirements conflict
- multiple architecture choices are plausible
- a decision blocks implementation
- continuing would require an unsupported assumption

AgentKit should make this pushback legitimate by letting the agent close as blocked with a recorded human question.

## 8. First MVP Interpretation

The first useful version should support the lifecycle manually through CLI commands and local files.

Minimum surfaces:

- `agentkit init`
- `agentkit start`
- `agentkit check`
- `agentkit docs-impact`
- `agentkit lint-architecture`
- `agentkit review-guidance`
- `agentkit close`
- `agentkit install-hooks`
- generated AgentKit skill
- repository-local task state
- local check and review receipts

This list is a capability checklist, not the order for a single feature task.

Repository setup capabilities such as `init`, hook installation, skill generation, docs structure, links, and rules should happen before concrete task execution whenever possible.

Concrete task capabilities such as `start`, checks, status/reminder sampling, review guidance, fallback, and `close` happen per task.

The MVP does not need a daemon or hosted control plane.

The lifecycle extension adds `agentkit status` and `agentkit remind` so agents and adapters can sample task state directly.

Post-agent reminders can be delivered by AgentKit's own lightweight `agentkit watch` adapter, ProjectMan, Symphony, editor integrations, agent runtime hooks, or other local triggers.
