# Review Guidance

Status: Draft

## Purpose

This document defines how AgentKit should help an implementing agent request clean-context review.

AgentKit does not need to create a separate review artifact by default. The lightweight baseline is to return guidance to the implementing agent:

- whether review is expected
- how to spawn or request a clean-context reviewer
- what docs and code the reviewer should inspect
- a trigger policy
- expected reviewer output

The implementing agent can then spawn a sub-agent, call another agent, or hand the guidance to an external system such as Symphony.

AgentKit may optionally generate a context summary for external systems, logs, or debugging, but that is not the primary workflow.

## When Review Is Expected

Clean-context review should be expected for non-trivial changes.

Examples:

- new features
- new components
- public API changes
- data model changes
- state machine changes
- architecture or dependency changes
- security-sensitive changes
- orchestration or agent workflow changes
- bug fixes with broad blast radius
- changes where the implementing agent made important assumptions

Review can be skipped for low-risk changes if the implementing agent records why. A skip reason is an explicit closeout fallback: it may satisfy the review gate when the agent can explain why a full clean-context review would add little value for the current diff.

Examples:

- typo fixes
- formatting-only changes
- small copy edits
- local mechanical renames
- obvious test expectation updates caused by already-approved behavior

## Implementing Agent Responsibilities

Before requesting review, the implementing agent should:

1. Record or identify the repository paths that contain the original human intent.
2. Identify relevant design and component docs.
3. Summarize the implementation.
4. List changed files.
5. Run relevant tests and checks.
6. Read any lifecycle reminders emitted by `agentkit check`, `agentkit status`, or `agentkit remind`.
7. Note docs updates or explain why none were needed.
8. Ask AgentKit for review guidance.
9. Spawn or request a clean-context reviewer with that guidance when review is expected.
10. Fix meaningful reviewer findings.
11. Record durable design decisions, risks, or unresolved questions in the repository docs when they matter for future maintainability.
12. Acknowledge the completed review loop with `agentkit close --review-complete`, or record the low-risk fallback with `agentkit close --skip-review-reason "..."`.

The implementing agent should not ask for human review while obvious test failures, architecture lint failures, or stale-doc warnings remain unresolved.

## Reviewer Context

The reviewer should receive only the context needed to evaluate the change.

Recommended context:

- durable human-approved intent docs
- relevant design, component, spec, and ADR paths
- original user request as convenience context
- implementation summary
- changed files or diff
- test output
- AgentKit check output
- known assumptions
- open questions

The reviewer should not receive the full implementing agent conversation unless it is necessary. A cleaner context helps the reviewer catch drift instead of inheriting the implementer's assumptions.

The durable docs are the authority. Inline summaries in the reviewer prompt are useful for orientation, but they must point back to repository paths and should be treated as convenience context, not as the source of truth.

## Review Guidance

AgentKit should return instructions that the implementing agent can use to brief the reviewer.

The guidance should tell the implementing agent:

1. Provide durable intent source paths before any inline summary.
2. Read the project-level design docs first.
3. Read the component or feature docs related to the changed files.
4. Ask the reviewer to compare those docs and the original human request against the implementation.
5. Ask the reviewer to focus on intent drift, unsupported durable decisions, missing tests, stale docs, and architecture violations.
6. Fix meaningful reviewer findings before asking for human review.
7. After fixing reviewer findings, request another clean-context review pass.
8. Continue review -> fix -> review until no meaningful findings remain, or only low-value residual risks are left for the human.

## Reviewer Instructions

The implementing agent should ask the reviewer to compare intent against implementation.

Example instruction:

```text
Review this change from a clean context.

Durable intent sources:
- docs/design.md
- docs/components/<component>/design.md
- docs/components/<component>/testing.md

Treat these repository docs as the source of truth for human intent.
Any inline task summary is convenience context only.

Compare the durable human intent docs and original task against the implementation.

Look for:
- behavior that does not satisfy the stated intent
- unsupported durable product, architecture, API, workflow, or taste decisions
- missing tests
- stale or missing docs
- architecture rule violations
- reverse dependencies or layering violations
- overly broad changes
- hidden failure modes

Return findings ordered by severity.
For each finding, include:
- title
- severity
- affected file or area
- why it matters
- suggested fix

If there are no meaningful findings, say that clearly and mention any residual risk.
```

## Review Output

The reviewer should produce a concise findings-first report.

Recommended shape:

```md
## Findings

- [P1] ...
- [P2] ...

## Missing Tests

...

## Documentation Drift

...

## Residual Risk

...
```

The implementing agent should fix meaningful findings before involving the human.

One review pass is not a loop. A review loop requires at least one review pass, a fix pass, and a second review pass after the fixes.

`agentkit close` should treat a missing review loop as unfinished work when review is required. The required close signal is an acknowledgement by the implementing agent that the review loop happened for the current diff and meaningful findings were handled. AgentKit does not need to store reviewer transcripts or multi-pass finding logs as first-class state.

If reviewer findings create durable product, architecture, testing, or risk knowledge, the implementing agent should record that knowledge in the repository documentation system. AgentKit's job is to remind and gate; the docs carry long-lived intent.

If the task is blocked before review can happen, the agent should record the blocking human question and close the task as blocked rather than silently ending.

If review cannot be performed, the implementing agent must not mark the task completed. It should record why review could not happen, preserve the current state, ask the human a concrete question, and run `agentkit close --blocked-question "..."`.

Reminder adapters should treat missing required review as an open closeout gate. If the task is not blocked with a recorded human question, the adapter may re-activate the agent and ask it to complete review or close the task as blocked. `agentkit check`, `agentkit status`, `agentkit remind`, and an AgentKit-owned local `agentkit watch` process should all derive their guidance from the same task-state sampler. The watcher may provide this reminder delivery while it is running, but it should only deliver the reminder generated from AgentKit state; it should not perform the review or spawn agents itself.

The first watcher implementation is local and simple: `agentkit watch --once` emits one sampled reminder for tests and scripted integrations, while continuous `agentkit watch` repeats the same reminder loop until interrupted. Codex Stop-hook continuation should be installed explicitly with `agentkit install-codex-watchdog`, which wires `agentkit codex-stop-hook` through Codex's hook config layer and writes a diagnostic log when invoked.

## AgentKit Responsibilities

AgentKit should support the review loop by generating guidance:

- a reviewer prompt
- a list of relevant docs
- a list of changed files
- test and check summaries
- docs-impact summary
- architecture lint summary

AgentKit should also remind the implementing agent when review is expected.

Optional: AgentKit may generate a review context summary if the project wants a durable handoff artifact or needs to send the handoff to an external system. This should stay optional and should not turn AgentKit into a review transcript database.

## Maintenance Checks

Every implementation handoff should address three maintenance questions.

### 1. Documentation Sync

Did the change require documentation updates?

If yes, which docs were updated?

If no, why not?

### 2. Design Impact

Did the change affect product design, architecture, data model, API, workflow, state transitions, or agent behavior?

If yes, where was that design impact recorded?

If no, what implementation and tests prove the change stayed local?

### 3. Governance Constraints

Did the change respect repository rules?

Check:

- architecture lint
- dependency direction
- docs-impact warnings
- tests
- repository-specific AgentKit checks

## Relationship to Skills

The AgentKit skill for a repository should teach implementing agents how to request and follow this guidance.

The skill should include:

- when to request review
- how to run `agentkit review-guidance`
- what to pass to the reviewer
- how to spawn or request a reviewer in supported agent environments
- how to handle reviewer findings

This lets AgentKit inject review behavior into the implementing agent without needing to own every runtime or orchestration mechanism.

Root `AGENTS.md` should only point agents toward AgentKit entry commands and the AgentKit plugin skill. Detailed review behavior belongs in the bundled skill and this review guidance document, not in the root agent instruction file.
