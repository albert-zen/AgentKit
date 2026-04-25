# CLI Testing

## Strategy

The CLI should be tested at two levels:

- command function tests for behavior
- smoke tests for process-level argument routing

## Current Coverage

The first test slice covers command functions directly. Process-level tests can be added once the command set stabilizes.

Lifecycle command coverage should verify:

- `start` writes task state and reports durable intent sources
- `status` reports open tasks, missing gates, stale receipts, and blocked questions
- `remind` reports the next action derived from the same lifecycle state as `status`
- `check` can include lifecycle reminders without mutating task state beyond its normal check receipt
- `close` returns `needs_work` when open changes remain
- `close --blocked-question` records a blocked human question
- `close` requires a check receipt
- `close --review-complete` allows completion after required review

Hook command coverage should verify:

- `install-hooks` writes a Git `pre-commit` hook
- the hook invokes `agentkit check`

Watch command coverage should verify:

- `watch` calls the shared status/reminder logic
- `watch --once` emits one reminder and exits
- `watch` stops reminding for completed or traceably blocked tasks
- `watch` does not spawn agents or manage jobs
