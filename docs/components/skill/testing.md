# Skill And Codex Plugin Testing

Tests should verify that initialized repositories expose AgentKit through Codex's normal plugin shape:

- `plugins/agentkit/.codex-plugin/plugin.json` exists and names the plugin `agentkit`
- `plugins/agentkit/skills/agentkit/SKILL.md` exists
- `plugins/agentkit/assets/agentkit-icon.png` exists when the checked-in AgentKit plugin declares icon fields
- `.agents/plugins/marketplace.json` points to `./plugins/agentkit`
- `agentkit skill` updates the configured plugin skill output

Skill content tests should verify that the bundled skill teaches:

- why AgentKit exists for the current repo
- when to run `agentkit start` for repository-changing work
- when not to start a task for read-only exploration or question-answering
- when to ask the human for missing design
- how to run `check`, `status`, `remind`, and `watch`
- how to request clean-context review
- how to close completed or blocked work

Plugin tests should stay deterministic. They should validate file shape and manifest content without requiring Codex itself to install or reload the plugin.

Wakeup adapter tests should stay separate from plugin packaging tests. A Stop-hook adapter can be tested by feeding it Codex hook JSON and checking that it returns a continuation prompt only when AgentKit lifecycle state still has missing gates. Installer tests should verify that `install-codex-watchdog` writes Codex hook config through `.codex/hooks.json` plus `.codex/config.toml` and preserves unrelated hooks.

End-to-end Codex smoke tests should use a clean temporary Git repo:

- run `agentkit init`
- run `agentkit install-codex-watchdog --repo-local`
- commit the initialized baseline
- run `agentkit start --task "smoke"`
- run `codex exec -C <repo> --dangerously-bypass-approvals-and-sandbox ...`
- verify `.agentkit/codex-stop-hook.log` contains a `needs_work` Stop event followed by a closed or quiet state
- verify `agentkit status` reports `completed`

Do not write Codex JSONL output inside the test repo unless that output is ignored. A changing output file changes the diff fingerprint after each continuation and can make a legitimate blocked state immediately stale.
