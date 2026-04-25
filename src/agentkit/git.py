from __future__ import annotations

import subprocess
from pathlib import Path


def changed_paths(repo: Path) -> list[str]:
    commands = [
        ["git", "diff", "--name-only"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    paths: set[str] = set()
    for command in commands:
        result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
        if result.returncode != 0:
            continue
        paths.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return sorted(paths)


def is_git_repo(repo: Path) -> bool:
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo, text=True, capture_output=True)
    return result.returncode == 0 and result.stdout.strip() == "true"
