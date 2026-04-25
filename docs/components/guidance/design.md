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
- review guidance
- architecture lint orchestration
- task lifecycle guidance
- closeout requirements
- hook and reminder guidance
- reminder state and reminder text generation

## Boundary

Guidance should not replace semantic reasoning by the LLM. It should route, remind, template, and check.

Generated guidance should distinguish two audiences:

- agents using AgentKit need a concise operating protocol through the AgentKit plugin skill
- agents developing AgentKit need the durable product and component docs

The AgentKit skill should therefore explain how AgentKit helps the current task, when to run commands, when to ask for human design, and how to handle review and closeout. For Codex, that skill should be bundled through the AgentKit plugin rather than treated as a private `.codex` file. It should point to deeper docs instead of restating the full product roadmap.

Root agent guidance is even smaller than the skill. The AgentKit section in `AGENTS.md` should only introduce AgentKit as the maintainability harness and point to the CLI and plugin skill.

The skill should also explain command side effects and common ambiguity points:

- `agentkit start` writes task state
- `agentkit status` and `agentkit remind` are safe status/reminder reads
- common `intent-guidance` change types
- docs-only wording tasks usually do not need new product design unless they change meaning or command semantics
- review completion is an acknowledgement, not transcript storage

## Task Lifecycle Guidance

The guidance component should support `agentkit start` and `agentkit close`.

`init` should guide the agent to finish repository maintainability setup, not merely create files. It should point agents toward docs structure, component mappings, architecture rules, local skills, hooks, and project-specific configuration.

`start` should persist the task's durable context:

- task todo
- intent source docs
- docs to keep in working memory
- task focus notes from human-agent discussion
- affected components and likely code areas
- expected checks
- review expectation
- design gaps and blocked questions

The task may be started after human-agent discussion, or started early and refined once the discussion clarifies the focus.

`close` should verify that the task has either completed responsibly or stopped at a recorded human decision point.

Closeout should avoid noisy loops by using state:

- diff fingerprints invalidate stale check or review receipts
- successful `agentkit check` writes a check receipt for the current fingerprint
- `agentkit close` requires that check receipt before completing
- review-required tasks need an explicit review-complete signal
- skip reasons are valid as an explicit low-risk fallback for the current diff fingerprint
- unchanged diffs should not repeat identical acknowledged warnings forever
- blocked tasks with recorded human questions should wait for new input

Fallback handling is part of guidance. If checks or review cannot proceed, the agent must record the reason and human question, then still use `agentkit close --blocked-question "..."`.

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

`agentkit check`, `agentkit status`, `agentkit remind`, `agentkit watch`, and external adapters should all use this same sampler. `check` can show reminder output for convenience, but it should not become the only place reminder policy lives.

Current implementation modules:

- `task_state.py` reads and writes task state.
- `receipts.py` reads and writes receipt files.
- `lifecycle.py` evaluates task state, receipts, fingerprints, missing gates, and reminder text.
- `watch.py` delivers reminder text in a local loop.

Near-term task-state improvements should continue from the first focus-context support. `start` can record focus notes and focus docs; later task updates should add planned checks, changed scope, and task history beyond the single default `current` task.

## Hook Guidance

`install-hooks` should install Git-native hooks for deterministic checks.

The first hook is `pre-commit`, which should run `agentkit check`. AgentKit should not require agents to manually remember a separate pre-commit command, and hooks should not perform long-running LLM review.
