# Guidance Component Design

## Purpose

The guidance component gives the implementing agent practical next steps:

- what components are affected
- what docs to read
- whether design docs are missing
- where intent should be recorded
- whether docs may be stale
- what review guidance should be used
- how to start and close a task responsibly
- how to learn the using-AgentKit operating loop from the AgentKit plugin skill

## Owned Concepts

- component discovery
- docs recommendation
- design gap reporting
- docs-impact assessment
- maintainability budget reporting
- review guidance
- architecture lint orchestration
- task lifecycle guidance
- closeout requirements
- hook and reminder guidance
- reminder state and reminder text generation
- named, explainable lifecycle rule results

## Boundary

Guidance should not replace semantic reasoning by the LLM. It should route, remind, template, and check.

Generated guidance should distinguish two audiences:

- agents using AgentKit need a concise operating protocol through the AgentKit plugin skill
- agents developing AgentKit need the durable product and component docs

The AgentKit skill should therefore explain how AgentKit helps the current task, when to run commands, when to ask for human design, and how to handle review and closeout. For Codex, that skill should be bundled through the AgentKit plugin rather than treated as a private `.codex` file. It should point to deeper docs instead of restating the full product roadmap.

Root agent guidance is even smaller than the skill. The AgentKit section in `AGENTS.md` should introduce AgentKit as the maintainability harness, point to the CLI and plugin skill, and set a concise risk-based lifecycle boundary. Substantial changes affecting architecture, public behavior, state or data models, security boundaries, cross-component workflows, hooks or plugins, or otherwise needing durable design and review context should use the full lifecycle. Small, self-contained, low-risk changes may skip it when ownership is obvious and verification is focused. Read-only exploration, codebase orientation, and answering questions without edits do not need a lifecycle task.

The guidance should say that skipped work must start or resume a task before continuing if it expands beyond its stated boundary. It should also preserve repository authority: local policy may require lifecycle tracking for every write. Updating AgentKit's default template must not rewrite an existing repository's AgentKit section automatically.

The skill should also explain command side effects and common ambiguity points:

- `agentkit start` writes task state
- lifecycle tasks are required for substantial changes, not every repository write
- small changes may skip only when they are self-contained, low risk, clearly owned, and have focused verification
- skipped work that expands must start or resume a task before continuing
- repository-local policy may require a stricter lifecycle boundary
- `agentkit status` and `agentkit remind` are safe status/reminder reads
- `agentkit check` remains useful without an open task because deterministic checks do not require an implicit lifecycle mode
- `agentkit lint-maintainability` checks repo-local module size and responsibility budgets
- common `intent-guidance` change types
- docs-only wording tasks usually do not need new product design unless they change meaning or command semantics
- review completion is an acknowledgement, not transcript storage

## Task Lifecycle Guidance

The guidance component should support `agentkit start` and `agentkit close`.

`init` should guide the agent to finish repository maintainability setup, not merely create files. It should point agents toward docs structure, component mappings, architecture rules, local skills, hooks, and project-specific configuration.

It should also mention maintainability budgets as a later configuration step. New repositories often do not yet know which modules deserve strict limits, so the prompt should frame budgets as something to add once component responsibilities become clear.

`start` should persist the task's initial durable context:

- task todo
- intent source docs
- docs to keep in working memory
- task focus notes from human-agent discussion
- affected components and likely code areas
- expected checks
- review expectation
- design gaps and blocked questions

Command output should frame that context as part of the repository's intent file system, not only as lifecycle ceremony. `start`, `orient`, `docs-impact`, review guidance, and lifecycle reminders should use concise, gentle language that combines three ideas in one place:

- preserve what humans have already decided
- persist what future agents need to know in docs or tests
- ask the human when a durable product, architecture, API, workflow, or taste decision is missing

The task may be started after human-agent discussion, or started early and refined once the discussion clarifies the focus.

Later refinement uses `agentkit update`; repeating `start` is no longer the
recommended update path. Update changes only explicitly selected context and
cannot write derived readiness or validation evidence.

`close` should verify that the task has either completed responsibly or stopped at a recorded human decision point.

Closeout should avoid noisy loops by using state:

- diff fingerprints invalidate stale check or review receipts
- successful `agentkit check` writes a check receipt for the current fingerprint
- `agentkit close` requires that check receipt before completing
- review-required tasks need an explicit review-complete signal
- skip reasons are valid as an explicit low-risk fallback for the current diff fingerprint
- unchanged diffs should not repeat identical acknowledged warnings forever
- blocked tasks with recorded human questions should wait for new input

Fallback handling is part of the intent-file workflow, not a separate ceremony. If checks, review, or implementation cannot proceed because a durable decision is ambiguous or missing, the agent should keep going only on clear parts, record the blocker, ask the human for the missing intent, and use `agentkit close --blocked-question "..."` when the uncertainty prevents responsible progress.

Reminder guidance should distinguish state from delivery. AgentKit owns the open-task state, missing-gate detection, stale-receipt detection, and reminder text. Delivery can come from runtime adapters such as ProjectMan, Symphony, editor integrations, schedulers, or agent hooks, and it can also come from an AgentKit-owned local `agentkit watch` process.

`agentkit watch` should be treated as a first-party reminder adapter, not a new orchestration layer. It may poll local task state, emit reminder text, and call configured local notification commands. It should not spawn coding agents, manage queues, or perform semantic review.

For Codex, reminder delivery that continues a stopped turn should use explicit Codex hook configuration. The AgentKit plugin teaches the workflow, but `agentkit install-codex-watchdog` installs the Stop hook in `.codex/hooks.json` and enables `features.codex_hooks` in `.codex/config.toml`. This keeps skill distribution separate from runtime continuation wiring.

The guidance component should provide a shared lifecycle sampler:

- read task state
- compare task state with the current diff fingerprint
- inspect check and review receipts
- evaluate whether the task is open, completed, needs work, or blocked
- produce missing gates
- produce agent-facing reminder text

The sampler exposes the named rule id, outcome, reason, next action, and
blocking/advisory policy. `close` consumes the same evaluation instead of
maintaining a second gate sequence.

`agentkit check`, `agentkit status`, `agentkit remind`, `agentkit watch`, and external adapters should all use this same sampler. `check` can show reminder output for convenience, but it should not become the only place reminder policy lives.

Risk-based task entry does not change lifecycle state or receipt semantics. When no task is open, `check` should still run deterministic repository checks and may write its normal check receipt; the lifecycle reminder should remain quiet and no implicit task should be created. Once a task is started, the existing check, review, fingerprint, reminder, and closeout gates apply unchanged.

Current implementation modules:

- `templates.py` owns default AgentKit setup text, skill text, and Codex plugin templates.
- `architecture.py` owns Python import graph checks for configured dependency layers.
- `codex.py` owns Codex watchdog installation and Stop-hook adapter behavior.
- `task_state.py` reads and writes task state.
- `receipts.py` reads and writes receipt files.
- `maintainability.py` evaluates configured module size and responsibility budgets.
- `rules.py` evaluates task state, receipts, fingerprints, named rule results,
  and derived lifecycle readiness.
- `lifecycle.py` renders shared evaluation results as status and reminder text.
- `watch.py` delivers reminder text in a local loop.
- `versions.py` keeps independent version domains explicit.
- `migrations.py` plans and applies finite repository-envelope migrations;
  policy evaluation and task evidence remain outside it.

Repository upgrade follows the same durable-intent principle as lifecycle
guidance: preserve local policy, report unsupported ambiguity, and provide a
specific next action. New bounded agents blocks allow future managed guidance
to be identified without treating the rest of `AGENTS.md` as AgentKit-owned.

Task context now has an explicit schema-v1 model and domain-level update
operations for task/plan, focus notes/docs, and components. Planned-check,
changed-scope, or history features need separate demonstrated requirements;
they should not be approximated with arbitrary patching.

## Hook Guidance

`install-hooks` should install Git-native hooks for deterministic checks.

The first hook is `pre-commit`, which should run `agentkit check`. AgentKit should not require agents to manually remember a separate pre-commit command, and hooks should not perform long-running LLM review.
