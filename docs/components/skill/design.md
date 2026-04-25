# Skill And Codex Plugin Design

AgentKit should treat its agent-facing skill as a first-class repository component, not as a runtime-private generated file.

The canonical Codex-facing package lives under `plugins/agentkit/`:

- `.codex-plugin/plugin.json` identifies the AgentKit plugin.
- `skills/agentkit/SKILL.md` teaches agents how to use AgentKit during a coding task.
- `assets/agentkit-icon.png` provides the plugin marketplace and composer icon.
- `.agents/plugins/marketplace.json` exposes the local plugin through Codex's normal repo marketplace mechanism.

`agentkit init` should create this plugin surface by default. The intent is that a repo initialized with AgentKit can make the skill available to Codex through the same plugin directory and marketplace flow as other Codex plugins.

The skill remains an operating guide for agents using AgentKit. It should explain the task loop, command side effects, design-gap behavior, review expectations, lifecycle reminders, and closeout. It should not become the north-star product design for agents developing AgentKit itself.

Runtime-specific wakeup behavior is related but separate. Codex plugins can package the skill, but reliable Stop-hook delivery should be installed through Codex's normal hook config layer. `agentkit install-codex-watchdog` owns that explicit installation by writing or merging `<repo>/.codex/hooks.json` and enabling `features.codex_hooks` in `<repo>/.codex/config.toml`, or by doing the same in `CODEX_HOME` / `~/.codex` for user-local installation. The plugin skill can teach the workflow, while the Codex watchdog hook performs the runtime continuation.
