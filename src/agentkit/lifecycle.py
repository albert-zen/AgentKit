from __future__ import annotations

from pathlib import Path

from agentkit.render import bullet, section
from agentkit.rules import LifecycleEvaluation, evaluate_lifecycle


INTENT_REMINDER = (
    "Preserve what humans have already decided. Persist what future agents need to know. "
    "Ask when a durable decision is missing."
)

LifecycleSample = LifecycleEvaluation


def sample_lifecycle(repo: Path, task_id: str | None = None) -> LifecycleSample:
    return evaluate_lifecycle(repo, task_id)


def render_status(sample: LifecycleSample) -> str:
    rule_lines = [
        f"{result.rule_id}: {result.outcome.value} — {result.reason}"
        for result in sample.rule_results
    ]
    parts = [
        section("Lifecycle Status", [sample.state]),
        section("Task", [sample.task or sample.task_id]),
        section("Focus Docs", bullet(sample.focus_docs)),
        section("Focus Notes", bullet(sample.focus_notes)),
        section("Diff Fingerprint", [sample.diff_fingerprint]),
        section("Open Changes", bullet(sample.open_changes)),
        section("Rule Results", bullet(rule_lines)),
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
    if not sample.reminder_enabled:
        return section("AgentKit Reminder", ["No reminder selected for this lifecycle state by repository policy."])
    if sample.state == "ready_to_close":
        return "\n\n".join(
            [
                section(
                    "AgentKit Reminder",
                    [
                        "Task appears ready to close.",
                        INTENT_REMINDER,
                        "Before finishing, decide whether this work changed durable intent, behavior, boundaries, workflows, or testing expectations. If it did, persist the change in docs or tests; if not, a short no-persistence-needed note is enough.",
                    ],
                ),
                section("Next Actions", bullet(sample.next_actions)),
            ]
        )
    return "\n\n".join(
        [
            section("AgentKit Reminder", [f"Task `{sample.task_id}` is still open and needs work.", INTENT_REMINDER]),
            section("Missing Gates", bullet(sample.missing_gates)),
            section("Next Actions", bullet(sample.next_actions)),
        ]
    )


def status_text(repo: Path, task_id: str | None = None) -> str:
    return render_status(sample_lifecycle(repo, task_id))


def reminder_text(repo: Path, task_id: str | None = None) -> str:
    return render_reminder(sample_lifecycle(repo, task_id))
