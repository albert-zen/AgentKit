# AgentKit Implementation Model

Status: Draft

## Purpose

This document describes how AgentKit should provide concrete help to an implementing agent.

AgentKit is not trying to out-reason the LLM. It provides repository-local structure, routing, reminders, templates, and deterministic checks. The LLM agent still performs semantic understanding, design writing, implementation, and judgment.

## Product Shape

AgentKit should start as a CLI-first tool with a repository-local configuration file.

Primary interface:

```text
agentkit <command>
```

Primary configuration:

```text
agentkit.yml
```

Primary consumers:

- implementing agents
- reviewer agents
- humans configuring a repository

The output should be optimized for agents: clear, structured, copyable, and action-oriented.

## Core Commands

## `agentkit init`

Create a default AgentKit setup.

Outputs:

- `AGENTS.md`
- `agentkit.yml`
- starter docs tree
- starter architecture rules
- optional AgentKit skill

`init` should also guide the agent to configure the repository's maintainability system:

- docs root and durable intent locations
- component-to-doc mappings
- architecture layers and dependency rules
- project-specific links and conventions
- deterministic hooks through `agentkit install-hooks`

The output should make clear that the initialized repo may still need human-agent configuration work before it is truly maintainable.

## `agentkit start`

Start or resume an AgentKit task.

Inputs:

- task todo or task statement
- explicit component, optional
- known durable intent docs, optional
- focus docs or focus notes, optional
- expected changed paths, optional
- implementation plan text, optional

Outputs:

- task id
- durable intent source paths
- docs to keep in working memory
- affected components
- likely code areas
- suggested checks
- review expectation
- design gaps

Side effect:

- writes a repository-local task state file under `.agentkit/tasks/`

`start` should reuse the same component and docs analysis as `orient`, but it persists enough state for `close` to evaluate whether the task was responsibly finished.

The agent may run `start` after a design discussion, or run it earlier and later update the task context once the human-agent discussion clarifies the focus.

## `agentkit orient`

Help an agent start or continue a task.

Inputs:

- task text, optional
- changed paths, optional
- explicit component, optional
- git diff, optional

Outputs:

- likely affected components
- docs to read first
- missing design docs
- likely design impact
- suggested test areas
- relevant architecture rules
- whether the task likely needs human design confirmation

Example output:

```text
Likely affected components:
- orchestration
- frontend-board

Read first:
- docs/design.md
- docs/components/orchestration/design.md
- docs/components/orchestration/agent-run-lifecycle.md
- docs/architecture/dependency-rules.md

Design gap:
- No docs/components/orchestration/symphony-agent-spawn.md found.
  If this task changes run lifecycle or spawn semantics, ask the human to approve a design first.

Suggested tests:
- API creates agent run for valid issue
- invalid issue returns 404
- run status transitions reject invalid moves
- board groups runs by status
```

This is the command that provides the "what should I read and think about?" support.

## `agentkit intent-guidance`

Tell the agent where human-approved intent should be recorded.

AgentKit does not write the intent for the agent. It suggests placement and templates.

Inputs:

- task text
- affected component
- change type
- optional design summary

Outputs:

- target docs
- missing docs to create
- required headings
- ADR recommendation if the decision is cross-cutting
- testing doc recommendation

Example output:

```text
Record durable intent in:
- docs/components/orchestration/design.md

Create if approved:
- docs/components/orchestration/symphony-compatibility.md
- docs/components/orchestration/agent-run-lifecycle.md

Add tests section to:
- docs/components/orchestration/testing.md

ADR recommended:
- This introduces ProjectMan as a tracker/context source for Symphony-style execution.
```

This command replaces the ambiguous idea that AgentKit should "capture intent." The LLM captures and writes. AgentKit routes and constrains.

## `agentkit docs-impact`

Inspect changed paths and report likely affected docs.

Inputs:

- git diff by default
- optional explicit paths

Outputs:

- changed components
- docs likely affected
- docs changed
- missing docs-impact assessment

AgentKit should allow the implementing agent to record:

```text
Docs checked: no update needed because this change only refactors private helper names.
```

The first version can simply print guidance. Later versions can enforce a conventional note in the final response, commit message, or a local task file.

## `agentkit lint-architecture`

Check configured dependency rules.

AgentKit should support default starter rules, but the project owns its architecture.

Input comes from `agentkit.yml`:

```yaml
layers:
  domain:
    paths:
      - src/projectman/domain/**
    may_import: []
  repositories:
    paths:
      - src/projectman/repositories/**
    may_import:
      - domain
      - db
  services:
    paths:
      - src/projectman/services/**
    may_import:
      - domain
      - repositories
      - schemas
  api:
    paths:
      - src/projectman/api/**
    may_import:
      - services
      - schemas
```

The early implementation can focus on Python import checks because they are easy to implement deterministically for ProjectMan-like repositories.

Deterministic check adapters for additional languages are not about helping the LLM understand those languages. The LLM can already read many languages. These adapters only matter for checks that AgentKit itself runs, such as import graph analysis.

## `agentkit check`

Run configured checks:

- manifest validation
- docs existence
- docs-impact warning
- architecture lint
- optional project commands

This should be the command agents run before review.

## `agentkit close`

Close the current AgentKit task.

Inputs:

- task id, optional if there is only one open task
- blocked question, optional
- skip reason for low-risk work where review is not required, optional
- validation summary, optional
- review-complete flag, optional after the review loop has completed

Checks:

- current diff fingerprint
- whether `agentkit check` has run for that fingerprint
- whether docs impact was addressed
- whether review is required
- whether review -> fix -> review receipts exist when required
- whether meaningful review findings remain
- whether git status is clean or local policy allows uncommitted work
- whether blocked human questions are recorded

Outputs:

- `completed`
- `blocked`
- `needs_work`

`blocked` requires a recorded human question. It is not a silent escape hatch; it is a traceable handoff state for work that cannot responsibly continue without new human input.

Blocked close requires an existing task state from `agentkit start`. It may record open changes as part of the handoff, but it should not create a task from scratch.

The close command should not create an infinite loop. It should use receipts keyed by a diff fingerprint. If the diff has not changed, AgentKit should not repeat identical warnings after they have been acknowledged. If the diff changes, relevant check and review receipts become stale.

The MVP receipt model starts with check receipts written by successful `agentkit check` runs. Review receipts may begin as an explicit close-time assertion such as `agentkit close --review-complete`, with richer reviewer-result parsing added later. Check and review acknowledgements must be keyed to the current diff fingerprint so they cannot be reused after later commits or edits.

## Future `agentkit status` / `agentkit remind`

AgentKit should eventually expose task status and reminder generation as explicit commands.

Potential outputs:

- open task ids
- close state
- missing gates
- stale receipts
- blocked human questions
- reminder text for runtime adapters

These commands would let AgentKit own reminder logic while allowing ProjectMan, Symphony, editor integrations, OS schedulers, or agent runtimes to own delivery.

## `agentkit install-hooks`

Install repository-local hooks.

Initial hook:

- `.git/hooks/pre-commit` runs `agentkit check`

This should be a normal Git hook, not a separate manual command agents must remember. The purpose is to catch deterministic issues at the Git boundary.

AgentKit should not use pre-commit hooks for long-running LLM review, sub-agent spawning, or semantic judgment.

Hook installation should resolve the hook path through Git, so linked worktrees and non-standard Git directories are handled correctly.

## `agentkit review-guidance`

Tell the implementing agent how to request clean-context review.

Outputs:

- whether review is expected
- durable intent source paths
- docs reviewer should read
- changed files reviewer should inspect
- focus areas
- spawn/request instruction template

Example output:

```text
Review expected: yes, because this changes orchestration and API behavior.

Durable intent sources:
- docs/design.md
- docs/components/orchestration/design.md
- docs/components/orchestration/agent-run-lifecycle.md

Spawn a clean-context reviewer and ask it to:
1. Treat the durable intent sources above as the source of truth.
2. Treat any inline summary as convenience context only.
3. Review these changed files:
   - src/projectman/services/orchestration.py
   - src/projectman/api/routes/orchestration.py
   - web/src/views/agent-board.tsx
4. Compare the implementation against the docs and original task.
5. Report intent drift, missing tests, stale docs, and architecture violations.
```

AgentKit should not need to spawn the reviewer in the MVP. It tells the main agent how to do it.

## `agentkit skill`

Generate or update a repository-local AgentKit skill.

The skill should teach agents:

- how to run AgentKit commands
- where docs live
- how components map to docs
- when to ask for design
- when to request review guidance
- what the local architecture rules mean

This is one of the main ways AgentKit gives value to agents without building a large platform.

## Configuration Model

First draft of `agentkit.yml`:

```yaml
version: 1

docs:
  root: docs
  design: docs/design.md
  workflow: docs/workflow.md
  decisions: docs/decisions

components:
  orchestration:
    description: Agent execution, Symphony compatibility, run lifecycle.
    code:
      - src/projectman/services/orchestration.py
      - src/projectman/api/routes/orchestration.py
      - src/projectman/models.py
      - web/src/views/agent-board.tsx
    docs:
      - docs/components/orchestration/design.md
      - docs/components/orchestration/agent-run-lifecycle.md
      - docs/components/orchestration/testing.md
    required_docs:
      - design
      - testing

layers:
  services:
    paths:
      - src/projectman/services/**
    may_import:
      - domain
      - repositories
      - schemas
  api:
    paths:
      - src/projectman/api/**
    may_import:
      - services
      - schemas

review:
  require_for:
    - public_api
    - data_model
    - architecture
    - orchestration
  default: warn

skills:
  output: .codex/skills/agentkit/SKILL.md
```

## How The Three Key Supports Work

### 1. Tell The Agent What Factors Affect Which Areas

Mechanism:

- map paths to components through `agentkit.yml`
- inspect task text and changed paths
- match keywords and path patterns
- return affected docs, code areas, rules, and tests

Early version:

- path-based and explicit component-based

Later version:

- optionally LLM-assisted semantic matching, but only as guidance

### 2. Decide Whether Design Is Missing

Mechanism:

- each component declares required docs
- certain change types require certain docs
- if missing, AgentKit prints a design gap warning

Example:

```text
Change type "orchestration" requires:
- component design doc
- lifecycle doc
- testing doc

Missing:
- docs/components/orchestration/agent-run-lifecycle.md
```

AgentKit does not decide the design. It tells the agent that the design surface is missing.

### 3. Put Human Intent In The Right Place

Mechanism:

- component docs mapping
- templates
- ADR triggers
- testing-doc triggers

Example:

```text
This is component-local behavior.
Record it in:
- docs/components/orchestration/design.md

This changes a cross-cutting dependency boundary.
Also create an ADR under:
- docs/decisions/
```

The agent writes the content. AgentKit routes it.

## What AgentKit Should Not Do Early

- It should not try to fully understand or summarize every conversation.
- It should not pretend to judge documentation quality.
- It should not build a dashboard as a core product.
- It should not own agent spawning in the MVP.
- It should not enforce one universal architecture.
- It should not block small changes with heavy process.

## Concrete MVP Slice

The first implementation should be able to initialize a repository for maintainability and then run one real feature through start, execution, review, fallback, and close.

Minimum slice:

Repository setup:

1. Run `agentkit init` to scaffold and guide maintainability setup.
2. Configure `agentkit.yml`.
3. Validate component docs and code paths.
4. Run `agentkit install-hooks` to install deterministic Git checks.
5. Generate `.codex/skills/agentkit/SKILL.md`.

Concrete task:

1. Run `agentkit start --task "<task todo>"` to persist task context and durable intent sources.
2. Run `agentkit orient --path <changed path>` or `agentkit orient --component orchestration`.
3. Run `agentkit intent-guidance --component orchestration --change-type orchestration`.
4. Run `agentkit docs-impact`.
5. Run `agentkit lint-architecture` for Python imports.
6. Run `agentkit review-guidance`.
7. Run `agentkit close` to verify closeout or record a blocked human question.

If this works for ProjectMan's Symphony integration, AgentKit has proven its first useful value.
