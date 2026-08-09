# AgentKit

AgentKit is a lightweight agent-first development harness for personal and small-team software work.

It helps developers encode human intent, architecture boundaries, documentation structure, testing discipline, and review loops into a repository so coding agents can work quickly without drifting away from the product's design.

AgentKit is early software. The current implementation is a Python CLI plus a Codex plugin/skill bundle that helps an agent keep track of task state, durable intent, docs impact, architecture checks, review expectations, and closeout.

## Install From Source

```bash
pip install -e .[dev]
```

Then verify:

```bash
agentkit doctor
pytest -q
```

## Core Workflow

In a repository that should use AgentKit:

```bash
agentkit init
```

To import the versioned recommended lifecycle policy as explicit, auditable
repository configuration:

```bash
agentkit init --preset recommended-v1
```

`init` adopts AgentKit in a new repository, while `--preset` explicitly
materializes a selected lifecycle policy. Existing AgentKit repositories use a
separate, policy-preserving upgrade path:

```bash
agentkit doctor
agentkit upgrade --dry-run
agentkit upgrade
```

Upgrade changes only versioned AgentKit-managed repository structure. It does
not reapply a preset or reset components, rules, reminders, budgets, comments,
unknown configuration, task state, or receipts. A conflict is reported with
zero writes whenever ownership or losslessness cannot be proven.

Use the full lifecycle for substantial agent-led changes:

```bash
agentkit start --task "Describe the task"
agentkit update --set-plan "Implementation plan" --add-focus-doc docs/design.md
agentkit check
agentkit review-guidance
agentkit close --review-complete
```

Read-only work needs no lifecycle task. Small, self-contained, low-risk edits may skip it when ownership is obvious and verification is focused, unless repository-local guidance requires a stricter policy. If initially small work expands, start or resume the task before continuing.

Useful lifecycle commands:

- `agentkit update`: refine explicit task context without resetting unrelated state or evidence.
- `agentkit status`: show task state and missing closeout gates.
- `agentkit remind`: print the next reminder from current task state.
- `agentkit watch`: run a local reminder loop.
- `agentkit install-codex-watchdog --repo-local`: install explicit Codex Stop-hook wiring for the current repo.

## Codex Plugin

The repo includes a local Codex plugin under `plugins/agentkit`. The plugin packages the AgentKit skill and metadata so agents can learn the intended workflow from a durable, versioned source.

`agentkit init` can add the repo-local plugin marketplace entry and AgentKit guidance to `AGENTS.md`.

## Design Docs

The initial design lives in [docs/design.md](docs/design.md).

The intended human-agent workflow lives in [docs/workflow.md](docs/workflow.md).

The concrete implementation model lives in [docs/implementation-model.md](docs/implementation-model.md).

The clean-context review guidance contract lives in [docs/review-guidance.md](docs/review-guidance.md).

The product roadmap lives in [docs/roadmap.md](docs/roadmap.md).

The Association / State / Rule implementation boundary lives in
[docs/architecture/core-model.md](docs/architecture/core-model.md), governed by
[ADR 0001](docs/decisions/0001-association-state-rule-core.md).

Repository upgrade is governed by
[ADR 0002](docs/decisions/0002-repository-upgrade-preserves-user-intent.md).

## License

MIT
