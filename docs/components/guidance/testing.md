# Guidance Testing

## Strategy

Guidance tests should use small temporary repositories and assert that AgentKit returns useful output for:

- component orientation
- docs-impact mapping
- maintainability budget warnings and failures
- architecture violations
- review guidance
- task start output
- intent system reminder wording in start, orient, docs-impact, review, and lifecycle output
- task close status
- hook installation behavior
- status and reminder output
- watch once output
- AgentKit plugin skill operating-loop guidance

The tests should not assert exact prose unless the wording is part of the contract.

## Task Lifecycle Tests

`start` tests should verify that AgentKit records:

- task todo
- durable intent sources
- focus docs or focus notes when provided
- affected components
- relevant docs
- expected checks
- review expectation

`close` tests should verify:

- missing check receipts produce `needs_work`
- missing required review receipts produce `needs_work`
- completed close requires a check receipt and review-complete signal when review is expected
- skip reason does not satisfy required review
- blocked tasks can close only with a recorded question
- blocked close requires an existing started task
- stale receipts are invalidated when the diff fingerprint changes
- clean-tree evidence is invalidated when HEAD changes
- completed state remains terminal when its fingerprint is unchanged, even if
  local receipt files are later cleaned up
- each lifecycle gate exposes a stable rule id, outcome, reason, and next action
- status, reminders, close, and Codex delivery consume the shared evaluation
- unchanged acknowledged warnings do not repeat indefinitely

Fallback tests should verify that blocked closure preserves:

- human question
- open changes
- existing task state
- enough context for a human to resume the work

Reminder tests should eventually verify:

- open tasks produce reminder text
- reminders preserve the core intent-system wording about preserving human decisions, persisting future context, and asking when durable decisions are missing
- completed tasks do not produce reminders
- blocked tasks wait for new human input
- no-task status scopes `agentkit start` guidance to work that needs lifecycle tracking
- `agentkit check` without an open task still runs deterministic checks and does not create an implicit task
- stale receipts produce actionable missing-gate messages
- `check`, `status`, `remind`, and `watch` derive reminders from the same sampler
- reminder rendering does not change task state beyond the normal receipt side effects of the command that displays it
- concurrent task/receipt writers use independent temporary files and leave a valid atomic result

Skill tests should verify that the AgentKit plugin skill teaches:

- that substantial architecture, public-behavior, state/data-model, security-boundary, cross-component, and hook/plugin changes use the lifecycle
- that read-only work needs no lifecycle task
- that small, self-contained, low-risk edits may skip when ownership is obvious and verification is focused
- representative small-change examples
- that skipped work must start or resume before continuing if it expands
- that repository-local policy may be stricter
- the lifecycle operating loop
- when to ask the human for design
- command side effects, especially that `start` writes task state
- common `intent-guidance` change types
- docs-only wording task policy
- review acknowledgement without storing reviewer transcripts
- status/remind/watch usage

Mock-agent adoption tests should ask a clean agent to use the AgentKit plugin skill for a small representative task and report the workflow it would follow. Useful failures include missing command side-effect warnings, unclear docs-only review policy, and unavailable skill file access in the agent runtime.

Agent instruction tests should verify that `init` keeps `AGENTS.md` concise and does not duplicate the full skill or product design there. Repeated `init` calls should be idempotent, and an existing marked AgentKit section should not be rewritten to the latest default policy. `doctor` should accept concise local guidance based on the AgentKit marker without requiring exact default prose, including stricter repository policy.

Watcher tests should eventually verify:

- `agentkit watch` reuses the same reminder/status logic as the CLI
- watcher output is stateful and does not repeat closed or blocked tasks
- watcher configuration cannot turn AgentKit into a job runner
- local notification failures are reported without corrupting task state
- Codex watchdog installation writes hook config through the Codex config layer instead of relying only on plugin-local hook packaging
- Codex Stop-hook diagnostics make it clear whether Codex invoked the hook at all

Codex plugin tests should verify:

- `init` creates `plugins/agentkit/.codex-plugin/plugin.json`
- `init` creates `plugins/agentkit/skills/agentkit/SKILL.md`
- `init` creates `.agents/plugins/marketplace.json`
- the plugin declares the AgentKit Stop-hook adapter when that adapter is part of the runtime integration

## Hook Tests

`install-hooks` tests should verify that:

- a Git repository receives a `.git/hooks/pre-commit` file
- the hook invokes `agentkit check`
- repeated installation is idempotent
- hook installation fails clearly outside a Git repository
