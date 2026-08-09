from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentkit.commands import (
    check,
    close_task,
    codex_stop_hook,
    docs_impact,
    doctor,
    generate_skill,
    install_codex_watchdog,
    init_repo,
    install_hooks,
    intent_guidance,
    lint_architecture,
    lint_maintainability,
    orient,
    remind_task,
    review_guidance,
    start_task,
    status_task,
    update_task,
    upgrade_repo,
)
from agentkit.watch import watch_task


def main(argv: list[str] | None = None) -> None:
    argv = _normalize_global_repo_arg(list(argv if argv is not None else sys.argv[1:]))
    parser = argparse.ArgumentParser(prog="agentkit")
    parser.add_argument("--repo", default=".", help="Repository root. Defaults to current directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument(
        "--preset",
        help="Materialize a versioned policy preset, currently recommended-v1.",
    )

    upgrade_parser = subparsers.add_parser("upgrade")
    upgrade_parser.add_argument("--dry-run", action="store_true")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--component", action="append", default=[])
    start_parser.add_argument("--path", action="append", default=[])
    start_parser.add_argument("--task", default="")
    start_parser.add_argument("--plan", default="")
    start_parser.add_argument("--focus-note", action="append", default=[])
    start_parser.add_argument("--focus-doc", action="append", default=[])

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--task-id")
    update_parser.add_argument("--set-task", help="Replace the task statement.")
    update_parser.add_argument("--set-plan", help="Replace the implementation plan.")
    update_parser.add_argument("--add-focus-note", action="append", default=[], help="Add once; repeatable.")
    update_parser.add_argument("--remove-focus-note", action="append", default=[], help="Remove if present; repeatable.")
    update_parser.add_argument("--add-focus-doc", action="append", default=[], help="Add once; repeatable.")
    update_parser.add_argument("--remove-focus-doc", action="append", default=[], help="Remove if present; repeatable.")
    update_parser.add_argument("--add-component", action="append", default=[], help="Add once; repeatable.")
    update_parser.add_argument("--remove-component", action="append", default=[], help="Remove if present; repeatable.")

    orient_parser = subparsers.add_parser("orient")
    orient_parser.add_argument("--component", action="append", default=[])
    orient_parser.add_argument("--path", action="append", default=[])
    orient_parser.add_argument("--task", default="")

    intent_parser = subparsers.add_parser("intent-guidance")
    intent_parser.add_argument("--component")
    intent_parser.add_argument("--change-type")

    impact_parser = subparsers.add_parser("docs-impact")
    impact_parser.add_argument("--path", action="append", default=[])

    subparsers.add_parser("lint-architecture")
    subparsers.add_parser("lint-maintainability")
    subparsers.add_parser("check")
    subparsers.add_parser("doctor")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--task-id")
    remind_parser = subparsers.add_parser("remind")
    remind_parser.add_argument("--task-id")
    subparsers.add_parser("skill")

    close_parser = subparsers.add_parser("close")
    close_parser.add_argument("--task-id")
    close_parser.add_argument("--blocked-question")
    close_parser.add_argument("--review-complete", action="store_true")
    close_parser.add_argument("--skip-review-reason")

    hooks_parser = subparsers.add_parser("install-hooks")
    hooks_parser.add_argument("--force", action="store_true")

    codex_watchdog_parser = subparsers.add_parser("install-codex-watchdog")
    codex_watchdog_scope = codex_watchdog_parser.add_mutually_exclusive_group()
    codex_watchdog_scope.add_argument("--repo-local", action="store_true", help="Install into <repo>/.codex")
    codex_watchdog_scope.add_argument("--user-local", action="store_true", help="Install into CODEX_HOME or ~/.codex")
    codex_watchdog_parser.add_argument("--force", action="store_true")
    codex_watchdog_parser.add_argument("--log-path", default=".agentkit/codex-stop-hook.log")

    codex_stop_parser = subparsers.add_parser("codex-stop-hook")
    codex_stop_parser.add_argument("--log")

    watch_parser = subparsers.add_parser("watch")
    watch_parser.add_argument("--interval", type=float, default=30.0)
    watch_parser.add_argument("--once", action="store_true")

    review_parser = subparsers.add_parser("review-guidance")
    review_parser.add_argument("--component", action="append", default=[])
    review_parser.add_argument("--path", action="append", default=[])
    review_parser.add_argument("--task", default="")

    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()

    try:
        if args.command == "init":
            print(init_repo(repo, force=args.force, preset=args.preset))
        elif args.command == "upgrade":
            code, output = upgrade_repo(repo, dry_run=args.dry_run)
            print(output)
            if code:
                raise SystemExit(code)
        elif args.command == "start":
            print(
                start_task(
                    repo,
                    component_names=args.component,
                    paths=args.path,
                    task=args.task,
                    plan=args.plan,
                    focus_notes=args.focus_note,
                    focus_docs=args.focus_doc,
                )
            )
        elif args.command == "orient":
            print(orient(repo, component_names=args.component, paths=args.path, task=args.task))
        elif args.command == "update":
            print(
                update_task(
                    repo,
                    task_id=args.task_id,
                    set_task=args.set_task,
                    set_plan=args.set_plan,
                    add_focus_notes=args.add_focus_note,
                    remove_focus_notes=args.remove_focus_note,
                    add_focus_docs=args.add_focus_doc,
                    remove_focus_docs=args.remove_focus_doc,
                    add_components=args.add_component,
                    remove_components=args.remove_component,
                )
            )
        elif args.command == "intent-guidance":
            print(intent_guidance(repo, component_name=args.component, change_type=args.change_type))
        elif args.command == "docs-impact":
            print(docs_impact(repo, paths=args.path or None))
        elif args.command == "lint-architecture":
            code, output = lint_architecture(repo)
            print(output)
            raise SystemExit(code)
        elif args.command == "lint-maintainability":
            code, output = lint_maintainability(repo)
            print(output)
            raise SystemExit(code)
        elif args.command == "check":
            code, output = check(repo)
            print(output)
            raise SystemExit(code)
        elif args.command == "doctor":
            code, output = doctor(repo)
            print(output)
            raise SystemExit(code)
        elif args.command == "status":
            print(status_task(repo, task_id=args.task_id))
        elif args.command == "remind":
            print(remind_task(repo, task_id=args.task_id))
        elif args.command == "close":
            code, output = close_task(
                repo,
                task_id=args.task_id,
                blocked_question=args.blocked_question,
                review_complete=args.review_complete,
                skip_review_reason=args.skip_review_reason,
            )
            print(output)
            raise SystemExit(code)
        elif args.command == "install-hooks":
            print(install_hooks(repo, force=args.force))
        elif args.command == "install-codex-watchdog":
            scope = "user" if args.user_local else "repo"
            print(install_codex_watchdog(repo, scope=scope, force=args.force, log_path=args.log_path))
        elif args.command == "codex-stop-hook":
            code, output = codex_stop_hook(repo, sys.stdin.read(), log_path=args.log)
            if output:
                print(output)
            raise SystemExit(code)
        elif args.command == "watch":
            raise SystemExit(watch_task(repo, interval_seconds=args.interval, once=args.once))
        elif args.command == "review-guidance":
            print(review_guidance(repo, component_names=args.component, paths=args.path, task=args.task))
        elif args.command == "skill":
            print(generate_skill(repo))
    except Exception as exc:
        print(f"agentkit error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

def _normalize_global_repo_arg(argv: list[str]) -> list[str]:
    if "--repo" in argv:
        index = argv.index("--repo")
        if index > 0 and index + 1 < len(argv):
            repo_pair = [argv.pop(index), argv.pop(index)]
            return repo_pair + argv
    for index, item in enumerate(argv):
        if item.startswith("--repo=") and index > 0:
            repo_arg = argv.pop(index)
            return [repo_arg] + argv
    return argv


if __name__ == "__main__":
    main()
