from __future__ import annotations

import hashlib
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
        paths.update(
            path
            for path in (line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
            if not path.startswith(".agentkit/")
        )
    return sorted(paths)


def is_git_repo(repo: Path) -> bool:
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo, text=True, capture_output=True)
    return result.returncode == 0 and result.stdout.strip() == "true"


def diff_fingerprint(repo: Path) -> str:
    if not is_git_repo(repo):
        return "no-git"
    commands = [
        ["git", "diff", "--binary"],
        ["git", "diff", "--cached", "--binary"],
    ]
    digest = hashlib.sha256()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True)
    if head.returncode == 0:
        digest.update(b"HEAD\0")
        digest.update(head.stdout.strip().encode("utf-8"))
    for command in commands:
        result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
        if result.returncode == 0:
            digest.update(result.stdout.encode("utf-8"))
    result = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo, text=True, capture_output=True)
    if result.returncode == 0:
        for line in sorted(item.strip() for item in result.stdout.splitlines() if item.strip()):
            if line.replace("\\", "/").startswith(".agentkit/"):
                continue
            path = repo / line
            normalized = line.replace("\\", "/").encode("utf-8")
            digest.update(len(normalized).to_bytes(8, "big"))
            digest.update(normalized)
            if path.is_file():
                content = path.read_bytes()
                digest.update(len(content).to_bytes(8, "big"))
                digest.update(content)
    return digest.hexdigest()[:16]


def git_path(repo: Path, path: str) -> Path:
    result = subprocess.run(["git", "rev-parse", "--git-path", path], cwd=repo, text=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or f"Unable to resolve git path: {path}")
    resolved = Path(result.stdout.strip())
    if not resolved.is_absolute():
        resolved = repo / resolved
    return resolved
