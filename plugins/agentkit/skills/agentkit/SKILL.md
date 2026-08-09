---
name: agentkit
description: Preserve human intent and project maintainability by guiding agents to read durable intent files and persist meaningful design, docs, and test changes.
---

# AgentKit Skill

This repository uses AgentKit.

## What AgentKit Gives You

AgentKit keeps your work tied to durable repo intent. Use it to:

- find the docs and components relevant to a task
- remember the task's closeout gates
- check docs impact and architecture rules
- get lifecycle reminders while you work
- ask for clean-context review before human attention
- close the task as completed or blocked

The skill is an operating guide. For deeper product or architecture intent, read the durable docs that AgentKit returns.

## When To Start A Task

Use the AgentKit task lifecycle for substantial changes that affect architecture, public behavior, state or data models, security boundaries, cross-component workflows, hooks or plugins, or otherwise need durable design and review context.

Do not start a task for read-only exploration, codebase orientation, answering architecture questions, or lightweight audits with no edits. Read the relevant docs directly and use `agentkit status` or `agentkit remind` only if you need to inspect an already-open task.

Small, self-contained, low-risk edits may also skip the lifecycle when ownership is obvious and verification is focused. Examples include:

- a local launcher fallback
- test-only maintenance
- narrowly scoped wording that does not change product meaning
- a similarly reversible, one-owner fix

If skipped work expands beyond its stated boundary, start or resume an AgentKit task before continuing so the lifecycle gates apply to the expanded change.

Repository-local policy may be stricter and require the lifecycle for every write. Follow the repository's `AGENTS.md` and other local instructions when they set a stricter boundary.

## Lifecycle Operating Loop

1. Start or resume the task with `agentkit start`.
2. Read the durable intent sources in the output.
3. Refine task context with `agentkit update` when later discussion changes the task, plan, focus, or components.
4. If design is missing or ambiguous for product behavior, API, data model, workflow, architecture, or state transitions, ask the human before implementing that part.
5. Implement against tests and the repo's architecture rules.
6. Run `agentkit check` and read any lifecycle reminder it prints.
7. Run `agentkit review-guidance` and request clean-context review when expected.
8. Fix meaningful reviewer findings.
9. Run `agentkit close --review-complete`, or close as blocked with a recorded human question.

## Start Of Task

For substantial repository-changing work, run:

```text
agentkit start
```

`start` writes repository-local task state under `.agentkit/`. Do not run it for read-only work or a qualifying small edit unless local policy requires tracking. If untracked work grows into a substantial change, run `start` or resume the task before continuing.

If you know the component, run:

```text
agentkit start --component <name>
```

After discussion clarifies an already-started task, preserve the refined
context without resetting start-time state:

```text
agentkit update --set-task "<refined task>" --set-plan "<plan>" \
  --add-focus-note "<human-approved focus>" --add-focus-doc <path>
```

`update` supports set semantics for task/plan and duplicate-safe add/remove
semantics for focus notes, focus docs, and components. It cannot update
lifecycle status, fingerprints, or validation evidence.

Use `agentkit start --component <name>` when you already know the component. Otherwise, include the task text and let AgentKit infer affected components.

## Init, Preset, And Upgrade

These operations have different ownership boundaries:

- `agentkit init` adopts AgentKit and creates the latest repository format.
- `agentkit init --preset recommended-v1` explicitly imports a policy; it may
  change policy because the user selected it.
- `agentkit upgrade --dry-run` plans structural migration for an existing
  AgentKit repository without writing repository files or receipts.
- `agentkit upgrade` applies only the proven AgentKit-managed envelope changes
  in that plan. It preserves repository policy, configuration content, task
  state, and receipts.

Review every reported conflict. If AgentKit cannot prove that a customized or
ambiguous artifact is managed and losslessly replaceable, it intentionally
writes nothing; do not work around that result by rerunning init or selecting a
preset.

## During Design

Use:

```text
agentkit intent-guidance --component <name> --change-type <type>
```

Write the actual design content yourself. AgentKit tells you where it belongs.

Useful change-type values include `architecture`, `data_model`, `public_api`, `orchestration`, `workflow`, `tests`, and `docs`.

For docs-only wording tasks, ask the human for design only when the wording changes product meaning, command semantics, public behavior, workflow expectations, or accepted terminology. For local copyedits that preserve meaning, proceed with focused docs checks and review expectations from AgentKit.

## Before Review

Run:

```text
agentkit check
agentkit review-guidance
```

If review is expected, use a separate Clean Context Sub-Agent Reviewer with the guidance AgentKit returns when subagents are available. Same-thread self-review does not count as review complete. If subagents are not available, use the low-risk skip-review path only when appropriate.

Do not treat review as a transcript storage task. AgentKit only needs the main agent to acknowledge that the review loop was completed for the current diff. If review reveals durable design, risk, or testing knowledge, record that in the repository docs.

For low-risk docs-only wording changes, review may still be expected by local policy. Use `agentkit review-guidance` to decide. If the change is truly low risk, close with `agentkit close --skip-review-reason "..."` only when AgentKit allows it.

## Lifecycle Reminders

Use:

```text
agentkit status
agentkit remind
```

`status` shows task facts and missing gates. `remind` shows the next action. `agentkit check` may also include lifecycle reminders.

`agentkit check` remains useful without an open lifecycle task: it runs the repository's deterministic checks and reports that no task is open without creating an implicit task. This is sufficient for focused verification of a qualifying small edit; use additional project tests appropriate to the change.

For a local reminder loop, use:

```text
agentkit watch
```

For Codex Stop-hook reminders, install explicit hook wiring:

```text
agentkit install-codex-watchdog --repo-local
```

If a Stop hook does not appear to run, check `.agentkit/codex-stop-hook.log`. No log usually means Codex did not invoke the hook.

## Close Task

Before ending the task, run:

```text
agentkit close --review-complete
```

If blocked on human input, run:

```text
agentkit close --blocked-question "..."
```

Use blocked close when continuing would require an unsupported assumption. Include the human question clearly.
