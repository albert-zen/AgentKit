from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from agentkit.commands import check, close_task, init_repo, start_task
from agentkit.codex import codex_stop_hook
from agentkit.lifecycle import reminder_text, status_text
from agentkit.git import diff_fingerprint
from agentkit.receipts import receipt_path
from agentkit.rules import RuleOutcome, evaluate_lifecycle
from agentkit.watch import watch_task


def _committed_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "agentkit@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "AgentKit"], cwd=path, check=True)
    init_repo(path)
    (path / "src").mkdir()
    (path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=path, check=True, capture_output=True)


def test_named_rules_explain_current_lifecycle_failures(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])

    evaluation = evaluate_lifecycle(tmp_path)
    results = {result.rule_id: result for result in evaluation.rule_results}

    assert tuple(results) == (
        "working_tree_clean",
        "check_receipt_current",
        "review_addressed",
        "blocked_question_recorded",
    )
    assert results["working_tree_clean"].outcome is RuleOutcome.PASS
    assert results["check_receipt_current"].outcome is RuleOutcome.FAIL
    assert results["check_receipt_current"].reason
    assert results["check_receipt_current"].next_action == "Run `agentkit check` for the current diff."
    assert results["review_addressed"].outcome is RuleOutcome.FAIL
    assert results["blocked_question_recorded"].outcome is RuleOutcome.NOT_APPLICABLE


def test_current_receipt_and_review_evaluate_once_for_close(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    assert check(tmp_path)[0] == 0

    preview = evaluate_lifecycle(tmp_path, review_complete=True, transition="complete")
    assert preview.blocking_failures == ()
    code, _ = close_task(tmp_path, review_complete=True)

    assert code == 0
    completed = evaluate_lifecycle(tmp_path)
    assert completed.state == "completed"
    assert all(not result.failed_and_blocking for result in completed.rule_results)


def test_clean_tree_evidence_becomes_stale_after_head_changes(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    assert check(tmp_path)[0] == 0
    assert close_task(tmp_path, review_complete=True)[0] == 0

    (tmp_path / "src" / "example.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "later head"], cwd=tmp_path, check=True, capture_output=True)

    evaluation = evaluate_lifecycle(tmp_path)
    results = {result.rule_id: result for result in evaluation.rule_results}
    assert evaluation.state == "needs_work"
    assert results["check_receipt_current"].outcome is RuleOutcome.FAIL
    assert results["review_addressed"].outcome is RuleOutcome.FAIL


@pytest.mark.parametrize(
    "receipt_content",
    [
        "",
        '{"status": "failed"}',
        '{"status": "passed", "fingerprint": "another-diff"}',
    ],
)
def test_malformed_or_nonpassing_check_receipt_is_not_evidence(
    tmp_path: Path, receipt_content: str
) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    fingerprint = diff_fingerprint(tmp_path)
    path = receipt_path(tmp_path, "checks", fingerprint)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(receipt_content, encoding="utf-8")

    result = {
        item.rule_id: item for item in evaluate_lifecycle(tmp_path).rule_results
    }["check_receipt_current"]

    assert result.outcome is RuleOutcome.FAIL


def test_blocked_transition_is_explained_by_named_question_rule(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])

    missing = evaluate_lifecycle(tmp_path, transition="blocked", blocked_question="")
    recorded = evaluate_lifecycle(tmp_path, transition="blocked", blocked_question="Need a decision")

    missing_rule = {item.rule_id: item for item in missing.rule_results}["blocked_question_recorded"]
    recorded_rule = {item.rule_id: item for item in recorded.rule_results}["blocked_question_recorded"]
    assert missing_rule.outcome is RuleOutcome.FAIL
    assert missing_rule.failed_and_blocking
    assert recorded_rule.outcome is RuleOutcome.PASS
    assert not recorded_rule.failed_and_blocking


def test_repository_can_make_clean_tree_rule_advisory(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    raw = yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))
    raw["rules"] = {"working_tree_clean": {"severity": "warning"}}
    (tmp_path / "agentkit.yml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    subprocess.run(["git", "add", "agentkit.yml"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "configure rules"], cwd=tmp_path, check=True, capture_output=True)
    start_task(tmp_path, component_names=["core"])
    (tmp_path / "notes.md").write_text("open\n", encoding="utf-8")
    assert check(tmp_path)[0] == 0

    evaluation = evaluate_lifecycle(tmp_path, transition="complete", review_complete=True)
    clean_rule = {item.rule_id: item for item in evaluation.rule_results}["working_tree_clean"]

    assert clean_rule.outcome is RuleOutcome.FAIL
    assert not clean_rule.failed_and_blocking
    assert evaluation.blocking_failures == ()
    assert close_task(tmp_path, review_complete=True)[0] == 0


def test_repository_can_disable_check_gate_without_disabling_evidence_invariant(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    raw = yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))
    raw["rules"] = {"check_receipt_current": {"enabled": False}}
    (tmp_path / "agentkit.yml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    subprocess.run(["git", "add", "agentkit.yml"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "configure rules"], cwd=tmp_path, check=True, capture_output=True)
    start_task(tmp_path, component_names=["core"])

    evaluation = evaluate_lifecycle(tmp_path, transition="complete", review_complete=True)
    receipt_rule = {item.rule_id: item for item in evaluation.rule_results}["check_receipt_current"]

    assert receipt_rule.outcome is RuleOutcome.NOT_APPLICABLE
    assert close_task(tmp_path, review_complete=True)[0] == 0


def test_review_skip_policy_can_disallow_skip(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    raw = yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))
    raw["rules"] = {"review_addressed": {"allow_skip": False}}
    raw["review"]["require_for"] = ["core"]
    (tmp_path / "agentkit.yml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    subprocess.run(["git", "add", "agentkit.yml"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "configure rules"], cwd=tmp_path, check=True, capture_output=True)
    start_task(tmp_path, component_names=["core"])
    assert check(tmp_path)[0] == 0

    evaluation = evaluate_lifecycle(
        tmp_path, transition="complete", skip_review_reason="claimed low risk"
    )

    review_rule = {item.rule_id: item for item in evaluation.rule_results}["review_addressed"]
    assert review_rule.outcome is RuleOutcome.FAIL
    assert "does not permit skips" in review_rule.reason
    assert close_task(tmp_path, skip_review_reason="claimed low risk")[0] == 1


def test_status_exposes_named_rule_results_and_reminder_selection(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    raw = yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))
    raw["reminders"] = {"open_task": False}
    (tmp_path / "agentkit.yml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    subprocess.run(["git", "add", "agentkit.yml"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "configure reminders"], cwd=tmp_path, check=True, capture_output=True)
    start_task(tmp_path, component_names=["core"])

    evaluation = evaluate_lifecycle(tmp_path)

    assert evaluation.state == "needs_work"
    assert not evaluation.reminder_needed
    assert "check_receipt_current: fail" in status_text(tmp_path)
    assert "No reminder selected" in reminder_text(tmp_path)
    assert codex_stop_hook(tmp_path, "{}")[1] == ""
    outputs: list[str] = []
    assert watch_task(tmp_path, once=True, output=outputs.append) == 0
    assert outputs == []


def test_watcher_suppresses_ready_to_close_node(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    raw = yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))
    raw["rules"] = {
        "check_receipt_current": {"enabled": False},
        "review_addressed": {"enabled": False},
    }
    raw["reminders"] = {"ready_to_close": False}
    (tmp_path / "agentkit.yml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    subprocess.run(["git", "add", "agentkit.yml"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "configure reminders"], cwd=tmp_path, check=True, capture_output=True)
    start_task(tmp_path, component_names=["core"])
    outputs: list[str] = []

    assert evaluate_lifecycle(tmp_path).state == "ready_to_close"
    assert watch_task(tmp_path, once=True, output=outputs.append) == 0
    assert outputs == []


def test_watcher_suppresses_stale_terminal_node(tmp_path: Path) -> None:
    _committed_repo(tmp_path)
    raw = yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))
    raw["reminders"] = {"stale_terminal": False}
    (tmp_path / "agentkit.yml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    subprocess.run(["git", "add", "agentkit.yml"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "configure reminders"], cwd=tmp_path, check=True, capture_output=True)
    start_task(tmp_path, component_names=["core"])
    assert check(tmp_path)[0] == 0
    assert close_task(tmp_path, review_complete=True)[0] == 0
    (tmp_path / "src" / "example.py").write_text("VALUE = 2\n", encoding="utf-8")
    outputs: list[str] = []

    evaluation = evaluate_lifecycle(tmp_path)
    assert evaluation.stale_terminal
    assert not evaluation.reminder_needed
    assert watch_task(tmp_path, once=True, output=outputs.append) == 0
    assert outputs == []
