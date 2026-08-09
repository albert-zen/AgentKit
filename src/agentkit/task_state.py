from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from agentkit.fs import write_json_atomic


DEFAULT_TASK_ID = "current"
TASK_STATE_SCHEMA_VERSION = 1
TASK_LIFECYCLE_STATUSES = {"open", "completed", "blocked"}


@dataclass(frozen=True)
class TaskState:
    """Persisted task facts; lifecycle readiness is deliberately not stored here."""

    schema_version: int = TASK_STATE_SCHEMA_VERSION
    task_id: str = DEFAULT_TASK_ID
    status: str = "open"
    task: str = ""
    plan: str = ""
    focus_notes: tuple[str, ...] = ()
    focus_docs: tuple[str, ...] = ()
    components: tuple[str, ...] = ()
    durable_intent_sources: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    design_gaps: tuple[str, ...] = ()
    suggested_checks: tuple[str, ...] = ()
    review_expected: bool = False
    diff_fingerprint: str = ""
    blocked_question: str | None = None
    open_changes: tuple[str, ...] = ()
    review_complete: bool = False
    review_fingerprint: str | None = None
    skip_review_reason: str | None = None
    skip_review_fingerprint: str | None = None
    extra: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TaskState:
        if not isinstance(raw, dict):
            raise ValueError("Task state must be a JSON object")
        schema_version = raw.get("schema_version", TASK_STATE_SCHEMA_VERSION)
        if type(schema_version) is not int or schema_version != TASK_STATE_SCHEMA_VERSION:
            raise ValueError(f"Unsupported task state schema_version: {schema_version}")

        known = {
            "schema_version",
            "task_id",
            "status",
            "task",
            "plan",
            "focus_notes",
            "focus_docs",
            "components",
            "durable_intent_sources",
            "changed_paths",
            "design_gaps",
            "suggested_checks",
            "review_expected",
            "diff_fingerprint",
            "blocked_question",
            "open_changes",
            "review_complete",
            "review_fingerprint",
            "skip_review_reason",
            "skip_review_fingerprint",
        }
        status = _string(raw, "status", "open")
        if status not in TASK_LIFECYCLE_STATUSES:
            raise ValueError(
                "Task state field `status` must be one of: blocked, completed, open; "
                f"got {status!r}"
            )
        return cls(
            schema_version=TASK_STATE_SCHEMA_VERSION,
            task_id=_string(raw, "task_id", DEFAULT_TASK_ID),
            status=status,
            task=_string(raw, "task"),
            plan=_string(raw, "plan"),
            focus_notes=_string_tuple(raw, "focus_notes"),
            focus_docs=_string_tuple(raw, "focus_docs"),
            components=_string_tuple(raw, "components"),
            durable_intent_sources=_string_tuple(raw, "durable_intent_sources"),
            changed_paths=_string_tuple(raw, "changed_paths"),
            design_gaps=_string_tuple(raw, "design_gaps"),
            suggested_checks=_string_tuple(raw, "suggested_checks"),
            review_expected=_boolean(raw, "review_expected"),
            diff_fingerprint=_string(raw, "diff_fingerprint"),
            blocked_question=_optional_string(raw, "blocked_question"),
            open_changes=_string_tuple(raw, "open_changes"),
            review_complete=_boolean(raw, "review_complete"),
            review_fingerprint=_optional_string(raw, "review_fingerprint"),
            skip_review_reason=_optional_string(raw, "skip_review_reason"),
            skip_review_fingerprint=_optional_string(raw, "skip_review_fingerprint"),
            extra={key: value for key, value in raw.items() if key not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            **self.extra,
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "status": self.status,
            "task": self.task,
            "plan": self.plan,
            "focus_notes": list(self.focus_notes),
            "focus_docs": list(self.focus_docs),
            "components": list(self.components),
            "durable_intent_sources": list(self.durable_intent_sources),
            "changed_paths": list(self.changed_paths),
            "design_gaps": list(self.design_gaps),
            "suggested_checks": list(self.suggested_checks),
            "review_expected": self.review_expected,
            "diff_fingerprint": self.diff_fingerprint,
            "open_changes": list(self.open_changes),
            "review_complete": self.review_complete,
        }
        optional = {
            "blocked_question": self.blocked_question,
            "review_fingerprint": self.review_fingerprint,
            "skip_review_reason": self.skip_review_reason,
            "skip_review_fingerprint": self.skip_review_fingerprint,
        }
        result.update({key: value for key, value in optional.items() if value is not None})
        return result

    def with_changes(self, **changes: Any) -> TaskState:
        return replace(self, **changes)


def task_path(repo: Path, task_id: str | None = None) -> Path:
    return repo / ".agentkit" / "tasks" / f"{task_id or DEFAULT_TASK_ID}.json"


def load_task_state(repo: Path, task_id: str | None = None) -> TaskState | None:
    path = task_path(repo, task_id)
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return TaskState.from_dict(raw)


def write_task_state(repo: Path, state: TaskState, task_id: str | None = None) -> None:
    path = task_path(repo, task_id or state.task_id)
    write_json_atomic(path, state.to_dict())


def _string(raw: dict[str, Any], key: str, default: str = "") -> str:
    value = raw.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"Task state field `{key}` must be a string")
    return value


def _optional_string(raw: dict[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Task state field `{key}` must be a string or null")
    return value


def _string_tuple(raw: dict[str, Any], key: str) -> tuple[str, ...]:
    value = raw.get(key, []) or []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"Task state field `{key}` must be a list of strings")
    return tuple(value)


def _boolean(raw: dict[str, Any], key: str) -> bool:
    value = raw.get(key, False)
    if not isinstance(value, bool):
        raise ValueError(f"Task state field `{key}` must be a boolean")
    return value
