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

- durable intent sources
- affected components
- relevant docs
- expected checks
- review expectation

`close` tests should verify:

- missing check receipts produce `needs_work`
- missing required review receipts produce `needs_work`
- completed close requires a check receipt and review-complete signal when review is expected
- blocked tasks can close only with a recorded question
- blocked close requires an existing started task
- stale receipts are invalidated when the diff fingerprint changes
- unchanged acknowledged warnings do not repeat indefinitely

## Hook Tests

`install-hooks` tests should verify that:

- a Git repository receives a `.git/hooks/pre-commit` file
- the hook invokes `agentkit check`
- repeated installation is idempotent
- hook installation fails clearly outside a Git repository
