from __future__ import annotations

import subprocess
from pathlib import Path

from agentkit.commands import check, close_task, init_repo, start_task
from agentkit.git import diff_fingerprint
from agentkit.lifecycle import sample_lifecycle
from agentkit.receipts import receipt_path


def _committed_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "agentkit@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "AgentKit"], cwd=path, check=True)
    init_repo(path)
    (path / "src").mkdir()
    (path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=path, check=True, capture_output=True)


def test_open_task_characterization_requires_current_check_and_review(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])

    before_check = sample_lifecycle(tmp_path)
    assert before_check.state == "needs_work"
    assert before_check.missing_gates == (
        "missing check receipt for current diff",
        "missing required review receipt for current diff",
    )

    code, _ = check(tmp_path)
    assert code == 0
    after_check = sample_lifecycle(tmp_path)
    assert after_check.state == "needs_work"
    assert after_check.missing_gates == ("missing required review receipt for current diff",)


def test_dirty_task_characterization_requires_clean_tree_and_new_check(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    (tmp_path / "src" / "example.py").write_text("VALUE = 2\n", encoding="utf-8")

    sample = sample_lifecycle(tmp_path)

    assert sample.state == "needs_work"
    assert sample.missing_gates == (
        "open changes still need commit or blocked handoff",
        "missing check receipt for current diff",
        "missing required review receipt for current diff",
    )


def test_completion_characterization_accepts_current_check_and_review(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    assert check(tmp_path)[0] == 0

    code, output = close_task(tmp_path, review_complete=True)

    assert code == 0
    assert "completed" in output
    assert sample_lifecycle(tmp_path).state == "completed"


def test_completed_characterization_stays_terminal_if_same_diff_receipt_is_deleted(
    tmp_path: Path,
) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    assert check(tmp_path)[0] == 0
    assert close_task(tmp_path, review_complete=True)[0] == 0
    receipt_path(tmp_path, "checks", diff_fingerprint(tmp_path)).unlink()

    completed = sample_lifecycle(tmp_path)

    assert completed.state == "completed"
    results = {item.rule_id: item.outcome.value for item in completed.rule_results}
    assert results["check_receipt_current"] == "not_applicable"
    assert results["review_addressed"] == "not_applicable"


def test_blocked_characterization_records_question_and_detects_stale_diff(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    (tmp_path / "notes.md").write_text("first\n", encoding="utf-8")

    code, output = close_task(tmp_path, blocked_question="Which policy should apply?")
    assert code == 0
    assert "blocked" in output
    blocked = sample_lifecycle(tmp_path)
    assert blocked.state == "blocked"
    assert blocked.blocked_question == "Which policy should apply?"

    (tmp_path / "notes.md").write_text("second\n", encoding="utf-8")
    stale = sample_lifecycle(tmp_path)
    assert stale.state == "needs_work"
    assert stale.missing_gates == ("task state is stale because the diff changed after it was blocked",)
