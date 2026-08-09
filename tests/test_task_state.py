from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from agentkit.cli import main
from agentkit.commands import check, close_task, init_repo, start_task, update_task
from agentkit.task_state import TaskState, load_task_state, write_task_state
from agentkit.receipts import has_receipt, write_receipt


def test_unversioned_task_state_loads_as_schema_v1_and_migrates_on_write(tmp_path: Path) -> None:
    path = tmp_path / ".agentkit" / "tasks" / "current.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"task_id": "current", "task": "legacy", "focus_notes": ["keep me"], "custom": 7}),
        encoding="utf-8",
    )

    state = load_task_state(tmp_path)

    assert isinstance(state, TaskState)
    assert state.schema_version == 1
    assert state.task == "legacy"
    assert state.focus_notes == ("keep me",)
    write_task_state(tmp_path, state)
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["schema_version"] == 1
    assert persisted["custom"] == 7


def test_unknown_task_state_schema_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / ".agentkit" / "tasks" / "current.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"schema_version": 99, "task_id": "current"}', encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported task state schema_version: 99"):
        load_task_state(tmp_path)

    path.write_text('{"schema_version": "1", "task_id": "current"}', encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported task state schema_version: 1"):
        load_task_state(tmp_path)


@pytest.mark.parametrize("status", ["needs_work", "ready_to_close", "anything"])
def test_persisted_task_state_rejects_derived_or_unknown_status(tmp_path: Path, status: str) -> None:
    path = tmp_path / ".agentkit" / "tasks" / "current.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "status": status}), encoding="utf-8")

    with pytest.raises(ValueError, match="must be one of"):
        load_task_state(tmp_path)


def test_start_writes_explicit_schema_version(tmp_path: Path) -> None:
    init_repo(tmp_path)

    start_task(tmp_path, task="initial")

    persisted = json.loads((tmp_path / ".agentkit" / "tasks" / "current.json").read_text(encoding="utf-8"))
    assert persisted["schema_version"] == 1


def test_unversioned_open_task_remains_usable_by_existing_lifecycle(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    start_task(tmp_path, task="legacy lifecycle")
    path = tmp_path / ".agentkit" / "tasks" / "current.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("schema_version")
    path.write_text(json.dumps(raw), encoding="utf-8")

    assert check(tmp_path)[0] == 0
    assert close_task(tmp_path)[0] == 0
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1


def test_update_changes_only_requested_context_with_idempotent_list_semantics(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(
        tmp_path,
        task="initial",
        plan="old plan",
        focus_notes=["existing"],
        focus_docs=["docs/design.md"],
    )
    before = load_task_state(tmp_path)
    assert before is not None

    update_task(
        tmp_path,
        set_task="refined",
        set_plan="new plan",
        add_focus_notes=["existing", "new"],
        remove_focus_notes=["absent"],
        add_focus_docs=["docs/design.md", "docs/workflow.md"],
        remove_focus_docs=["missing.md"],
        add_components=["cli", "cli"],
        remove_components=["missing"],
    )
    update_task(
        tmp_path,
        add_focus_notes=["new"],
        remove_focus_notes=["existing", "absent"],
        remove_focus_docs=["docs/design.md"],
        add_components=["cli"],
        remove_components=["core"],
    )

    after = load_task_state(tmp_path)
    assert after is not None
    assert after.task == "refined"
    assert after.plan == "new plan"
    assert after.focus_notes == ("new",)
    assert after.focus_docs == ("docs/workflow.md",)
    assert after.components == ("cli",)
    assert after.status == before.status
    assert after.diff_fingerprint == before.diff_fingerprint
    assert after.review_complete == before.review_complete
    assert after.review_fingerprint == before.review_fingerprint


def test_update_does_not_reopen_terminal_task(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(tmp_path, task="initial")
    state = load_task_state(tmp_path)
    assert state is not None
    write_task_state(tmp_path, state.with_changes(status="blocked", blocked_question="Need input"))

    update_task(tmp_path, set_plan="continue after input", add_focus_notes=["do not reopen"])

    updated = load_task_state(tmp_path)
    assert updated is not None
    assert updated.status == "blocked"
    assert updated.blocked_question == "Need input"
    assert updated.plan == "continue after input"


def test_update_requires_existing_task(tmp_path: Path) -> None:
    init_repo(tmp_path)

    with pytest.raises(ValueError, match="Run `agentkit start`"):
        update_task(tmp_path, set_task="missing")


def test_update_cli_exposes_domain_arguments(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    init_repo(tmp_path)
    start_task(tmp_path, task="initial")

    main(
        [
            "--repo",
            str(tmp_path),
            "update",
            "--set-task",
            "refined",
            "--set-plan",
            "plan",
            "--add-focus-note",
            "note",
            "--add-focus-doc",
            "docs/design.md",
            "--add-component",
            "cli",
            "--remove-component",
            "core",
        ]
    )

    output = capsys.readouterr().out
    state = load_task_state(tmp_path)
    assert state is not None
    assert "Task Updated" in output
    assert state.task == "refined"
    assert state.plan == "plan"
    assert state.focus_notes == ("note",)
    assert state.focus_docs == ("docs/design.md",)
    assert state.components == ("cli",)


def test_concurrent_task_state_writes_use_independent_atomic_files(tmp_path: Path) -> None:
    values = [f"task-{index}" for index in range(80)]

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(lambda value: write_task_state(tmp_path, TaskState(task=value)), values))

    state = load_task_state(tmp_path)
    assert state is not None
    assert state.task in values
    assert list((tmp_path / ".agentkit").rglob("*.tmp")) == []


def test_concurrent_receipt_writes_remain_valid_and_atomic(tmp_path: Path) -> None:
    fingerprint = "current-fingerprint"

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(
            pool.map(
                lambda index: write_receipt(
                    tmp_path,
                    "checks",
                    fingerprint,
                    {"status": "passed", "writer": str(index)},
                ),
                range(80),
            )
        )

    assert has_receipt(tmp_path, "checks", fingerprint)
    assert list((tmp_path / ".agentkit").rglob("*.tmp")) == []
