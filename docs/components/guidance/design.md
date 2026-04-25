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

## Boundary

Guidance should not replace semantic reasoning by the LLM. It should route, remind, template, and check.

## Task Lifecycle Guidance

The guidance component should support `agentkit start` and `agentkit close`.

`start` should persist the task's durable context:

- intent source docs
- docs to keep in working memory
- affected components and likely code areas
- expected checks
- review expectation
- design gaps and blocked questions

`close` should verify that the task has either completed responsibly or stopped at a recorded human decision point.

Closeout should avoid noisy loops by using state:

- diff fingerprints invalidate stale check or review receipts
- successful `agentkit check` writes a check receipt for the current fingerprint
- `agentkit close` requires that check receipt before completing
- review-required tasks need an explicit review-complete signal or skip reason
- unchanged diffs should not repeat identical acknowledged warnings forever
- blocked tasks with recorded human questions should wait for new input

## Hook Guidance

`install-hooks` should install Git-native hooks for deterministic checks.

The first hook is `pre-commit`, which should run `agentkit check`. AgentKit should not require agents to manually remember a separate pre-commit command, and hooks should not perform long-running LLM review.
