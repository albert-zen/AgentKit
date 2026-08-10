# AgentKit

AgentKit is a lightweight agent-first development harness for personal and small-team software work.

It helps developers encode human intent, architecture boundaries, documentation structure, testing discipline, and review loops into a repository so coding agents can work quickly without drifting away from the product's design.

AgentKit is early software. The current implementation is a Python CLI plus a Codex plugin/skill bundle that helps an agent keep track of task state, durable intent, docs impact, architecture checks, review expectations, and closeout.

## Requirements

AgentKit requires Python 3.11 or newer.

## Install 0.2.0

The first supported release channel is the GitHub tag `v0.2.0`. AgentKit is
not yet published on PyPI. Install the tagged release as an isolated CLI with
[`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install "agentkit @ git+https://github.com/albert-zen/AgentKit.git@v0.2.0"
```

The tag in the URL fixes the installed source to AgentKit 0.2.0. Verify the
installed command before using it in a repository:

```bash
agentkit --help
```

For development from a checkout, install the project and its test dependencies
instead:

```bash
python -m pip install -e ".[dev]"
pytest -q
```

## Adopt AgentKit In A New Project

After installing the CLI, initialize a new AgentKit repository with the
versioned recommended policy:

```bash
cd /path/to/project
agentkit init --preset recommended-v1
agentkit doctor
agentkit check
```

`recommended-v1` materializes the selected lifecycle rules and reminders in
`agentkit.yml` so the repository can inspect, version, and deliberately edit
them. Plain `agentkit init` remains available for adoption without importing
that preset.

## Upgrade An Existing AgentKit Repository

Package installation and repository migration are separate. First update the
installed CLI to the tagged release:

```bash
uv tool install --force "agentkit @ git+https://github.com/albert-zen/AgentKit.git@v0.2.0"
```

Then, inside each existing AgentKit repository, diagnose and preview the
migration before applying it:

```bash
cd /path/to/existing-project
agentkit doctor
agentkit upgrade --dry-run
agentkit upgrade
```

Upgrade migrates only versioned AgentKit-managed structure. It preserves user
configuration and policy (including components, layers, rules, reminders, and
budgets), project instructions and documentation, and local task state and
validation receipts. It does not reapply a preset. If ownership or a lossless
transformation cannot be proven, AgentKit reports a conflict and writes
nothing.

After upgrade, inspect the diff and run repository-specific tests plus the
AgentKit verification commands:

```bash
git diff --check
git diff
agentkit doctor
agentkit check
# Run the project's normal test command, for example: pytest -q
```

See [ADR 0002](docs/decisions/0002-repository-upgrade-preserves-user-intent.md)
for the migration safety contract and [CHANGELOG.md](CHANGELOG.md) for 0.2.0
release notes.

## Core Task Workflow

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
