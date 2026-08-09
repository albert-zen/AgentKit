# Skill And Codex Plugin Design

AgentKit should treat its agent-facing skill as a first-class repository component, not as a runtime-private generated file.

The canonical Codex-facing package lives under `plugins/agentkit/`:

- `.codex-plugin/plugin.json` identifies the AgentKit plugin.
- `skills/agentkit/SKILL.md` teaches agents how to use AgentKit during a coding task.
- `assets/agentkit-icon.png` provides the plugin marketplace and composer icon.
- `.agents/plugins/marketplace.json` exposes the local plugin through Codex's normal repo marketplace mechanism.

`agentkit init` should create this plugin surface by default. The intent is that a repo initialized with AgentKit can make the skill available to Codex through the same plugin directory and marketplace flow as other Codex plugins.

The skill distinguishes adoption, policy import, and structural migration:
`init` creates a latest-format repository, `init --preset` imports explicit
policy, and `upgrade` preserves existing policy while migrating only proven
AgentKit-managed structure. It should direct agents to review dry-run conflicts
rather than overwrite customized content.

The skill remains an operating guide for agents using AgentKit. It should explain the task loop, command side effects, design-gap behavior, review expectations, lifecycle reminders, and closeout. It should not become the north-star product design for agents developing AgentKit itself.

The task loop distinguishes `start` from `update`. `start` establishes initial
lifecycle context; after later discussion, the skill directs agents to
`agentkit update` for explicit task/plan replacement and duplicate-safe
focus/component additions or removals. The skill must state that update cannot
change lifecycle status, fingerprints, or validation evidence.

The skill should also make the risk-based lifecycle boundary explicit. Agents should use `agentkit start`, `check`, review guidance, and `close` for substantial changes affecting architecture, public behavior, state or data models, security boundaries, cross-component workflows, hooks or plugins, or otherwise needing durable design and review context. Agents should not start a task for read-only exploration, codebase orientation, or answering questions.

Small, self-contained, low-risk edits may skip the lifecycle when ownership is obvious and verification is focused. The skill should give representative examples such as a local launcher fallback, test-only maintenance, narrowly scoped wording that preserves product meaning, or a similarly reversible one-owner fix. If skipped work expands beyond its stated boundary, the agent must start or resume a task before continuing. Repository-local instructions remain authoritative and may require the lifecycle for every write.

`agentkit check` should be presented as useful focused verification even when no task is open. It runs deterministic repository checks without creating a second implicit task mode; once a task is started, normal lifecycle and receipt semantics apply.

The skill and plugin descriptions should present AgentKit's product role consistently: preserving human intent and project maintainability by guiding agents to read durable intent files and persist meaningful design, documentation, and test changes. The description should not make AgentKit sound primarily like a generic check runner or lifecycle ceremony tool.

Runtime-specific wakeup behavior is related but separate. Codex plugins can package the skill, but reliable Stop-hook delivery should be installed through Codex's normal hook config layer. `agentkit install-codex-watchdog` owns that explicit installation by writing or merging `<repo>/.codex/hooks.json` and enabling `features.codex_hooks` in `<repo>/.codex/config.toml`, or by doing the same in `CODEX_HOME` / `~/.codex` for user-local installation. The plugin skill can teach the workflow, while the Codex watchdog hook performs the runtime continuation.
