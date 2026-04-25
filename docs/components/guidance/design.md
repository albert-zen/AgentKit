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
- skip reasons are only valid when review is not required for low-risk work
- unchanged diffs should not repeat identical acknowledged warnings forever
- blocked tasks with recorded human questions should wait for new input

Fallback handling is part of guidance. If checks or review cannot proceed, the agent must record the reason and human question, then still use `agentkit close --blocked-question "..."`.

Reminder guidance should distinguish state from delivery. AgentKit owns the open-task state, missing-gate detection, stale-receipt detection, and reminder text. Delivery can come from runtime adapters such as ProjectMan, Symphony, editor integrations, schedulers, or agent hooks, and it can also come from an AgentKit-owned local `agentkit watch` process.

`agentkit watch` should be treated as a first-party reminder adapter, not a new orchestration layer. It may poll local task state, emit reminder text, and call configured local notification commands. It should not spawn coding agents, manage queues, or perform semantic review.

## Hook Guidance

`install-hooks` should install Git-native hooks for deterministic checks.

The first hook is `pre-commit`, which should run `agentkit check`. AgentKit should not require agents to manually remember a separate pre-commit command, and hooks should not perform long-running LLM review.
