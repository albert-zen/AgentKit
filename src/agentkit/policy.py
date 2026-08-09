from __future__ import annotations

from dataclasses import dataclass


NAMED_RULE_IDS = (
    "working_tree_clean",
    "check_receipt_current",
    "review_addressed",
    "blocked_question_recorded",
)
REMINDER_KEYS = ("open_task", "ready_to_close", "stale_terminal")
SUPPORTED_PRESETS = {"recommended-v1": 1}


@dataclass(frozen=True)
class PresetConfig:
    source: str
    name: str
    version: int


@dataclass(frozen=True)
class LifecycleRuleConfig:
    rule_id: str
    enabled: bool = True
    severity: str = "error"
    allow_skip: bool = True


@dataclass(frozen=True)
class ReminderConfig:
    open_task: bool = True
    ready_to_close: bool = True
    stale_terminal: bool = True
