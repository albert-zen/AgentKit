from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agentkit.policy import (
    NAMED_RULE_IDS,
    REMINDER_KEYS,
    SUPPORTED_PRESETS,
    LifecycleRuleConfig,
    PresetConfig,
    ReminderConfig,
)


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
    preset: PresetConfig | None = None
    rules: dict[str, LifecycleRuleConfig] = field(default_factory=dict)
    reminders: ReminderConfig = field(default_factory=ReminderConfig)


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
    preset_raw = raw.get("preset")
    rules_raw = raw["rules"] if "rules" in raw else {}
    reminders_raw = raw["reminders"] if "reminders" in raw else {}

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

    preset = _parse_preset(preset_raw)
    rules = _parse_rules(rules_raw)
    reminders = _parse_reminders(reminders_raw)
    _validate_materialized_policy(preset, rules_raw, reminders_raw)

    return AgentKitConfig(
        version=int(raw.get("version", 1)),
        docs=docs,
        components=components,
        layers=layers,
        review=review,
        skills=skills,
        maintainability=maintainability,
        preset=preset,
        rules=rules,
        reminders=reminders,
    )


def _parse_preset(raw: object) -> PresetConfig | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("AgentKit config field `preset` must be a mapping")
    unknown = set(raw) - {"source", "name", "version"}
    if unknown:
        raise ValueError(f"Unknown preset option: {sorted(unknown)[0]}")
    source = raw.get("source", "")
    name = raw.get("name", "")
    version = raw.get("version", 0)
    if not isinstance(source, str) or not isinstance(name, str) or type(version) is not int:
        raise ValueError("Preset provenance requires string source/name and an integer version")
    if source != "agentkit" or name not in SUPPORTED_PRESETS or SUPPORTED_PRESETS[name] != version:
        raise ValueError(f"Unknown AgentKit preset provenance: source={source!r}, name={name!r}, version={version}")
    return PresetConfig(source=source, name=name, version=version)


def _parse_rules(raw: object) -> dict[str, LifecycleRuleConfig]:
    if not isinstance(raw, dict):
        raise ValueError("AgentKit config field `rules` must be a mapping")
    unknown_rules = set(raw) - set(NAMED_RULE_IDS)
    if unknown_rules:
        raise ValueError(f"Unknown lifecycle rule: {sorted(unknown_rules)[0]}")

    result: dict[str, LifecycleRuleConfig] = {}
    for rule_id in NAMED_RULE_IDS:
        value = raw.get(rule_id, {})
        if not isinstance(value, dict):
            raise ValueError(f"Lifecycle rule `{rule_id}` must be a mapping")
        allowed = {"enabled", "severity"}
        if rule_id == "review_addressed":
            allowed.add("allow_skip")
        unknown_options = set(value) - allowed
        if unknown_options:
            option = sorted(unknown_options)[0]
            raise ValueError(f"Lifecycle rule `{rule_id}` does not support option `{option}`")
        enabled = value.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"Lifecycle rule `{rule_id}` option `enabled` must be a boolean")
        severity = value.get("severity", "error")
        if severity not in {"error", "warning"}:
            raise ValueError(f"Lifecycle rule `{rule_id}` severity must be `error` or `warning`")
        allow_skip = value.get("allow_skip", True)
        if not isinstance(allow_skip, bool):
            raise ValueError(f"Lifecycle rule `{rule_id}` option `allow_skip` must be a boolean")
        result[rule_id] = LifecycleRuleConfig(
            rule_id=rule_id,
            enabled=enabled,
            severity=severity,
            allow_skip=allow_skip,
        )
    return result


def _parse_reminders(raw: object) -> ReminderConfig:
    if not isinstance(raw, dict):
        raise ValueError("AgentKit config field `reminders` must be a mapping")
    unknown = set(raw) - set(REMINDER_KEYS)
    if unknown:
        raise ValueError(f"Unknown lifecycle reminder: {sorted(unknown)[0]}")
    values: dict[str, bool] = {}
    for key in REMINDER_KEYS:
        value = raw.get(key, True)
        if not isinstance(value, bool):
            raise ValueError(f"Lifecycle reminder `{key}` must be a boolean")
        values[key] = value
    return ReminderConfig(**values)


def _validate_materialized_policy(
    preset: PresetConfig | None, rules_raw: object, reminders_raw: object
) -> None:
    if preset is None:
        return
    if not isinstance(rules_raw, dict) or not isinstance(reminders_raw, dict):
        return  # The shape-specific parser has already produced the actionable error.
    missing_rules = set(NAMED_RULE_IDS) - set(rules_raw)
    missing_reminders = set(REMINDER_KEYS) - set(reminders_raw)
    if missing_rules or missing_reminders:
        missing = [
            *[f"rules.{rule_id}" for rule_id in sorted(missing_rules)],
            *[f"reminders.{key}" for key in sorted(missing_reminders)],
        ]
        raise ValueError(
            f"Materialized preset `{preset.name}` is incomplete; add explicit values for: "
            + ", ".join(missing)
        )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
