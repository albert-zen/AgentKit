from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentkit.config import AgentKitConfig, load_config
from agentkit.git import changed_paths, diff_fingerprint, is_git_repo
from agentkit.receipts import has_receipt
from agentkit.policy import LifecycleRuleConfig
from agentkit.task_state import DEFAULT_TASK_ID, TaskState, load_task_state


class RuleOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    outcome: RuleOutcome
    reason: str
    next_action: str | None = None
    blocking: bool = True

    @property
    def failed_and_blocking(self) -> bool:
        return self.outcome is RuleOutcome.FAIL and self.blocking


@dataclass(frozen=True)
class LifecycleEvaluation:
    task_id: str
    state: str
    task: str
    diff_fingerprint: str
    open_changes: tuple[str, ...]
    rule_results: tuple[RuleResult, ...]
    missing_gates: tuple[str, ...]
    next_actions: tuple[str, ...]
    focus_notes: tuple[str, ...] = ()
    focus_docs: tuple[str, ...] = ()
    blocked_question: str | None = None
    stale_terminal: bool = False
    reminder_enabled: bool = True

    @property
    def blocking_failures(self) -> tuple[RuleResult, ...]:
        return tuple(result for result in self.rule_results if result.failed_and_blocking)

    @property
    def reminder_needed(self) -> bool:
        return self.reminder_enabled and self.state in {"needs_work", "ready_to_close"}


def evaluate_lifecycle(
    repo: Path,
    task_id: str | None = None,
    *,
    transition: str = "status",
    review_complete: bool = False,
    skip_review_reason: str | None = None,
    blocked_question: str | None = None,
    task_state: TaskState | None = None,
    config: AgentKitConfig | None = None,
) -> LifecycleEvaluation:
    if transition not in {"status", "complete", "blocked"}:
        raise ValueError(f"Unknown lifecycle transition: {transition}")
    task_name = task_id or DEFAULT_TASK_ID
    state = task_state if task_state is not None else load_task_state(repo, task_name)
    policy = config or load_config(repo)
    current_changes = tuple(changed_paths(repo) if is_git_repo(repo) else [])
    current_fingerprint = diff_fingerprint(repo)

    if state is None:
        results = tuple(
            _not_applicable(rule_id, policy.rules[rule_id], "No lifecycle task is open.")
            for rule_id in policy.rules
        )
        return LifecycleEvaluation(
            task_id=task_name,
            state="no_task",
            task="",
            diff_fingerprint=current_fingerprint,
            open_changes=current_changes,
            rule_results=results,
            missing_gates=(),
            next_actions=(
                "Run `agentkit start --task \"...\"` before repository-changing work that needs lifecycle tracking.",
            ),
            reminder_enabled=False,
        )

    effective = state.with_changes(
        review_complete=state.review_complete or review_complete,
        review_fingerprint=current_fingerprint if review_complete else state.review_fingerprint,
        skip_review_reason=skip_review_reason if skip_review_reason is not None else state.skip_review_reason,
        skip_review_fingerprint=current_fingerprint if skip_review_reason is not None else state.skip_review_fingerprint,
        blocked_question=blocked_question if transition == "blocked" else state.blocked_question,
    )
    terminal_current = bool(
        transition == "status"
        and state.status == "completed"
        and (not state.diff_fingerprint or state.diff_fingerprint == current_fingerprint)
    )
    if terminal_current:
        rule_transition = "terminal"
    elif transition == "status" and state.status == "blocked":
        rule_transition = "blocked"
    else:
        rule_transition = transition
    rule_results = (
        _working_tree_clean(policy.rules["working_tree_clean"], current_changes, rule_transition),
        _check_receipt_current(policy.rules["check_receipt_current"], repo, current_fingerprint, rule_transition),
        _review_addressed(
            policy.rules["review_addressed"], effective, current_fingerprint, rule_transition
        ),
        _blocked_question_recorded(policy.rules["blocked_question_recorded"], effective, rule_transition),
    )

    persisted_status = state.status or "open"
    terminal = persisted_status in {"completed", "blocked"}
    stale_terminal = bool(terminal and state.diff_fingerprint and state.diff_fingerprint != current_fingerprint)
    blocking_failures = tuple(result for result in rule_results if result.failed_and_blocking)

    if stale_terminal:
        closed_word = "blocked" if persisted_status == "blocked" else "completed"
        lifecycle_state = "needs_work"
        missing = (f"task state is stale because the diff changed after it was {closed_word}",)
        actions = (
            "Run `agentkit start --task \"...\"` for the new repository-changing work, or restore the previous diff before relying on the closed state.",
            "If the new change cannot continue without human input, close as blocked with a recorded question.",
        )
    elif persisted_status == "completed" and not blocking_failures:
        lifecycle_state = "completed"
        missing = ()
        actions = ("No action needed. This task is completed.",)
    elif persisted_status == "blocked" and not blocking_failures:
        lifecycle_state = "blocked"
        missing = ()
        actions = ("Wait for human input before continuing this task.",)
    else:
        missing = tuple(result.reason for result in blocking_failures)
        actions = tuple(
            dict.fromkeys(result.next_action for result in blocking_failures if result.next_action)
        )
        if blocking_failures:
            lifecycle_state = "needs_work"
        else:
            lifecycle_state = "ready_to_close"
            actions = (_close_action(effective, policy),)

    reminder_enabled = _reminder_enabled(policy, lifecycle_state, stale_terminal)
    return LifecycleEvaluation(
        task_id=task_name,
        state=lifecycle_state,
        task=state.task,
        diff_fingerprint=current_fingerprint,
        open_changes=current_changes,
        rule_results=rule_results,
        missing_gates=missing,
        next_actions=actions,
        focus_notes=state.focus_notes,
        focus_docs=state.focus_docs,
        blocked_question=effective.blocked_question if persisted_status == "blocked" or transition == "blocked" else None,
        stale_terminal=stale_terminal,
        reminder_enabled=reminder_enabled,
    )


def _working_tree_clean(
    policy: LifecycleRuleConfig, open_changes: tuple[str, ...], transition: str
) -> RuleResult:
    if transition == "blocked":
        return _not_applicable("working_tree_clean", policy, "Blocked handoff may preserve open changes.")
    if transition == "terminal":
        return _not_applicable("working_tree_clean", policy, "Current completed state does not reopen terminal gates.")
    if not policy.enabled:
        return _not_applicable("working_tree_clean", policy, "Rule disabled by repository policy.")
    if not open_changes:
        return _passed("working_tree_clean", policy, "Working tree has no open changes.")
    return _failed(
        "working_tree_clean",
        policy,
        "open changes still need commit or blocked handoff",
        "Commit the changes, or close as blocked with a recorded human question if progress is impossible.",
    )


def _check_receipt_current(
    policy: LifecycleRuleConfig, repo: Path, fingerprint: str, transition: str
) -> RuleResult:
    if transition == "blocked":
        return _not_applicable("check_receipt_current", policy, "Blocked handoff does not require checks to pass.")
    if transition == "terminal":
        return _not_applicable("check_receipt_current", policy, "Current completed state does not reopen terminal evidence.")
    if not policy.enabled:
        return _not_applicable("check_receipt_current", policy, "Rule disabled by repository policy.")
    if has_receipt(repo, "checks", fingerprint):
        return _passed("check_receipt_current", policy, "A successful check receipt matches the current diff fingerprint.")
    return _failed(
        "check_receipt_current",
        policy,
        "missing check receipt for current diff",
        "Run `agentkit check` for the current diff.",
    )


def _review_addressed(
    policy: LifecycleRuleConfig, state: TaskState, fingerprint: str, transition: str
) -> RuleResult:
    if transition == "blocked":
        return _not_applicable("review_addressed", policy, "Blocked handoff does not require review completion.")
    if transition == "terminal":
        return _not_applicable("review_addressed", policy, "Current completed state does not reopen terminal evidence.")
    if not policy.enabled:
        return _not_applicable("review_addressed", policy, "Rule disabled by repository policy.")
    if not state.review_expected:
        return _not_applicable("review_addressed", policy, "Review is not required for this task.")
    if state.review_complete and state.review_fingerprint == fingerprint:
        return _passed("review_addressed", policy, "Review completion is acknowledged for the current diff fingerprint.")
    if policy.allow_skip and state.skip_review_reason and state.skip_review_fingerprint == fingerprint:
        return _passed("review_addressed", policy, "An allowed low-risk review skip is recorded for the current diff fingerprint.")
    if state.skip_review_reason and state.skip_review_fingerprint == fingerprint and not policy.allow_skip:
        reason = "review skip is recorded but repository policy does not permit skips"
    else:
        reason = "missing required review receipt for current diff"
    return _failed(
        "review_addressed",
        policy,
        reason,
        "Run the review loop, then close with `agentkit close --review-complete`.",
    )


def _blocked_question_recorded(
    policy: LifecycleRuleConfig, state: TaskState, transition: str
) -> RuleResult:
    applies = transition == "blocked" or state.status == "blocked"
    if not applies:
        return _not_applicable("blocked_question_recorded", policy, "No blocked transition is being evaluated.")
    if not policy.enabled:
        return _not_applicable("blocked_question_recorded", policy, "Rule disabled by repository policy.")
    if state.blocked_question and state.blocked_question.strip():
        return _passed("blocked_question_recorded", policy, "A human question explains the blocked handoff.")
    return _failed(
        "blocked_question_recorded",
        policy,
        "blocked handoff requires a recorded human question",
        "Pass `--blocked-question \"...\"` with the decision needed from the human.",
    )


def _passed(rule_id: str, policy: LifecycleRuleConfig, reason: str) -> RuleResult:
    return RuleResult(rule_id, RuleOutcome.PASS, reason, blocking=policy.severity == "error")


def _failed(rule_id: str, policy: LifecycleRuleConfig, reason: str, action: str) -> RuleResult:
    return RuleResult(rule_id, RuleOutcome.FAIL, reason, action, blocking=policy.severity == "error")


def _not_applicable(rule_id: str, policy: LifecycleRuleConfig, reason: str) -> RuleResult:
    return RuleResult(rule_id, RuleOutcome.NOT_APPLICABLE, reason, blocking=policy.severity == "error")


def _close_action(state: TaskState, config: AgentKitConfig) -> str:
    review_policy = config.rules["review_addressed"]
    if state.review_expected and review_policy.enabled:
        if review_policy.allow_skip:
            return (
                "Run `agentkit close --review-complete` if review was completed, or "
                "`agentkit close --skip-review-reason \"...\"` for low-risk work."
            )
        return "Run `agentkit close --review-complete` after completing review."
    return "Run `agentkit close`."


def _reminder_enabled(config: AgentKitConfig, state: str, stale_terminal: bool) -> bool:
    if stale_terminal:
        return config.reminders.stale_terminal
    if state == "ready_to_close":
        return config.reminders.ready_to_close
    if state == "needs_work":
        return config.reminders.open_task
    return False
