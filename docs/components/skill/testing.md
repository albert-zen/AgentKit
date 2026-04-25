# Skill And Codex Plugin Testing

Tests should verify that initialized repositories expose AgentKit through Codex's normal plugin shape:

- `plugins/agentkit/.codex-plugin/plugin.json` exists and names the plugin `agentkit`
- `plugins/agentkit/skills/agentkit/SKILL.md` exists
- `.agents/plugins/marketplace.json` points to `./plugins/agentkit`
- `agentkit skill` updates the configured plugin skill output

Skill content tests should verify that the bundled skill teaches:

- why AgentKit exists for the current repo
- when to run `agentkit start`
- when to ask the human for missing design
- how to run `check`, `status`, `remind`, and `watch`
- how to request clean-context review
- how to close completed or blocked work

Plugin tests should stay deterministic. They should validate file shape and manifest content without requiring Codex itself to install or reload the plugin.

Wakeup adapter tests should stay separate from plugin packaging tests. A Stop-hook adapter can be tested by feeding it Codex hook JSON and checking that it returns a continuation prompt only when AgentKit lifecycle state still has missing gates.
