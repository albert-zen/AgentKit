from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentkit.git import changed_paths, diff_fingerprint, is_git_repo
from agentkit.receipts import has_receipt
from agentkit.render import bullet, section
from agentkit.task_state import DEFAULT_TASK_ID, load_task_state


@dataclass(frozen=True)
class LifecycleSample:
    task_id: str
    state: str
    task: str
    diff_fingerprint: str
    open_changes: tuple[str, ...]
    missing_gates: tuple[str, ...]
    next_actions: tuple[str, ...]
    blocked_question: str | None = None

    @property
    def reminder_needed(self) -> bool:
        return self.state == "needs_work" and bool(self.next_actions)


def sample_lifecycle(repo: Path, task_id: str | None = None) -> LifecycleSample:
    task_name = task_id or DEFAULT_TASK_ID
    state = load_task_state(repo, task_name)
    current_changes = tuple(changed_paths(repo) if is_git_repo(repo) else [])
    current_fingerprint = diff_fingerprint(repo)

    if state is None:
        return LifecycleSample(
            task_id=task_name,
            state="no_task",
            task="",
            diff_fingerprint=current_fingerprint,
            open_changes=current_changes,
            missing_gates=(),
            next_actions=("Run `agentkit start --task \"...\"` before working on a new task.",),
        )

    status = str(state.get("status") or "open")
    task = str(state.get("task") or "")
    stored_fingerprint = state.get("diff_fingerprint")
    stale_closed_state = bool(current_changes and stored_fingerprint and stored_fingerprint != current_fingerprint)
    if status in {"completed", "blocked"} and stale_closed_state:
        closed_word = "blocked" if status == "blocked" else "completed"
        return LifecycleSample(
            task_id=task_name,
            state="needs_work",
            task=task,
            diff_fingerprint=current_fingerprint,
            open_changes=current_changes,
            missing_gates=(f"task state is stale because the diff changed after it was {closed_word}",),
            next_actions=(
                "Run `agentkit start --task \"...\"` for the new work, or restore the previous diff before relying on the closed state.",
                "If the new change cannot continue without human input, close as blocked with a recorded question.",
            ),
            blocked_question=str(state.get("blocked_question") or "") if status == "blocked" else None,
        )
    if status == "completed":
        return LifecycleSample(
            task_id=task_name,
            state="completed",
            task=task,
            diff_fingerprint=current_fingerprint,
            open_changes=current_changes,
            missing_gates=(),
            next_actions=("No action needed. This task is completed.",),
        )
    if status == "blocked":
        question = str(state.get("blocked_question") or "")
        return LifecycleSample(
            task_id=task_name,
            state="blocked",
            task=task,
            diff_fingerprint=current_fingerprint,
            open_changes=current_changes,
            missing_gates=(),
            next_actions=("Wait for human input before continuing this task.",),
            blocked_question=question,
        )

    missing: list[str] = []
    actions: list[str] = []
    if current_changes:
        missing.append("open changes still need commit or blocked handoff")
        actions.append("Commit the changes, or close as blocked with a recorded human question if progress is impossible.")
    if not has_receipt(repo, "checks", current_fingerprint):
        missing.append("missing check receipt for current diff")
        actions.append("Run `agentkit check` for the current diff.")

    has_current_review = bool(state.get("review_complete")) and state.get("review_fingerprint") == current_fingerprint
    if state.get("review_expected") and not has_current_review:
        missing.append("missing required review receipt for current diff")
        actions.append("Run the review loop, then close with `agentkit close --review-complete`.")

    if not missing:
        actions.append("Run `agentkit close --review-complete` if review was completed, or close normally if review is not required.")

    return LifecycleSample(
        task_id=task_name,
        state="needs_work" if missing else "ready_to_close",
        task=task,
        diff_fingerprint=current_fingerprint,
        open_changes=current_changes,
        missing_gates=tuple(missing),
        next_actions=tuple(dict.fromkeys(actions)),
    )


def render_status(sample: LifecycleSample) -> str:
    parts = [
        section("Lifecycle Status", [sample.state]),
        section("Task", [sample.task or sample.task_id]),
        section("Diff Fingerprint", [sample.diff_fingerprint]),
        section("Open Changes", bullet(sample.open_changes)),
        section("Missing Gates", bullet(sample.missing_gates)),
    ]
    if sample.blocked_question:
        parts.append(section("Blocked Human Question", [sample.blocked_question]))
    parts.append(section("Next Actions", bullet(sample.next_actions)))
    return "\n\n".join(parts)


def render_reminder(sample: LifecycleSample) -> str:
    if sample.state == "no_task":
        return section("AgentKit Reminder", ["No reminder needed. No AgentKit task is open."])
    if sample.state == "completed":
        return section("AgentKit Reminder", ["No reminder needed. Task is completed."])
    if sample.state == "blocked":
        return "\n\n".join(
            [
                section("Task Blocked", [sample.blocked_question or "Blocked on human input."]),
                section("Reminder State", ["No reminder will repeat until new human input or changed task state."]),
            ]
        )
    if sample.state == "ready_to_close":
        return "\n\n".join(
            [
                section("AgentKit Reminder", ["Task appears ready to close."]),
                section("Next Actions", bullet(sample.next_actions)),
            ]
        )
    return "\n\n".join(
        [
            section("AgentKit Reminder", [f"Task `{sample.task_id}` is still open and needs work."]),
            section("Missing Gates", bullet(sample.missing_gates)),
            section("Next Actions", bullet(sample.next_actions)),
        ]
    )


def status_text(repo: Path, task_id: str | None = None) -> str:
    return render_status(sample_lifecycle(repo, task_id))


def reminder_text(repo: Path, task_id: str | None = None) -> str:
    return render_reminder(sample_lifecycle(repo, task_id))
