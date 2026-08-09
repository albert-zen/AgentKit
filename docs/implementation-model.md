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

## Internal Architecture

The implementation follows the Association / State / Rule model in
[architecture/core-model.md](architecture/core-model.md). Command routing and
delivery stay separate from lifecycle policy:

- `cli.py` parses arguments and delegates.
- `commands.py` keeps command-level orchestration and formatted outputs.
- `policy.py` owns the finite rule/reminder schema and policy value types.
- `config.py` parses repository associations and policy against that catalog.
- `presets.py` depends on the policy catalog and materializes versioned
  recommended values without owning rule identities.
- `versions.py` names package, repository-format, preset, task-state, and
  managed-artifact version domains without coupling their advancement.
- `migrations.py` owns finite sequential repository-format planning,
  ownership/conflict detection, byte-preserving changes, and rollback.
- `task_state.py` owns the schema-versioned `TaskState` model and
  `.agentkit/tasks/*.json` reads and writes.
- `receipts.py` owns check and review receipt paths and writes.
- `rules.py` owns named `RuleResult` evaluation over associations and state.
- `lifecycle.py` renders shared evaluation results as status and reminders.
- `watch.py` owns the local reminder loop and delegates policy to `lifecycle.py`.

The evaluator is reused by `close`, `status`, `remind`, `watch`, Codex hooks,
and external adapters. Evaluation does not write state. Commands with explicit
state or evidence semantics, such as `update`, `check`, and `close`, own their
respective writes.

## Core Commands

## `agentkit init`

Create a default AgentKit setup.

Outputs:

- `AGENTS.md`
- `agentkit.yml`
- starter docs tree
- starter architecture rules
- optional AgentKit skill

When writing `AGENTS.md`, `init` should create or append a concise low-level AgentKit section. The section should introduce AgentKit as the repo-local maintainability harness and point to the command entry points plus the AgentKit plugin skill. It should not duplicate the plugin skill.

The generated section should state the default risk-based lifecycle boundary, while allowing repository-local guidance to require stricter tracking. Re-running `init` should remain idempotent and should not automatically replace an existing marked AgentKit section with newer default wording.

`init` should also guide the agent to configure the repository's maintainability system:

- docs root and durable intent locations
- component-to-doc mappings
- architecture layers and dependency rules
- maintainability budgets once module responsibilities are clear
- project-specific links and conventions
- deterministic hooks through `agentkit install-hooks`

The output should make clear that the initialized repo may still need human-agent configuration work before it is truly maintainable.

`agentkit init --preset recommended-v1` explicitly imports the recommended
lifecycle policy. It writes preset source/version metadata plus the effective
named rule and reminder values into `agentkit.yml`. Reapplying the same preset
is idempotent and preserves supported repository overrides. On an existing
config with no policy sections, materialization appends a controlled YAML block
without rewriting comments or unrelated text. Partial/conflicting policy text
is rejected with a manual migration action. Plain `agentkit init` keeps its
existing configuration shape and behavior.

New initialization writes the latest repository format and a bounded,
managed-artifact-versioned agents block. It does not upgrade an existing v1
configuration; callers use `agentkit upgrade` for that operation.

## `agentkit upgrade`

Plan and apply are separate. `upgrade --dry-run` reads all affected files,
classifies ownership, computes final bytes, validates them in memory, and
renders source/target formats, migration ids, file changes, preserved policy,
conflicts, and next action. It does not call a receipt-writing check.

Apply first verifies that every source byte sequence still matches its plan,
then atomically replaces individual files. Originals remain available until
post-write configuration and managed-block validation succeeds; failure
restores every attempted file and each replacement preserves the original file
mode. Receipt-free manifest, architecture, and failing maintainability checks
run before and after application. Format v1 remains readable. Format v2 is the
current initialization target. Unknown future formats fail without downgrade.

The v1-to-v2 migration uses a controlled scalar edit rather than YAML
serialization. It preserves comments, unknown fields, order, formatting, and
policy values. Only byte-exact shipped legacy agent sections are automatically
bounded. Task schema v1 and receipts are independent and untouched.

## `agentkit doctor`

Audit repository readiness without changing files.

Outputs:

- readiness status
- ready checks
- recommended actions for missing required surfaces
- optional improvements for project-policy surfaces such as hooks or architecture layers

The first implementation should check for AgentKit entry guidance in `AGENTS.md` or `agents.md`, `agentkit.yml`, valid manifest references, component mappings, docs, the AgentKit plugin skill, and optional Git hooks.

`doctor` may recommend maintainability budgets when none are configured, but an empty budget list should not be treated as an invalid repo. Budgets are most useful after humans and agents understand the repository's module responsibilities well enough to set meaningful limits.

Doctor also performs read-only repository-format diagnosis and reports
`up_to_date`, `upgrade_available`, or `blocked` beside current/latest versions.

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
- focus docs and focus notes
- affected components
- likely code areas
- suggested checks
- review expectation
- design gaps

Side effect:

- writes a repository-local task state file under `.agentkit/tasks/`

`start` should reuse the same component and docs analysis as `orient`, but it persists enough state for `close` to evaluate whether the task was responsibly finished.

The lifecycle should be scoped by risk. Agents should run `start` for substantial changes affecting architecture, public behavior, state or data models, security boundaries, cross-component workflows, hooks or plugins, or otherwise needing durable design and review context. They should not start a task for read-only codebase orientation, lightweight audits, or answering questions without edits.

Small, self-contained, low-risk edits may skip the lifecycle when ownership is obvious and verification is focused. If skipped work expands beyond its stated boundary, the agent should start or resume a task before continuing. Repository-local policy may require a stricter boundary, including lifecycle tracking for every write.

The agent may run `start` after a design discussion, or run it earlier and later update the task context once the human-agent discussion clarifies the focus.

The current task state should preserve `focus_notes` and `focus_docs` so another agent can recover the task's human-approved emphasis without reading the original chat.

Task JSON uses schema version 1. Unversioned task files remain readable as v1
and receive the version marker on their next AgentKit write. Persisted task
facts do not store recomputable `needs_work` or `ready_to_close` conclusions.

## `agentkit update`

Change the explicit context of an existing task without re-running start-time
orientation or resetting unrelated state.

Supported operations:

- `--set-task` and `--set-plan` replace scalar context;
- `--add-focus-note` / `--remove-focus-note`;
- `--add-focus-doc` / `--remove-focus-doc`;
- `--add-component` / `--remove-component`.

Adds are duplicate-safe and removals are safe when already absent. Update does
not alter task lifecycle status, fingerprints, check receipts, review
acknowledgements, or unsupported arbitrary JSON fields. Terminal tasks are not
implicitly reopened.

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
- maintainability budget checks
- optional project commands

This should be the command agents run before review.

Maintainability budgets are repo-local reminders, not a replacement for formatters or language linters. Projects can configure file-level limits such as `max_lines`, `max_functions`, and `max_classes` in `agentkit.yml`; warning budgets surface pressure to split modules, while failing budgets can enforce hard boundaries when the project is ready.

An empty `maintainability.budgets` list means there are no budget checks to run. `check` should not nag about missing budgets; readiness nudges belong in `init` and `doctor`.

When budgets are configured and passing, `check` should summarize them with a compact count instead of listing every matched file. Detailed inventory belongs in `agentkit lint-maintainability`; `check` should expand maintainability output only for warnings or failures that need action.

`check` should stay safe for Git hooks: it must remain deterministic and must not spawn reviewers or require long-running LLM judgment. It may include a lifecycle reminder section derived from `.agentkit/` task state, so an agent that only remembers to run `check` still sees missing closeout gates.

`check` remains useful when no lifecycle task is open: it runs the same deterministic repository checks, may write its normal diff-keyed check receipt, and reports that no task is open. It should not create an implicit task or alternate lifecycle mode. This existing behavior is sufficient for focused verification of a qualifying small edit.

`check` should not be the only owner of reminder logic. The underlying status/reminder engine should be callable by `status`, `remind`, `watch`, and external adapters.

## `agentkit close`

Close the current AgentKit task.

Inputs:

- task id, optional if there is only one open task
- blocked question, optional
- skip reason for low-risk work where review is intentionally skipped, optional
- validation summary, optional
- review-complete flag, optional after the review loop has completed

Checks:

- current diff fingerprint
- whether `agentkit check` has run for that fingerprint
- docs-impact analysis is included in `check`, but is not represented as an
  independently satisfied receipt in this version
- whether review is required
- whether the implementing agent acknowledged the required review loop for the
  current fingerprint (AgentKit does not store reviewer transcripts/findings)
- whether git status is clean or local policy allows uncommitted work
- whether blocked human questions are recorded

Outputs:

- `completed`
- `blocked`
- `needs_work`

`blocked` requires a recorded human question. It is not a silent escape hatch; it is a traceable handoff state for work that cannot responsibly continue without new human input.

Blocked close requires an existing task state from `agentkit start`. It may record open changes as part of the handoff, but it should not create a task from scratch.

The close command should not create an infinite loop. It should use receipts keyed by a diff fingerprint. If the diff has not changed, AgentKit should not repeat identical warnings after they have been acknowledged. If the diff changes, relevant check and review receipts become stale.

The MVP receipt model starts with check receipts written by successful `agentkit check` runs. Review completion begins as an explicit close-time acknowledgement such as `agentkit close --review-complete`. Check and review acknowledgements must be keyed to the current diff fingerprint so they cannot be reused after later commits or edits.

AgentKit should not require storing reviewer transcripts, multi-pass review logs, or reviewer findings as first-class state. The main agent owns the review loop and is responsible for fixing meaningful findings. If a finding, decision, or unresolved issue is important for future maintainability, the agent should record it in the repository documentation system rather than in an AgentKit-specific review database.

Future versions may improve the review acknowledgement shape, but the product should stay lightweight: AgentKit reminds, gates, and records that review was completed for the current fingerprint; the repo docs carry durable design or risk knowledge.

## `agentkit status` / `agentkit remind`

AgentKit should expose task status and reminder generation as explicit commands backed by the same state sampler that `check` and `watch` use.

Potential outputs:

- open task ids
- close state
- missing gates
- stale receipts
- blocked human questions
- reminder text for runtime adapters

`status` is the facts view. It should be useful for humans, agents, and machine integrations that need to inspect the current lifecycle state.

`remind` is the action view. It should turn the same facts into next-step instructions, such as:

```text
Current task is open.
Missing gates:
- run agentkit check for the current diff
- complete the required review loop
- commit or record a blocked handoff

Next action:
Run the missing gate, or close as blocked with a recorded human question if progress is impossible.
```

These commands let AgentKit own reminder logic while allowing AgentKit's own watcher, ProjectMan, Symphony, editor integrations, OS schedulers, or agent runtimes to own delivery.

## `agentkit watch`

AgentKit provides a lightweight local watcher as a first-party reminder delivery adapter.

Responsibilities:

- read `.agentkit/` task state
- detect open tasks that are not `completed` or traceably `blocked`
- detect stale receipts and missing close gates
- generate or emit reminder messages
- optionally call configured local notification commands

Non-responsibilities:

- spawn coding agents
- manage job queues
- replace ProjectMan or Symphony
- perform semantic LLM review

`watch` should reuse the same status/reminder logic exposed by `status` or `remind`, so delivery remains separate from truth.

`watch` should keep reminding while a task is open and required gates are missing. Once `close` records `completed` or a traceable `blocked` state, the watcher should stop reminding for that task until new human input or changed task state makes it active again.

## `agentkit install-codex-watchdog`

Install Codex lifecycle hook wiring for AgentKit closeout reminders.

Outputs:

- installed scope
- written or updated files
- next verification instruction

Repo-local installation should write `<repo>/.codex/hooks.json` and `<repo>/.codex/config.toml`. User-local installation should write to `CODEX_HOME` when set, otherwise `~/.codex`. The installer should preserve unrelated hooks and config settings, append or update only the AgentKit Stop hook, and ensure `features.codex_hooks = true`.

The Stop hook command should call `agentkit codex-stop-hook --log ".agentkit/codex-stop-hook.log"` by default. The log is a diagnostic receipt: if an end-to-end Codex run stops without continuation and no log appears, Codex never invoked the hook.

The first successful Codex smoke test used a clean temporary repository with a committed AgentKit baseline. Codex initially answered the user's prompt, the Stop hook logged `needs_work`, Codex continued the turn with the AgentKit reminder, the agent ran `agentkit check`, then `agentkit close`, and a later Stop hook logged `completed`. A failed earlier smoke test wrote Codex JSONL output inside the repo, which changed the diff every continuation and made blocked state stale; future smoke tests should keep runner output outside the repo or ignore it.

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

Use a separate Clean Context Sub-Agent Reviewer and ask it to:
1. Treat the durable intent sources above as the source of truth.
2. Treat any inline summary as convenience context only.
3. Review these changed files:
   - src/projectman/services/orchestration.py
   - src/projectman/api/routes/orchestration.py
   - web/src/views/agent-board.tsx
4. Compare the implementation against the docs and original task.
5. Report intent drift, missing tests, stale docs, and architecture violations.
```

AgentKit should not need to spawn the reviewer in the MVP. It tells the main
agent how to do it. Same-thread self-review does not count as review complete;
when subagents are unavailable, the main agent should not mark review complete
based on its own same-thread self-review.

## `agentkit skill`

Generate or update a repository-local AgentKit skill.

The skill should teach agents using AgentKit in the current repository:

- how to run AgentKit commands
- where docs live
- how components map to docs
- when to ask for design
- when to request review guidance
- what the local architecture rules mean

This is one of the main ways AgentKit gives value to agents without building a large platform.

The AgentKit skill is an operating guide, not a developer design doc. It should live in the AgentKit Codex plugin by default, contain enough task protocol for a capable agent to use AgentKit well, and link out to durable docs for product philosophy, component details, and long-term roadmap.

## Configuration Model

First draft of `agentkit.yml`:

```yaml
version: 2

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
  source: plugins/agentkit/skills/agentkit/SKILL.md
  output: plugins/agentkit/skills/agentkit/SKILL.md

preset:
  source: agentkit
  name: recommended-v1
  version: 1

rules:
  working_tree_clean:
    enabled: true
    severity: error
  check_receipt_current:
    enabled: true
    severity: error
  review_addressed:
    enabled: true
    severity: error
    allow_skip: true
  blocked_question_recorded:
    enabled: true
    severity: error

reminders:
  open_task: true
  ready_to_close: true
  stale_terminal: true
```

These are finite named settings, not a workflow DSL. Unknown presets, rules,
options, and unsupported values fail configuration loading. Older configs with
no `preset`, `rules`, or `reminders` section retain the compatibility policy in
memory.

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
5. Generate `plugins/agentkit/skills/agentkit/SKILL.md` and expose it through `.agents/plugins/marketplace.json`.

Concrete task:

1. Run `agentkit start --task "<task todo>"` to persist task context and durable intent sources.
2. Run `agentkit orient --path <changed path>` or `agentkit orient --component orchestration`.
3. Run `agentkit intent-guidance --component orchestration --change-type orchestration`.
4. Run `agentkit docs-impact`.
5. Run `agentkit lint-architecture` for Python imports.
6. Run `agentkit review-guidance`.
7. Run `agentkit close` to verify closeout or record a blocked human question.

If this works for ProjectMan's Symphony integration, AgentKit has proven its first useful value.
