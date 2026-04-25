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

For each agent-led task:

```bash
agentkit start --task "Describe the task"
agentkit check
agentkit review-guidance
agentkit close --review-complete
```

Useful lifecycle commands:

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

## License

MIT
