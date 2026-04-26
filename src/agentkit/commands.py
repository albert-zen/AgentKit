from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path

from agentkit.config import AgentKitConfig, ComponentConfig, LayerConfig, load_config
from agentkit.fs import expand_patterns, matches_any, relpath
from agentkit.git import changed_paths, diff_fingerprint, git_path, is_git_repo
from agentkit.lifecycle import reminder_text, render_reminder, sample_lifecycle, status_text
from agentkit.maintainability import lint_maintainability
from agentkit.receipts import has_receipt, write_receipt
from agentkit.render import bullet, section
from agentkit.task_state import DEFAULT_TASK_ID, load_task_state, task_path, write_task_state


AGENTKIT_AGENT_SECTION_MARKER = "<!-- agentkit:agents-section -->"

AGENTKIT_AGENT_SECTION = f"""### AgentKit

{AGENTKIT_AGENT_SECTION_MARKER}
This repository uses AgentKit to keep agent-led changes tied to durable intent, checks, review, and closeout. For implementation, documentation edits, hook/plugin updates, or any repository-changing task, start with `agentkit start --task "..."`, use `agentkit check` plus `agentkit status` or `agentkit remind` while working, and finish with `agentkit close`. For read-only exploration, codebase orientation, or answering questions without edits, do not create an AgentKit task unless the work becomes long-running or the human asks for lifecycle tracking. For the full operating guide, read the AgentKit plugin skill.
"""

DEFAULT_AGENT_MD = f"""{AGENTKIT_AGENT_SECTION}
"""


DEFAULT_AGENTKIT_YML = """version: 1

docs:
  root: docs
  design: docs/design.md
  workflow: docs/workflow.md
  decisions: docs/decisions

components:
  core:
    description: Core product behavior.
    code:
      - src/**
    docs:
      - docs/design.md
    required_docs:
      - design
    keywords:
      - core

layers: {}

review:
  require_for:
    - public_api
    - data_model
    - architecture
    - orchestration
  default: warn

skills:
  source: plugins/agentkit/skills/agentkit/SKILL.md
  output: plugins/agentkit/skills/agentkit/SKILL.md

maintainability:
  budgets: []
"""

DEFAULT_SKILL_MD = """---
name: agentkit
description: Preserve human intent and project maintainability by guiding agents to read durable intent files and persist meaningful design, docs, and test changes.
---

# AgentKit Skill

This repository uses AgentKit.

## What AgentKit Gives You

AgentKit keeps your work tied to durable repo intent. Use it to:

- find the docs and components relevant to a task
- remember the task's closeout gates
- check docs impact and architecture rules
- get lifecycle reminders while you work
- ask for clean-context review before human attention
- close the task as completed or blocked

The skill is an operating guide. For deeper product or architecture intent, read the durable docs that AgentKit returns.

## When To Start A Task

Use the AgentKit task lifecycle for implementation work, documentation edits, hook/plugin changes, generated files, commits, or any task that changes repository state.

Do not start a task for read-only exploration, codebase orientation, answering architecture questions, or lightweight audits with no edits. In those cases, read the relevant docs directly and use `agentkit status` or `agentkit remind` only if you need to inspect an already-open task.

If read-only exploration turns into repository-changing work, start or resume the task before making edits so closeout gates apply to the change.

## Repository-Changing Operating Loop

1. Start or resume the task with `agentkit start`.
2. Read the durable intent sources in the output.
3. If design is missing or ambiguous for product behavior, API, data model, workflow, architecture, or state transitions, ask the human before implementing that part.
4. Implement against tests and the repo's architecture rules.
5. Run `agentkit check` and read any lifecycle reminder it prints.
6. Run `agentkit review-guidance` and request clean-context review when expected.
7. Fix meaningful reviewer findings.
8. Run `agentkit close --review-complete`, or close as blocked with a recorded human question.

## Start Of Task

For repository-changing work, run:

```text
agentkit start
```

`start` writes repository-local task state under `.agentkit/`. In a read-only audit, orientation pass, or question-answering task, do not run `start`; read this skill and use read-only commands such as `agentkit status` or `agentkit remind` only when they help inspect existing state.

If you know the component, run:

```text
agentkit start --component <name>
```

After discussion clarifies the task, preserve the focus:

```text
agentkit start --task "<refined task>" --focus-note "<human-approved focus>" --focus-doc <path>
```

Use `agentkit start --component <name>` when you already know the component. Otherwise, include the task text and let AgentKit infer affected components.

## During Design

Use:

```text
agentkit intent-guidance --component <name> --change-type <type>
```

Write the actual design content yourself. AgentKit tells you where it belongs.

Useful change-type values include `architecture`, `data_model`, `public_api`, `orchestration`, `workflow`, `tests`, and `docs`.

For docs-only wording tasks, ask the human for design only when the wording changes product meaning, command semantics, public behavior, workflow expectations, or accepted terminology. For local copyedits that preserve meaning, proceed with focused docs checks and review expectations from AgentKit.

## Before Review

Run:

```text
agentkit check
agentkit review-guidance
```

If review is expected, spawn or request a clean-context reviewer with the guidance AgentKit returns.

Do not treat review as a transcript storage task. AgentKit only needs the main agent to acknowledge that the review loop was completed for the current diff. If review reveals durable design, risk, or testing knowledge, record that in the repository docs.

For low-risk docs-only wording changes, review may still be expected by local policy. Use `agentkit review-guidance` to decide. If the change is truly low risk, close with `agentkit close --skip-review-reason "..."` only when AgentKit allows it.

## Lifecycle Reminders

Use:

```text
agentkit status
agentkit remind
```

`status` shows task facts and missing gates. `remind` shows the next action. `agentkit check` may also include lifecycle reminders.

For a local reminder loop, use:

```text
agentkit watch
```

For Codex Stop-hook reminders, install explicit hook wiring:

```text
agentkit install-codex-watchdog --repo-local
```

If a Stop hook does not appear to run, check `.agentkit/codex-stop-hook.log`. No log usually means Codex did not invoke the hook.

## Close Task

Before ending the task, run:

```text
agentkit close --review-complete
```

If blocked on human input, run:

```text
agentkit close --blocked-question "..."
```

Use blocked close when continuing would require an unsupported assumption. Include the human question clearly.
"""

DEFAULT_CODEX_PLUGIN_JSON = """{
  "name": "agentkit",
  "version": "0.1.0",
  "description": "Preserve human intent and project maintainability by guiding agents to read durable intent files and persist meaningful design, docs, and test changes.",
  "skills": "./skills/",
  "hooks": "./hooks.json",
  "interface": {
    "displayName": "AgentKit",
    "shortDescription": "Preserve human intent and project maintainability through durable intent files.",
    "longDescription": "AgentKit guides coding agents to read durable intent files before work and persist meaningful design, documentation, and test changes after work.",
    "developerName": "AgentKit",
    "category": "Productivity",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": [
      "Use AgentKit to start this task and follow the repository closeout workflow.",
      "Use AgentKit to check whether this task is ready for review and closeout."
    ]
  }
}
"""

DEFAULT_CODEX_PLUGIN_HOOKS_JSON = """{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "agentkit codex-stop-hook",
            "timeout": 30,
            "statusMessage": "Checking AgentKit task closeout"
          }
        ]
      }
    ]
  }
}
"""

DEFAULT_CODEX_MARKETPLACE_JSON = """{
  "name": "agentkit-local",
  "interface": {
    "displayName": "AgentKit Local"
  },
  "plugins": [
    {
      "name": "agentkit",
      "source": {
        "source": "local",
        "path": "./plugins/agentkit"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
"""

TASK_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "update",
    "change",
    "fix",
    "add",
    "new",
}


INTENT_SYSTEM_REMINDER = [
    "Preserve what humans have already decided. Persist what future agents need to know. Ask when a durable decision is missing.",
    "Use the intent files above as repository memory for human intent, design taste, boundaries, workflows, and testing expectations. If this work changes what future agents should rely on, update the relevant docs or tests; if it does not, note why no persistence update was needed.",
    "If the files do not answer an important product, architecture, API, workflow, or taste decision, continue only with the parts that are clear and ask the human for the missing intent. If the uncertainty blocks responsible progress, close as blocked with `agentkit close --blocked-question \"...\"`.",
]


def init_repo(repo: Path, force: bool = False) -> str:
    created: list[str] = []
    _ensure_agentkit_agents_section(_agents_path(repo), created, force)
    _write_if_missing(repo / "agentkit.yml", DEFAULT_AGENTKIT_YML, created, force)
    for directory in [
        repo / "docs",
        repo / "docs" / "architecture",
        repo / "docs" / "components",
        repo / "docs" / "decisions",
        repo / "docs" / "specs" / "active",
        repo / "docs" / "specs" / "completed",
        repo / "plugins" / "agentkit" / ".codex-plugin",
        repo / "plugins" / "agentkit" / "skills" / "agentkit",
        repo / ".agents" / "plugins",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
    _write_if_missing(repo / "docs" / "design.md", "# Design\n\nStatus: Draft\n", created, force)
    _write_if_missing(repo / "docs" / "workflow.md", "# Workflow\n\nStatus: Draft\n", created, force)
    _write_if_missing(repo / "docs" / "architecture" / "dependency-rules.md", "# Dependency Rules\n", created, force)
    _write_if_missing(repo / "plugins" / "agentkit" / ".codex-plugin" / "plugin.json", DEFAULT_CODEX_PLUGIN_JSON, created, force)
    _write_if_missing(repo / "plugins" / "agentkit" / "hooks.json", DEFAULT_CODEX_PLUGIN_HOOKS_JSON, created, force)
    _write_if_missing(repo / "plugins" / "agentkit" / "skills" / "agentkit" / "SKILL.md", DEFAULT_SKILL_MD, created, force)
    _ensure_agentkit_marketplace_entry(repo / ".agents" / "plugins" / "marketplace.json", created, force)
    return section("AgentKit Init", bullet(created or ["No files changed"]))


def doctor(repo: Path) -> tuple[int, str]:
    findings: list[str] = []
    ok: list[str] = []
    recommendations: list[str] = []

    agents_path = _agents_path(repo)
    if agents_path.exists():
        agents_text = agents_path.read_text(encoding="utf-8")
        if AGENTKIT_AGENT_SECTION_MARKER in agents_text:
            ok.append("AGENTS.md contains AgentKit entry guidance")
        else:
            findings.append("AGENTS.md is missing AgentKit entry guidance; run `agentkit init`")
    else:
        findings.append("Missing AGENTS.md; run `agentkit init`")

    config_path = repo / "agentkit.yml"
    configured_doc_paths: list[str] = []
    if config_path.exists():
        ok.append("agentkit.yml exists")
        try:
            config = load_config(repo)
            configured_doc_paths = [path for path in [config.docs.design, config.docs.workflow] if path]
            manifest_errors = validate_manifest(repo, config)
            if manifest_errors:
                findings.extend(manifest_errors)
            else:
                ok.append("manifest references are valid")
            if config.components:
                ok.append(f"components configured: {len(config.components)}")
            else:
                findings.append("No components configured in agentkit.yml")
            if config.layers:
                ok.append(f"architecture layers configured: {len(config.layers)}")
            else:
                recommendations.append("No architecture layers configured in agentkit.yml; add them when dependency direction matters")
            skill_source = repo / config.skills.source
            if skill_source.exists():
                ok.append("canonical AgentKit skill source exists")
            else:
                findings.append("Canonical AgentKit skill source is missing; run `agentkit init`")
            plugin_manifest = repo / "plugins" / "agentkit" / ".codex-plugin" / "plugin.json"
            if plugin_manifest.exists():
                ok.append("AgentKit Codex plugin manifest exists")
            else:
                findings.append("AgentKit Codex plugin manifest is missing; run `agentkit init`")
            marketplace = repo / ".agents" / "plugins" / "marketplace.json"
            if _has_agentkit_marketplace_entry(marketplace):
                ok.append("AgentKit Codex marketplace entry exists")
            else:
                findings.append("AgentKit Codex marketplace is missing; run `agentkit init`")
            skill_path = repo / config.skills.output
            if skill_path.exists():
                ok.append("runtime AgentKit skill output exists")
            else:
                findings.append("Generated AgentKit skill is missing; run `agentkit skill`")
        except Exception as exc:
            findings.append(f"Unable to load agentkit.yml: {exc}")
    else:
        findings.append("Missing agentkit.yml; run `agentkit init`")

    for doc in configured_doc_paths:
        if (repo / doc).exists():
            ok.append(f"{doc} exists")
        else:
            findings.append(f"Missing {doc}; run `agentkit init` or configure docs paths")

    if is_git_repo(repo):
        hook_path = git_path(repo, "hooks/pre-commit")
        if hook_path.exists():
            ok.append("pre-commit hook exists")
        else:
            recommendations.append("pre-commit hook missing; run `agentkit install-hooks` if local policy wants Git checks")
    codex_hooks_path = repo / ".codex" / "hooks.json"
    codex_config_path = repo / ".codex" / "config.toml"
    if _has_codex_watchdog_hook(codex_hooks_path, _codex_watchdog_command(".agentkit/codex-stop-hook.log")) and _codex_hooks_feature_enabled(codex_config_path):
        ok.append("Codex watchdog hook is installed")
    else:
        recommendations.append("Codex watchdog hook missing; run `agentkit install-codex-watchdog --repo-local` to enable Stop-hook reminders")

    code = 1 if findings else 0
    return (
        code,
        "\n\n".join(
            [
                section("AgentKit Doctor", ["ready" if code == 0 else "needs_attention"]),
                section("Ready Checks", bullet(ok)),
                section("Recommended Actions", bullet(findings)),
                section("Optional Improvements", bullet(recommendations)),
            ]
        ),
    )


def start_task(
    repo: Path,
    component_names: list[str] | None = None,
    paths: list[str] | None = None,
    task: str | None = None,
    plan: str | None = None,
    focus_notes: list[str] | None = None,
    focus_docs: list[str] | None = None,
) -> str:
    config = load_config(repo)
    explicit_focus_docs = focus_docs or []
    changed = paths or (changed_paths(repo) if is_git_repo(repo) else [])
    analysis_paths = [*changed, *explicit_focus_docs]
    components = find_components(config, analysis_paths, component_names or [], task or "")
    docs = sorted(dict.fromkeys([*recommended_docs(repo, config, components), *explicit_focus_docs]))
    gaps = design_gaps(repo, components)
    checks = suggested_checks(config, components)
    review_expected = _review_expected(config, components, task or "")
    task_id = DEFAULT_TASK_ID
    state = {
        "task_id": task_id,
        "status": "open",
        "task": task or "",
        "plan": plan or "",
        "focus_notes": focus_notes or [],
        "focus_docs": explicit_focus_docs,
        "components": [component.name for component in components],
        "durable_intent_sources": docs,
        "changed_paths": changed,
        "design_gaps": gaps,
        "suggested_checks": checks,
        "review_expected": review_expected,
        "diff_fingerprint": diff_fingerprint(repo),
    }
    write_task_state(repo, state, task_id)
    return "\n\n".join(
        [
            section("Task Started", [task_id]),
            section("Durable Intent Sources", bullet(docs)),
            section("Intent System Reminder", INTENT_SYSTEM_REMINDER),
            section("Focus Notes", bullet(focus_notes or [])),
            section("Affected Components", bullet([_component_label(item) for item in components])),
            section("Potential Design Gaps", bullet(gaps)),
            section("Suggested Tests And Checks", bullet(checks)),
            section("Review Expected", ["yes" if review_expected else "not required by current AgentKit policy"]),
        ]
    )


def close_task(
    repo: Path,
    task_id: str | None = None,
    blocked_question: str | None = None,
    review_complete: bool = False,
    skip_review_reason: str | None = None,
) -> tuple[int, str]:
    task_name = task_id or DEFAULT_TASK_ID
    path = task_path(repo, task_name)
    state = load_task_state(repo, task_name) or {}
    current_changes = changed_paths(repo) if is_git_repo(repo) else []
    current_fingerprint = diff_fingerprint(repo)
    if not path.exists():
        return (
            1,
            "\n\n".join(
                [
                    section("Close Status", ["needs_work"]),
                    section("Missing Task State", ["Run `agentkit start` before closing a task."]),
                ]
            ),
        )
    if blocked_question:
        state.update(
            {
                "task_id": task_name,
                "status": "blocked",
                "blocked_question": blocked_question,
                "open_changes": current_changes,
                "diff_fingerprint": current_fingerprint,
            }
        )
        write_task_state(repo, state, task_name)
        return (
            0,
            "\n\n".join(
                [
                    section("Close Status", ["blocked"]),
                    section("Blocked Human Question", [blocked_question]),
                    section("Next Step", ["Wait for human input before continuing this task."]),
                ]
            ),
        )
    if current_changes:
        return (
            1,
            "\n\n".join(
                [
                    section("Close Status", ["needs_work"]),
                    section("Open Changes", bullet(current_changes)),
                    section(
                        "Required Action",
                        [
                            "Commit or intentionally stage/handoff the changes according to local policy.",
                            "If blocked on human input, run `agentkit close --blocked-question \"...\"`.",
                        ],
                    ),
                ]
            ),
        )
    if not has_receipt(repo, "checks", current_fingerprint):
        return (
            1,
            "\n\n".join(
                [
                    section("Close Status", ["needs_work"]),
                    section("Missing Check Receipt", ["Run `agentkit check` for the current diff before closing."]),
                ]
            ),
        )
    if review_complete:
        state["review_complete"] = True
        state["review_fingerprint"] = current_fingerprint
    if skip_review_reason:
        state["skip_review_reason"] = skip_review_reason
        state["skip_review_fingerprint"] = current_fingerprint
    has_current_review = state.get("review_complete") and state.get("review_fingerprint") == current_fingerprint
    has_current_skip = state.get("skip_review_reason") and state.get("skip_review_fingerprint") == current_fingerprint
    if state.get("review_expected") and not has_current_review and not has_current_skip:
        write_task_state(repo, state, task_name)
        return (
            1,
            "\n\n".join(
                [
                    section("Close Status", ["needs_work"]),
                    section(
                        "Missing Review Receipt",
                        ["Pass `--review-complete` after review loop, or `--skip-review-reason \"...\"` for low-risk work."],
                    ),
                ]
            ),
        )
    close_status = "completed"
    state.update({"task_id": task_name, "status": close_status, "diff_fingerprint": current_fingerprint})
    write_task_state(repo, state, task_name)
    parts = [section("Close Status", [close_status])]
    if has_current_skip:
        parts.append(section("Review Skipped", [str(state["skip_review_reason"])]))
    return (0, "\n\n".join(parts))


def install_hooks(repo: Path, force: bool = False) -> str:
    if not is_git_repo(repo):
        raise ValueError("install-hooks requires a Git repository")
    hook_path = git_path(repo, "hooks/pre-commit")
    if hook_path.exists() and not force:
        return section("Hooks", ["pre-commit already exists; use --force to overwrite"])
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(
        "#!/bin/sh\n"
        "agentkit check\n",
        encoding="utf-8",
    )
    hook_path.chmod(0o755)
    return section("Hooks Installed", [relpath(hook_path, repo)])


def install_codex_watchdog(
    repo: Path,
    *,
    scope: str = "repo",
    force: bool = False,
    log_path: str = ".agentkit/codex-stop-hook.log",
    codex_home: Path | None = None,
) -> str:
    if scope not in {"repo", "user"}:
        raise ValueError("scope must be 'repo' or 'user'")
    target_root = repo / ".codex" if scope == "repo" else _codex_home(codex_home)
    hooks_path = target_root / "hooks.json"
    config_path = target_root / "config.toml"
    target_root.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    command = _codex_watchdog_command(log_path)
    _ensure_codex_watchdog_hook(hooks_path, command, force, created)
    _ensure_codex_hooks_feature(config_path, created)
    return "\n\n".join(
        [
            section("Codex Watchdog Installed", [scope]),
            section("Files", bullet(created or [str(hooks_path), str(config_path)])),
            section(
                "Next Verification",
                [
                    "Start a new Codex session in this repo, leave an AgentKit task open, and confirm the Stop hook writes the diagnostic log or continues the turn.",
                ],
            ),
        ]
    )


def codex_stop_hook(repo: Path, payload_text: str, log_path: str | None = None) -> tuple[int, str]:
    payload: dict[str, object] = {}
    if payload_text.strip():
        loaded = json.loads(payload_text)
        if isinstance(loaded, dict):
            payload = loaded
    hook_repo = _repo_from_hook_payload(repo, payload)
    sample = sample_lifecycle(hook_repo)
    if log_path:
        _append_codex_stop_log(hook_repo, log_path, sample.state)
    if sample.state not in {"needs_work", "ready_to_close"}:
        return (0, "")
    reminder = render_reminder(sample)
    reason = (
        f"{reminder}\n\n"
        "AgentKit has not reached a valid closeout state. Continue the task, complete the missing gates, "
        "or run `agentkit close --blocked-question \"...\"` if human input is required."
    )
    return (0, json.dumps({"decision": "block", "reason": reason}))


def orient(
    repo: Path,
    component_names: list[str] | None = None,
    paths: list[str] | None = None,
    task: str | None = None,
) -> str:
    config = load_config(repo)
    components = find_components(config, paths or [], component_names or [], task or "")
    docs = recommended_docs(repo, config, components)
    gaps = design_gaps(repo, components)
    checks = suggested_checks(config, components)
    impact = likely_impact(config, components, task or "")

    lines = [
        section("Affected Components", bullet([_component_label(item) for item in components])),
        section("Read First", bullet(docs)),
        section("Intent System Reminder", INTENT_SYSTEM_REMINDER),
        section("Potential Design Gaps", bullet(gaps)),
        section("Likely Design Impact", bullet(impact)),
        section("Suggested Tests And Checks", bullet(checks)),
    ]
    return "\n\n".join(lines)


def intent_guidance(repo: Path, component_name: str | None, change_type: str | None) -> str:
    config = load_config(repo)
    components = find_components(config, [], [component_name] if component_name else [], change_type or "")
    target_docs = recommended_docs(repo, config, components)
    additions: list[str] = []
    change = (change_type or "").lower()
    if change in {"architecture", "data_model", "public_api", "orchestration", "workflow"}:
        decisions = config.docs.decisions or "docs/decisions"
        additions.append(f"Consider an ADR under {decisions}/ for the {change} decision.")
    if components:
        for component in components:
            component_dir = f"{config.docs.root}/components/{component.name}"
            additions.append(f"If missing, create {component_dir}/testing.md for validation strategy.")
    return "\n\n".join(
        [
            section("Record Durable Intent In", bullet(target_docs)),
            section("Templates Or Additions To Consider", bullet(additions)),
            section(
                "Agent Responsibility",
                [
                    "The LLM agent writes the design content.",
                    "AgentKit only routes the intent to the right repository location and reminds the agent which headings/docs matter.",
                ],
            ),
        ]
    )


def docs_impact(repo: Path, paths: list[str] | None = None) -> str:
    config = load_config(repo)
    changed = paths or (changed_paths(repo) if is_git_repo(repo) else [])
    components = find_components(config, changed, [], "")
    related_docs = sorted({doc for component in components for doc in component.docs})
    docs_changed = [
        path
        for path in changed
        if path.startswith(f"{config.docs.root}/") or path in related_docs
    ]
    missing = [doc for doc in related_docs if doc not in docs_changed]
    mapped_paths = [
        path
        for path in changed
        if any(matches_any(path, component.code) or matches_any(path, component.docs) for component in config.components.values())
    ]
    unmapped = [path for path in changed if path not in mapped_paths and path != "agentkit.yml"]
    return "\n\n".join(
        [
            section("Changed Paths", bullet(changed)),
            section("Unmapped Changed Paths", bullet(unmapped)),
            section("Affected Components", bullet([_component_label(item) for item in components])),
            section("Related Docs", bullet(related_docs)),
            section("Docs Changed", bullet(docs_changed)),
            section(
                "Persistence Decision Needed",
                bullet(missing)
                + [
                    "AgentKit is not saying every related doc must change. Decide whether this work changes durable intent, public behavior, boundaries, workflows, or testing expectations.",
                    "If it does, update the relevant docs or tests. If it does not, mention why no persistence update was needed. If the right answer depends on missing human intent, ask the human or close as blocked.",
                ]
                if missing
                else [
                    "No related docs are missing from the current change set, based on AgentKit mapping.",
                    "Still decide whether the work changes durable intent, behavior, boundaries, workflows, or testing expectations; if not, a short no-persistence-needed note is enough.",
                ],
            ),
        ]
    )


def check(repo: Path) -> tuple[int, str]:
    config = load_config(repo)
    errors = validate_manifest(repo, config)
    lint_code, lint_text = lint_architecture(repo)
    maintainability_code, maintainability_text = lint_maintainability(repo)
    impact_text = docs_impact(repo)
    code = 1 if errors or lint_code or maintainability_code else 0
    if code == 0:
        write_receipt(repo, "checks", diff_fingerprint(repo), {"status": "passed"})
    parts = [
        section("Manifest", ["OK"] if not errors else bullet(errors)),
        impact_text,
        lint_text,
        maintainability_text,
        section("Lifecycle Reminder", [reminder_text(repo)]),
    ]
    return (code, "\n\n".join(parts))


def status_task(repo: Path, task_id: str | None = None) -> str:
    return status_text(repo, task_id)


def remind_task(repo: Path, task_id: str | None = None) -> str:
    return reminder_text(repo, task_id)


def review_guidance(
    repo: Path,
    component_names: list[str] | None = None,
    paths: list[str] | None = None,
    task: str | None = None,
) -> str:
    config = load_config(repo)
    changed = paths or (changed_paths(repo) if is_git_repo(repo) else [])
    components = find_components(config, changed, component_names or [], task or "")
    docs = recommended_docs(repo, config, components)
    review_expected = _review_expected(config, components, task or "")
    reviewer_steps = [
        "Spawn or request a clean-context reviewer when your environment supports it.",
        "Give the reviewer durable intent source paths first, then changed files and validation output.",
        "Do not make an inline summary the source of truth; if you include one, label it as a convenience summary and tell the reviewer to verify it against the durable docs.",
        "Tell the reviewer to compare the durable human intent docs and original task against the implementation.",
        "Ask it to report intent drift, unsupported durable decisions, missing tests, stale docs, architecture violations, and hidden failure modes.",
        "If the implementation makes a product, architecture, API, workflow, or taste decision that the intent files do not support, document it, revise it, or bring it back to the human as a blocked question.",
        "Fix meaningful findings before asking the human to spend attention.",
        "After fixing reviewer findings, run another clean-context review pass.",
        "Repeat review -> fix -> review until no meaningful findings remain, or only low-value residual risks are left for the human.",
    ]
    return "\n\n".join(
        [
            section("Review Expected", ["yes" if review_expected else "not required by current AgentKit policy"]),
            section("Durable Intent Sources", bullet(docs)),
            section("Reviewer Should Read", bullet(docs)),
            section("Reviewer Should Inspect", bullet(changed)),
            section("Instruction For Implementing Agent", reviewer_steps),
            section(
                "Review Loop Policy",
                [
                    "One review pass is not a loop.",
                    "A loop requires at least: review, fix, second review.",
                    "If the second review finds meaningful issues, continue the loop.",
                ],
            ),
        ]
    )


def generate_skill(repo: Path) -> str:
    config = load_config(repo)
    output = repo / config.skills.output
    output.parent.mkdir(parents=True, exist_ok=True)
    component_names = ", ".join(sorted(config.components)) or "none configured"
    source = repo / config.skills.source
    template = source.read_text(encoding="utf-8") if source.exists() else DEFAULT_SKILL_MD
    content = template.replace("{{ component_names }}", component_names)
    output.write_text(content, encoding="utf-8")
    return "\n\n".join(
        [
            section("Skill Generated", [relpath(output, repo)]),
            section("Skill Source", [relpath(source, repo) if source.exists() else "built-in default"]),
        ]
    )


def validate_manifest(repo: Path, config: AgentKitConfig) -> list[str]:
    errors: list[str] = []
    for path in [config.docs.design, config.docs.workflow]:
        if path and not (repo / path).exists():
            errors.append(f"Missing docs file: {path}")
    for component in config.components.values():
        for doc in component.docs:
            if not (repo / doc).exists():
                errors.append(f"Component {component.name} references missing doc: {doc}")
        for code_path in component.code:
            if not _pattern_has_match(repo, code_path):
                errors.append(f"Component {component.name} references missing code path/pattern: {code_path}")
    for layer in config.layers.values():
        for pattern in layer.paths:
            if not _pattern_has_match(repo, pattern):
                errors.append(f"Layer {layer.name} references missing path/pattern: {pattern}")
    for budget in config.maintainability.budgets:
        for pattern in budget.paths:
            if not _pattern_has_match(repo, pattern):
                errors.append(f"Maintainability budget {budget.name} references missing path/pattern: {pattern}")
    return errors


def lint_architecture(repo: Path) -> tuple[int, str]:
    config = load_config(repo)
    if not config.layers:
        return (0, section("Architecture Lint", ["No layers configured"]))

    files_by_layer: dict[str, list[Path]] = {
        name: [path for path in expand_patterns(repo, layer.paths) if path.suffix == ".py"]
        for name, layer in config.layers.items()
    }
    path_to_layer: dict[str, str] = {}
    for name, files in files_by_layer.items():
        for path in files:
            path_to_layer[relpath(path, repo)] = name

    module_to_layer = _python_module_index(repo, path_to_layer)
    violations: list[str] = []
    for layer_name, files in files_by_layer.items():
        layer = config.layers[layer_name]
        allowed = set(layer.may_import) | {layer_name}
        for file_path in files:
            for imported in _imports_from(file_path, repo, module_to_layer):
                imported_layer = _resolve_imported_layer(imported, module_to_layer)
                if imported_layer and imported_layer not in allowed:
                    violations.append(
                        f"{relpath(file_path, repo)} ({layer_name}) imports {imported} ({imported_layer}), allowed: {sorted(allowed)}"
                    )
    return (1 if violations else 0, section("Architecture Lint", bullet(violations) if violations else ["OK"]))


def find_components(
    config: AgentKitConfig,
    paths: list[str],
    component_names: list[str],
    task: str,
) -> list[ComponentConfig]:
    selected: dict[str, ComponentConfig] = {}
    for name in component_names:
        if name and name in config.components:
            selected[name] = config.components[name]
    normalized_paths = [path.replace("\\", "/") for path in paths]
    for component in config.components.values():
        if any(matches_any(path, component.code) or matches_any(path, component.docs) for path in normalized_paths):
            selected[component.name] = component
    task_tokens = _meaningful_tokens(task)
    if task_tokens:
        for component in config.components.values():
            component_tokens = {
                *_meaningful_tokens(component.name),
                *_meaningful_tokens(component.description),
                *component.keywords,
            }
            if task_tokens & component_tokens:
                selected[component.name] = component
    return [selected[name] for name in sorted(selected)]


def recommended_docs(repo: Path, config: AgentKitConfig, components: list[ComponentConfig]) -> list[str]:
    docs: list[str] = []
    for path in [config.docs.design, config.docs.workflow]:
        if path:
            docs.append(path)
    for component in components:
        docs.extend(component.docs)
    return sorted(dict.fromkeys(docs))


def design_gaps(repo: Path, components: list[ComponentConfig]) -> list[str]:
    gaps: list[str] = []
    for component in components:
        for doc in component.docs:
            if not (repo / doc).exists():
                gaps.append(f"{component.name}: missing {doc}")
    return gaps


def suggested_checks(config: AgentKitConfig, components: list[ComponentConfig]) -> list[str]:
    checks = ["agentkit docs-impact", "agentkit lint-architecture", "project tests relevant to changed behavior"]
    for component in components:
        if any("test" in doc for doc in component.docs):
            checks.append(f"review {component.name} testing docs")
    return sorted(dict.fromkeys(checks))


def likely_impact(config: AgentKitConfig, components: list[ComponentConfig], task: str) -> list[str]:
    impacts: set[str] = set()
    text = " ".join([task, *[component.name + " " + component.description for component in components]]).lower()
    keywords = {
        "public_api": ["api", "endpoint", "route", "sdk"],
        "data_model": ["model", "schema", "database", "migration", "table"],
        "architecture": ["architecture", "layer", "dependency", "boundary"],
        "workflow": ["workflow", "state", "lifecycle", "status"],
        "orchestration": ["agent", "symphony", "spawn", "worker", "run"],
        "tests": ["test", "tdd", "validation"],
    }
    for impact, words in keywords.items():
        if any(word in text for word in words):
            impacts.add(impact)
    return sorted(impacts)


def _write_if_missing(path: Path, content: str, created: list[str], force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path.name if path.parent == path.parent.parent else path.as_posix())


def _ensure_agentkit_agents_section(path: Path, created: list[str], force: bool) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_AGENT_MD, encoding="utf-8")
        created.append(path.name)
        return
    text = path.read_text(encoding="utf-8")
    if AGENTKIT_AGENT_SECTION_MARKER in text:
        return
    separator = "\n\n" if text.strip() else ""
    path.write_text(f"{text.rstrip()}{separator}{AGENTKIT_AGENT_SECTION}\n", encoding="utf-8")
    created.append(f"{path.name} AgentKit section")


def _ensure_agentkit_marketplace_entry(path: Path, created: list[str], force: bool) -> None:
    agentkit_entry = {
        "name": "agentkit",
        "source": {
            "source": "local",
            "path": "./plugins/agentkit",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CODEX_MARKETPLACE_JSON, encoding="utf-8")
        created.append(path.as_posix())
        return
    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    if not isinstance(data, dict):
        raise ValueError(".agents/plugins/marketplace.json must contain a JSON object")
    data.setdefault("name", "agentkit-local")
    interface = data.setdefault("interface", {})
    if isinstance(interface, dict):
        interface.setdefault("displayName", "AgentKit Local")
    plugins = data.setdefault("plugins", [])
    if not isinstance(plugins, list):
        raise ValueError(".agents/plugins/marketplace.json plugins field must be a list")
    for index, item in enumerate(plugins):
        if isinstance(item, dict) and item.get("name") == "agentkit":
            if force or not _is_agentkit_marketplace_entry(item):
                plugins[index] = agentkit_entry
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                created.append("marketplace AgentKit entry")
            return
    plugins.append(agentkit_entry)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    created.append("marketplace AgentKit entry")


def _ensure_codex_watchdog_hook(path: Path, command: str, force: bool, created: list[str]) -> None:
    agentkit_group = {
        "hooks": [
            {
                "type": "command",
                "command": command,
                "timeout": 30,
                "statusMessage": "Checking AgentKit task closeout",
            }
        ]
    }
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    else:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{path} hooks field must be a JSON object")
    stop_hooks = hooks.setdefault("Stop", [])
    if not isinstance(stop_hooks, list):
        raise ValueError(f"{path} hooks.Stop field must be a list")
    for index, group in enumerate(stop_hooks):
        if _is_agentkit_codex_stop_group(group):
            if force or not _is_expected_agentkit_codex_stop_group(group, command):
                stop_hooks[index] = agentkit_group
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                created.append(path.as_posix())
            return
    stop_hooks.append(agentkit_group)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    created.append(path.as_posix())


def _ensure_codex_hooks_feature(path: Path, created: list[str]) -> None:
    if not path.exists():
        path.write_text("[features]\ncodex_hooks = true\n", encoding="utf-8")
        created.append(path.as_posix())
        return
    text = path.read_text(encoding="utf-8")
    if _features_section_has_codex_hooks(text, "true") or re.search(r"(?m)^\s*features\.codex_hooks\s*=\s*true\s*$", text):
        return
    if re.search(r"(?m)^\s*features\.codex_hooks\s*=\s*false\s*$", text):
        updated = re.sub(r"(?m)^(\s*features\.codex_hooks\s*=\s*)false\s*$", r"\1true", text, count=1)
        path.write_text(updated, encoding="utf-8")
        created.append(path.as_posix())
        return
    inline_features = re.search(r"(?m)^(\s*features\s*=\s*\{)([^}\n]*)(\}\s*)$", text)
    if inline_features:
        body = inline_features.group(2)
        if re.search(r"\bcodex_hooks\s*=\s*true\b", body):
            return
        if re.search(r"\bcodex_hooks\s*=\s*false\b", body):
            new_body = re.sub(r"\bcodex_hooks\s*=\s*false\b", "codex_hooks = true", body, count=1)
        else:
            prefix = f"{body.rstrip()}, " if body.strip() else ""
            new_body = f"{prefix}codex_hooks = true "
        updated = text[: inline_features.start(2)] + new_body + text[inline_features.end(2) :]
        path.write_text(updated, encoding="utf-8")
        created.append(path.as_posix())
        return
    lines = text.splitlines()
    bounds = _features_section_bounds(lines)
    if bounds:
        start, end = bounds
        for index in range(start, end):
            if re.match(r"^\s*codex_hooks\s*=\s*false\s*$", lines[index]):
                lines[index] = re.sub(r"^(\s*codex_hooks\s*=\s*)false\s*$", r"\1true", lines[index])
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                created.append(path.as_posix())
                return
        lines.insert(start, "codex_hooks = true")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        created.append(path.as_posix())
        return
    if re.search(r"(?m)^\s*features\.", text):
        separator = "" if text.endswith("\n") or not text else "\n"
        path.write_text(f"{text}{separator}features.codex_hooks = true\n", encoding="utf-8")
        created.append(path.as_posix())
        return
    separator = "" if text.endswith("\n") or not text else "\n"
    path.write_text(f"{text}{separator}\n[features]\ncodex_hooks = true\n", encoding="utf-8")
    created.append(path.as_posix())


def _agents_path(repo: Path) -> Path:
    for name in ["AGENTS.md", "agents.md"]:
        candidate = repo / name
        if candidate.exists():
            return candidate
    return repo / "AGENTS.md"


def _has_agentkit_marketplace_entry(path: Path) -> bool:
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    if not isinstance(data, dict):
        return False
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        return False
    return any(isinstance(item, dict) and _is_agentkit_marketplace_entry(item) for item in plugins)


def _has_codex_watchdog_hook(path: Path, expected_command: str | None = None) -> bool:
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return False
    if not isinstance(data, dict):
        return False
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False
    stop_hooks = hooks.get("Stop")
    if not isinstance(stop_hooks, list):
        return False
    if expected_command:
        return any(_is_expected_agentkit_codex_stop_group(group, expected_command) for group in stop_hooks)
    return any(_is_agentkit_codex_stop_group(group) for group in stop_hooks)


def _codex_hooks_feature_enabled(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return bool(
        _features_section_has_codex_hooks(text, "true")
        or re.search(r"(?m)^\s*features\.codex_hooks\s*=\s*true\s*$", text)
        or re.search(r"(?m)^\s*features\s*=\s*\{[^}\n]*\bcodex_hooks\s*=\s*true\b[^}\n]*\}\s*$", text)
    )


def _is_agentkit_marketplace_entry(item: dict[str, object]) -> bool:
    source = item.get("source")
    policy = item.get("policy")
    return (
        item.get("name") == "agentkit"
        and isinstance(source, dict)
        and source.get("source") == "local"
        and source.get("path") == "./plugins/agentkit"
        and isinstance(policy, dict)
        and policy.get("installation") == "AVAILABLE"
        and policy.get("authentication") == "ON_INSTALL"
        and item.get("category") == "Productivity"
    )


def _is_agentkit_codex_stop_group(group: object) -> bool:
    return isinstance(group, dict) and any(
        isinstance(item, dict) and str(item.get("command", "")).startswith("agentkit codex-stop-hook")
        for item in group.get("hooks", [])
    )


def _is_expected_agentkit_codex_stop_group(group: object, expected_command: str) -> bool:
    return isinstance(group, dict) and any(
        isinstance(item, dict) and item.get("command") == expected_command for item in group.get("hooks", [])
    )


def _codex_watchdog_command(log_path: str) -> str:
    return f'agentkit codex-stop-hook --log "{log_path}"'


def _features_section_has_codex_hooks(text: str, value: str) -> bool:
    lines = text.splitlines()
    bounds = _features_section_bounds(lines)
    if not bounds:
        return False
    start, end = bounds
    return any(re.match(rf"^\s*codex_hooks\s*=\s*{value}\s*$", line) for line in lines[start:end])


def _features_section_bounds(lines: list[str]) -> tuple[int, int] | None:
    start: int | None = None
    for index, line in enumerate(lines):
        if re.match(r"^\s*\[features]\s*$", line):
            start = index + 1
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if re.match(r"^\s*\[[^\]]+]\s*$", lines[index]):
            end = index
            break
    return start, end


def _append_codex_stop_log(repo: Path, log_path: str, state: str) -> None:
    path = Path(log_path)
    if not path.is_absolute():
        path = repo / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8") if not path.exists() else None
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "Stop", "state": state}) + "\n")


def _codex_home(override: Path | None = None) -> Path:
    if override:
        return override
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return Path(env_home)
    return Path.home() / ".codex"


def _repo_from_hook_payload(default_repo: Path, payload: dict[str, object]) -> Path:
    cwd = payload.get("cwd")
    start = Path(str(cwd)).resolve() if cwd else default_repo
    for candidate in [start, *start.parents]:
        if (candidate / "agentkit.yml").exists():
            return candidate
    return default_repo


def _component_label(component: ComponentConfig) -> str:
    return f"{component.name}: {component.description}" if component.description else component.name


def _pattern_has_match(repo: Path, pattern: str) -> bool:
    if any(char in pattern for char in "*?["):
        return any(repo.glob(pattern.replace("\\", "/")))
    return (repo / pattern).exists()


def _imports_from(path: Path, repo: Path, module_to_layer: dict[str, str]) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_import_from(path, repo, node.module, node.level)
            if resolved:
                imports.append(resolved)
                imports.extend(
                    f"{resolved}.{alias.name}"
                    for alias in node.names
                    if _resolve_imported_layer(f"{resolved}.{alias.name}", module_to_layer)
                )
    return imports


def _resolve_import_from(path: Path, repo: Path, module: str | None, level: int) -> str | None:
    if level == 0:
        return module
    current = _module_name_for_path(path, repo)
    if not current:
        return module
    package_parts = current.split(".")[:-1]
    if level > 1:
        package_parts = package_parts[: -(level - 1)]
    if module:
        package_parts.extend(module.split("."))
    return ".".join(part for part in package_parts if part)


def _python_module_index(repo: Path, path_to_layer: dict[str, str]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path, layer in path_to_layer.items():
        if not path.endswith(".py"):
            continue
        module_name = _module_name_for_relpath(path)
        if module_name:
            index[module_name] = layer
    return index


def _module_name_for_path(path: Path, repo: Path) -> str | None:
    return _module_name_for_relpath(relpath(path, repo))


def _module_name_for_relpath(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    without_suffix = path[:-3]
    parts = without_suffix.split("/")
    if "src" in parts:
        parts = parts[parts.index("src") + 1 :]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else None


def _resolve_imported_layer(imported: str, module_to_layer: dict[str, str]) -> str | None:
    parts = imported.split(".")
    for end in range(len(parts), 0, -1):
        candidate = ".".join(parts[:end])
        if candidate in module_to_layer:
            return module_to_layer[candidate]
        dotted_prefix = f"{candidate}."
        descendant_layers = {
            layer
            for module, layer in module_to_layer.items()
            if module.startswith(dotted_prefix)
        }
        if len(descendant_layers) == 1:
            return next(iter(descendant_layers))
    return None


def _review_expected(config: AgentKitConfig, components: list[ComponentConfig], task: str) -> bool:
    text = " ".join([task, *[component.name + " " + component.description for component in components]]).lower()
    return any(item.lower() in text for item in config.review.require_for) or bool(components)


def _meaningful_tokens(text: str) -> set[str]:
    normalized = "".join(char.lower() if char.isalnum() else " " for char in text)
    return {
        token
        for token in normalized.split()
        if len(token) > 2 and token not in TASK_STOPWORDS
    }
