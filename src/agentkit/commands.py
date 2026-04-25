from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from agentkit.config import AgentKitConfig, ComponentConfig, LayerConfig, load_config
from agentkit.fs import expand_patterns, matches_any, relpath
from agentkit.git import changed_paths, diff_fingerprint, git_path, is_git_repo
from agentkit.render import bullet, section


DEFAULT_AGENT_MD = """# AGENTS.md

This repository uses AgentKit.

Before changing code:
- Run `agentkit start` with the relevant component, task, or changed paths.
- Read the durable intent sources and docs AgentKit recommends.
- Ask the human for design when AgentKit reports a design gap for a product, architecture, API, data model, workflow, or state-machine change.

After changing code:
- Run relevant tests.
- Run `agentkit check`.
- Update docs when behavior, architecture, public contracts, workflows, data models, or testing strategy changed.
- Run `agentkit review-guidance` for non-trivial work.
- Run `agentkit close --review-complete` before ending a reviewed task. If blocked, record the human question with `agentkit close --blocked-question "..."`.
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
  output: .codex/skills/agentkit/SKILL.md
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


def init_repo(repo: Path, force: bool = False) -> str:
    created: list[str] = []
    _write_if_missing(repo / "AGENTS.md", DEFAULT_AGENT_MD, created, force)
    _write_if_missing(repo / "agentkit.yml", DEFAULT_AGENTKIT_YML, created, force)
    for directory in [
        repo / "docs",
        repo / "docs" / "architecture",
        repo / "docs" / "components",
        repo / "docs" / "decisions",
        repo / "docs" / "specs" / "active",
        repo / "docs" / "specs" / "completed",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
    _write_if_missing(repo / "docs" / "design.md", "# Design\n\nStatus: Draft\n", created, force)
    _write_if_missing(repo / "docs" / "workflow.md", "# Workflow\n\nStatus: Draft\n", created, force)
    _write_if_missing(repo / "docs" / "architecture" / "dependency-rules.md", "# Dependency Rules\n", created, force)
    return section("AgentKit Init", bullet(created or ["No files changed"]))


def start_task(
    repo: Path,
    component_names: list[str] | None = None,
    paths: list[str] | None = None,
    task: str | None = None,
    plan: str | None = None,
) -> str:
    config = load_config(repo)
    changed = paths or (changed_paths(repo) if is_git_repo(repo) else [])
    components = find_components(config, changed, component_names or [], task or "")
    docs = recommended_docs(repo, config, components)
    gaps = design_gaps(repo, components)
    checks = suggested_checks(config, components)
    review_expected = _review_expected(config, components, task or "")
    task_dir = repo / ".agentkit" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    task_id = "current"
    state = {
        "task_id": task_id,
        "status": "open",
        "task": task or "",
        "plan": plan or "",
        "components": [component.name for component in components],
        "durable_intent_sources": docs,
        "changed_paths": changed,
        "design_gaps": gaps,
        "suggested_checks": checks,
        "review_expected": review_expected,
        "diff_fingerprint": diff_fingerprint(repo),
    }
    (task_dir / f"{task_id}.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return "\n\n".join(
        [
            section("Task Started", [task_id]),
            section("Durable Intent Sources", bullet(docs)),
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
    task_name = task_id or "current"
    task_path = repo / ".agentkit" / "tasks" / f"{task_name}.json"
    state: dict[str, object] = {}
    if task_path.exists():
        state = json.loads(task_path.read_text(encoding="utf-8"))
    current_changes = changed_paths(repo) if is_git_repo(repo) else []
    current_fingerprint = diff_fingerprint(repo)
    if not task_path.exists():
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
        task_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
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
    check_receipt = repo / ".agentkit" / "receipts" / "checks" / f"{current_fingerprint}.json"
    if not check_receipt.exists():
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
    if state.get("review_expected") and not has_current_review:
        task_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
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
    state.update({"task_id": task_name, "status": "completed", "diff_fingerprint": current_fingerprint})
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return (0, section("Close Status", ["completed"]))


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


def _write_receipt(repo: Path, kind: str, fingerprint: str, payload: dict[str, str]) -> None:
    receipt_dir = repo / ".agentkit" / "receipts" / kind
    receipt_dir.mkdir(parents=True, exist_ok=True)
    content = {"fingerprint": fingerprint, **payload}
    (receipt_dir / f"{fingerprint}.json").write_text(json.dumps(content, indent=2), encoding="utf-8")


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
        section("Potential Design Gaps", bullet(gaps)),
        section("Likely Design Impact", bullet(impact)),
        section("Suggested Tests And Checks", bullet(checks)),
    ]
    if gaps:
        lines.append(
            section(
                "Human Design Check",
                [
                    "If this task changes product behavior, API, data model, architecture, workflow, or state transitions, ask the human to approve the missing design before implementing that part.",
                    "If other parts are clear, continue with those and isolate the blocked decision.",
                ],
            )
        )
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
                "Docs Impact Assessment Needed",
                bullet(missing)
                if missing
                else ["No related docs are missing from the current change set, based on AgentKit mapping."],
            ),
        ]
    )


def check(repo: Path) -> tuple[int, str]:
    config = load_config(repo)
    errors = validate_manifest(repo, config)
    lint_code, lint_text = lint_architecture(repo)
    impact_text = docs_impact(repo)
    parts = [
        section("Manifest", ["OK"] if not errors else bullet(errors)),
        impact_text,
        lint_text,
    ]
    code = 1 if errors or lint_code else 0
    if code == 0:
        _write_receipt(repo, "checks", diff_fingerprint(repo), {"status": "passed"})
    return (code, "\n\n".join(parts))


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
        "Ask it to report intent drift, unsupported assumptions, missing tests, stale docs, architecture violations, and hidden failure modes.",
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
    content = f"""---
name: agentkit
description: Use AgentKit to orient coding agents, enforce repository-local maintainability rules, check docs impact, and request clean-context review guidance.
---

# AgentKit Skill

This repository uses AgentKit.

## Start Of Task

Run:

```text
agentkit start
```

If you know the component, run:

```text
agentkit start --component <name>
```

Configured components: {component_names}

## During Design

Use:

```text
agentkit intent-guidance --component <name> --change-type <type>
```

Write the actual design content yourself. AgentKit tells you where it belongs.

## Before Review

Run:

```text
agentkit check
agentkit review-guidance
```

If review is expected, spawn or request a clean-context reviewer with the guidance AgentKit returns.

## Close Task

Before ending the task, run:

```text
agentkit close --review-complete
```

If blocked on human input, run:

```text
agentkit close --blocked-question "..."
```
"""
    output.write_text(content, encoding="utf-8")
    return section("Skill Generated", [relpath(output, repo)])


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
