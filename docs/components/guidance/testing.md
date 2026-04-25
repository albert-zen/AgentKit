# Guidance Testing

## Strategy

Guidance tests should use small temporary repositories and assert that AgentKit returns useful output for:

- component orientation
- docs-impact mapping
- architecture violations
- review guidance
- task start output
- task close status
- hook installation behavior

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
- unchanged acknowledged warnings do not repeat indefinitely

Fallback tests should verify that blocked closure preserves:

- human question
- open changes
- existing task state
- enough context for a human to resume the work

Reminder tests should eventually verify:

- open tasks produce reminder text
- completed tasks do not produce reminders
- blocked tasks wait for new human input
- stale receipts produce actionable missing-gate messages
- `check`, `status`, `remind`, and `watch` derive reminders from the same sampler
- reminder rendering does not change task state beyond the normal receipt side effects of the command that displays it

Watcher tests should eventually verify:

- `agentkit watch` reuses the same reminder/status logic as the CLI
- watcher output is stateful and does not repeat closed or blocked tasks
- watcher configuration cannot turn AgentKit into a job runner
- local notification failures are reported without corrupting task state

## Hook Tests

`install-hooks` tests should verify that:

- a Git repository receives a `.git/hooks/pre-commit` file
- the hook invokes `agentkit check`
- repeated installation is idempotent
- hook installation fails clearly outside a Git repository
