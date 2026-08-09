# CLI Component Design

## Purpose

The CLI is the primary interface for agents and humans. It routes commands to deterministic AgentKit behaviors and prints agent-readable guidance.

## Owned Concepts

- command names
- argument parsing
- repository root selection
- process exit codes

## Boundaries

The CLI should stay thin. It should parse arguments and delegate behavior to command functions. It should not contain configuration parsing, path matching, architecture lint logic, or git diff logic.

Architecture lint implementation belongs in `architecture.py`; CLI and command routing should only expose and call it.

## Public Commands

- `agentkit init`
- `agentkit doctor`
- `agentkit upgrade`
- `agentkit start`
- `agentkit update`
- `agentkit orient`
- `agentkit intent-guidance`
- `agentkit status`
- `agentkit remind`
- `agentkit docs-impact`
- `agentkit lint-architecture`
- `agentkit lint-maintainability`
- `agentkit check`
- `agentkit review-guidance`
- `agentkit close`
- `agentkit install-hooks`
- `agentkit install-codex-watchdog`
- `agentkit watch`
- `agentkit skill`
- `agentkit codex-stop-hook`

## Lifecycle Commands

`start` and `close` are lifecycle gates for agent work.

`start` captures durable task context and writes a task state file. `close` verifies whether the task is completed, still needs work, or is blocked on a recorded human question.

`start` should accept focus context such as `--focus-note` and `--focus-doc` so agents can persist the human-approved emphasis of a task after discussion.

`update` is the dedicated way to refine an existing task. It exposes only
domain operations for setting task/plan text and adding or removing focus
notes, focus docs, and components. It must not expose arbitrary JSON patching
or lifecycle/evidence fields.

`close` accepts `--review-complete` after a required review loop and `--skip-review-reason` as an explicit low-risk fallback where review is intentionally skipped.

`status` and `remind` expose the current lifecycle state without changing it. `status` should print facts about open tasks, missing gates, stale receipts, and blocked handoffs. `remind` should print agent-facing next actions derived from those facts.

`check` may include lifecycle reminders in its output, but the CLI should still route status/reminder computation through shared guidance logic instead of implementing reminder policy itself.

`close --review-complete` is an acknowledgement by the implementing agent that the required review loop was completed for the current diff and meaningful findings were handled. It is not a command for storing reviewer transcripts.

## Init And Doctor Commands

`init` creates the default AgentKit surfaces and ensures `AGENTS.md` or `agents.md` contains a small low-level AgentKit entry section. It should not overwrite an existing agent instruction file just to add AgentKit guidance.

`doctor` audits readiness without changing files. It should report required missing surfaces separately from optional improvements.

`doctor` also reports current/latest repository format and
`up_to_date`/`upgrade_available`/`blocked`. `upgrade --dry-run` renders a
complete zero-write plan; `upgrade` applies it. The CLI only routes and renders
these operations—migration ownership and atomicity live below the command
adapter. Upgrade is not an alias for `init --preset`.

## Hook Commands

`install-hooks` installs Git-triggered deterministic hooks. It should not create a separate manual pre-commit workflow for agents.

`install-codex-watchdog` installs Codex lifecycle hook configuration through Codex's normal hook discovery layer. Repo-local installation writes `<repo>/.codex/hooks.json` and `<repo>/.codex/config.toml`; user-local installation writes to `CODEX_HOME` or `~/.codex`. The installer should merge with existing hook files instead of replacing unrelated hooks.

`codex-stop-hook` is the Codex Stop-hook adapter. It reads Codex hook JSON from stdin, samples AgentKit lifecycle state, optionally writes a diagnostic log, and returns a Codex continuation response only when the task still needs closeout work.

## Watch Command

`watch` runs a lightweight local reminder loop. It should call the same status/reminder logic as `status`, `remind`, and `check`, then deliver the resulting reminder text while it is running.

The CLI should expose interval and output options when needed, but it should not turn `watch` into an agent runner or job scheduler.

The first implementation supports `--once` for tests and for agents that want a one-shot reminder through the same watch entry point.
