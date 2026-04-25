from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_TASK_ID = "current"


def task_path(repo: Path, task_id: str | None = None) -> Path:
    return repo / ".agentkit" / "tasks" / f"{task_id or DEFAULT_TASK_ID}.json"


def load_task_state(repo: Path, task_id: str | None = None) -> dict[str, Any] | None:
    path = task_path(repo, task_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_task_state(repo: Path, state: dict[str, Any], task_id: str | None = None) -> None:
    path = task_path(repo, task_id or str(state.get("task_id") or DEFAULT_TASK_ID))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
