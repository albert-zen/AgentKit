from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_NAME = "agentkit.yml"


@dataclass(frozen=True)
class DocsConfig:
    root: str = "docs"
    design: str = "docs/design.md"
    workflow: str | None = "docs/workflow.md"
    decisions: str | None = "docs/decisions"


@dataclass(frozen=True)
class ComponentConfig:
    name: str
    description: str = ""
    code: tuple[str, ...] = ()
    docs: tuple[str, ...] = ()
    required_docs: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class LayerConfig:
    name: str
    paths: tuple[str, ...] = ()
    may_import: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewConfig:
    require_for: tuple[str, ...] = ()
    default: str = "warn"


@dataclass(frozen=True)
class SkillConfig:
    source: str = "plugins/agentkit/skills/agentkit/SKILL.md"
    output: str = "plugins/agentkit/skills/agentkit/SKILL.md"


@dataclass(frozen=True)
class MaintainabilityBudgetConfig:
    name: str
    paths: tuple[str, ...] = ()
    max_lines: int | None = None
    max_functions: int | None = None
    max_classes: int | None = None
    mode: str = "warn"
    guidance: str = ""


@dataclass(frozen=True)
class MaintainabilityConfig:
    budgets: tuple[MaintainabilityBudgetConfig, ...] = ()


@dataclass(frozen=True)
class AgentKitConfig:
    version: int = 1
    docs: DocsConfig = field(default_factory=DocsConfig)
    components: dict[str, ComponentConfig] = field(default_factory=dict)
    layers: dict[str, LayerConfig] = field(default_factory=dict)
    review: ReviewConfig = field(default_factory=ReviewConfig)
    skills: SkillConfig = field(default_factory=SkillConfig)
    maintainability: MaintainabilityConfig = field(default_factory=MaintainabilityConfig)


def load_config(repo: Path, config_path: Path | None = None) -> AgentKitConfig:
    path = config_path or repo / DEFAULT_CONFIG_NAME
    if not path.exists():
        raise FileNotFoundError(f"AgentKit config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"AgentKit config must be a mapping: {path}")
    return parse_config(raw)


def parse_config(raw: dict[str, Any]) -> AgentKitConfig:
    docs_raw = raw.get("docs") or {}
    components_raw = raw.get("components") or {}
    layers_raw = raw.get("layers") or {}
    review_raw = raw.get("review") or {}
    skills_raw = raw.get("skills") or {}
    maintainability_raw = raw.get("maintainability") or {}

    docs = DocsConfig(
        root=str(docs_raw.get("root", "docs")),
        design=str(docs_raw.get("design", "docs/design.md")),
        workflow=_optional_str(docs_raw.get("workflow", "docs/workflow.md")),
        decisions=_optional_str(docs_raw.get("decisions", "docs/decisions")),
    )

    components = {
        str(name): ComponentConfig(
            name=str(name),
            description=str(value.get("description", "")),
            code=tuple(str(item) for item in value.get("code", []) or []),
            docs=tuple(str(item) for item in value.get("docs", []) or []),
            required_docs=tuple(str(item) for item in value.get("required_docs", []) or []),
            keywords=tuple(str(item).lower() for item in value.get("keywords", []) or []),
        )
        for name, value in components_raw.items()
        if isinstance(value, dict)
    }

    layers = {
        str(name): LayerConfig(
            name=str(name),
            paths=tuple(str(item) for item in value.get("paths", []) or []),
            may_import=tuple(str(item) for item in value.get("may_import", []) or []),
        )
        for name, value in layers_raw.items()
        if isinstance(value, dict)
    }

    review = ReviewConfig(
        require_for=tuple(str(item) for item in review_raw.get("require_for", []) or []),
        default=str(review_raw.get("default", "warn")),
    )

    skills = SkillConfig(
        source=str(skills_raw.get("source", "plugins/agentkit/skills/agentkit/SKILL.md")),
        output=str(skills_raw.get("output", "plugins/agentkit/skills/agentkit/SKILL.md")),
    )

    budgets_raw = maintainability_raw.get("budgets", []) if isinstance(maintainability_raw, dict) else []
    budgets = tuple(
        MaintainabilityBudgetConfig(
            name=str(value.get("name") or f"budget-{index + 1}"),
            paths=tuple(str(item) for item in value.get("paths", []) or []),
            max_lines=_optional_int(value.get("max_lines")),
            max_functions=_optional_int(value.get("max_functions")),
            max_classes=_optional_int(value.get("max_classes")),
            mode=str(value.get("mode", "warn")),
            guidance=str(value.get("guidance", "")),
        )
        for index, value in enumerate(budgets_raw)
        if isinstance(value, dict)
    )
    maintainability = MaintainabilityConfig(budgets=budgets)

    return AgentKitConfig(
        version=int(raw.get("version", 1)),
        docs=docs,
        components=components,
        layers=layers,
        review=review,
        skills=skills,
        maintainability=maintainability,
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
