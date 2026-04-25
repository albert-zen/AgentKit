# CLI Testing

## Strategy

The CLI should be tested at two levels:

- command function tests for behavior
- smoke tests for process-level argument routing

## Current Coverage

The first test slice covers command functions directly. Process-level tests can be added once the command set stabilizes.

Lifecycle command coverage should verify:

- `start` writes task state and reports durable intent sources
- `close` returns `needs_work` when open changes remain
- `close --blocked-question` records a blocked human question
- `close` requires a check receipt
- `close --review-complete` allows completion after required review

Hook command coverage should verify:

- `install-hooks` writes a Git `pre-commit` hook
- the hook invokes `agentkit check`
