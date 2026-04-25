from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentkit.commands import (
    check,
    close_task,
    docs_impact,
    generate_skill,
    init_repo,
    install_hooks,
    intent_guidance,
    lint_architecture,
    orient,
    review_guidance,
    start_task,
)


def main(argv: list[str] | None = None) -> None:
    argv = _normalize_global_repo_arg(list(argv if argv is not None else sys.argv[1:]))
    parser = argparse.ArgumentParser(prog="agentkit")
    parser.add_argument("--repo", default=".", help="Repository root. Defaults to current directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--force", action="store_true")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--component", action="append", default=[])
    start_parser.add_argument("--path", action="append", default=[])
    start_parser.add_argument("--task", default="")
    start_parser.add_argument("--plan", default="")

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
    subparsers.add_parser("check")
    subparsers.add_parser("skill")

    close_parser = subparsers.add_parser("close")
    close_parser.add_argument("--task-id")
    close_parser.add_argument("--blocked-question")
    close_parser.add_argument("--review-complete", action="store_true")
    close_parser.add_argument("--skip-review-reason")

    hooks_parser = subparsers.add_parser("install-hooks")
    hooks_parser.add_argument("--force", action="store_true")

    review_parser = subparsers.add_parser("review-guidance")
    review_parser.add_argument("--component", action="append", default=[])
    review_parser.add_argument("--path", action="append", default=[])
    review_parser.add_argument("--task", default="")

    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()

    try:
        if args.command == "init":
            print(init_repo(repo, force=args.force))
        elif args.command == "start":
            print(start_task(repo, component_names=args.component, paths=args.path, task=args.task, plan=args.plan))
        elif args.command == "orient":
            print(orient(repo, component_names=args.component, paths=args.path, task=args.task))
        elif args.command == "intent-guidance":
            print(intent_guidance(repo, component_name=args.component, change_type=args.change_type))
        elif args.command == "docs-impact":
            print(docs_impact(repo, paths=args.path or None))
        elif args.command == "lint-architecture":
            code, output = lint_architecture(repo)
            print(output)
            raise SystemExit(code)
        elif args.command == "check":
            code, output = check(repo)
            print(output)
            raise SystemExit(code)
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
